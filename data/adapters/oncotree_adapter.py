import requests
from adapters import Adapter

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


class Oncotree(Adapter):
    SOURCE = 'Oncotree'
    SOURCE_URL = 'https://oncotree.mskcc.org/'
    API_URL = 'https://oncotree.mskcc.org:443/api/tumorTypes'

    def __init__(self, type):
        self.type = type

        if type == 'node':
            self.dataset = 'ontology_term'
            self.label = 'ontology_term'
        else:
            self.dataset = 'ontology_relationship'
            self.label = 'ontology_relationship'

        super(Oncotree, self).__init__()

    def process_file(self):
        oncotree_json = requests.get(Oncotree.API_URL).json()
        for node in oncotree_json:
            # reformating for one illegal term: MDS/MPN
            key = node['code'].replace('/', '_')

            if self.type == 'node':
                _id = 'Oncotree_' + key
                _props = {
                    'term_id': 'Oncotree_' + node['code'],
                    'term_name': node['name'],
                    # could add those two new props for ontology terms in future
                    # 'main_type': node['mainType'],
                    # 'tissue': node['tissue'],
                    'source': Oncotree.SOURCE,
                    # didn't find individual uri for each node so not sure if this is appropriate
                    'uri': Oncotree.SOURCE_URL
                }

                yield(_id, self.label, _props)

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
                        'type': type,
                        'source': Oncotree.SOURCE,
                    }

                    yield(_id, _source, _target, self.label, _props)

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
                                'type': type,
                                'source': Oncotree.SOURCE,
                            }

                            yield(_id, _source, _target, self.label, _props)
