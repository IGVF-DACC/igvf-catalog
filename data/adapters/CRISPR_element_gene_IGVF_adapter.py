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
    'CRISPR_element_gene_IGVF' /
    'crispr_element_gene_igvf_definitions.json'
)


def _load_crispr_e2g_definitions() -> Tuple[dict, dict]:
    with open(_CRISPR_E2G_DEFINITIONS_PATH, encoding='utf-8') as definitions_file:
        raw_definitions = json.load(definitions_file)
    raw_definitions.pop('_context', None)
    file_config = raw_definitions.pop('files', {})
    layouts = dict(raw_definitions)
    return layouts, file_config


# Layout specs and per-accession parser config live in crispr_element_gene_igvf_definitions.json.
CRISPR_E2G_LAYOUTS, CRISPR_E2G_FILE_CONFIG = _load_crispr_e2g_definitions()


# name_hg38 / name-style intervals: chr:start-end.
_HG38_INTERVAL_RE = re.compile(
    r'^(?P<c>chr[^:]+):(?P<s1>\d+)-(?P<s2>\d+)$'
)
_ENSEMBL_GENE_ID_RE = re.compile(r'^ENSG[0-9]{11}(?:_PAR_Y)?$')

# Colmap keys that map row columns but are not edge metric properties.
_IGVF_E2G_LAYOUT_KEYS = frozenset({
    'readout_gene', 'promoter_gene', 'chr', 'start', 'end',
    'name_hg38', 'element_type', 'promoter_gene_map', 'source_annotation',
    'source_annotation_map',
})


