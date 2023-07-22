import obonet
import json
import os

from db.arango_db import ArangoDB
from adapters import Adapter

#### Description on obo file ####
#################################


class Cellosaurus(Adapter):
    SOURCE = 'Cellosaurus'
    SOURCE_URL_PREFIX = 'https://www.cellosaurus.org/'
    NODE_KEYS = ['name', 'synonym', 'subset']
    EDGE_KEYS = ['xref', 'relationship']
    EDGE_TYPES = ['database cross-reference',
                  'originate from same individual as', 'derived from']

    SKIP_BIOCYPHER = True
    OUTPUT_PATH = './parsed-data'

    def __init__(self, filepath, type='node', dry_run=True):
        self.filepath = filepath
        self.type = type
        self.dry_run = dry_run
        if type == 'node':
            self.dataset = 'ontology_term'
        else:
            self.dataset = 'ontology_relationship'

        self.output_filepath = '{}/{}_{}.json'.format(
            Cellosaurus.OUTPUT_PATH,
            self.dataset,
            Cellosaurus.SOURCE
        )

        super(Cellosaurus, self).__init__()

    def process_file(self):
        self.parsed_data_file = open(self.output_filepath, 'w')
        graph = obonet.read_obo(self.filepath)
        if self.type == 'node':
            for node in graph.nodes():
                node_dict = graph.nodes[node]
                if self.type == 'node':
                    synonyms = None
                    # e.g. "HL-1 Friendly Myeloma 653" RELATED []
                    if node_dict.get('synonyms'):
                        synonyms = [syn.split('"')[1]
                                    for syn in node_dict['synonyms']]

                    props = {
                        '_key': node,
                        'uri': Cellosaurus.SOURCE_URL_PREFIX + node,
                        'term_id': node,
                        'term_name': node_dict.get('name', None),
                        'synonyms': synonyms,
                        'source': Cellosaurus.SOURCE,
                        'subset': node_dict.get('subset', None)
                    }
                    self.save_props(props)
        else:
            same_individual_pairs = []
            for node in graph.nodes():
                node_dict = graph.nodes[node]
                if node_dict.get('xref'):
                    edge_type = 'database cross-reference'
                    # could have url for each xref, need some work from cellosaurus_xrefs.txt
                    for xref in node_dict['xref']:
                        xref_key = self.to_key(xref)

                        key = '{}_{}_{}'.format(
                            node,
                            'oboInOwl.hasDbXref',  # check
                            xref_key
                        )

                        props = {
                            '_key': key,
                            '_from': 'ontology_terms/' + node,
                            '_to': 'ontology_terms/' + xref_key,
                            'type': edge_type,
                            'source': Cellosaurus.SOURCE
                        }

                        self.save_props(props)

                if node_dict.get('relationship'):
                    for relation in node_dict['relationship']:
                        edge_type, to_node_key = relation.split(' ')[:2]
                        if edge_type == 'originate_from_same_individual_as':  # symmetric relationship, check redundancy
                            if '-'.join([to_node_key, node]) in same_individual_pairs:
                                continue
                            else:
                                same_individual_pairs.append(
                                    '-'.join([node, to_node_key]))

                        key = '{}_{}_{}'.format(
                            node,
                            edge_type,
                            to_node_key
                        )

                        props = {
                            '_key': key,
                            '_from': 'ontology_terms/' + node,
                            '_to': 'ontology_terms/' + to_node_key,
                            'type': edge_type.replace('_', ' '),
                            'source': Cellosaurus.SOURCE
                        }

                        self.save_props(props)

        self.parsed_data_file.close()
        self.save_to_arango()

    def save_props(self, props):
        json.dump(props, self.parsed_data_file)
        self.parsed_data_file.write('\n')

    def save_to_arango(self):
        if self.dry_run:
            print(self.arangodb()[0])
        else:
            os.system(self.arangodb()[0])

    def arangodb(self):
        return ArangoDB().generate_json_import_statement(self.output_filepath, self.collection, type=self.type)

    def to_key(self, xref):  # need more edits
        key = xref.replace(':', '_').replace('/', '_').replace(' ', '_')
        return key
