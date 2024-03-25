import csv
import os
import json
from adapters import Adapter
from db.arango_db import ArangoDB

# Example lines in merged_PPI.UniProt.csv (and merged_PPI_mouse.UniProt.csv for mouse):
# Protein ID 1,Protein ID 2,PMID,Detection Method,Detection Method (PSI-MI),Interaction Type,Interaction Type (PSI-MI),Confidence Value (biogrid),Confidence Value (intact),Source
# P0CL82,P36888,[28625976],genetic interference,MI:0254,sensu biogrid,MI:2371,,,BioGRID
# Q9Y243,Q9Y6H6,[33961781],affinity chromatography technology,MI:0004,physical association,MI:0915,0.990648979,,BioGRID


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

        if 'mouse' in self.filepath.split('/')[-1]:
            self.organism = 'Mus musculus'
        else:
            self.organism = 'Homo sapiens'

        super(ProteinsInteraction, self).__init__()

    def process_file(self):
        parsed_data_file = open(self.output_filepath, 'w')

        with open(self.filepath, 'r') as interaction_file:
            interaction_csv = csv.reader(interaction_file)
            next(interaction_csv)
            for row in interaction_csv:
                # skip detection method = 'genetic interference', they need to be in genes_genes
                if row[3] == 'genetic interference':
                    continue

                pmid_url = 'http://pubmed.ncbi.nlm.nih.gov/'
                pmids = [pmid.replace("'", '') for pmid in row[2].replace(
                    '[', '').replace(']', '').split(', ')]

                # load each combination of protein pairs + detection method + pmids as individual edges
                _key = '_'.join(
                    [row[0], row[1], row[4].replace(':', '_')] + pmids)

                props = {
                    '_key': _key,
                    '_from': 'proteins/' + row[0],
                    '_to': 'proteins/' + row[1],

                    'detection_method': row[3],
                    'detection_method_code': row[4],
                    'interaction_type': row[5],
                    'interaction_type_code': row[6],
                    'confidence_value_biogrid:long': float(row[7]) if row[7] else None,
                    'confidence_value_intact:long': float(row[-2]) if row[-2] else None,
                    'source': row[-1],  # BioGRID or IntAct or BioGRID; IntAct
                    'pmids': [pmid_url + pmid for pmid in pmids],
                    'organism': self.organism
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
