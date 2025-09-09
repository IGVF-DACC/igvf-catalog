import json
from typing import Optional

import requests
from requests.adapters import HTTPAdapter, Retry
from json import JSONDecodeError
from jsonschema import Draft202012Validator, ValidationError

from adapters.writer import Writer
from schemas.registry import get_schema

# This adapter is used to parse Reactome pathway data.
# the input file is last modified on 2024-06-03 and is available at: https://reactome.org/download/current/ReactomePathways.txt
# Example pathway input file:
# R-GGA-199992	trans-Golgi Network Vesicle Budding	Gallus gallus
# R-HSA-164843	2-LTR circle formation	Homo sapiens
# R-HSA-73843	5-Phosphoribose 1-diphosphate biosynthesis	Homo sapiens
# R-HSA-1971475	A tetrasaccharide linker sequence is required for GAG synthesis	Homo sapiens
# R-HSA-5619084	ABC transporter disorders	Homo sapiens


class ReactomePathway:

    def __init__(self, filepath=None, dry_run=False, writer: Optional[Writer] = None, validate=False, **kwargs):
        self.filepath = filepath
        self.label = 'pathway'
        self.dataset = 'pathway'
        self.dry_run = dry_run
        self.writer = writer
        self.validate = validate
        if self.validate:
            self.schema = get_schema(
                'nodes', 'pathways', self.__class__.__name__)
            self.validator = Draft202012Validator(self.schema)

    def validate_doc(self, doc):
        try:
            self.validator.validate(doc)
        except ValidationError as e:
            raise ValueError(f'Document validation failed: {e.message}')

    def process_file(self):
        self.writer.open()
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
                        if self.validate:
                            self.validate_doc(to_json)
                        self.writer.write(json.dumps(to_json))
                        self.writer.write('\n')
                    except JSONDecodeError as e:
                        print(
                            f'Can not query for {query}. The status code is {response.status_code}. The text is {response.text}')
                        raise JSONDecodeError()

        self.writer.close()
