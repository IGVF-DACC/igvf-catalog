import csv
import gzip
import json
import math
from typing import Optional

from adapters.base import BaseAdapter
from adapters.gene_validator import GeneValidator
from adapters.helpers import bulk_check_variants_in_arangodb, load_variant, get_file_fileset_by_accession_in_arangodb
from adapters.writer import Writer

# CRISPR-Millipede outputs for CD19 enhancer screens omit a gene column; readout is always CD19.
CRISPR_MILLIPEDE_FILE_ACCESSIONS = frozenset({
    'IGVFFI4769NVJT',
    'IGVFFI8101RHSC',
})
CD19_ENSEMBL_ID = 'ENSG00000177455'
# CRISPR-Millipede regression outputs include intercept terms that are not variant effects.
CRISPR_MILLIPEDE_INTERCEPT_ROW_IDS = frozenset({
    'intercept_exp0_rep0',
    'intercept_exp0_rep1',
    'intercept_exp0_rep2',
    'Intercept',
})

# Example from IGVFFI9602ILPC (Variant-EFFECTS)
# variant	chr	pos	ref	alt	effect_allele	other_allele	gene	gene_symbol	effect_size	log2_fold_change	p_nominal_nlog10	fdr_nlog10	fdr_method	power	VariantID_h19
# NC_000010.11:79347444::CCTCCTCAGG chr10   79347444        CCTCCTCAGG  CCTCCTCAGG      ENSG00000108179 PPIF    -0.022057224    -0.032178046    1.86224451  1.778299483 Benjamini-Hochberg  0.054202114 chr10:81107199:A>ACCTCCTCAGG

# Example from IGVFFI8101RHSC (CRISPR-Millipede / CD19 enhancer screen)
# variants,PIP,Betas,Coefficient StdDev
# NC_000016.10:28930710:G:A,0.0284163262526425,-0.0116633875205405,0.0699744682130392


