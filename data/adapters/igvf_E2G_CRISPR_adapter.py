import csv
import gzip
import json
import re
from typing import Dict, List, Optional, Tuple

from adapters.base import BaseAdapter
from adapters.helpers import build_regulatory_region_id, get_file_fileset_by_accession_in_arangodb
from adapters.gene_validator import GeneValidator
from adapters.writer import Writer

# CRUDO TAP-seq (IGVFFI5903QAWP): TSS rows do not carry promoter Ensembl IDs
# directly, so map the row type to the promoter gene here.
CRUDO_TSS_PROMOTER_GENE = {
    'CCND1_TSS': 'ENSG00000110092',
    'KITLG_TSS': 'ENSG00000049130',
    'SSFA2_TSS': 'ENSG00000138434',
    'FAM3C_TSS': 'ENSG00000196937',
    'MYC_TSS': 'ENSG00000136997',
}

CRUDO_SOURCE_ANNOTATION = {
    'putative_enhancer': 'enhancer',
    **{row_type: 'promoter' for row_type in CRUDO_TSS_PROMOTER_GENE},
}


# Header inventory for IGVF CRISPR E2G files. Layouts are grouped by exact
# header overlap so incoming files can be assigned to an existing layout when
# possible; accession notes only keep dataset-specific context.
CRISPR_E2G_LAYOUTS = {
    't_cell_perturb_seq': {
        'columns': (
            'p_val', 'avg_log2FC', 'pct.1', 'pct.2', 'p_val_adj',
            'guide_id', 'target_gene', 'intended_target_name',
            'intended_target_chr', 'intended_target_start', 'intended_target_end',
        ),
        'semantic_columns': {
            'target_gene': 'intended_target_name',
            'readout_gene': 'target_gene',
            'element_coordinates': (
                'intended_target_chr', 'intended_target_start', 'intended_target_end',
            ),
            'metrics': ('p_val', 'p_val_adj', 'avg_log2FC', 'pct.1', 'pct.2'),
        },
    },
    'hcasmc_promoter_sceptre': {
        'columns': (
            'intended_target_name', 'Intended_target_gene_id', 'guide_id(s)',
            'targeting_chr', 'targeting_start', 'targeting_end', 'gene_id',
            'gene_symbol', 'sceptre_log2_fc', 'sceptre_p_value',
            'sceptre_adj_p_value', 'significant', 'type',
        ),
        'semantic_columns': {
            'target_gene': 'Intended_target_gene_id',
            'intended_target_label': 'intended_target_name',
            'readout_gene': 'gene_id',
            'element_coordinates': ('targeting_chr', 'targeting_start', 'targeting_end'),
            'metrics': (
                'sceptre_p_value', 'sceptre_adj_p_value',
                'sceptre_log2_fc', 'significant',
            ),
        },
    },
    'scaled_screen': {
        'columns': (
            'guide_id', 'spacer_g_start', 'protospacer', 'targeting', 'type',
            'guide_chr', 'guide_start', 'guide_end', 'strand', 'pam',
            'genomic_element', 'intended_target_chr', 'intended_target_start',
            'intended_target_end', 'response_id', 'hgnc_symbol',
            'n_nonzero_trt', 'n_nonzero_cntrl', 'pass_qc', 'p_value',
            'log_2_fold_change', 'full_piggyflex_oligo', 'putative_target_genes',
            'putative_target_genes_hgnc',
        ),
        'semantic_columns': {
            'target_gene': 'putative_target_genes',
            'readout_gene': 'response_id',
            'source_annotation': 'genomic_element',
            'element_coordinates': (
                'intended_target_chr', 'intended_target_start', 'intended_target_end',
            ),
            'metrics': ('p_value', 'log_2_fold_change', 'pass_qc'),
            'notes': 'Distinct layout; not covered by the generic Perturb-seq mapper.',
        },
    },
    'wtc11_cm_tf_perturb_seq': {
        'delimiter': ',',
        'columns': (
            'idx', 'gene_names', 'gene_name_ensembl', 'chromosome',
            'pos', 'strand', 'color_idx', 'chr_idx', 'genomic_element', 'region',
            'intended_target_name', 'intended_target_name_ensmbl', 'num_cell',
            'bin', 'log(pval)-hypergeom', 'fc', 'Significance_score',
            'fc_by_rand_dist_cpm', 'pval-empirical', 'cpm_perturb', 'cpm_bg',
            'log2fc',
        ),
        'semantic_columns': {
            'target_gene': 'intended_target_name_ensmbl',
            'intended_target_label': 'intended_target_name',
            'readout_gene': 'gene_name_ensembl',
            'source_annotation': 'genomic_element',
            'element_coordinates': 'region',
            'metrics': (
                'Significance_score', 'log2fc', 'fc',
                'log(pval)-hypergeom', 'fc_by_rand_dist_cpm',
                'pval-empirical', 'cpm_perturb', 'cpm_bg', 'num_cell',
            ),
            'notes': (
                'pySpade CSV layout. Significance_score is natural log p-value '
                'after background correction; log2fc is emitted as log2FC for '
                'Perturb-seq scoring, with fold-change ratios retained separately.'
            ),
        },
    },
    'mechanoenhancer': {
        'columns': (
            'p_val', 'avg_log2FC', 'pct.1', 'pct.2', 'p_val_adj',
            'gene_symbol', 'ensembl_id', 'intended_target_name',
            'intended_target_chr', 'intended_target_start', 'intended_target_end',
        ),
        'semantic_columns': {
            'readout_gene': 'ensembl_id',
            'element_coordinates': ('intended_target_chr', 'intended_target_start', 'intended_target_end'),
            'metrics': ('p_val', 'p_val_adj', 'avg_log2FC', 'pct.1', 'pct.2'),
        },
    },
    'tap_seq_sceptre_power_15': {
        'columns': (
            'intended_target_name', 'guide_id(s)', 'targeting_chr',
            'targeting_start', 'targeting_end', 'type', 'gene_id', 'gene_symbol',
            'sceptre_log2_fc', 'sceptre_p_value', 'sceptre_adj_p_value',
            'significant', 'sample_term_name', 'sample_term_id',
            'sample_summary_short', 'power_at_effect_size_15', 'notes',
        ),
        'semantic_columns': {
            'readout_gene': 'gene_id',
            'element_coordinates': ('targeting_chr', 'targeting_start', 'targeting_end'),
            'metrics': (
                'sceptre_p_value', 'sceptre_adj_p_value',
                'sceptre_log2_fc', 'significant',
            ),
        },
    },
    'tap_seq_sceptre_power_xx': {
        'columns': (
            'intended_target_name', 'guide_id(s)', 'targeting_chr',
            'targeting_start', 'targeting_end', 'type', 'gene_id', 'gene_symbol',
            'sceptre_log2_fc', 'sceptre_p_value', 'sceptre_adj_p_value',
            'significant', 'sample_term_name', 'sample_term_id',
            'sample_summary_short', 'power_at_effect_size_XX', 'notes',
        ),
        'semantic_columns': {
            'readout_gene': 'gene_id',
            'element_coordinates': ('targeting_chr', 'targeting_start', 'targeting_end'),
            'metrics': (
                'sceptre_p_value', 'sceptre_adj_p_value',
                'sceptre_log2_fc', 'significant',
            ),
        },
    },
    'crudo_tap_seq': {
        'columns': (
            'name_hg19', 'name_hg38', 'type', 'n', 'TargetGene', 'TargetGeneID',
            'EnhancerEffect.noAux.Rep1', 'EnhancerEffect.noAux.Rep2',
            'EnhancerEffect.noAux', 'ci95.EnhancerEffect.noAux.Rep1',
            'ci95.EnhancerEffect.noAux.Rep2', 'ci95.EnhancerEffect.noAux',
            'pval.EnhancerEffect.noAux.Rep1', 'pval.EnhancerEffect.noAux.Rep2',
            'pval.EnhancerEffect.noAux', 'adj.pval.EnhancerEffect.noAux.Rep1',
            'adj.pval.EnhancerEffect.noAux.Rep2', 'adj.pval.EnhancerEffect.noAux',
            'Significant',
        ),
        'semantic_columns': {
            'promoter_gene_map': CRUDO_TSS_PROMOTER_GENE,
            'readout_gene': 'TargetGeneID',
            'source_annotation': 'type',
            'source_annotation_map': CRUDO_SOURCE_ANNOTATION,
            'element_coordinates': 'name_hg38',
            'metrics': (
                'pval.EnhancerEffect.noAux', 'EnhancerEff.pval',
                'adj.pval.EnhancerEffect.noAux', 'EnhancerEff.pval.adj',
                'EnhancerEffect.noAux', 'EnhancerEff', 'Significant',
            ),
        },
    },
    'facs_screen': {
        'columns': (
            'FRACTEL_pval', 'FRACTEL_pval_fdr_corr', 'FRACTEL_effect_size',
            'intended_target_name', 'intended_target_chr', 'intended_target_start',
            'intended_target_end', 'readout_gene', 'readout_gene_symbol',
        ),
        'semantic_columns': {
            'target_gene': 'intended_target_name',
            'readout_gene': 'readout_gene',
            'element_coordinates': (
                'intended_target_chr', 'intended_target_start', 'intended_target_end',
            ),
            'metrics': (
                'FRACTEL_pval', 'FRACTEL_pval_fdr_corr', 'FRACTEL_effect_size',
            ),
        },
    },
}


