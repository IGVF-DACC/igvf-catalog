import csv
import gzip
import json
import math
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from adapters.base import BaseAdapter
from adapters.helpers import build_regulatory_region_id, get_file_fileset_by_accession_in_arangodb
from adapters.gene_validator import GeneValidator
from adapters.writer import Writer

_CRISPR_E2G_DEFINITIONS_PATH = (
    Path(__file__).resolve().parents[1] /
    'data_loading_support_files' /
    'IGVF_E2G_CRISPR' /
    'igvf_e2g_crispr_definitions.json'
)


def _load_crispr_e2g_definitions() -> Tuple[dict, dict]:
    with open(_CRISPR_E2G_DEFINITIONS_PATH, encoding='utf-8') as definitions_file:
        raw_definitions = json.load(definitions_file)
    file_config = raw_definitions.pop('files', {})
    layouts = dict(raw_definitions)
    return layouts, file_config


# Layout specs and per-accession parser config live in igvf_e2g_crispr_definitions.json.
CRISPR_E2G_LAYOUTS, CRISPR_E2G_FILE_CONFIG = _load_crispr_e2g_definitions()


# name_hg38 / name-style intervals: chr:start-end.
_HG38_INTERVAL_RE = re.compile(
    r'^(?P<c>chr[^:]+):(?P<s1>\d+)-(?P<s2>\d+)$'
)

# Colmap keys that map row columns but are not edge metric properties.
_IGVF_E2G_LAYOUT_KEYS = frozenset({
    'readout_gene', 'promoter_gene', 'chr', 'start', 'end',
    'name_hg38', 'element_type', 'promoter_gene_map', 'source_annotation',
    'source_annotation_map',
})


