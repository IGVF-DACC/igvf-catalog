import json
from typing import Optional

from adapters.archive_utils import get_file_accession, get_files_from_folder
from adapters.base import BaseAdapter
from adapters.helpers import get_file_fileset_by_accession_in_arangodb
from adapters.writer import Writer

# Tumor types are downloaded from the OncoTree API as a flat JSON array and
# uploaded to the IGVF portal as a reference file:
#   https://data.igvf.org/reference-files/IGVFFI4975UFZM/
# Original API: https://oncotree.mskcc.org/api/tumorTypes?version=oncotree_latest_stable
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
#
# The flattened API omits the root TISSUE node; this adapter injects it so
# level-1 subclass edges (e.g. SKIN → TISSUE) have a target term.
# The hierarchical classification tree can also be explored from:
# https://oncotree.mskcc.org/


class Oncotree(BaseAdapter):
    SOURCE = 'Oncotree'
    URI = 'https://oncotree.mskcc.org/'
    SOURCE_URL = 'https://oncotree.mskcc.org/api/tumorTypes'
    ALLOWED_LABELS = ['node', 'edge']
    ROOT_NODE = {
        'code': 'TISSUE',
        'name': 'Tissue',
        'parent': None,
        'externalReferences': {
            'NCI': ['C12801'],
            'UMLS': ['C0040300'],
        },
    }

    def __init__(self, filepath, label, writer: Optional[Writer] = None, validate=False, **kwargs):
        super().__init__(filepath, label, writer, validate)
        self.file_accession = get_file_accession(filepath)

    def _get_schema_type(self):
        if self.label == 'node':
            return 'nodes'
        return 'edges'

    def _get_collection_name(self):
        if self.label == 'node':
            return 'ontology_terms'
        return 'ontology_terms_ontology_terms'

    def parse(self):
        self.writer.add_tag('portal_accessions', self.file_accession)
        file_metadata = get_file_fileset_by_accession_in_arangodb(
            self.file_accession)
        self.collection_class = file_metadata['class']
        self.method = file_metadata['method']

        for member in get_files_from_folder(self.filepath):
            with member.open() as input_file:
                oncotree_json = json.load(input_file)
            break

        if not any(node.get('code') == 'TISSUE' for node in oncotree_json):
            oncotree_json = [Oncotree.ROOT_NODE] + oncotree_json

        for node in oncotree_json:
            # reformating for one illegal term: MDS/MPN
            key = node['code'].replace('/', '_')

            if self.label == 'node':
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
                    'source_url': Oncotree.SOURCE_URL,
                    'class': self.collection_class,
                    'method': self.method,
                    'files_filesets': 'files_filesets/' + self.file_accession,
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
                        'class': self.collection_class,
                        'method': self.method,
                        'files_filesets': 'files_filesets/' + self.file_accession,
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
                                'class': self.collection_class,
                                'method': self.method,
                                'files_filesets': 'files_filesets/' + self.file_accession,
                            }

                            if self.validate:
                                self.validate_doc(_props)
                            self.writer.write(json.dumps(_props))
                            self.writer.write('\n')