# Per-file parser expectations. Mixed promoter/enhancer layouts should declare
# a source_annotation column, with source_annotation_map when file-native values
# need normalization. crispr_modality is still emitted from files_filesets;
# expected_crispr_modality is a drift check against released IGVF metadata.
# title is an unused shorthand name for the dataset.
CRISPR_E2G_FILE_CONFIG = {
    'IGVFFI3069QCRA': {
        'title': 'T-cell CRISPRa Perturb-seq',
        'targeted_element_types': ['promoter'],
        'layout': 't_cell_perturb_seq',
        'expected_crispr_modality': 'activation',
    },
    'IGVFFI5749WPVK': {
        'title': 'T-cell CRISPRi Perturb-seq',
        'targeted_element_types': ['promoter'],
        'layout': 't_cell_perturb_seq',
        'expected_crispr_modality': 'interference',
    },
    'IGVFFI6376HTIF': {
        'title': 'HCASMC Pilot Parse Perturb-seq',
        'targeted_element_types': ['promoter'],
        'layout': 'hcasmc_promoter_sceptre',
        'expected_crispr_modality': 'interference',
    },
    'IGVFFI0206LUDV': {
        'title': 'HCASMC 971-gene Parse Perturb-seq',
        'targeted_element_types': ['promoter'],
        'layout': 'hcasmc_promoter_sceptre',
        'expected_crispr_modality': 'interference',
    },
    'IGVFFI4544JMWL': {
        'title': 'Scaled scCRISPRa screen',
        'targeted_element_types': ['promoter', 'enhancer'],
        'layout': 'scaled_screen',
        'expected_crispr_modality': 'activation',
    },
    'IGVFFI0830FXFI': {
        'title': 'WTC-11 CM TF-Perturb-seq',
        'targeted_element_types': ['promoter', 'enhancer'],
        'layout': 'wtc11_cm_tf_perturb_seq',
        'expected_crispr_modality': 'interference',
    },
    'IGVFFI5903QAWP': {
        'title': 'CRUDO TAP-seq',
        'targeted_element_types': ['promoter', 'enhancer'],
        'layout': 'crudo_tap_seq',
        'expected_crispr_modality': 'interference',
    },
    'IGVFFI6296RCJK': {
        'title': 'Mechanoenhancer Perturb-seq',
        'targeted_element_types': ['enhancer'],
        'layout': 'mechanoenhancer',
        'expected_crispr_modality': 'interference',
    },
    'IGVFFI6600VCYY': {
        'title': 'EC-TAP-seq D0',
        'targeted_element_types': ['enhancer'],
        'layout': 'tap_seq_sceptre_power_15',
        'expected_crispr_modality': 'interference',
    },
    'IGVFFI7195XKBC': {
        'title': 'EC-TAP-seq D2',
        'targeted_element_types': ['enhancer'],
        'layout': 'tap_seq_sceptre_power_15',
        'expected_crispr_modality': 'interference',
    },
    'IGVFFI9246AJEK': {
        'title': 'EC-TAP-seq D4',
        'targeted_element_types': ['enhancer'],
        'layout': 'tap_seq_sceptre_power_15',
        'expected_crispr_modality': 'interference',
    },
    'IGVFFI3434YAPX': {
        'title': '9p21 DC-TAP-seq',
        'targeted_element_types': ['enhancer'],
        'layout': 'tap_seq_sceptre_power_xx',
        'expected_crispr_modality': 'interference',
    },
    'IGVFFI1168JUYR': {
        'title': 'HCASMC DC-TAP-seq',
        'targeted_element_types': ['enhancer'],
        'layout': 'tap_seq_sceptre_power_xx',
        'expected_crispr_modality': 'interference',
    },
    'IGVFFI9100GKNS': {
        'title': 'T-cell CRISPRko IL7R FACS screen, BATF3 OE',
        'targeted_element_types': ['promoter'],
        'layout': 'facs_screen',
        'expected_crispr_modality': 'knockout',
    },
    'IGVFFI6268OASM': {
        'title': 'T-cell CRISPRko IL7R FACS screen',
        'targeted_element_types': ['promoter'],
        'layout': 'facs_screen',
        'expected_crispr_modality': 'knockout',
    },
    'IGVFFI1336XWXJ': {
        'title': 'T-cell CRISPRi CCR7 FACS screen',
        'targeted_element_types': ['promoter'],
        'layout': 'facs_screen',
        'expected_crispr_modality': 'interference',
    },
    'IGVFFI3089UGHM': {
        'title': 'T-cell CRISPRa CCR7 FACS screen',
        'targeted_element_types': ['promoter'],
        'layout': 'facs_screen',
        'expected_crispr_modality': 'activation',
    },
}


