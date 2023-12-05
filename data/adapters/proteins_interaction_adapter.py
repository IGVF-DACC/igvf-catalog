import csv
import os
import json
from adapters import Adapter
from db.arango_db import ArangoDB

# Example lines in merged_PPI.UniProt.example.csv:
# Protein ID 1,Protein ID 2,Detection Method,Detection Method (PSI-MI),Interaction Type,Interaction Type (PSI-MI),Confidence Value,Source,PMIDs
# O75340,Q8WUM4,pull down,MI:0096,direct interaction,MI:0407,0.87,BioGRID; IntAct,"['9880530', '18940611', '18256029']"
# Q13111,P24941,pull down,MI:0096,direct interaction,MI:0407,0.44,BioGRID; IntAct,['16826239']


class ProteinsInteraction(Adapter):

    OUTPUT_PATH = './parsed-data'
    SKIP_BIOCYPHER = True

    def __init__(self, filepath, label, dry_run=True):
        self.filepath = filepath
        self.dataset = label
        self.label = label
        self.dry_run = dry_run
        self.type = 'edge'
        self.output_filepath = '{}/{}.json'.format(
            ProteinsInteraction.OUTPUT_PATH,
            self.dataset
        )

        super(ProteinsInteraction, self).__init__()

    def process_file(self):
        parsed_data_file = open(self.output_filepath, 'w')

        with open(self.filepath, 'r') as interaction_file:
            interaction_csv = csv.reader(interaction_file)
            next(interaction_csv)
            for row in interaction_csv:
                pmid_url = 'http://pubmed.ncbi.nlm.nih.gov/'
                pmids = [pmid_url + pmid.replace("'", '') for pmid in row[8].replace(
                    '[', '').replace(']', '').split(', ')]

                _key = row[0] + '_' + row[1]
                # needs to append detection method, interaction type... if we want to load those same pairs individually
                props = {
                    '_key': _key,
                    '_from': 'proteins/' + row[0],
                    '_to': 'proteins/' + row[1],

                    'detection_method': row[2],
                    'detection_method_code': row[3],
                    'interaction_type': row[4],
                    'interaction_type_code': row[5],
                    'confidence_value': row[6],
                    'source': row[7],  # BioGRID or IntAct or BioGRID; IntAct
                    'pmids': pmids
                }
                json.dump(props, parsed_data_file)
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