class IGVFE2GCRISPR(BaseAdapter):

    ALLOWED_LABELS = [
        'genomic_element',
        'genomic_element_gene'
    ]
    SOURCE = 'IGVF'
    COLLECTION_LABEL = 'regulatory element effect on gene expression'
    SIGNIFICANCE_THRESHOLD = 0.05
    DEFAULT_MAX_LOG10_PVALUE = 240  # encode_E2G_CRISPR_adapter fallback

    @staticmethod
    def _normalize_ensembl_gene_id(gene_id: str) -> str:
        if not gene_id:
            return gene_id
        normalized = gene_id.strip().rstrip(');,')
        # Accept IDs like ENSG00000174038.13 by stripping version suffix.
        normalized = re.sub(
            r'^(ENSG[0-9]{11}(?:_PAR_Y)?)\.[0-9]+$',
            r'\1',
            normalized
        )
        return normalized

    @staticmethod
    def _parse_bool(value):
        if value is None:
            return None
        normalized = str(value).strip().lower()
        if normalized in {'true', 't', '1'}:
            return True
        if normalized in {'false', 'f', '0'}:
            return False
        return None

    def _row_load_error(self, message: str) -> None:
        raise ValueError(f'{self.file_accession}: {message}')

    def _file_config(self) -> dict:
        config = CRISPR_E2G_FILE_CONFIG.get(self.file_accession, {})
        if not config:
            self.logger.warning(
                'No CRISPR E2G file config for accession %s; '
                'using promoter/enhancer per-row heuristic. Add this file under '
                '"files" in igvf_e2g_crispr_definitions.json.',
                self.file_accession,
            )
        return config

    def _layout(self) -> dict:
        config = self._file_config()
        layout_name = config.get('layout')
        if not layout_name:
            return {}
        layout = CRISPR_E2G_LAYOUTS.get(layout_name)
        if layout is None:
            raise ValueError(
                f'File {self.file_accession} references unknown CRISPR E2G layout: '
                f'{layout_name}'
            )
        return layout

    def _targeted_element_types(self) -> list:
        config = self._file_config()
        targeted_element_types = config.get('targeted_element_types')
        if not targeted_element_types:
            return ['promoter', 'enhancer']
        return targeted_element_types

    def _skip_column_value_matches(
        self,
        column: str,
        cell: str,
        expected: str,
    ) -> bool:
        if column in ('ensembl_id', 'TargetGeneID', 'gene_id', 'target_gene'):
            return (
                self._normalize_ensembl_gene_id(cell)
                == self._normalize_ensembl_gene_id(expected)
            )
        return cell.strip() == expected

    def _matches_configured_skip_row(
        self,
        row: list,
        name_to_idx: Dict[str, int],
        skip_spec: dict,
    ) -> bool:
        for column, expected in skip_spec.items():
            if column in ('notes', 'catalog_notes'):
                continue
            idx = name_to_idx.get(column)
            if idx is None or idx >= len(row):
                return False
            if not self._skip_column_value_matches(
                    column, row[idx], expected):
                return False
        return True

    def _is_explicitly_skipped_row(
        self,
        row: list,
        name_to_idx: Dict[str, int],
    ) -> bool:
        for skip_spec in self._file_config().get('skip_rows', []):
            if self._matches_configured_skip_row(row, name_to_idx, skip_spec):
                return True
        return False

    def _promoter_gene_and_source_annotation(
        self,
        targeted_element_types: list,
        intended_target_name: str,
        intended_target_gene_raw: str,
    ) -> Tuple[Optional[str], str]:
        """
        Returns (promoter_gene, source_annotation).
        Raises ValueError for rows that cannot be loaded; use skip_rows for known exceptions.
        """
        supports_promoter = 'promoter' in targeted_element_types
        supports_enhancer = 'enhancer' in targeted_element_types
        if not supports_promoter:
            return (None, 'enhancer')
        if not supports_enhancer:
            if not isinstance(intended_target_name, str) or not re.match(
                r'^ENSG[0-9]{11}(?:_PAR_Y)?$', intended_target_name
            ):
                self._row_load_error(
                    f'promoter-targeted file but target gene id '
                    f'{intended_target_gene_raw!r} is not a valid Ensembl gene id pattern.'
                )
            if not self.gene_validator.validate(intended_target_name):
                self._row_load_error(
                    f'intended promoter gene {intended_target_gene_raw!r} is not a valid '
                    f'gene after normalization ({intended_target_name!r}).'
                )
            return (intended_target_name, 'promoter')
        # Mixed promoter/enhancer files use the row value to determine source annotation.
        promoter_gene = None
        source_annotation = 'enhancer'
        if isinstance(intended_target_name, str) and re.match(
            r'^ENSG[0-9]{11}(?:_PAR_Y)?$', intended_target_name
        ):
            if self.gene_validator.validate(intended_target_name):
                promoter_gene = intended_target_name
                source_annotation = 'promoter'
            else:
                self._row_load_error(
                    f'intended promoter gene {intended_target_gene_raw!r} is not a valid '
                    f'gene after normalization ({intended_target_name!r}).'
                )
        return (promoter_gene, source_annotation)

    def _source_annotation_column_promoter_gene_and_source_annotation(
        self,
        row: list,
        colmap: Dict[str, Optional[int]],
        intended_target_name: str,
        intended_target_gene_raw: str,
        readout_gene: str,
    ) -> Tuple[Optional[str], str]:
        source_idx = colmap.get('source_annotation')
        if source_idx is None or source_idx >= len(row):
            self._row_load_error('missing source annotation column.')
        source_annotation_raw = row[source_idx].strip()
        source_annotation_map = colmap.get('source_annotation_map') or {}
        if source_annotation_map:
            source_annotation = source_annotation_map.get(
                source_annotation_raw,
                source_annotation_map.get(source_annotation_raw.lower()),
            )
        else:
            source_annotation = source_annotation_raw.lower()
        if source_annotation == 'enhancer':
            return None, 'enhancer'
        if source_annotation != 'promoter':
            self._row_load_error(
                f'unsupported source annotation value {source_annotation_raw!r}.'
            )
        type_idx = colmap.get('element_type')
        row_type = (
            row[type_idx].strip()
            if type_idx is not None and type_idx < len(row)
            else ''
        )
        if row_type == 'TSS':
            promoter_gene = readout_gene
        else:
            promoter_gene = intended_target_name
        if not isinstance(promoter_gene, str) or not re.match(
            r'^ENSG[0-9]{11}(?:_PAR_Y)?$', promoter_gene
        ):
            self._row_load_error(
                f'promoter row target gene {intended_target_gene_raw!r} is not a valid '
                f'Ensembl gene id pattern.'
            )
        if not self.gene_validator.validate(promoter_gene):
            self._row_load_error(
                f'promoter row target gene {promoter_gene!r} is not valid.'
            )
        return promoter_gene, 'promoter'

    @staticmethod
    def _parse_element_coordinates_hg38(name_hg38: str) -> Tuple[str, str, str]:
        s = (name_hg38 or '').strip()
        m = _HG38_INTERVAL_RE.match(s)
        if m:
            c, s1, s2 = m['c'], m['s1'], m['s2']
            i1, i2 = int(s1), int(s2)
            if i1 <= i2:
                return c, s1, s2
            return c, s2, s1
        raise ValueError(f'Unrecognized name_hg38 interval: {name_hg38!r}')

    def _gene_raw_from_name_hg38_row(
        self,
        row,
        name_idx: int,
        type_idx: Optional[int],
        promoter_gene_map: Optional[Dict[str, str]] = None,
    ) -> Tuple[str, str, str, str]:
        name_cell = row[name_idx]
        chr_, start, end = self._parse_element_coordinates_hg38(name_cell)
        row_type = (
            row[type_idx].strip()
            if type_idx is not None and type_idx < len(row)
            else ''
        )
        if promoter_gene_map and row_type in promoter_gene_map:
            gene_raw = promoter_gene_map[row_type]
        else:
            gene_raw = name_cell
        return chr_, start, end, gene_raw

    @staticmethod
    def _perturb_seq_negative_control(row: list, type_col: Optional[int]) -> bool:
        if type_col is None or type_col >= len(row):
            return False
        return row[type_col].strip() == 'negative_control'

    @staticmethod
    def _non_targeting_control(row: list, source_annotation_col: Optional[int]) -> bool:
        if source_annotation_col is None or source_annotation_col >= len(row):
            return False
        return row[source_annotation_col].strip().lower() == 'non-targeting'

    def _resolve_explicit_interval(
        self,
        row: list,
        col: Dict[str, Optional[int]],
    ) -> Optional[Tuple[str, str, str, str]]:
        ci, si, ei, pi = col['chr'], col['start'], col['end'], col['promoter_gene']
        if ci is None or si is None or ei is None:
            return None
        if ci >= len(row) or si >= len(row) or ei >= len(row):
            return None
        c_raw, s_raw, e_raw = row[ci].strip(), row[si].strip(), row[ei].strip()
        if not (c_raw and s_raw and e_raw):
            return None
        gene_raw = row[pi] if pi is not None and pi < len(row) else ''
        return (c_raw, s_raw, e_raw, gene_raw)

    def _resolve_name_hg38_interval(
        self,
        row: list,
        col: Dict[str, Optional[int]],
        name_to_idx: Optional[Dict[str, int]] = None,
    ) -> Optional[Tuple[str, str, str, str]]:
        ni = col['name_hg38']
        if ni is None:
            return None
        if ni >= len(row):
            self._row_load_error(
                f'missing name_hg38 (row has {len(row)} columns).'
            )
        if not row[ni].strip():
            self._row_load_error('missing or empty name_hg38.')
        try:
            chr_, start, end, gene_raw = self._gene_raw_from_name_hg38_row(
                row, ni, col['element_type'], col.get('promoter_gene_map'))
        except ValueError as err:
            self._row_load_error(str(err))
        pi = col['promoter_gene']
        if pi is not None and pi < len(row) and row[pi].strip():
            gene_raw = row[pi]
        return chr_, start, end, gene_raw

    def _resolve_perturb_seq_element(
        self,
        row: list,
        col: Dict[str, Optional[int]],
        name_to_idx: Optional[Dict[str, int]] = None,
    ) -> Optional[Tuple[str, str, str, str]]:
        explicit = self._resolve_explicit_interval(row, col)
        if explicit is not None:
            return explicit
        from_name = self._resolve_name_hg38_interval(row, col, name_to_idx)
        if from_name is not None:
            return from_name
        self._row_load_error(
            'missing coordinates (chr/start/end or name_hg38).'
        )

    @staticmethod
    def _candidate_columns(value) -> Tuple[str, ...]:
        if value is None:
            return ()
        if isinstance(value, str):
            return (value,)
        return tuple(value)

    @staticmethod
    def _pick_column(name_to_idx: Dict[str, int], *candidates) -> Optional[int]:
        for candidate in candidates:
            for name in IGVFE2GCRISPR._candidate_columns(candidate):
                if name in name_to_idx:
                    return name_to_idx[name]
        return None

    def _columns_from_layout(self, name_to_idx: Dict[str, int]) -> Dict[str, Optional[int]]:
        layout = self._layout()
        semantic_columns = layout.get('semantic_columns', {})
        element_coordinates = semantic_columns.get('element_coordinates')
        colmap = {
            'readout_gene': self._pick_column(
                name_to_idx, semantic_columns.get('readout_gene')),
            'promoter_gene': self._pick_column(
                name_to_idx,
                semantic_columns.get('perturbed_gene'),
            ),
            'significant': None,
            'name_hg38': None,
            'element_type': self._pick_column(name_to_idx, 'type'),
            'promoter_gene_map': semantic_columns.get('promoter_gene_map'),
            'source_annotation': self._pick_column(
                name_to_idx, semantic_columns.get('source_annotation')),
            'source_annotation_map': semantic_columns.get('source_annotation_map'),
            'chr': None,
            'start': None,
            'end': None,
        }
        if isinstance(element_coordinates, (tuple, list)):
            if len(element_coordinates) >= 3:
                colmap['chr'] = self._pick_column(
                    name_to_idx, element_coordinates[0])
                colmap['start'] = self._pick_column(
                    name_to_idx, element_coordinates[1])
                colmap['end'] = self._pick_column(
                    name_to_idx, element_coordinates[2])
        else:
            colmap['name_hg38'] = self._pick_column(
                name_to_idx, element_coordinates)
        colmap['promoter_gene'] = self._pick_column(
            name_to_idx,
            semantic_columns.get('perturbed_gene'),
        )
        for source_column, catalog_field in semantic_columns.get(
            'metrics', {}
        ).items():
            if colmap.get(catalog_field) is not None:
                continue
            metric_idx = self._pick_column(name_to_idx, source_column)
            if metric_idx is not None:
                colmap[catalog_field] = metric_idx
        return colmap

    def _metrics_from_row(
        self,
        row: list,
        colmap: Dict[str, Optional[int]],
    ) -> dict:
        metrics = {}
        for key, col_idx in colmap.items():
            if key in _IGVF_E2G_LAYOUT_KEYS or col_idx is None:
                continue
            if col_idx >= len(row):
                continue
            cell = row[col_idx].strip()
            if key == 'significant':
                significant = self._parse_bool(row[col_idx])
                if significant is not None:
                    metrics[key] = significant
            elif cell:
                try:
                    value = float(cell)
                    metrics[key] = value
                except ValueError as err:
                    self._row_load_error(
                        f'metric {key!r} is not a float ({row[col_idx]!r}): {err}'
                    )
        return metrics

    @staticmethod
    def _p_values_from_row(
        row: list,
        colmap: Dict[str, Optional[int]],
    ) -> Tuple[Optional[float], Optional[float]]:
        p_value = None
        p_value_adj = None
        for key, target in (
            ('p_value', 'p_value'),
            ('p_value_adj', 'p_value_adj'),
        ):
            col_idx = colmap.get(key)
            if col_idx is None or col_idx >= len(row):
                continue
            cell = row[col_idx].strip()
            if not cell:
                continue
            try:
                value = float(cell)
            except ValueError:
                continue
            if target == 'p_value':
                p_value = value
            else:
                p_value_adj = value
        return p_value, p_value_adj

    @staticmethod
    def _update_neg_log10_cap(
        current_max: Optional[float],
        p_value: Optional[float],
    ) -> Optional[float]:
        if p_value is None or p_value <= 0:
            return current_max
        neg_log10 = -math.log10(p_value)
        if current_max is None or neg_log10 > current_max:
            return neg_log10
        return current_max

    def _passes_row_prefilters(
        self,
        row: list,
        name_to_idx: Dict[str, int],
        colmap: Dict[str, Optional[int]],
        *,
        is_scaled_screen: bool,
        is_pyspade: bool,
        method: str,
        uses_name_hg38: bool,
    ) -> bool:
        if not row:
            return False
        if self._is_explicitly_skipped_row(row, name_to_idx):
            return False
        if is_scaled_screen and not self._scaled_screen_row_should_load(
                row, name_to_idx, colmap):
            return False
        if is_pyspade and self._non_targeting_control(
                row, colmap.get('source_annotation')):
            return False
        if uses_name_hg38 or method == 'Perturb-seq':
            if self._perturb_seq_negative_control(row, colmap.get('element_type')):
                return False
        return True

    def _compute_neg_log10_caps(
        self,
        reader,
        name_to_idx: Dict[str, int],
        colmap: Dict[str, Optional[int]],
        *,
        is_scaled_screen: bool,
        is_pyspade: bool,
        method: str,
        uses_name_hg38: bool,
    ) -> Tuple[float, float]:
        max_p: Optional[float] = None
        max_p_adj: Optional[float] = None
        for row in reader:
            if not self._passes_row_prefilters(
                row,
                name_to_idx,
                colmap,
                is_scaled_screen=is_scaled_screen,
                is_pyspade=is_pyspade,
                method=method,
                uses_name_hg38=uses_name_hg38,
            ):
                continue
            p_value, p_value_adj = self._p_values_from_row(row, colmap)
            max_p = self._update_neg_log10_cap(max_p, p_value)
            max_p_adj = self._update_neg_log10_cap(max_p_adj, p_value_adj)
        return (
            max_p if max_p is not None else self.DEFAULT_MAX_LOG10_PVALUE,
            max_p_adj if max_p_adj is not None else self.DEFAULT_MAX_LOG10_PVALUE,
        )

    def _neg_log10_p_value(self, p_value: float, cap: float) -> float:
        if p_value <= 0:
            return cap
        return -math.log10(p_value)

    @staticmethod
    def _log2_one_minus_depletion(depletion: float) -> Optional[float]:
        complement = 1.0 - depletion
        if complement > 0:
            return math.log2(complement)
        return None

    def _apply_standard_neg_log10_fields(self, metrics: dict) -> None:
        """Derive neg_log10_p_value and neg_log10_p_value_adj from p-values when present."""
        if 'p_value' in metrics and 'neg_log10_p_value' not in metrics:
            metrics['neg_log10_p_value'] = self._neg_log10_p_value(
                metrics['p_value'], self._max_neg_log10_p_value_cap)
        if 'p_value_adj' in metrics and 'neg_log10_p_value_adj' not in metrics:
            metrics['neg_log10_p_value_adj'] = self._neg_log10_p_value(
                metrics['p_value_adj'], self._max_neg_log10_p_value_adj_cap)

    def _apply_standard_significant_field(self, metrics: dict) -> None:
        """Set significant from p_value_adj or p_value when not provided by the source file."""
        if 'significant' in metrics:
            return
        p_value = metrics.get('p_value_adj')
        if p_value is None:
            p_value = metrics.get('p_value')
        if p_value is not None:
            metrics['significant'] = p_value < self.SIGNIFICANCE_THRESHOLD
        else:
            metrics['significant'] = False

    def _apply_crudo_tap_seq_positive_control_significant(
        self,
        row: list,
        colmap: Dict[str, Optional[int]],
        metrics: dict,
    ) -> None:
        """CRUDO TAP-seq TSS rows are positive controls; always significant."""
        if self._file_config().get('layout') != 'crudo_tap_seq':
            return
        type_idx = colmap.get('element_type')
        promoter_gene_map = colmap.get('promoter_gene_map') or {}
        if type_idx is None or type_idx >= len(row):
            return
        if row[type_idx].strip() in promoter_gene_map:
            metrics['significant'] = True

    def _apply_adapter_calculated_fields(
        self,
        row: list,
        colmap: Dict[str, Optional[int]],
        metrics: dict,
    ) -> dict:
        for rule in self._layout().get('adapter_calculated_fields', []):
            rule_type = rule['rule']
            if rule_type == 'neg_log10':
                self._apply_neg_log10_rule(rule, metrics)
            elif rule_type == 'log2_one_minus':
                self._apply_log2_one_minus_rule(rule, metrics)
            else:
                raise ValueError(
                    f'File {self.file_accession} uses unknown adapter calculated '
                    f'field rule: {rule_type!r}'
                )
        self._apply_standard_neg_log10_fields(metrics)
        self._apply_standard_significant_field(metrics)
        self._apply_crudo_tap_seq_positive_control_significant(
            row, colmap, metrics)
        return metrics

    def _apply_neg_log10_rule(self, rule: dict, metrics: dict) -> None:
        source_value = metrics.get(rule['from'])
        if source_value is None:
            return
        metrics[rule['field']] = self._neg_log10_p_value(
            source_value,
            self._max_neg_log10_p_value_cap
            if rule['from'] == 'p_value'
            else self._max_neg_log10_p_value_adj_cap,
        )

    def _apply_log2_one_minus_rule(self, rule: dict, metrics: dict) -> None:
        base = metrics.get(rule['from'])
        if base is None:
            return
        depletion = base
        add_field = rule.get('add')
        if add_field is not None:
            offset = metrics.get(add_field)
            if offset is None:
                return
            depletion = base + offset
        subtract_field = rule.get('subtract')
        if subtract_field is not None:
            offset = metrics.get(subtract_field)
            if offset is None:
                return
            depletion = base - offset
        log2fc = self._log2_one_minus_depletion(depletion)
        if log2fc is not None:
            metrics[rule['field']] = log2fc

    @staticmethod
    def _genomic_element_gene_edge(
        *,
        _key: str,
        _from: str,
        readout_gene: str,
        source_url: str,
        file_accession: str,
        file_fileset: dict,
        method: str,
        crispr_modality: str,
        metrics: dict,
    ) -> dict:
        """Build a genomic_elements_genes edge (see IGVFE2GCRISPR schema)."""
        edge = {
            '_key': _key,
            '_from': _from,
            '_to': f'genes/{readout_gene}',
            'source': IGVFE2GCRISPR.SOURCE,
            'source_url': source_url,
            'files_filesets': f'files_filesets/{file_accession}',
            'label': IGVFE2GCRISPR.COLLECTION_LABEL,
            'class': file_fileset['class'],
            'name': 'modulates expression of',
            'inverse_name': 'expression modulated by',
            'method': method,
            'crispr_modality': crispr_modality,
            'biological_context': file_fileset['simple_sample_summaries'][0],
            'biosample_term': file_fileset['samples'][0],
            'treatments_term_ids': file_fileset['treatments_term_ids'],
        }
        if 'p_value' in metrics:
            edge['p_value'] = metrics['p_value']
        if 'p_value_adj' in metrics:
            edge['p_value_adj'] = metrics['p_value_adj']
        edge['neg_log10_p_value'] = metrics['neg_log10_p_value']
        if 'neg_log10_p_value_adj' in metrics:
            edge['neg_log10_p_value_adj'] = metrics['neg_log10_p_value_adj']
        edge['log2FC'] = metrics['log2FC']
        if 'log2FC_ci95_lower' in metrics:
            edge['log2FC_ci95_lower'] = metrics['log2FC_ci95_lower']
        if 'log2FC_ci95_upper' in metrics:
            edge['log2FC_ci95_upper'] = metrics['log2FC_ci95_upper']
        if 'pct_1' in metrics:
            edge['pct_1'] = metrics['pct_1']
        if 'pct_2' in metrics:
            edge['pct_2'] = metrics['pct_2']
        edge['significant'] = metrics['significant']
        if 'effect_size' in metrics:
            edge['effect_size'] = metrics['effect_size']
        if 'effect_size_ci_95' in metrics:
            edge['effect_size_ci_95'] = metrics['effect_size_ci_95']
        if 'num_guides' in metrics:
            edge['num_guides'] = metrics['num_guides']
        if 'fold_change' in metrics:
            edge['fold_change'] = metrics['fold_change']
        if 'background_corrected_fold_change' in metrics:
            edge['background_corrected_fold_change'] = metrics['background_corrected_fold_change']
        if 'ln_p_value' in metrics:
            edge['ln_p_value'] = metrics['ln_p_value']
        if 'hypergeometric_ln_p_value' in metrics:
            edge['hypergeometric_ln_p_value'] = metrics['hypergeometric_ln_p_value']
        if 'cpm_perturb' in metrics:
            edge['cpm_perturb'] = metrics['cpm_perturb']
        if 'cpm_bg' in metrics:
            edge['cpm_bg'] = metrics['cpm_bg']
        if 'num_cells' in metrics:
            edge['num_cells'] = metrics['num_cells']
        return edge

    def _scaled_screen_passes_qc(
        self,
        row: list,
        name_to_idx: Dict[str, int],
    ) -> bool:
        pass_qc_idx = name_to_idx.get('pass_qc')
        if pass_qc_idx is None:
            self._row_load_error('missing pass_qc column for scaled screen.')
        if pass_qc_idx >= len(row):
            return False
        return self._parse_bool(row[pass_qc_idx]) is True

    def _scaled_screen_has_targeted_element(
        self,
        row: list,
        colmap: Dict[str, Optional[int]],
    ) -> bool:
        type_idx = colmap.get('element_type')
        if type_idx is not None and type_idx < len(row):
            if row[type_idx].strip().lower() == 'non-targeting':
                return False
        for col_name in ('chr', 'start', 'end'):
            col_idx = colmap.get(col_name)
            if col_idx is None or col_idx >= len(row):
                return False
            value = row[col_idx].strip()
            if not value or value.lower() in {'nan', 'na', 'none'}:
                return False
        return True

    def _scaled_screen_row_should_load(
        self,
        row: list,
        name_to_idx: Dict[str, int],
        colmap: Dict[str, Optional[int]],
    ) -> bool:
        return (
            self._scaled_screen_passes_qc(row, name_to_idx)
            and self._scaled_screen_has_targeted_element(row, colmap)
        )

    @staticmethod
    def _scaled_screen_perturbed_genes(value: str) -> List[str]:
        cell = (value or '').strip()
        if not cell:
            return []
        try:
            parsed = json.loads(cell)
            if isinstance(parsed, str):
                return [parsed]
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            pass
        return re.findall(r'ENSG[0-9]{11}(?:_PAR_Y)?(?:\.[0-9]+)?', cell)

    def _scaled_screen_promoter_gene_and_source_annotation(
        self,
        row: list,
        colmap: Dict[str, Optional[int]],
        perturbed_gene_raw: str,
    ) -> Tuple[Optional[str], str]:
        source_idx = colmap.get('source_annotation')
        if source_idx is None or source_idx >= len(row):
            self._row_load_error(
                'missing genomic_element column for scaled screen.')
        source_annotation = row[source_idx].strip().lower()
        if source_annotation == 'enhancer':
            return None, 'enhancer'
        if source_annotation != 'promoter':
            self._row_load_error(
                f'unsupported genomic_element value {row[source_idx]!r}.'
            )

        perturbed_genes = self._scaled_screen_perturbed_genes(
            perturbed_gene_raw)
        if not perturbed_genes:
            self._row_load_error(
                'missing perturbed gene in putative_target_genes.'
            )
        promoter_gene = self._normalize_ensembl_gene_id(perturbed_genes[0])
        if not self.gene_validator.validate(promoter_gene):
            self._row_load_error(
                f'perturbed gene {perturbed_genes[0]!r} is not valid.'
            )
        return promoter_gene, 'promoter'

    @staticmethod
    def _better_scaled_screen_hit(
        current: Optional[dict],
        candidate: dict,
    ) -> bool:
        if current is None:
            return True
        candidate_p = candidate.get('p_value')
        current_p = current.get('p_value')
        if candidate_p is None:
            return False
        if current_p is None:
            return True
        return candidate_p < current_p

    def _check_unique_element_gene(
        self,
        element_gene_id: str,
        seen_element_gene_ids: set,
    ) -> None:
        if element_gene_id in seen_element_gene_ids:
            raise ValueError(
                f'Duplicate element_gene edge in {self.file_accession}: {element_gene_id}'
            )
        seen_element_gene_ids.add(element_gene_id)

    def __init__(self, filepath, label, source_url, writer: Optional[Writer] = None, validate=False, **kwargs):
        self.source_url = source_url
        self.file_accession = source_url.split('/')[-2]
        self.gene_validator = GeneValidator()
        self._max_neg_log10_p_value_cap = self.DEFAULT_MAX_LOG10_PVALUE
        self._max_neg_log10_p_value_adj_cap = self.DEFAULT_MAX_LOG10_PVALUE

        super().__init__(filepath, label, writer, validate)

    def _get_schema_type(self):
        """Return schema type based on label."""
        if self.label == 'genomic_element':
            return 'nodes'
        else:
            return 'edges'

    def _get_collection_name(self):
        """Get collection based on label."""
        if self.label == 'genomic_element':
            return 'genomic_elements'
        else:
            return 'genomic_elements_genes'

    def _open_data_reader(
        self,
        layout: dict,
    ) -> Tuple[object, csv.reader, Dict[str, int]]:
        data_file = gzip.open(self.filepath, 'rt')
        reader = csv.reader(
            data_file, delimiter=layout.get('delimiter', '\t'))
        header = next(reader)
        name_to_idx = {h.strip(): i for i, h in enumerate(header)}
        return data_file, reader, name_to_idx

    def process_file(self):
        self.writer.open()
        file_fileset = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        method = file_fileset['method']
        crispr_modality = file_fileset.get('crispr_modality')
        targeted_element_types = self._targeted_element_types()
        layout = self._layout()
        layout_name = self._file_config().get('layout')
        is_scaled_screen = layout_name == 'scaled_screen'
        is_pyspade = layout_name == 'pySpade'

        if not layout:
            raise ValueError(
                f'File {self.file_accession} has no CRISPR E2G layout; add it under '
                f'"files" in igvf_e2g_crispr_definitions.json.'
            )

        scan_file, scan_reader, scan_name_to_idx = self._open_data_reader(
            layout)
        try:
            scan_colmap = self._columns_from_layout(scan_name_to_idx)
            uses_name_hg38 = scan_colmap['name_hg38'] is not None
            self._max_neg_log10_p_value_cap, self._max_neg_log10_p_value_adj_cap = (
                self._compute_neg_log10_caps(
                    scan_reader,
                    scan_name_to_idx,
                    scan_colmap,
                    is_scaled_screen=is_scaled_screen,
                    is_pyspade=is_pyspade,
                    method=method,
                    uses_name_hg38=uses_name_hg38,
                )
            )
        finally:
            scan_file.close()

        genomic_coordinates_to_element_id = {}
        scaled_screen_best_edges = {}
        seen_element_gene_ids = set()
        data_file, reader, name_to_idx = self._open_data_reader(layout)
        try:
            colmap = self._columns_from_layout(name_to_idx)
            uses_name_hg38 = colmap['name_hg38'] is not None
            uses_explicit_coordinates = (
                colmap.get('chr') is not None
                and colmap.get('start') is not None
                and colmap.get('end') is not None
            )

            for row in reader:
                if not self._passes_row_prefilters(
                    row,
                    name_to_idx,
                    colmap,
                    is_scaled_screen=is_scaled_screen,
                    is_pyspade=is_pyspade,
                    method=method,
                    uses_name_hg38=uses_name_hg38,
                ):
                    continue

                if uses_explicit_coordinates:
                    intended_target_chr = row[colmap['chr']]
                    intended_target_start = row[colmap['start']]
                    intended_target_end = row[colmap['end']]
                    promoter_idx = colmap.get('promoter_gene')
                    if promoter_idx is not None and promoter_idx < len(row):
                        intended_target_gene_raw = row[promoter_idx]
                    else:
                        intended_target_gene_raw = ''
                    read_idx = colmap['readout_gene']
                    if read_idx is None or read_idx >= len(row):
                        self._row_load_error('missing readout gene column.')
                    readout_gene_raw = row[read_idx]
                elif uses_name_hg38 or method == 'Perturb-seq':
                    (
                        intended_target_chr,
                        intended_target_start,
                        intended_target_end,
                        intended_target_gene_raw,
                    ) = self._resolve_perturb_seq_element(
                        row, colmap, name_to_idx)
                    read_idx = colmap['readout_gene']
                    if read_idx is None or read_idx >= len(row):
                        self._row_load_error('missing readout gene column.')
                    readout_gene_raw = row[read_idx]
                else:
                    self._row_load_error(
                        'missing coordinates (chr/start/end or name_hg38).'
                    )

                intended_target_name = self._normalize_ensembl_gene_id(
                    intended_target_gene_raw)
                readout_gene = self._normalize_ensembl_gene_id(
                    readout_gene_raw)
                if not self.gene_validator.validate(readout_gene):
                    self._row_load_error(
                        f'readout gene {readout_gene_raw!r} is not a valid gene after '
                        f'normalization ({readout_gene!r}).'
                    )
                if is_scaled_screen:
                    promoter_gene, source_annotation = (
                        self._scaled_screen_promoter_gene_and_source_annotation(
                            row,
                            colmap,
                            intended_target_gene_raw,
                        )
                    )
                elif colmap.get('source_annotation') is not None:
                    promoter_gene, source_annotation = (
                        self._source_annotation_column_promoter_gene_and_source_annotation(
                            row,
                            colmap,
                            intended_target_name,
                            intended_target_gene_raw,
                            readout_gene,
                        )
                    )
                else:
                    promoter_gene, source_annotation = (
                        self._promoter_gene_and_source_annotation(
                            targeted_element_types,
                            intended_target_name,
                            intended_target_gene_raw,
                        )
                    )
                element_coordinates = (
                    intended_target_chr,
                    intended_target_start,
                    intended_target_end,
                    promoter_gene,
                    source_annotation,
                )
                if element_coordinates not in genomic_coordinates_to_element_id:
                    element_id = build_regulatory_region_id(
                        intended_target_chr,
                        intended_target_start,
                        intended_target_end,
                        'CRISPR',
                    )
                    genomic_coordinates_to_element_id[element_coordinates] = element_id
                else:
                    element_id = genomic_coordinates_to_element_id[
                        element_coordinates]

                metrics = self._metrics_from_row(row, colmap)
                metrics = self._apply_adapter_calculated_fields(
                    row, colmap, metrics)

                if self.label == 'genomic_element_gene':
                    _id = '_'.join(
                        [element_id, readout_gene, self.file_accession])
                    _props = self._genomic_element_gene_edge(
                        _key=_id,
                        _from=(
                            'genomic_elements/' + element_id + '_'
                            + self.file_accession
                        ),
                        readout_gene=readout_gene,
                        source_url=self.source_url,
                        file_accession=self.file_accession,
                        file_fileset=file_fileset,
                        method=method,
                        crispr_modality=crispr_modality,
                        metrics=metrics,
                    )
                    if is_scaled_screen:
                        current = scaled_screen_best_edges.get(_id)
                        if self._better_scaled_screen_hit(current, _props):
                            scaled_screen_best_edges[_id] = _props
                    else:
                        self._check_unique_element_gene(
                            _id, seen_element_gene_ids)
                        if self.validate:
                            self.validate_doc(_props)
                        self.writer.write(json.dumps(_props))
                        self.writer.write('\n')

            if self.label == 'genomic_element_gene' and is_scaled_screen:
                for _props in scaled_screen_best_edges.values():
                    self._check_unique_element_gene(
                        _props['_key'], seen_element_gene_ids)
                    if self.validate:
                        self.validate_doc(_props)
                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')

            if self.label == 'genomic_element':
                for genomic_element, element_id in genomic_coordinates_to_element_id.items():
                    source_annotation = genomic_element[4]
                    promoter_gene = genomic_element[3]
                    _id = element_id + '_' + self.file_accession
                    _props = {
                        '_key': _id,
                        'name': _id,
                        'chr': genomic_element[0],
                        'start': int(genomic_element[1]),
                        'end': int(genomic_element[2]),
                        'method': method,
                        'source_annotation': source_annotation,
                        'source': IGVFE2GCRISPR.SOURCE,
                        'source_url': self.source_url,
                        'type': 'tested elements',
                        'files_filesets': 'files_filesets/' + self.file_accession
                    }
                    if source_annotation == 'promoter':
                        if not promoter_gene:
                            raise ValueError(
                                f'Promoter element {_id} is missing promoter_gene.')
                        _props['promoter_of'] = f'genes/{promoter_gene}'
                    if self.validate:
                        self.validate_doc(_props)
                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')
        finally:
            data_file.close()
        self.writer.close()
