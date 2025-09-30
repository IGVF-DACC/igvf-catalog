import csv
import json
import os
import gzip
import re
from typing import Optional
from schemas.registry import get_schema
from jsonschema import Draft202012Validator, ValidationError

from adapters.helpers import bulk_query_coding_variants_in_arangodb, bulk_query_coding_variants_from_hgvsc_in_arangodb, bulk_query_coding_variants_Met1_in_arangodb
from adapters.file_fileset_adapter import FileFileSet
from adapters.writer import Writer

# Example line from file from CYP2C19 VAMP-seq (IGVFFI0629IIQU.tsv.gz):
# variant	score	standard_error	rep1_score	rep2_score	rep3_score
# ENSP00000360372.3:p.Ala103Cys	0.902654998066618	0.0551255935523091	0.79741948771822	0.983743944202336	0.926801562279298

# Example line from file from F9 VAMP-seq(MultiSTEP) (IGVFFI8987JRZH.tsv.gz)
# variant	score	standard_error	rep1_tile1_score	rep1_tile2_score	rep1_tile3_score	rep2_tile1_score	rep2_tile2_score	rep2_tile3_score	rep3_tile1_score	rep3_tile2_score	rep3_tile3_score
# ENSP00000218099.2:p.Ile334Val	1.0288110839938078	0.07662282613325597			0.9213742806403278			0.9878924294091088			1.1771665419319868

# Note: parsing phenotype term from input arg for now, possible to query it from funcional_assay_mechanisms
# An extra set of coding variants for VAMP-seq (e.g. aa changes to Ter requiring multiple bases & synonymous variants) are loaded from data/data_loading_support_files/map_VAMP_synonmous_variants.py