# name_hg38 / name-style intervals: chr:start-end.
_HG38_INTERVAL_RE = re.compile(
    r'^(?P<c>chr[^:]+):(?P<s1>\d+)-(?P<s2>\d+)$'
)

# I keys that map row columns but are not numeric edge metrics.
_IGVF_E2G_LAYOUT_KEYS = frozenset({
    'readout_gene', 'promoter_gene', 'chr', 'start', 'end',
    'name_hg38', 'element_type', 'promoter_gene_map', 'source_annotation',
    'source_annotation_map',
})


_IGVF_E2G_METRIC_COLUMN_TO_KEY = {
    'EnhancerEff.pval': 'p_value',
    'p_val': 'p_value',
    'sceptre_p_value': 'p_value',
    'pval.EnhancerEffect.noAux': 'p_value',
    'FRACTEL_pval': 'p_value',
    'p_value': 'p_value',
    'pval-empirical': 'p_value',
    'Significance_score': 'significance_score',
    'log(pval)-hypergeom': 'hypergeometric_log_p_value',
    'EnhancerEff.pval.adj': 'p_value_adj',
    'p_val_adj': 'p_value_adj',
    'sceptre_adj_p_value': 'p_value_adj',
    'adj.pval.EnhancerEffect.noAux': 'p_value_adj',
    'FRACTEL_pval_fdr_corr': 'p_value_adj',
    'EnhancerEff': 'effect_size',
    'EnhancerEffect.noAux': 'effect_size',
    'FRACTEL_effect_size': 'effect_size',
    'fc': 'fold_change',
    'fc_by_rand_dist_cpm': 'background_corrected_fold_change',
    'avg_log2FC': 'log2FC',
    'sceptre_log2_fc': 'log2FC',
    'log_2_fold_change': 'log2FC',
    'log2fc': 'log2FC',
    'pct.1': 'pct_1',
    'pct.2': 'pct_2',
    'cpm_perturb': 'cpm_perturb',
    'cpm_bg': 'cpm_bg',
    'num_cell': 'num_cells',
    'significant': 'significant',
    'Significant': 'significant',
}


