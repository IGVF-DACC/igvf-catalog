import csv
import gzip
import json
from typing import Optional

from adapters.base import BaseAdapter
from adapters.gene_validator import GeneValidator
from adapters.helpers import bulk_check_variants_in_arangodb, load_variant, get_file_fileset_by_accession_in_arangodb
from adapters.writer import Writer

# Example from IGVFFI9602ILPC (Variant-EFFECTS / V2G CRISPR)
# variant	chr	pos	ref	alt	effect_allele	other_allele	gene	gene_symbol	effect_size	log2_fold_change	p_nominal_nlog10	fdr_nlog10	fdr_method	power	VariantID_h19
# NC_000010.11:79347444::CCTCCTCAGG	chr10	79347444		CCTCCTCAGG	CCTCCTCAGG		ENSG00000108179	PPIF	-0.022057224	-0.032178046	1.86224451	1.778299483	Benjamini-Hochberg	0.054202114	chr10:81107199:A>ACCTCCTCAGG


class IGVFV2GCRISPR(BaseAdapter):
    ALLOWED_LABELS = ['variant', 'variant_gene']
    SOURCE = 'IGVF'
    CHUNK_SIZE = 6500

    def __init__(self, filepath, label, source_url, writer: Optional[Writer] = None, validate=False, **kwargs):
        self.source_url = source_url
        self.file_accession = source_url.rstrip('/').split('/')[-1]
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
    def _open_tsv(filepath):
        if filepath.endswith('.gz'):
            return gzip.open(filepath, 'rt')
        return open(filepath, 'r')

    def parse(self):
        with self._open_tsv(self.filepath) as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader)
            chunk = []
            for i, row in enumerate(reader, 1):
                chunk.append(row)
                if i % IGVFV2GCRISPR.CHUNK_SIZE == 0:
                    self.process_chunk(chunk)
                    chunk = []

            if chunk:
                self.process_chunk(chunk)

    def process_chunk(self, chunk):
        spdi_to_variant = {}
        spdi_to_row = {}
        skipped_spdis = []
        for row in chunk:
            gene = row[7]
            if not self.gene_validator.validate(gene):
                raise ValueError(
                    f'{gene} is not a valid gene.')

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

        if skipped_spdis:
            self.logger.warning(f'Skipped {len(skipped_spdis)} variants:')
            for skipped in skipped_spdis:
                self.logger.warning(
                    f"  - {skipped['variant_id']}: {skipped['reason']}")
            with open('./skipped_variants.jsonl', 'a') as out:
                for skipped in skipped_spdis:
                    out.write(json.dumps(skipped) + '\n')

        loaded_variants = bulk_check_variants_in_arangodb(
            list(spdi_to_variant.keys()))

        if self.label == 'variant':
            self.process_variants(spdi_to_variant, loaded_variants)
        elif self.label == 'variant_gene':
            self.process_edge(spdi_to_row, loaded_variants)

    def process_variants(self, spdi_to_variant, loaded_variants):
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

    def process_edge(self, spdi_to_row, loaded_variants):
        for variant in spdi_to_row:
            if variant in loaded_variants:
                for row in spdi_to_row[variant]:
                    edge_props = {
                        '_key': f'{variant}_{row[7]}_{self.file_accession}',
                        '_from': f'variants/{variant}',
                        '_to': f'genes/{row[7]}',
                        'effect_size': float(row[9]),
                        'log2_fold_change': float(row[10]),
                        'neg_log10_pvalue': float(row[11]),
                        'neg_log10_pvalue_adj': float(row[12]),
                        'power': float(row[14]) if row[14] else None,
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
