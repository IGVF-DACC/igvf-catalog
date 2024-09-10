from adapters import Adapter
import gzip
import json
import os
from db.arango_db import ArangoDB
import requests
from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import JSONDecodeError

# This adapter is used to parse Reactome pathway data.
# the input file is last modified on 2024-06-03 and is available at: https://reactome.org/download/current/ReactomePathways.txt
# Example pathway input file:
# R-GGA-199992	trans-Golgi Network Vesicle Budding	Gallus gallus
# R-HSA-164843	2-LTR circle formation	Homo sapiens
# R-HSA-73843	5-Phosphoribose 1-diphosphate biosynthesis	Homo sapiens
# R-HSA-1971475	A tetrasaccharide linker sequence is required for GAG synthesis	Homo sapiens
# R-HSA-5619084	ABC transporter disorders	Homo sapiens


class ReactomePathway(Adapter):

    OUTPUT_FOLDER = './parsed-data'

    def __init__(self, filepath=None, dry_run=False):

        self.filepath = filepath
        self.label = 'pathway'
        self.dataset = 'pathway'
        if not os.path.exists(ReactomePathway.OUTPUT_FOLDER):
            os.makedirs(ReactomePathway.OUTPUT_FOLDER)
        self.output_filepath = '{}/{}.json'.format(
            ReactomePathway.OUTPUT_FOLDER,
            self.dataset,
        )
        self.dry_run = dry_run

        super(ReactomePathway, self).__init__()

    def process_file(self):
        parsed_data_file = open(self.output_filepath, 'w')
        session = requests.Session()
        retries = Retry(total=5, backoff_factor=1,
                        status_forcelist=[500, 502, 503, 504])
        session.mount('https://', HTTPAdapter(max_retries=retries))

        with open(self.filepath) as input:
            for line in input:
                id, name, organism = line.strip().split('\t')
                if organism == 'Homo sapiens':
                    to_json = {
                        '_key': id,
                        'name': name,
                        'organism': organism,
                        'source': 'Reactome',
                        'source_url': 'https://reactome.org/'
                    }

                    try:
                        query = 'https://reactome.org/ContentService/data/query/' + id
                        response = session.get(query)
                        if response.status_code == 404:
                            print(
                                f'Fail to find pathway {id}. The source file may be outdated')
                            continue
                        data = response.json()
                        id_version = data['stIdVersion']
                        is_in_disease = data['isInDisease']
                        name_aliases = data['name']
                        is_top_level_pathway = False
                        if data['className'] == 'TopLevelPathway':
                            is_top_level_pathway = True
                        to_json.update(
                            {
                                'id_version': id_version,
                                'is_in_disease': is_in_disease,
                                'name_aliases': name_aliases,
                                'is_top_level_pathway': is_top_level_pathway
                            }
                        )
                        if is_in_disease:
                            disease = data.get('disease')
                            disease_ontology_terms = []
                            for d in disease:
                                disease_ontology_term = 'ontology_terms/' + \
                                    d['databaseName'] + '_' + d['identifier']
                                disease_ontology_terms.append(
                                    disease_ontology_term)
                            to_json.update(
                                {'disease_ontology_terms': disease_ontology_terms}
                            )
                        go_biological_process = data.get('goBiologicalProcess')
                        if go_biological_process:
                            to_json.update(
                                {
                                    'go_biological_process': 'ontology_terms/' + go_biological_process['databaseName'] + '_' + go_biological_process['accession']
                                }
                            )
                        json.dump(to_json, parsed_data_file)
                        parsed_data_file.write('\n')
                    except JSONDecodeError as e:
                        print(
                            f'Can not query for {query}. The status code is {response.status_code}. The text is {response.text}')
                        raise JSONDecodeError()

        parsed_data_file.close()
        self.save_to_arango()

    def arangodb(self):
        return ArangoDB().generate_json_import_statement(self.output_filepath, self.collection)

    def save_to_arango(self):
        if self.dry_run:
            print(self.arangodb()[0])
        else:
            os.system(self.arangodb()[0])
