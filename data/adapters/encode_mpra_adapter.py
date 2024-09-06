import csv
import gzip
import json
import os
from adapters import Adapter
from adapters.helpers import build_regulatory_region_id
from db.arango_db import ArangoDB


# Example rows from ENCODE lenti-MPRA bed file ENCFF802FUV.bed: (the last two columns are the same for all rows)
# Column 7: activity score (i.e. log2(RNA/DNA)); Column 8: DNA count; Column 9: RNA count
# chr1	10410	10610	HepG2_DNasePeakNoPromoter1	212	+	-0.843	0.307	0.171	-1	-1

class EncodeMPRA(Adapter):

    SOURCE = 'ENCODE_MPRA'

    ALLOWED_LABELS = [
        'regulatory_region',
        'regulatory_region_biosample'
    ]
    OUTPUT_PATH = './parsed-data'

    def __init__(self, filepath, label, source_url, biological_context, dry_run=True):  # other?
        if label not in EncodeMPRA.ALLOWED_LABELS:
            raise ValueError('Ivalid label. Allowed values: ' +
                             ','.join(EncodeMPRA.ALLOWED_LABELS))
        self.filepath = filepath
        self.label = label
        self.source_url = source_url
        self.file_accession = source_url.split('/')[-2]
        self.biological_context = biological_context
        self.dataset = label
        self.dry_run = dry_run
        self.type = 'edge'
        if(self.label == 'regulatory_region'):
            self.type = 'node'

        self.output_filepath = '{}/{}.json'.format(
            self.OUTPUT_PATH,
            self.dataset
        )

        super(EncodeMPRA, self).__init__()

    def process_file(self):
        parsed_data_file = open(self.output_filepath, 'w')
        with gzip.open(self.filepath, 'rt') as mpra_file:
            mpra_csv = csv.reader(mpra_file, delimiter='\t')
            for row in mpra_csv:
                chr = row[0]
                start = row[1]
                end = row[2]

                regulatory_region_id = build_regulatory_region_id(
                    chr, start, end, 'MPRA'
                )

                if self.label == 'regulatory_region':
                    _id = regulatory_region_id
                    _props = {
                        '_key': _id,
                        'chr': chr,
                        'start': start,
                        'end': end,
                        'type': 'MPRA_tested_regulatory_element',
                        'source': EncodeMPRA.SOURCE,
                        'source_url': self.source_url
                    }

                    json.dump(_props, parsed_data_file)
                    parsed_data_file.write('\n')

                elif self.label == 'regulatory_region_biosample':
                    _id = '_'.join(
                        [regulatory_region_id, self.file_accession, self.biological_context])
                    _source = 'regulatory_regions/' + regulatory_region_id
                    _target = 'ontology_terms/' + self.biological_context
                    _props = {
                        '_key': _id,
                        '_from': _source,
                        '_to': _target,
                        'type': 'MPRA_expression_tested',
                        'element_name': row[3],
                        'strand': row[5],
                        'activity_score': row[6],
                        'bed_score': row[4],
                        'DNA_count': row[7],
                        'RNA_count': row[8],
                        'source': EncodeMPRA.SOURCE,
                        'source_url': self.source_url
                    }
                    json.dump(_props, parsed_data_file)
                    parsed_data_file.write('\n')
        parsed_data_file.close()
        self.save_to_arango()

    def save_to_arango(self):
        if self.dry_run:
            print(self.arangodb()[0])
        else:
            os.system(self.arangodb()[0])

    def arangodb(self):
        return ArangoDB().generate_json_import_statement(self.output_filepath, self.collection, type=self.type)
