import csv
import json
import os

import pickle
from adapters import Adapter
from db.arango_db import ArangoDB

# Example line from file from CYP2C19 VAMP-seq (IGVFFI5890AHYL):
# variant	abundance_score	abundance_sd	abundance_se	ci_upper	ci_lower	abundance_Rep1	abundance_Rep2	abundance_Rep3
# ENSP00000360372.3:p.Ala103Cys	0.902654998066618	0.0954803288299908	0.0551255935523091	0.9564024517801190	0.8489075443531170	0.7974194877182200	0.983743944202336	0.926801562279298
# ENSP00000360372.3:p.Ala103Asp	0.5857497278869870	0.0603323988117348	0.0348329266948109	0.6197118314144270	0.5517876243595460	0.5265040329858070	0.647113071129789	0.5836320795453640


class VAMPAdapter(Adapter):
    ALLOWED_LABELS = ['vamp_coding_variants_phenotypes']
    SOURCE = 'VAMP-seq'
    SOURCE_URL = 'https://data.igvf.org/analysis-sets/IGVFDS0368ZLPX/'
    CODING_VARIANTS_MAPPING_PATH = './data_loading_support_files/VAMP_coding_variants_ids.pkl'

    PHENOTYPE_TERM = 'OBA_0000128'  # protein stability

    OUTPUT_PATH = './parsed-data'

    def __init__(self, filepath, label='vamp_coding_variants_phenotypes', dry_run=True):
        if label not in VAMPAdapter.ALLOWED_LABELS:
            raise ValueError('Ivalid label. Allowed values: ' +
                             ','.join(VAMPAdapter.ALLOWED_LABELS))

        self.filepath = filepath
        self.label = label
        self.dataset = label
        self.type = 'edge'
        self.dry_run = dry_run
        self.output_filepath = '{}/{}.json'.format(
            self.OUTPUT_PATH,
            self.dataset
        )
        super().__init__()

    def process_file(self):
        parsed_data_file = open(self.output_filepath, 'w')
        self.load_coding_variant_id()

        with open(self.filepath, 'r') as vamp_file:
            vamp_csv = csv.reader(vamp_file)
            next(vamp_csv)
            for row in vamp_csv:
                if not row[1]:  # no abundance score
                    continue

                if row[0] in self.coding_variant_id:
                    for _id in self.coding_variant_id[row[0]]:
                        edge_key = _id + '_' + VAMPAdapter.PHENOTYPE_TERM
                        _props = {
                            '_key': edge_key,
                            '_from': 'coding_variants/' + _id,
                            '_to': 'ontology_terms/' + VAMPAdapter.PHENOTYPE_TERM,
                            'abundance_score:long': float(row[1]),
                            'abundance_sd:long': float(row[2]) if row[2] else None,
                            'abundance_se:long': float(row[3]) if row[3] else None,
                            'ci_upper:long': float(row[4]) if row[4] else None,
                            'ci_lower:long': float(row[5]) if row[5] else None,
                            'abundance_Rep1:long': float(row[6]) if row[6] else None,
                            'abundance_Rep2:long': float(row[7]) if row[7] else None,
                            'abundance_Rep3:long': float(row[8]) if row[8] else None,
                            'source': VAMPAdapter.SOURCE,
                            'source_url': VAMPAdapter.SOURCE_URL
                        }

                        json.dump(_props, parsed_data_file)
                        parsed_data_file.write('\n')

        parsed_data_file.close()
        self.save_to_arango()

    def load_coding_variant_id(self):
        self.coding_variant_id = {}
        with open(VAMPAdapter.CODING_VARIANTS_MAPPING_PATH, 'rb') as coding_variant_id_file:
            self.coding_variant_id = pickle.load(coding_variant_id_file)

    def save_to_arango(self):
        if self.dry_run:
            print(self.arangodb()[0])
        else:
            os.system(self.arangodb()[0])

    def arangodb(self):
        return ArangoDB().generate_json_import_statement(self.output_filepath, self.collection, type=self.type)