class VAMPAdapter:
    ALLOWED_LABELS = ['coding_variants_phenotypes']
    SOURCE = 'IGVF'
    PHENOTYPE_EDGE_NAME = 'mutational effect'
    PHENOTYPE_EDGE_INVERSE_NAME = 'altered due to mutation'
    CHUNK_SIZE = 1000

    def __init__(self, filepath, label='coding_variants_phenotypes', phenotype_term=None, writer: Optional[Writer] = None, validate=False, **kwargs):
        if label not in VAMPAdapter.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(VAMPAdapter.ALLOWED_LABELS))
        self.label = label
        self.filepath = filepath
        self.file_accession = os.path.basename(self.filepath).split('.')[0]
        self.source_url = 'https://data.igvf.org/tabular-files/' + self.file_accession
        self.phenotype_term = phenotype_term
        self.files_filesets = FileFileSet(self.file_accession)
        self.writer = writer
        self.validate = validate
        if self.validate:
            if self.label == 'coding_variants_phenotypes':
                self.schema = get_schema(
                    'edges', 'coding_variants_phenotypes', self.__class__.__name__)
            self.validator = Draft202012Validator(self.schema)

    def validate_doc(self, doc):
        try:
            self.validator.validate(doc)
        except ValidationError as e:
            raise ValueError(f'Document validation failed: {e.message}')

    def process_coding_variant_phenotype_chunk(self, chunk, type='hgvsp'):
        skipped_coding_variants = []
        if type == 'hgvsp':
            mapped_coding_variants = bulk_query_coding_variants_in_arangodb(
                [(row[0].split(':')[0].split('.')[0], row[0].split(':')[1].strip()) for row in chunk])
        elif type == 'hgvsc':  # query from hgvsc at transcript level
            mapped_coding_variants = bulk_query_coding_variants_from_hgvsc_in_arangodb(
                [(row[0].split(':')[0].split('.')[0], row[0].split(':')[1].strip()) for row in chunk])
        elif type == 'Met1':  # Met1 case
            mapped_coding_variants = bulk_query_coding_variants_Met1_in_arangodb(
                [(row[0].split(':')[0].split('.')[0], row[0].split(':')[1].strip()) for row in chunk])
        else:
            print('Invalid type in bulk coding variants query.')
            return

        for row in chunk:
            query_pair = (row[0].split(':')[0].split('.')[
                0], row[0].split(':')[1].strip())
            if query_pair not in mapped_coding_variants:
                print(
                    f'ERROR: {row[0]} not found in coding variants collection')
                skipped_coding_variants.append(row[0])
            else:
                coding_variant_ids = mapped_coding_variants[query_pair]
                for coding_variant_id in coding_variant_ids:
                    edge_key = coding_variant_id + '_' + \
                        self.phenotype_term + '_' + self.file_accession
                    _props = {
                        '_key': edge_key,
                        '_from': 'coding_variants/' + coding_variant_id,
                        '_to': 'ontology_terms/' + self.phenotype_term,
                        'source': self.SOURCE,
                        'source_url': self.source_url,
                        'name': self.PHENOTYPE_EDGE_NAME,
                        'inverse_name': self.PHENOTYPE_EDGE_INVERSE_NAME,
                        'files_filesets': 'files_filesets/' + self.file_accession,
                        'simple_sample_summaries': self.igvf_metadata_props.get('simple_sample_summaries'),
                        'method': self.igvf_metadata_props.get('method'),
                        'biological_context': self.igvf_metadata_props['samples'][0] if 'samples' in self.igvf_metadata_props else None,
                    }
                    for i, value in enumerate(row[1:], 1):
                        prop = {}
                        prop[self.header[i]] = float(value) if value else None
                        _props.update(prop)

                    if self.validate:
                        self.validate_doc(_props)

                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')

        if skipped_coding_variants:
            with open(f'./skipped_coding_variants_{self.file_accession}.txt', 'a') as skipped_list:
                for skipped in skipped_coding_variants:
                    skipped_list.write(skipped + '\n')

    def process_coding_variant_phenotype_chunk(self, chunk, type='hgvsp'):
        skipped_coding_variants = []
        if type == 'hgvsp':
            mapped_coding_variants = bulk_query_coding_variants_in_arangodb(
                [(row[0].split(':')[0].split('.')[0], row[0].split(':')[1].strip()) for row in chunk])
        elif type == 'hgvsc':  # query from hgvsc at transcript level
            mapped_coding_variants = bulk_query_coding_variants_from_hgvsc_in_arangodb(
                [(row[0].split(':')[0].split('.')[0], row[0].split(':')[1].strip()) for row in chunk])
        elif type == 'Met1':  # Met1 case
            mapped_coding_variants = bulk_query_coding_variants_Met1_in_arangodb(
                [(row[0].split(':')[0].split('.')[0], row[0].split(':')[1].strip()) for row in chunk])
        else:
            print('Invalid type in bulk coding variants query.')
            return

        for row in chunk:
            query_pair = (row[0].split(':')[0].split('.')[
                0], row[0].split(':')[1].strip())
            if query_pair not in mapped_coding_variants:
                print(
                    f'ERROR: {row[0]} not found in coding variants collection')
                skipped_coding_variants.append(row[0])
            else:
                coding_variant_ids = mapped_coding_variants[query_pair]
                for coding_variant_id in coding_variant_ids:
                    edge_key = coding_variant_id + '_' + \
                        self.phenotype_term + '_' + self.file_accession
                    _props = {
                        '_key': edge_key,
                        '_from': 'coding_variants/' + coding_variant_id,
                        '_to': 'ontology_terms/' + self.phenotype_term,
                        'source': self.SOURCE,
                        'source_url': self.source_url,
                        'name': self.PHENOTYPE_EDGE_NAME,
                        'inverse_name': self.PHENOTYPE_EDGE_INVERSE_NAME,
                        'files_filesets': 'files_filesets/' + self.file_accession,
                        'simple_sample_summaries': self.igvf_metadata_props.get('simple_sample_summaries'),
                        'method': self.igvf_metadata_props.get('method'),
                        'biological_context': self.igvf_metadata_props['samples'][0] if 'samples' in self.igvf_metadata_props else None,
                    }
                    for i, value in enumerate(row[1:], 1):
                        prop = {}
                        prop[self.header[i]] = float(value) if value else None
                        _props.update(prop)

                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')

        if skipped_coding_variants:
            with open(f'./skipped_coding_variants_{self.file_accession}.txt', 'a') as skipped_list:
                for skipped in skipped_coding_variants:
                    skipped_list.write(skipped + '\n')

    def process_file(self):
        self.writer.open()
        self.igvf_metadata_props = self.files_filesets.query_fileset_files_props_igvf(
            self.file_accession)[0]
        # process those rows all together at the end (arango query is different from hgvsp rows)
        hgvsc_rows = []
        met1_rows = []
        pattern_Met1 = re.compile(r'p\.Met1[A-Za-z]{3}')
        with gzip.open(self.filepath, 'rt') as vamp_file:
            vamp_csv = csv.reader(vamp_file, delimiter='\t')
            self.header = next(vamp_csv)
            chunk = []

            for i, row in enumerate(vamp_csv, 1):
                # transcript level scores e.g. ENST00000371321.9:c.948C>T
                if row[0].startswith('ENST'):
                    hgvsc_rows.append(row)
                # special query for Met1 case (aa alt not in _keys)
                elif pattern_Met1.search(row[0]):
                    met1_rows.append(row)
                else:
                    chunk.append(row)
                if len(chunk) % self.CHUNK_SIZE == 0:
                    if self.label == 'coding_variants_phenotypes':
                        self.process_coding_variant_phenotype_chunk(chunk)
                    chunk = []

            if chunk != []:
                if self.label == 'coding_variants_phenotypes':
                    self.process_coding_variant_phenotype_chunk(chunk)

            self.process_coding_variant_phenotype_chunk(
                hgvsc_rows, type='hgvsc')

            self.process_coding_variant_phenotype_chunk(met1_rows, type='Met1')

        self.writer.close()