class CRISPRElementGeneIGVF(BaseAdapter):

    ALLOWED_LABELS = [
        'genomic_element',
        'genomic_element_gene'
    ]
    SOURCE = 'IGVF'
    COLLECTION_LABEL = 'regulatory element effect on gene expression'
    SIGNIFICANCE_THRESHOLD = 0.05
    # Two-tailed normal critical value for SIGNIFICANCE_THRESHOLD (≈ normsinv(0.975)).
    Z_SCORE_SIGNIFICANCE_THRESHOLD = 1.959963984540054
    # CRISPR_element_gene_ENCODE_adapter; max log10pvalue from file is 235
    MAX_LOG10_PVALUE = 240
    OPTIONAL_EDGE_METRIC_FIELDS = frozenset({
        'p_value',
        'p_value_adj',
        'neg_log10_pvalue_adj',
        'log2FC_ci95_lower',
        'log2FC_ci95_upper',
        'pct_1',
        'pct_2',
        'effect_size',
        'effect_size_ci_95',
        'num_guides',
        'fold_change',
        'background_corrected_fold_change',
        'gamma_approximation_ln_p_value',
        'hypergeometric_ln_p_value',
        'empirical_p_value',
        'cpm_perturb',
        'cpm_bg',
        'num_cells',
        'z_score',
        't_score',
        'idr',
    })

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

    @staticmethod
    def _cell(row: list, idx: Optional[int], default: str = '') -> str:
        if idx is None or idx >= len(row):
            return default
        return row[idx].strip()

    @classmethod
    def _is_ensembl_gene_id(cls, gene) -> bool:
        return isinstance(gene, str) and bool(_ENSEMBL_GENE_ID_RE.match(gene))

    @staticmethod
    def _uses_perturb_seq_coordinates(
        uses_name_hg38: bool,
        method: str,
    ) -> bool:
        return uses_name_hg38 or method == 'Perturb-seq'

    def _write_doc(self, props: dict) -> None:
        if self.validate:
            self.validate_doc(props)
        self.writer.write(json.dumps(props))
        self.writer.write('\n')

    def _require_valid_promoter_gene(
        self,
        promoter_gene: str,
        raw_for_error: str,
        *,
        pattern_error: Optional[str] = None,
        validate_error: Optional[str] = None,
    ) -> None:
        if not self._is_ensembl_gene_id(promoter_gene):
            self._row_load_error(
                pattern_error
                or (
                    f'promoter row target gene {raw_for_error!r} is not a valid '
                    f'Ensembl gene id pattern.'
                )
            )
        if not self.gene_validator.validate(promoter_gene):
            self._row_load_error(
                validate_error
                or f'promoter row target gene {promoter_gene!r} is not valid.'
            )

    def _source_annotation_from_row(
        self,
        row: list,
        colmap: Dict[str, Optional[int]],
        *,
        missing_column_error: str,
    ) -> str:
        source_idx = colmap.get('source_annotation')
        if source_idx is None or source_idx >= len(row):
            self._row_load_error(missing_column_error)
        source_annotation_raw = row[source_idx].strip()
        source_annotation_map = colmap.get('source_annotation_map') or {}
        if source_annotation_map:
            return source_annotation_map.get(
                source_annotation_raw,
                source_annotation_map.get(source_annotation_raw.lower()),
            )
        return source_annotation_raw.lower()

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
        for skip_spec in self.file_config.get('skip_rows', []):
            if self._matches_configured_skip_row(row, name_to_idx, skip_spec):
                return True
        return False

    @staticmethod
    def _non_promoter_source_annotation(targeted_element_types: list) -> str:
        """Label used for non-promoter elements (enhancer, distal element, etc.)."""
        for annotation in targeted_element_types:
            if annotation != 'promoter':
                return annotation
        return 'enhancer'

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
        supports_non_promoter = any(
            annotation != 'promoter' for annotation in targeted_element_types
        )
        if not supports_promoter:
            return (None, self._non_promoter_source_annotation(targeted_element_types))
        if not supports_non_promoter:
            self._require_valid_promoter_gene(
                intended_target_name,
                intended_target_gene_raw,
                pattern_error=(
                    f'promoter-targeted file but target gene id '
                    f'{intended_target_gene_raw!r} is not a valid Ensembl gene id pattern.'
                ),
                validate_error=(
                    f'intended promoter gene {intended_target_gene_raw!r} is not a valid '
                    f'gene after normalization ({intended_target_name!r}).'
                ),
            )
            return (intended_target_name, 'promoter')
        promoter_gene = None
        source_annotation = self._non_promoter_source_annotation(
            targeted_element_types)
        if self._is_ensembl_gene_id(intended_target_name):
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
        source_annotation = self._source_annotation_from_row(
            row,
            colmap,
            missing_column_error='missing source annotation column.',
        )
        if source_annotation in {'enhancer', 'distal element'}:
            return None, source_annotation
        if source_annotation != 'promoter':
            source_idx = colmap['source_annotation']
            self._row_load_error(
                f'unsupported source annotation value {row[source_idx].strip()!r}.'
            )
        row_type = self._cell(row, colmap.get('element_type'))
        promoter_gene = (
            readout_gene if row_type == 'TSS' else intended_target_name
        )
        self._require_valid_promoter_gene(
            promoter_gene, intended_target_gene_raw)
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
        row_type = self._cell(row, type_idx)
        if promoter_gene_map and row_type in promoter_gene_map:
            gene_raw = promoter_gene_map[row_type]
        else:
            gene_raw = name_cell
        return chr_, start, end, gene_raw

    @staticmethod
    def _perturb_seq_negative_control(row: list, type_col: Optional[int]) -> bool:
        return CRISPRElementGeneIGVF._cell(row, type_col) == 'negative_control'

    @staticmethod
    def _non_targeting_control(row: list, source_annotation_col: Optional[int]) -> bool:
        return CRISPRElementGeneIGVF._cell(row, source_annotation_col).lower() == 'non-targeting'

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
    ) -> Optional[Tuple[str, str, str, str]]:
        explicit = self._resolve_explicit_interval(row, col)
        if explicit is not None:
            return explicit
        from_name = self._resolve_name_hg38_interval(row, col)
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
            for name in CRISPRElementGeneIGVF._candidate_columns(candidate):
                if name in name_to_idx:
                    return name_to_idx[name]
        return None

    def _columns_from_layout(self, name_to_idx: Dict[str, int]) -> Dict[str, Optional[int]]:
        semantic_columns = self.layout.get('semantic_columns', {})
        element_coordinates = semantic_columns.get('element_coordinates')
        colmap = {
            'readout_gene': self._pick_column(
                name_to_idx, semantic_columns.get('readout_gene')),
            'promoter_gene': self._pick_column(
                name_to_idx,
                semantic_columns.get('perturbed_gene'),
            ),
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
        for catalog_field, source_column in semantic_columns.get(
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
            if not cell or cell.lower() in {'na', 'nan', 'none', 'null'}:
                continue
            try:
                metrics[key] = float(cell)
            except ValueError as err:
                self._row_load_error(
                    f'metric {key!r} is not a float ({row[col_idx]!r}): {err}'
                )
        return metrics

    @classmethod
    def _neg_log10_pvalue(cls, p_value: float) -> float:
        if p_value <= 0:
            return cls.MAX_LOG10_PVALUE
        return -math.log10(p_value)

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
        if self.layout.get('require_pass_qc') and not self._passes_qc_column(
                row, name_to_idx):
            return False
        if is_scaled_screen and not self._scaled_screen_has_targeted_element(
                row, colmap):
            return False
        if is_pyspade and self._non_targeting_control(
                row, colmap.get('source_annotation')):
            return False
        if self._uses_perturb_seq_coordinates(uses_name_hg38, method):
            if self._perturb_seq_negative_control(row, colmap.get('element_type')):
                return False
        return True

    @staticmethod
    def _log2_one_minus_depletion(depletion: float) -> Optional[float]:
        complement = 1.0 - depletion
        if complement > 0:
            return math.log2(complement)
        return None

    def _apply_standard_neg_log10_fields(self, metrics: dict) -> None:
        """Derive neg_log10_pvalue and neg_log10_pvalue_adj from p-values when present."""
        if 'p_value' in metrics and 'neg_log10_pvalue' not in metrics:
            metrics['neg_log10_pvalue'] = self._neg_log10_pvalue(
                metrics['p_value'])
        if 'p_value_adj' in metrics and 'neg_log10_pvalue_adj' not in metrics:
            metrics['neg_log10_pvalue_adj'] = self._neg_log10_pvalue(
                metrics['p_value_adj'])

    def _apply_standard_significant_field(self, metrics: dict) -> None:
        """Set significant from p-values or |z_score| using SIGNIFICANCE_THRESHOLD."""
        p_value = metrics.get('p_value_adj')
        if p_value is None:
            p_value = metrics.get('p_value')
        if p_value is not None:
            metrics['significant'] = p_value < self.SIGNIFICANCE_THRESHOLD
            return
        z_score = metrics.get('z_score')
        if z_score is not None:
            metrics['significant'] = (
                abs(z_score) >= self.Z_SCORE_SIGNIFICANCE_THRESHOLD
            )
            return
        metrics['significant'] = False

    def _apply_adapter_calculated_fields(
        self,
        row: list,
        colmap: Dict[str, Optional[int]],
        metrics: dict,
    ) -> dict:
        for rule in self.layout.get('adapter_calculated_fields', []):
            rule_type = rule['rule']
            if rule_type == 'neg_log10':
                self._apply_neg_log10_rule(rule, metrics)
            elif rule_type == 'log2_one_minus':
                self._apply_log2_one_minus_rule(rule, metrics)
            elif rule_type == 'exp_ln_p':
                self._apply_exp_ln_p_rule(rule, metrics)
            else:
                raise ValueError(
                    f'File {self.file_accession} uses unknown adapter calculated '
                    f'field rule: {rule_type!r}'
                )
        self._apply_standard_neg_log10_fields(metrics)
        self._apply_standard_significant_field(metrics)
        return metrics

    def _apply_neg_log10_rule(self, rule: dict, metrics: dict) -> None:
        source_value = metrics.get(rule['from'])
        if source_value is None:
            return
        metrics[rule['field']] = self._neg_log10_pvalue(source_value)

    def _apply_exp_ln_p_rule(self, rule: dict, metrics: dict) -> None:
        """Derive a p-value from a natural-log p-value field (p = exp(ln_p))."""
        if rule['field'] in metrics:
            return
        ln_p_value = metrics.get(rule['from'])
        if ln_p_value is None:
            return
        metrics[rule['field']] = math.exp(ln_p_value)

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
            depletion += offset
        subtract_field = rule.get('subtract')
        if subtract_field is not None:
            offset = metrics.get(subtract_field)
            if offset is None:
                return
            depletion -= offset
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
        """Build a genomic_elements_genes edge (see CRISPRElementGeneIGVF schema)."""
        edge = {
            '_key': _key,
            '_from': _from,
            '_to': f'genes/{readout_gene}',
            'source': CRISPRElementGeneIGVF.SOURCE,
            'source_url': source_url,
            'files_filesets': f'files_filesets/{file_accession}',
            'label': CRISPRElementGeneIGVF.COLLECTION_LABEL,
            'class': file_fileset['class'],
            'name': 'modulates expression of',
            'inverse_name': 'expression modulated by',
            'method': method,
            'crispr_modality': crispr_modality,
            'biological_context': file_fileset['simple_sample_summaries'][0],
            'biosample_term': file_fileset['samples'][0],
            'treatments_term_ids': file_fileset['treatments_term_ids'],
        }
        edge['significant'] = metrics['significant']
        if 'neg_log10_pvalue' in metrics:
            edge['neg_log10_pvalue'] = metrics['neg_log10_pvalue']
        if 'log2FC' in metrics:
            edge['log2FC'] = metrics['log2FC']
        for field in CRISPRElementGeneIGVF.OPTIONAL_EDGE_METRIC_FIELDS:
            if field in metrics:
                edge[field] = metrics[field]
        return edge

    def _passes_qc_column(
        self,
        row: list,
        name_to_idx: Dict[str, int],
    ) -> bool:
        """Return True when pass_qc is explicitly true. Missing column is an error."""
        pass_qc_idx = name_to_idx.get('pass_qc')
        if pass_qc_idx is None:
            self._row_load_error('missing pass_qc column.')
        if pass_qc_idx >= len(row):
            return False
        return self._parse_bool(row[pass_qc_idx]) is True

    def _scaled_screen_has_targeted_element(
        self,
        row: list,
        colmap: Dict[str, Optional[int]],
    ) -> bool:
        type_idx = colmap.get('element_type')
        if self._cell(row, type_idx).lower() == 'non-targeting':
            return False
        for col_name in ('chr', 'start', 'end'):
            value = self._cell(row, colmap.get(col_name))
            if not value or value.lower() in {'nan', 'na', 'none'}:
                return False
        return True

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
        source_annotation = self._source_annotation_from_row(
            row,
            colmap,
            missing_column_error=(
                'missing genomic_element column for scaled screen.'
            ),
        )
        if source_annotation == 'enhancer':
            return None, 'enhancer'
        if source_annotation != 'promoter':
            source_idx = colmap['source_annotation']
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
        self._require_valid_promoter_gene(
            promoter_gene,
            perturbed_genes[0],
            validate_error=(
                f'perturbed gene {perturbed_genes[0]!r} is not valid.'
            ),
        )
        return promoter_gene, 'promoter'

    @staticmethod
    def _better_scaled_screen_hit(
        current: Optional[dict],
        candidate: dict,
    ) -> bool:
        """Return True when candidate should replace current (lower p_value wins).

        Scaled-screen files can emit multiple guides per element-gene pair; keep
        the row with the most significant p_value. Rows without p_value are never
        chosen over a row that has one; if the stored hit lacks p_value, replace
        it with any candidate that has p_value so we can compare on later rows.
        """
        if current is None:
            return True
        candidate_p = candidate.get('p_value')
        current_p = current.get('p_value')
        if candidate_p is None:
            return False
        if current_p is None:
            return True
        return candidate_p < current_p

    @staticmethod
    def _better_crispr_surf_hit(
        current: Optional[Tuple[dict, float]],
        candidate_fdr: float,
    ) -> bool:
        """Return True when candidate should replace current (lower FDR wins)."""
        if current is None:
            return True
        return candidate_fdr < current[1]

    def _resolve_intended_target_from_row(
        self,
        row: list,
        colmap: Dict[str, Optional[int]],
        method: str,
        *,
        uses_explicit_coordinates: bool,
        uses_name_hg38: bool,
    ) -> Tuple[str, str, str, str]:
        if uses_explicit_coordinates:
            promoter_idx = colmap.get('promoter_gene')
            return (
                row[colmap['chr']],
                row[colmap['start']],
                row[colmap['end']],
                row[promoter_idx] if promoter_idx is not None and promoter_idx < len(
                    row) else '',
            )
        if self._uses_perturb_seq_coordinates(uses_name_hg38, method):
            resolved = self._resolve_perturb_seq_element(row, colmap)
            if resolved is not None:
                return resolved
        self._row_load_error(
            'missing coordinates (chr/start/end or name_hg38).'
        )

    def _promoter_gene_and_source_annotation_for_row(
        self,
        row: list,
        colmap: Dict[str, Optional[int]],
        *,
        is_scaled_screen: bool,
        intended_target_name: str,
        intended_target_gene_raw: str,
        readout_gene: str,
    ) -> Tuple[Optional[str], str]:
        if is_scaled_screen:
            return self._scaled_screen_promoter_gene_and_source_annotation(
                row,
                colmap,
                intended_target_gene_raw,
            )
        if colmap.get('source_annotation') is not None:
            return self._source_annotation_column_promoter_gene_and_source_annotation(
                row,
                colmap,
                intended_target_name,
                intended_target_gene_raw,
                readout_gene,
            )
        return self._promoter_gene_and_source_annotation(
            self.targeted_element_types,
            intended_target_name,
            intended_target_gene_raw,
        )

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

        super().__init__(filepath, label, writer, validate)

        self.file_config = CRISPR_E2G_FILE_CONFIG.get(self.file_accession, {})
        if not self.file_config:
            self.logger.warning(
                'No CRISPR E2G file config for accession %s; '
                'using promoter/enhancer per-row heuristic. Add this file under '
                '"files" in crispr_element_gene_igvf_definitions.json.',
                self.file_accession,
            )
        layout_name = self.file_config.get('layout')
        if not layout_name:
            self.layout = {}
        else:
            layout = CRISPR_E2G_LAYOUTS.get(layout_name)
            if layout is None:
                raise ValueError(
                    f'File {self.file_accession} references unknown CRISPR E2G layout: '
                    f'{layout_name}'
                )
            self.layout = layout
        targeted_element_types = self.file_config.get('targeted_element_types')
        if not targeted_element_types:
            targeted_element_types = ['promoter', 'enhancer']
        self.targeted_element_types = targeted_element_types

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

    def parse(self):
        self.writer.add_tag('portal_accessions', self.file_accession)

        file_fileset = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        method = file_fileset['method']
        crispr_modality = file_fileset.get('crispr_modality')
        layout_name = self.file_config.get('layout')
        is_scaled_screen = layout_name == 'scaled_screen'
        is_pyspade = layout_name == 'pySpade'
        is_crispr_surf = layout_name == 'crispr_surf'
        genomic_coordinates_to_element_id = {}
        scaled_screen_best_edges = {}
        crispr_surf_best_edges = {}
        seen_element_gene_ids = set()
        constant_readout_gene = self.file_config.get('readout_gene')
        with gzip.open(self.filepath, 'rt', encoding='utf-8-sig') as data_file:
            reader = csv.reader(
                data_file, delimiter=self.layout.get('delimiter', '\t'))
            header = next(reader)
            name_to_idx = {h.strip(): i for i, h in enumerate(header)}

            if not self.layout:
                raise ValueError(
                    f'File {self.file_accession} has no CRISPR E2G layout; add it under '
                    f'"files" in crispr_element_gene_igvf_definitions.json.'
                )
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

                (
                    intended_target_chr,
                    intended_target_start,
                    intended_target_end,
                    intended_target_gene_raw,
                ) = self._resolve_intended_target_from_row(
                    row,
                    colmap,
                    method,
                    uses_explicit_coordinates=uses_explicit_coordinates,
                    uses_name_hg38=uses_name_hg38,
                )

                if constant_readout_gene:
                    readout_gene_raw = constant_readout_gene
                else:
                    read_idx = colmap['readout_gene']
                    if read_idx is None or read_idx >= len(row):
                        self._row_load_error('missing readout gene column.')
                    readout_gene_raw = row[read_idx]

                intended_target_name = self._normalize_ensembl_gene_id(
                    intended_target_gene_raw)
                readout_gene = self._normalize_ensembl_gene_id(
                    readout_gene_raw)
                if not self.gene_validator.validate(readout_gene):
                    self._row_load_error(
                        f'readout gene {readout_gene_raw!r} is not a valid gene after '
                        f'normalization ({readout_gene!r}).'
                    )
                promoter_gene, source_annotation = (
                    self._promoter_gene_and_source_annotation_for_row(
                        row,
                        colmap,
                        is_scaled_screen=is_scaled_screen,
                        intended_target_name=intended_target_name,
                        intended_target_gene_raw=intended_target_gene_raw,
                        readout_gene=readout_gene,
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
                    elif is_crispr_surf:
                        fdr_idx = name_to_idx.get('FDR')
                        if fdr_idx is None or fdr_idx >= len(row):
                            self._row_load_error('missing FDR column.')
                        try:
                            candidate_fdr = float(row[fdr_idx].strip())
                        except ValueError as err:
                            self._row_load_error(
                                f'FDR is not a float ({row[fdr_idx]!r}): {err}'
                            )
                        current = crispr_surf_best_edges.get(_id)
                        if self._better_crispr_surf_hit(current, candidate_fdr):
                            crispr_surf_best_edges[_id] = (
                                _props, candidate_fdr)
                    else:
                        self._check_unique_element_gene(
                            _id, seen_element_gene_ids)
                        self._write_doc(_props)

            if self.label == 'genomic_element_gene' and is_scaled_screen:
                for _props in scaled_screen_best_edges.values():
                    self._check_unique_element_gene(
                        _props['_key'], seen_element_gene_ids)
                    self._write_doc(_props)

            if self.label == 'genomic_element_gene' and is_crispr_surf:
                for _props, _fdr in crispr_surf_best_edges.values():
                    self._check_unique_element_gene(
                        _props['_key'], seen_element_gene_ids)
                    self._write_doc(_props)

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
                        'source': CRISPRElementGeneIGVF.SOURCE,
                        'source_url': self.source_url,
                        'type': 'tested elements',
                        'files_filesets': 'files_filesets/' + self.file_accession
                    }
                    if source_annotation == 'promoter':
                        if not promoter_gene:
                            raise ValueError(
                                f'Promoter element {_id} is missing promoter_gene.')
                        _props['promoter_of'] = f'genes/{promoter_gene}'
                    self._write_doc(_props)
