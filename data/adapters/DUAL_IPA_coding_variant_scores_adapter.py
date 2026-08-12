import csv
import json
import os
import gzip
from typing import Optional

from adapters.base import BaseAdapter
from adapters.helpers import bulk_query_coding_variants_from_spdi_in_arangodb, get_file_fileset_by_accession_in_arangodb
from adapters.writer import Writer

# Example line from DUAL-IPA score file (IGVFFI6224HZMG.tsv.gz):
# spdi	symbol	ensembl_gene_id	ccsb_mutation_id	CCSB_referenece_orf_id	hgvs_orf	hgvs_protein	avg_gfp	avg_mcherry	avg_GFP_mCherry_ratio	wt_GFP_mCherry_ratio	allele_wt_ratio	dualipa_abun_score	dualipa_abun_change
# NC_000016.10:89100729:G:C  ACSF3  ENSG00000176715  CCSBVarC008268  CCSBORF71337  49G>C  ENSP00000320646.4:p.Ala17Pro  795.99  4593.57  0.2886  0.3983  0.7247  -1.2568  Uncertain

FLOAT_COLUMNS = ['avg_gfp', 'avg_mcherry', 'avg_GFP_mCherry_ratio',
                 'wt_GFP_mCherry_ratio', 'allele_wt_ratio', 'dualipa_abun_score']
STRING_COLUMNS = ['dualipa_abun_change']


class DUALIPAAdapter(BaseAdapter):
    ALLOWED_LABELS = ['coding_variants_phenotypes']
    SOURCE = 'IGVF'
    LABEL = 'protein variant effect'
    PHENOTYPE_EDGE_NAME = 'mutational effect'
    PHENOTYPE_EDGE_INVERSE_NAME = 'altered due to mutation'
    PHENOTYPE_TERM = 'BAO_0040014'
    CHUNK_SIZE = 100

    def __init__(self, filepath, label='coding_variants_phenotypes', writer: Optional[Writer] = None, validate=False, **kwargs):
        self.file_accession = os.path.basename(filepath).split('.')[0]
        self.source_url = 'https://data.igvf.org/tabular-files/' + self.file_accession

        super().__init__(filepath, label, writer, validate)

    def _get_schema_type(self):
        return 'edges'

    def _get_collection_name(self):
        return 'coding_variants_phenotypes'

    def process_coding_variant_phenotype_chunk(self, chunk, file_fileset_obj):
        skipped_coding_variants = []
        # col 0 = spdi, col 6 = hgvs_protein e.g. ENSP00000320646.4:p.Ala17Pro
        mapped_coding_variants = bulk_query_coding_variants_from_spdi_in_arangodb(
            [(row[0], row[6].split(':')[0].split('.')[0],
              row[6].split(':')[1].strip()) for row in chunk]
        )

        for row in chunk:
            query_pair = (row[0], row[6].split(':')[0].split(
                '.')[0], row[6].split(':')[1].strip())
            if query_pair not in mapped_coding_variants:
                self.logger.error(
                    f'ERROR: {row[0]} / {row[6]} not found in coding variants collection')
                skipped_coding_variants.append(row[0])
            else:
                coding_variant_ids = mapped_coding_variants[query_pair]
                for coding_variant_id in coding_variant_ids:
                    edge_key = coding_variant_id + '_' + \
                        self.PHENOTYPE_TERM + '_' + self.file_accession
                    _props = {
                        '_key': edge_key,
                        '_from': 'coding_variants/' + coding_variant_id,
                        '_to': 'ontology_terms/' + self.PHENOTYPE_TERM,
                        'source': self.SOURCE,
                        'source_url': self.source_url,
                        'name': self.PHENOTYPE_EDGE_NAME,
                        'inverse_name': self.PHENOTYPE_EDGE_INVERSE_NAME,
                        'files_filesets': 'files_filesets/' + self.file_accession,
                        'method': file_fileset_obj['method'] if file_fileset_obj else None,
                        'class': file_fileset_obj['class'] if file_fileset_obj else None,
                        'label': DUALIPAAdapter.LABEL,
                        'biological_context': file_fileset_obj['simple_sample_summaries'][0] if file_fileset_obj else None,
                        'biosample_term': file_fileset_obj['samples'][0] if file_fileset_obj else None,
                    }

                    for col in FLOAT_COLUMNS:
                        idx = self.header.index(col)
                        _props[col] = float(row[idx]) if row[idx] else None
                    for col in STRING_COLUMNS:
                        idx = self.header.index(col)
                        _props[col] = row[idx] if row[idx] else None

                    if self.validate:
                        self.validate_doc(_props)

                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')

        if skipped_coding_variants:
            with open(f'./skipped_coding_variants_{self.file_accession}.txt', 'a') as skipped_list:
                for skipped in skipped_coding_variants:
                    skipped_list.write(skipped + '\n')

    def parse(self):
        file_fileset_obj = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        if file_fileset_obj is None:
            self.logger.warning(
                f'WARNING: file_fileset not found for {self.file_accession}, file_fileset fields will be None')
        with gzip.open(self.filepath, 'rt') as dual_ipa_file:
            self.writer.add_tag('portal_accessions', self.file_accession)
            dual_ipa_csv = csv.reader(dual_ipa_file, delimiter='\t')
            self.header = next(dual_ipa_csv)
            chunk = []

            for row in dual_ipa_csv:
                chunk.append(row)
                if len(chunk) % self.CHUNK_SIZE == 0:
                    if self.label == 'coding_variants_phenotypes':
                        self.process_coding_variant_phenotype_chunk(
                            chunk, file_fileset_obj)
                    chunk = []

            if chunk:
                if self.label == 'coding_variants_phenotypes':
                    self.process_coding_variant_phenotype_chunk(
                        chunk, file_fileset_obj)