class IGVFE2GCRISPR(BaseAdapter):

    ALLOWED_LABELS = [
        'genomic_element',
        'genomic_element_gene'
    ]
    SOURCE = 'IGVF'
    COLLECTION_LABEL = 'regulatory element effect on gene expression'

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

    def _file_config(self) -> dict:
        config = CRISPR_E2G_FILE_CONFIG.get(self.file_accession, {})
        if not config:
            self.logger.warning(
                'No CRISPR_E2G_FILE_CONFIG entry for accession %s; '
                'using promoter/enhancer per-row heuristic. Add this file to the map in '
                'igvf_E2G_CRISPR_adapter.py.',
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

    def _resolve_crispr_modality(self, file_fileset: dict) -> Optional[str]:
        crispr_modality = file_fileset.get('crispr_modality')
        expected = self._file_config().get('expected_crispr_modality')
        if expected and crispr_modality and expected != crispr_modality:
            self.logger.warning(
                'File %s has crispr_modality %s in files_filesets, but '
                'CRISPR_E2G_FILE_CONFIG expects %s.',
                self.file_accession,
                crispr_modality,
                expected,
            )
        return crispr_modality or expected

    def _promoter_gene_and_source_annotation(
        self,
        targeted_element_types: list,
        intended_target_name: str,
        intended_target_gene_raw: str,
    ) -> Optional[Tuple[Optional[str], str]]:
        """
        Returns (promoter_gene, source_annotation) or None if the row should be skipped.
        """
        supports_promoter = 'promoter' in targeted_element_types
        supports_enhancer = 'enhancer' in targeted_element_types
        if not supports_promoter:
            return (None, 'enhancer')
        if not supports_enhancer:
            if not isinstance(intended_target_name, str) or not re.match(
                r'^ENSG[0-9]{11}(?:_PAR_Y)?$', intended_target_name
            ):
                self.logger.warning(
                    'Skipping row: file %s is promoter-targeted but intended_target_name '
                    '"%s" is not a valid Ensembl gene id pattern.',
                    self.file_accession,
                    intended_target_gene_raw,
                )
                return None
            if not self.gene_validator.validate(intended_target_name):
                self.logger.warning(
                    'Skipping row: intended promoter gene "%s" is not a valid gene after '
                    'normalization ("%s").',
                    intended_target_gene_raw,
                    intended_target_name,
                )
                return None
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
                self.logger.warning(
                    'Skipping row: intended promoter gene "%s" is not a valid gene after '
                    'normalization ("%s").',
                    intended_target_gene_raw,
                    intended_target_name,
                )
                return None
        return (promoter_gene, source_annotation)

    def _source_annotation_column_promoter_gene_and_source_annotation(
        self,
        row: list,
        colmap: Dict[str, Optional[int]],
        intended_target_name: str,
        intended_target_gene_raw: str,
    ) -> Optional[Tuple[Optional[str], str]]:
        source_idx = colmap.get('source_annotation')
        if source_idx is None or source_idx >= len(row):
            self.logger.warning(
                'Skipping row in %s: missing source annotation column.',
                self.file_accession,
            )
            return None
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
            self.logger.warning(
                'Skipping row in %s: unsupported source annotation value %r.',
                self.file_accession,
                source_annotation_raw,
            )
            return None
        if not isinstance(intended_target_name, str) or not re.match(
            r'^ENSG[0-9]{11}(?:_PAR_Y)?$', intended_target_name
        ):
            self.logger.warning(
                'Skipping promoter row in %s: target gene "%s" is not a valid '
                'Ensembl gene id pattern.',
                self.file_accession,
                intended_target_gene_raw,
            )
            return None
        if not self.gene_validator.validate(intended_target_name):
            self.logger.warning(
                'Skipping promoter row in %s: target gene "%s" is not valid.',
                self.file_accession,
                intended_target_name,
            )
            return None
        return intended_target_name, 'promoter'

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
        if ni is None or ni >= len(row) or not row[ni].strip():
            return None
        try:
            chr_, start, end, gene_raw = self._gene_raw_from_name_hg38_row(
                row, ni, col['element_type'], col.get('promoter_gene_map'))
        except ValueError as err:
            self.logger.warning(
                'Skipping row in %s: %s',
                self.file_accession,
                err,
            )
            return None
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
        self.logger.warning(
            'Skipping row in %s: missing coordinates (chr/start/end or name_hg38).',
            self.file_accession,
        )
        return None

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
                semantic_columns.get('target_gene'),
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
            semantic_columns.get('target_gene'),
        )
        for metric_column in semantic_columns.get('metrics', ()):
            metric_key = _IGVF_E2G_METRIC_COLUMN_TO_KEY.get(metric_column)
            if not metric_key or colmap.get(metric_key) is not None:
                continue
            metric_idx = self._pick_column(name_to_idx, metric_column)
            if metric_idx is not None:
                colmap[metric_key] = metric_idx
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
                except ValueError:
                    self.logger.warning(
                        'Skipping metric %s in %s: not a float (%r).',
                        key,
                        self.file_accession,
                        row[col_idx],
                    )
        return metrics

    def _scaled_screen_passes_qc(
        self,
        row: list,
        name_to_idx: Dict[str, int],
    ) -> bool:
        pass_qc_idx = name_to_idx.get('pass_qc')
        if pass_qc_idx is None or pass_qc_idx >= len(row):
            self.logger.warning(
                'Skipping row in %s: missing pass_qc column for scaled screen.',
                self.file_accession,
            )
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
    def _scaled_screen_target_genes(value: str) -> List[str]:
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
        target_gene_raw: str,
    ) -> Optional[Tuple[Optional[str], str]]:
        source_idx = colmap.get('source_annotation')
        if source_idx is None or source_idx >= len(row):
            self.logger.warning(
                'Skipping row in %s: missing genomic_element column for scaled screen.',
                self.file_accession,
            )
            return None
        source_annotation = row[source_idx].strip().lower()
        if source_annotation == 'enhancer':
            return None, 'enhancer'
        if source_annotation != 'promoter':
            self.logger.warning(
                'Skipping row in %s: unsupported genomic_element value %r.',
                self.file_accession,
                row[source_idx],
            )
            return None

        target_genes = self._scaled_screen_target_genes(target_gene_raw)
        if not target_genes:
            self.logger.warning(
                'Skipping promoter row in %s: missing target gene in putative_target_genes.',
                self.file_accession,
            )
            return None
        promoter_gene = self._normalize_ensembl_gene_id(target_genes[0])
        if not self.gene_validator.validate(promoter_gene):
            self.logger.warning(
                'Skipping promoter row in %s: target gene "%s" is not valid.',
                self.file_accession,
                target_genes[0],
            )
            return None
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

    def parse(self):
        file_fileset = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        method = file_fileset['method']
        crispr_modality = self._resolve_crispr_modality(file_fileset)
        targeted_element_types = self._targeted_element_types()
        layout = self._layout()
        is_scaled_screen = self.file_accession == 'IGVFFI4544JMWL'
        genomic_coordinates_to_element_id = {}
        scaled_screen_best_edges = {}
        seen_element_gene_ids = set()
        with gzip.open(self.filepath, 'rt') as data_file:
            reader = csv.reader(
                data_file, delimiter=layout.get('delimiter', '\t'))
            header = next(reader)
            name_to_idx = {h.strip(): i for i, h in enumerate(header)}

            if layout:
                colmap = self._columns_from_layout(name_to_idx)
            elif method == 'CRISPR screen':
                colmap = {
                    'p_value': name_to_idx['FRACTEL_pval'],
                    'p_value_adj': name_to_idx['FRACTEL_pval_fdr_corr'],
                    'effect_size': name_to_idx['FRACTEL_effect_size'],
                    'readout_gene': name_to_idx['readout_gene'],
                    'promoter_gene': name_to_idx['intended_target_name'],
                    'chr': name_to_idx['intended_target_chr'],
                    'start': name_to_idx['intended_target_start'],
                    'end': name_to_idx['intended_target_end'],
                }
            else:
                raise ValueError(f'Method: {method} is unsupported.')

            for row in reader:
                if not row:
                    continue
                if is_scaled_screen and not self._scaled_screen_row_should_load(
                        row, name_to_idx, colmap):
                    continue

                if method == 'Perturb-seq':
                    if self._perturb_seq_negative_control(row, colmap['element_type']):
                        continue
                    interval = self._resolve_perturb_seq_element(row, colmap)
                    if interval is None:
                        continue
                    (
                        intended_target_chr,
                        intended_target_start,
                        intended_target_end,
                        intended_target_gene_raw,
                    ) = interval
                    read_idx = colmap['readout_gene']
                    if read_idx is None or read_idx >= len(row):
                        self.logger.warning(
                            'Skipping row in %s: missing readout gene column.',
                            self.file_accession,
                        )
                        continue
                    readout_gene_raw = row[read_idx]
                else:
                    intended_target_chr = row[colmap['chr']]
                    intended_target_start = row[colmap['start']]
                    intended_target_end = row[colmap['end']]
                    intended_target_gene_raw = row[colmap['promoter_gene']]
                    readout_gene_raw = row[colmap['readout_gene']]

                intended_target_name = self._normalize_ensembl_gene_id(
                    intended_target_gene_raw)
                readout_gene = self._normalize_ensembl_gene_id(
                    readout_gene_raw)
                if not self.gene_validator.validate(readout_gene):
                    self.logger.warning(
                        'Skipping row: readout gene "%s" is not a valid gene after '
                        'normalization ("%s").',
                        readout_gene_raw,
                        readout_gene,
                    )
                    continue
                if is_scaled_screen:
                    resolved = self._scaled_screen_promoter_gene_and_source_annotation(
                        row,
                        colmap,
                        intended_target_gene_raw,
                    )
                elif colmap.get('source_annotation') is not None:
                    resolved = self._source_annotation_column_promoter_gene_and_source_annotation(
                        row,
                        colmap,
                        intended_target_name,
                        intended_target_gene_raw,
                    )
                else:
                    resolved = self._promoter_gene_and_source_annotation(
                        targeted_element_types,
                        intended_target_name,
                        intended_target_gene_raw,
                    )
                if resolved is None:
                    continue
                promoter_gene, source_annotation = resolved

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

                if self.label == 'genomic_element_gene':
                    _id = '_'.join(
                        [element_id, readout_gene, self.file_accession])
                    _source = (
                        'genomic_elements/' + element_id + '_' + self.file_accession
                    )
                    _props = {
                        '_key': _id,
                        '_from': _source,
                        '_to': 'genes/' + readout_gene,
                        'source': IGVFE2GCRISPR.SOURCE,
                        'source_url': self.source_url,
                        'files_filesets': 'files_filesets/' + self.file_accession,
                        'label': self.COLLECTION_LABEL,
                        'class': file_fileset['class'],
                        'name': 'modulates expression of',
                        'inverse_name': 'expression modulated by',
                        'method': method,
                        'crispr_modality': crispr_modality,
                        'biological_context': file_fileset['simple_sample_summaries'][0],
                        'biosample_term': file_fileset['samples'][0],
                        'treatments_term_ids': file_fileset['treatments_term_ids'],
                    }
                    _props.update(metrics)
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
