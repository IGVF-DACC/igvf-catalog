import json
import requests
from typing import Optional
from jsonschema import Draft202012Validator, ValidationError

from schemas.registry import get_schema

from adapters.writer import Writer

# The tumor types are available from oncotree api: https://oncotree.mskcc.org:443/api/tumorTypes
# Example for one tumor type node:
# {'code': 'MMB',
#  'color': 'Gray',
#  'name': 'Medullomyoblastoma',
#  'mainType': 'Embryonal Tumor',
#  'externalReferences': {'UMLS': ['C0205833'], 'NCI': ['C3706']},
#  'tissue': 'CNS/Brain',
#  'children': {},
#  'parent': 'EMBT',
#  'history': [],
#  'level': 3,
#  'revocations': [],
#  'precursors': []},

# The hierarchical classification tree can also be explored from: https://oncotree.mskcc.org/


class Oncotree:
    SOURCE = 'Oncotree'
    URI = 'https://oncotree.mskcc.org/'
    API_URL = 'https://oncotree.mskcc.org:443/api/tumorTypes'
    SOURCE_URL = 'https://oncotree.mskcc.org/api/tumorTypes'

    def __init__(self, type, writer: Optional[Writer] = None, validate=False, **kwargs):
        self.type = type
        self.writer = writer
        self.validate = validate
        if self.validate:
            if self.type == 'node':
                self.schema = get_schema(
                    'nodes', 'ontology_terms', self.__class__.__name__)
            else:
                self.schema = get_schema(
                    'edges', 'ontology_terms_ontology_terms', self.__class__.__name__)
            self.validator = Draft202012Validator(self.schema)

    def validate_doc(self, doc):
        try:
            self.validator.validate(doc)
        except ValidationError as e:
            raise ValueError(f'Document validation failed: {e.message}')

    def process_file(self):
        self.writer.open()
        oncotree_json = requests.get(Oncotree.API_URL).json()
        for node in oncotree_json:
            # reformating for one illegal term: MDS/MPN
            key = node['code'].replace('/', '_')

            if self.type == 'node':
                _id = 'Oncotree_' + key
                _props = {
                    '_key': _id,
                    'term_id': 'Oncotree_' + node['code'],
                    'name': node['name'],
                    # could add those two new props for ontology terms in future
                    # 'main_type': node['mainType'],
                    # 'tissue': node['tissue'],
                    'source': Oncotree.SOURCE,
                    # didn't find individual uri for each node so not sure if this is appropriate
                    'uri': Oncotree.URI,
                    'source_url': Oncotree.SOURCE_URL
                }

                if self.validate:
                    self.validate_doc(_props)
                self.writer.write(json.dumps(_props))
                self.writer.write('\n')

            else:
                _source = 'ontology_terms/Oncotree_' + key

                if node['parent'] is not None:  # node['parent'] is a single str
                    type = 'subclass'
                    parent_key = node['parent'].replace('/', '_')
                    _id = '{}_{}_{}'.format(
                        'Oncotree_' + key,
                        'rdf-schema.subClassOf',
                        'Oncotree_' + parent_key
                    )
                    _target = 'ontology_terms/Oncotree_' + parent_key
                    _props = {
                        'name': type,
                        'inverse_name': 'type of',
                        '_key': _id,
                        '_from': _source,
                        '_to': _target,
                        'type': type,
                        'source': Oncotree.SOURCE,
                    }

                    if self.validate:
                        self.validate_doc(_props)
                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')

                if node['externalReferences']:
                    type = 'database cross-reference'
                    if node['externalReferences'].get('NCI') is not None:
                        for NCIT_id in node['externalReferences']['NCI']:
                            _id = '{}_{}_{}'.format(
                                'Oncotree_' + key,
                                'oboInOwl.hasDbXref',
                                'NCIT_' + NCIT_id
                            )
                            _target = 'ontology_terms/NCIT_' + NCIT_id
                            _props = {
                                'name': type,
                                'inverse_name': 'database cross-reference',
                                '_key': _id,
                                '_from': _source,
                                '_to': _target,
                                'type': type,
                                'source': Oncotree.SOURCE,
                            }

                            if self.validate:
                                self.validate_doc(_props)
                            self.writer.write(json.dumps(_props))
                            self.writer.write('\n')
        self.writer.close()
