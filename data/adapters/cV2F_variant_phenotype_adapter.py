import csv
import json
import os
import gzip
from adapters.file_fileset_adapter import FileFileSet
from adapters.helpers import bulk_check_variants_in_arangodb, load_variant

from typing import Optional
from adapters.writer import Writer

# load 1 sample-agnostic cV2F file + 9 sample-specific cV2F files, each file has the same input variants
# only load rows with predicted scores passing threshold
# sample parsing from the metadata fields under prediction set , not from files

# Example rows from sample-agnostic cV2F file (IGVFFI1931RMNE.tsv.gz)
# PredictionValue threshold 0.75
# VariantChr      VariantStart    VariantEnd      EffectAllele    OtherAllele     SPDI_ID GOOntology      BiosampleTermName       BiosampleTerm   PredictionType  PredictionValue
# chr1    10203   10203   A       C       NC_000001.11:10202:C:A  GO:0003674      AGNOSTIC                continuous score        0.384271964430809

# Example rows from sample-specific cV2F file (IGVFFI4594QVDO.tsv.gz)
# PredictionValue threshold 0.75
# VariantChr      VariantStart    VariantEnd      EffectAllele    OtherAllele     SPDI_ID GOOntology      BiosampleTermName       BiosampleTerm   PredictionType  PredictionValue
# chr1    10203   10203   A       C       NC_000001.11:10202:C:A  GO:0003674      K562    EFO_0002067     continuous score        0.368436226248741


class cV2F:
    # don't expect to load novel variants from cV2F prediction file - input variants should be from Y2AVE set
    ALLOWED_LABELS = ['variants', 'variants_phenotypes']
    SOURCE = 'IGVF'
    PHENOTYPE_TERM = 'GO_0003674'  # Molecular Function
    THRESHOLD = 0.75

    def __init__(self, filepath, label='variants_phenotypes', writer: Optional[Writer] = None, **kwargs):
        if label not in cV2F.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(cV2F.ALLOWED_LABELS))

        self.filepath = filepath
        self.file_accession = os.path.basename(self.filepath).split('.')[0]
        self.source_url = 'https://data.igvf.org/tabular-files/' + self.file_accession
        self.label = label
        self.writer = writer
        self.files_filesets = FileFileSet(self.file_accession)

    def process_variants_chunk(self, chunk):
        loaded_spdis = bulk_check_variants_in_arangodb(
            [row[5] for row in chunk])
        for row in chunk:
            if row[5] not in loaded_spdis:
                variant_props, skipped = load_variant(row[5])
                if variant_props:
                    variant_props.update({
                        'source': self.SOURCE,
                        'source_url': self.source_url,
                        'files_filesets': 'files_filesets/' + self.file_accession
                    })
                    self.writer.write(json.dumps(variant_props))
                    self.writer.write('\n')
                elif skipped:
                    print(
                        f"Invalid variant: {skipped['variant_id']} - {skipped['reason']}")

    def process_variants_phenotypes_chunk(self, chunk):
        self.igvf_metadata_props = self.files_filesets.query_fileset_files_props_igvf(
            self.file_accession)[0]
        loaded_spdis = bulk_check_variants_in_arangodb(
            [row[5] for row in chunk])
        for row in chunk:
            if row[5] not in loaded_spdis:
                _, skipped = load_variant(row[5])
                # skipping invalid variants (e.g. mismatched ref cases) in original file
                if skipped is not None:
                    print(
                        f"Invalid variant: {skipped['variant_id']} - {skipped['reason']}")
                    continue
            # create edge if variant already loaded or is valid
            spdi = row[5]
            edge_key = spdi + '_' + self.PHENOTYPE_TERM + '_' + self.file_accession
            props = {
                '_key': edge_key,
                '_from': 'variants/' + spdi,
                '_to': 'ontology_terms/' + self.PHENOTYPE_TERM,
                'score': float(row[-1]),
                'source': self.SOURCE,
                'source_url': self.source_url,
                'name': 'associated with',
                'inverse_name': 'associated with',
                'files_filesets': 'files_filesets/' + self.file_accession,
                'simple_sample_summaries': self.igvf_metadata_props.get('simple_sample_summaries'),
                'method': self.igvf_metadata_props.get('method')
            }
            if self.igvf_metadata_props.get('samples'):
                props.update(
                    {'biological_context': self.igvf_metadata_props['samples'][0]})

            self.writer.write(json.dumps(props))
            self.writer.write('\n')

    def process_file(self):
        self.writer.open()
        with gzip.open(self.filepath, 'rt') as input_file:
            reader = csv.reader(input_file, delimiter='\t')
            next(reader)
            headers = next(reader)
            chunk_size = 6500
            chunk = []

            for i, row in enumerate(reader, 1):
                if float(row[-1]) >= cV2F.THRESHOLD:  # only load rows passing threshold
                    chunk.append(row)
                    if len(chunk) >= chunk_size:
                        if self.label == 'variants':
                            self.process_variants_chunk(chunk)
                        elif self.label == 'variants_phenotypes':
                            self.process_variants_phenotypes_chunk(
                                chunk)
                        chunk = []
        if chunk:
            if self.label == 'variants':
                self.process_variants_chunk(chunk)
            elif self.label == 'variants_phenotypes':
                self.process_variants_phenotypes_chunk(
                    chunk)

        self.writer.close()