class IGVFV2GCRISPR(BaseAdapter):
    ALLOWED_LABELS = ['variant', 'variant_gene']
    SOURCE = 'IGVF'
    CHUNK_SIZE = 6500
    P_VALUE_SIGNIFICANCE_THRESHOLD = 0.05
    PIP_SIGNIFICANCE_THRESHOLD = 0.1

    def __init__(self, filepath, label, source_url, writer: Optional[Writer] = None, validate=False, **kwargs):
        self.source_url = source_url
        self.file_accession = source_url.rstrip('/').split('/')[-1]
        self.is_crispr_millipede = self.file_accession in CRISPR_MILLIPEDE_FILE_ACCESSIONS
        self.gene_validator = GeneValidator()

        file_fileset = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        self.method = file_fileset['method']
        self.simple_sample_summaries = file_fileset['simple_sample_summaries']
        self.biosample_term = file_fileset['samples'][0]
        self.treatments_term_ids = file_fileset['treatments_term_ids']
        self.crispr_modality = file_fileset.get('crispr_modality')

        super().__init__(filepath, label, writer, validate)

    def _get_schema_type(self):
        if self.label == 'variant':
            return 'nodes'
        return 'edges'

    def _get_collection_name(self):
        if self.label == 'variant':
            return 'variants'
        return 'variants_genes'

    @staticmethod
    def _open_file(filepath):
        if filepath.endswith('.gz'):
            return gzip.open(filepath, 'rt')
        return open(filepath, 'r')

    @staticmethod
    def _crispr_millipede_intercept_row_id(variant_id: str) -> Optional[str]:
        """Return the intercept row id when the row is a known CRISPR-Millipede model term."""
        normalized = variant_id.strip()
        if normalized in CRISPR_MILLIPEDE_INTERCEPT_ROW_IDS:
            return normalized
        return None

    def _log_skipped_crispr_millipede_intercept_rows(self, intercept_row_ids: list[str]) -> None:
        if not intercept_row_ids:
            return
        self.logger.info(
            'Skipping %d CRISPR-Millipede intercept model term row(s) in %s '
            '(not variants): %s',
            len(intercept_row_ids),
            self.file_accession,
            ', '.join(intercept_row_ids),
        )

    @staticmethod
    def _fractional_effect_size_to_log2_fold_change(effect_size: float) -> Optional[float]:
        """Convert fractional expression change to log2 fold-change.

        effect_size is (expression_effect_allele / expression_other_allele) - 1,
        so log2FC = log2(1 + effect_size). Matches Variant-EFFECTS log2_fold_change.
        """
        ratio = 1 + effect_size
        if ratio <= 0:
            return None
        return math.log2(ratio)

    @staticmethod
    def _neg_log10_to_pvalue(neg_log10_pvalue: float) -> float:
        return 10 ** (-neg_log10_pvalue)

    @classmethod
    def _is_variant_effects_significant(cls, neg_log10_pvalue_adj: Optional[float]) -> bool:
        if neg_log10_pvalue_adj is None:
            return False
        return cls._neg_log10_to_pvalue(neg_log10_pvalue_adj) < cls.P_VALUE_SIGNIFICANCE_THRESHOLD

    @classmethod
    def _is_millipede_significant(cls, posterior_inclusion_probability: Optional[float]) -> bool:
        if posterior_inclusion_probability is None:
            return False
        return posterior_inclusion_probability > cls.PIP_SIGNIFICANCE_THRESHOLD

    def parse(self):
        self.writer.add_tag('portal_accessions', self.file_accession)
        if self.is_crispr_millipede:
            self._parse_crispr_millipede()
        else:
            self._parse_variant_effects()

    def _parse_variant_effects(self):
        with self._open_file(self.filepath) as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader)
            chunk = []
            for i, row in enumerate(reader, 1):
                chunk.append(row)
                if i % IGVFV2GCRISPR.CHUNK_SIZE == 0:
                    self._process_variant_effects_chunk(chunk)
                    chunk = []

            if chunk:
                self._process_variant_effects_chunk(chunk)

    def _parse_crispr_millipede(self):
        with self._open_file(self.filepath) as f:
            reader = csv.reader(f, delimiter=',')
            header = next(reader)
            name_to_idx = {h.strip(): i for i, h in enumerate(header)}
            chunk = []
            for i, row in enumerate(reader, 1):
                chunk.append((row, name_to_idx))
                if i % IGVFV2GCRISPR.CHUNK_SIZE == 0:
                    self._process_crispr_millipede_chunk(chunk)
                    chunk = []

            if chunk:
                self._process_crispr_millipede_chunk(chunk)

    def _process_variant_effects_chunk(self, chunk):
        spdi_to_variant = {}
        spdi_to_row = {}
        skipped_spdis = []
        for row in chunk:
            gene = row[7]
            if not self.gene_validator.validate(gene):
                raise ValueError(f'{gene} is not a valid gene.')

            spdi = row[0]
            variant, skipped_message = load_variant(spdi)

            if variant:
                normalized_spdi = variant['spdi']
                spdi_to_variant[normalized_spdi] = variant
                if normalized_spdi not in spdi_to_row:
                    spdi_to_row[normalized_spdi] = []
                spdi_to_row[normalized_spdi].append(row)

            if skipped_message is not None:
                skipped_spdis.append(skipped_message)

        self._finish_chunk(spdi_to_variant, spdi_to_row, skipped_spdis)

    def _process_crispr_millipede_chunk(self, chunk):
        if not self.gene_validator.validate(CD19_ENSEMBL_ID):
            raise ValueError(f'{CD19_ENSEMBL_ID} is not a valid gene.')

        spdi_to_variant = {}
        spdi_to_row = {}
        skipped_spdis = []
        skipped_intercept_rows = []
        for row, name_to_idx in chunk:
            spdi = row[name_to_idx['variants']].strip()
            intercept_row_id = self._crispr_millipede_intercept_row_id(spdi)
            if intercept_row_id is not None:
                skipped_intercept_rows.append(intercept_row_id)
                continue

            variant, skipped_message = load_variant(spdi)

            if variant:
                normalized_spdi = variant['spdi']
                spdi_to_variant[normalized_spdi] = variant
                if normalized_spdi not in spdi_to_row:
                    spdi_to_row[normalized_spdi] = []
                spdi_to_row[normalized_spdi].append(row)

            if skipped_message is not None:
                skipped_spdis.append(skipped_message)

        self._log_skipped_crispr_millipede_intercept_rows(
            skipped_intercept_rows)
        self._finish_chunk(spdi_to_variant, spdi_to_row, skipped_spdis)

    def _finish_chunk(self, spdi_to_variant, spdi_to_row, skipped_spdis):
        if skipped_spdis:
            self.logger.warning(f'Skipped {len(skipped_spdis)} variants:')
            for skipped in skipped_spdis:
                self.logger.warning(
                    f"  - {skipped['variant_id']}: {skipped['reason']}")
            with open('./skipped_variants.jsonl', 'a') as out:
                for skipped in skipped_spdis:
                    out.write(json.dumps(skipped) + '\n')

        if self.label == 'variant':
            loaded_variants = bulk_check_variants_in_arangodb(
                list(spdi_to_variant.keys()),
                excluded_files_filesets=f'files_filesets/{self.file_accession}',
            )
        else:
            loaded_variants = bulk_check_variants_in_arangodb(
                list(spdi_to_variant.keys()))

        if self.label == 'variant':
            self._write_variants(spdi_to_variant, loaded_variants)
        elif self.label == 'variant_gene':
            if self.is_crispr_millipede:
                self._write_crispr_millipede_edges(
                    spdi_to_row, loaded_variants)
            else:
                self._write_variant_effects_edges(spdi_to_row, loaded_variants)

    def _write_variants(self, spdi_to_variant, loaded_variants):
        for spdi, variant in spdi_to_variant.items():
            if spdi in loaded_variants:
                continue
            variant.update({
                'source': self.SOURCE,
                'source_url': self.source_url,
                'files_filesets': f'files_filesets/{self.file_accession}'
            })
            if self.validate:
                self.validate_doc(variant)
            self.writer.write(json.dumps(variant) + '\n')

    def _write_variant_effects_edges(self, spdi_to_row, loaded_variants):
        for variant in spdi_to_row:
            if variant in loaded_variants:
                for row in spdi_to_row[variant]:
                    neg_log10_pvalue_adj = float(row[12])
                    edge_props = {
                        '_key': f'{variant}_{row[7]}_{self.file_accession}',
                        '_from': f'variants/{variant}',
                        '_to': f'genes/{row[7]}',
                        'effect_size': float(row[9]),
                        'log2FC': float(row[10]),
                        'neg_log10_pvalue': float(row[11]),
                        'neg_log10_pvalue_adj': neg_log10_pvalue_adj,
                        'power': float(row[14]) if row[14] else None,
                        'posterior_inclusion_probability': None,
                        'coefficient_stddev': None,
                        'significant': self._is_variant_effects_significant(
                            neg_log10_pvalue_adj),
                        'class': 'observed data',
                        'label': 'variant effect on gene expression',
                        'name': 'modulates expression of',
                        'inverse_name': 'expression modulated by',
                        'source': self.SOURCE,
                        'source_url': self.source_url,
                        'files_filesets': f'files_filesets/{self.file_accession}',
                        'method': self.method,
                        'crispr_modality': self.crispr_modality,
                        'biological_context': self.simple_sample_summaries[0],
                        'biosample_term': self.biosample_term,
                        'treatments_term_ids': self.treatments_term_ids,
                    }

                    if self.validate:
                        self.validate_doc(edge_props)
                    self.writer.write(json.dumps(edge_props) + '\n')

    def _write_crispr_millipede_edges(self, spdi_to_row, loaded_variants):
        for variant in spdi_to_row:
            if variant in loaded_variants:
                for row in spdi_to_row[variant]:
                    effect_size = float(row[2])
                    posterior_inclusion_probability = float(row[1])
                    edge_props = {
                        '_key': f'{variant}_{CD19_ENSEMBL_ID}_{self.file_accession}',
                        '_from': f'variants/{variant}',
                        '_to': f'genes/{CD19_ENSEMBL_ID}',
                        'effect_size': effect_size,
                        'log2FC': self._fractional_effect_size_to_log2_fold_change(
                            effect_size),
                        'neg_log10_pvalue': None,
                        'neg_log10_pvalue_adj': None,
                        'power': None,
                        'posterior_inclusion_probability': posterior_inclusion_probability,
                        'coefficient_stddev': float(row[3]),
                        'significant': self._is_millipede_significant(
                            posterior_inclusion_probability),
                        'class': 'observed data',
                        'label': 'variant effect on gene expression',
                        'name': 'modulates expression of',
                        'inverse_name': 'expression modulated by',
                        'source': self.SOURCE,
                        'source_url': self.source_url,
                        'files_filesets': f'files_filesets/{self.file_accession}',
                        'method': self.method,
                        'crispr_modality': self.crispr_modality,
                        'biological_context': self.simple_sample_summaries[0],
                        'biosample_term': self.biosample_term,
                        'treatments_term_ids': self.treatments_term_ids,
                    }

                    if self.validate:
                        self.validate_doc(edge_props)
                    self.writer.write(json.dumps(edge_props) + '\n')
