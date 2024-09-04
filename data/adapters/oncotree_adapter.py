import json
import os
import requests
from typing import Optional

from adapters import Adapter
from db.arango_db import ArangoDB
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
    SOURCE_URL = 'https://oncotree.mskcc.org/'
    API_URL = 'https://oncotree.mskcc.org:443/api/tumorTypes'

    def __init__(self, type, dry_run=True, writer: Optional[Writer] = None):
        self.type = type

        if self.type == 'node':
            self.dataset = 'ontology_term'
            self.label = 'ontology_term'
        else:
            self.dataset = 'ontology_relationship'
            self.label = 'ontology_relationship'
        self.dry_run = dry_run
        self.writer = writer

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
                    'uri': Oncotree.SOURCE_URL
                }

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

                            self.writer.write(json.dumps(_props))
                            self.writer.write('\n')
        self.writer.close()

    def save_to_arango(self):
        if self.dry_run:
            print(self.arangodb()[0])
        else:
            os.system(self.arangodb()[0])

    def arangodb(self):
        return ArangoDB().generate_json_import_statement(self.writer.destination, self.collection, type=self.type)
