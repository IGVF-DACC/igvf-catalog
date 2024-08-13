import os
import json
import gzip
import urllib
import tempfile
import rdflib
from owlready2 import *

from db.arango_db import ArangoDB
from adapters import Adapter


class Ontology(Adapter):
    OUTPUT_PATH = './parsed-data'

    ONTOLOGIES = {
        'uberon': 'https://api.data.igvf.org/reference-files/IGVFFI7985BGYI/@@download/IGVFFI7985BGYI.owl.gz',
        'clo': 'https://api.data.igvf.org/reference-files/IGVFFI7115PAJX/@@download/IGVFFI7115PAJX.owl.gz',
        'cl': 'https://api.data.igvf.org/reference-files/IGVFFI0402TNDW/@@download/IGVFFI0402TNDW.owl.gz',
        'hpo': 'https://api.data.igvf.org/reference-files/IGVFFI1298JRGV/@@download/IGVFFI1298JRGV.owl.gz',
        'mondo': 'https://api.data.igvf.org/reference-files/IGVFFI5120YZYR/@@download/IGVFFI5120YZYR.owl.gz',
        'go': 'https://api.data.igvf.org/reference-files/IGVFFI8306RHIV/@@download/IGVFFI8306RHIV.owl.gz',
        'efo': 'https://api.data.igvf.org/reference-files/IGVFFI1837PEKQ/@@download/IGVFFI1837PEKQ.owl.gz',
        'chebi': 'https://api.data.igvf.org/reference-files/IGVFFI6182DQZM/@@download/IGVFFI6182DQZM.owl.gz',
        'vario': 'https://api.data.igvf.org/reference-files/IGVFFI4219OZTA/@@download/IGVFFI4219OZTA.owl.gz',
        'orphanet': 'https://api.data.igvf.org/reference-files/IGVFFI8953HXRQ/@@download/IGVFFI8953HXRQ.owl.gz',
        'ncit': 'https://api.data.igvf.org/reference-files/IGVFFI2369NSDT/@@download/IGVFFI2369NSDT.owl.gz'
    }

    GO_SUBONTOLGIES = ['molecular_function',
                       'cellular_component', 'biological_process']

    HAS_PART = rdflib.term.URIRef('http://purl.obolibrary.org/obo/BFO_0000051')
    PART_OF = rdflib.term.URIRef('http://purl.obolibrary.org/obo/BFO_0000050')
    SUBCLASS = rdflib.term.URIRef(
        'http://www.w3.org/2000/01/rdf-schema#subClassOf')
    DB_XREF = rdflib.term.URIRef(
        'http://www.geneontology.org/formats/oboInOwl#hasDbXref')

    LABEL = rdflib.term.URIRef('http://www.w3.org/2000/01/rdf-schema#label')
    RESTRICTION = rdflib.term.URIRef(
        'http://www.w3.org/2002/07/owl#Restriction')
    TYPE = rdflib.term.URIRef(
        'http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
    ON_PROPERTY = rdflib.term.URIRef(
        'http://www.w3.org/2002/07/owl#onProperty')
    SOME_VALUES_FROM = rdflib.term.URIRef(
        'http://www.w3.org/2002/07/owl#someValuesFrom')
    ALL_VALUES_FROM = rdflib.term.URIRef(
        'http://www.w3.org/2002/07/owl#allValuesFrom')
    NAMESPACE = rdflib.term.URIRef(
        'http://www.geneontology.org/formats/oboInOwl#hasOBONamespace')
    EXACT_SYNONYM = rdflib.term.URIRef(
        'http://www.geneontology.org/formats/oboInOwl#hasExactSynonym')
    RELATED_SYNONYM = rdflib.term.URIRef(
        'http://www.geneontology.org/formats/oboInOwl#hasRelatedSynonym')
    DESCRIPTION = rdflib.term.URIRef(
        'http://purl.obolibrary.org/obo/IAO_0000115')

    PREDICATES = [SUBCLASS, DB_XREF]
    RESTRICTION_PREDICATES = [HAS_PART, PART_OF]

    def __init__(self, ontology, dry_run=True):
        if ontology not in Ontology.ONTOLOGIES.keys():
            raise ValueError('Ontology not supported.')

        self.dataset = 'ontology_term'
        self.label = 'ontology_term'

        self.dry_run = dry_run
        self.ontology = ontology

        super(Ontology, self).__init__()

    def process_file(self):
        path = '{}/{}-'.format(Ontology.OUTPUT_PATH, self.ontology)

        # primary: for example, Go ontology defining a Go term
        # secondary: for example, HPO ontology defining a Go term
        # primary data will replace secondary data when loading into DB
        self.outputs = {
            'node': {
                'primary': open(path + 'node-primary.json', 'w'),
                'secondary': open(path + 'node-secondary.json', 'w')
            },
            'edge': {
                'primary': open(path + 'edge-primary.json', 'w'),
                'secondary': open(path + 'edge-secondary.json', 'w')
            }
        }

        self.process_ontology()

        for t in self.outputs.keys():
            self.outputs[t]['primary'].close()
            self.outputs[t]['secondary'].close()

            self.save_to_arango(type=t)

    def process_ontology(self):
        print('Downloading {}...'.format(self.ontology))

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            with urllib.request.urlopen(Ontology.ONTOLOGIES[self.ontology]) as response:
                with gzip.GzipFile(fileobj=response) as uncompressed:
                    file_content = uncompressed.read()
                    temp_file.write(file_content)

            temp_file_path = temp_file.name
            onto = get_ontology(temp_file_path).load()

        self.graph = default_world.as_rdflib_graph()

        print('Caching values...')

        self.clear_cache()
        self.cache_edge_properties()
        self.cache_node_properties()

        print('Processing {}...'.format(self.ontology))

        for predicate in Ontology.PREDICATES:
            nodes = self.process_edges(predicate)

            if self.ontology != 'go':
                self.process_nodes(nodes)
            else:
                # Go nodes are processed independently of predicates to consider subontologies
                nodes_in_go_namespaces = self.find_go_nodes(self.graph)
                self.process_nodes(nodes, nodes_in_go_namespaces)

    def process_edges(self, predicate):
        nodes = set()

        edges = list(self.graph.subject_objects(
            predicate=predicate, unique=True))
        for edge in edges:
            from_node, to_node = edge

            if self.is_blank(from_node):
                continue

            if self.is_blank(to_node):
                if self.is_a_restriction_block(to_node):
                    restriction_predicate, restriction_node = self.read_restriction_block(
                        to_node)
                    if restriction_predicate is None or restriction_node is None:
                        continue

                    predicate = restriction_predicate
                    to_node = restriction_node

                # Ignore literal nodes such as numeric values and strings. Example: BNode('397')
                if isinstance(to_node, rdflib.term.BNode):
                    continue

            nodes.add(from_node)
            nodes.add(to_node)

            from_node_key = Ontology.to_key(from_node)
            predicate_key = Ontology.to_key(predicate)
            to_node_key = Ontology.to_key(to_node)

            if from_node_key is None or predicate_key is None or to_node_key is None:
                continue

            if predicate == Ontology.DB_XREF:
                if to_node.__class__ == rdflib.term.Literal:
                    if str(to_node) == str(from_node):
                        print('Skipping self xref for: ' + from_node_key)
                        continue

                    # only accepting IDs in the form <ontology>:<ontology_id>
                    if len(str(to_node).split(':')) != 2:
                        print(
                            'Unsupported format for xref: ' + str(to_node))
                        continue

                    to_node_key = str(to_node).replace(':', '_')

                    if from_node_key == to_node_key:
                        print('Skipping self xref for: ' + from_node_key)
                        continue
                else:
                    print('Ignoring non literal xref: {}'.format(str(to_node)))
                    continue

            key = '{}_{}_{}'.format(
                from_node_key,
                predicate_key,
                to_node_key
            )
            props = {
                '_key': key,
                '_from': 'ontology_terms/' + from_node_key,
                '_to': 'ontology_terms/' + to_node_key,
                'type': self.predicate_name(predicate),
                'type_uri': str(predicate),
                'source': self.ontology.upper()
            }

            self.save_props(props, True, 'edge')

        return nodes

    def process_nodes(self, nodes, go_namespaces={}):
        for node in nodes:
            # avoiding blank nodes and other arbitrary node types
            if not isinstance(node, rdflib.term.URIRef):
                continue

            term_id = str(node).split('/')[-1]

            key = Ontology.to_key(node)
            if key is None:
                continue

            props = {
                '_key': key,
                'uri': str(node),
                'term_id': str(node).split('/')[-1],
                'name': ', '.join(set(self.get_all_property_values_from_node(node, 'term_names'))).lower(),
                'description': ' '.join(set(self.get_all_property_values_from_node(node, 'descriptions'))),
                'synonyms': list(set(self.get_all_property_values_from_node(node, 'related_synonyms') +
                                     self.get_all_property_values_from_node(node, 'exact_synonyms'))),
                'source': self.ontology.upper(),
                'subontology': go_namespaces.get(node, None)
            }

            self.save_props(props, primary=(
                self.ontology in term_id.lower()), prop_type='node')

    def save_props(self, props, primary=True, prop_type='node'):
        save_to = self.outputs[prop_type]['primary']
        if not primary:
            save_to = self.outputs[prop_type]['secondary']

        json.dump(props, save_to)
        save_to.write('\n')

    def predicate_name(self, predicate):
        predicate = str(predicate)
        if predicate == str(Ontology.HAS_PART):
            return 'has part'
        elif predicate == str(Ontology.PART_OF):
            return 'part of'
        elif predicate == str(Ontology.SUBCLASS):
            return 'subclass'
        elif predicate == str(Ontology.DB_XREF):
            return 'database cross-reference'
        return ''

    # "http://purl.obolibrary.org/obo/CLO_0027762#subclass?id=123" => "CLO_0027762.subclass_id=123"
    # "12345" => "number_12345" - there are cases where URIs are just numbers, e.g. HPO

    @classmethod
    def to_key(cls, node_uri):
        components = str(node_uri).split('/')

        key = components[-1]
        key = key.replace('#', '.').replace('?', '_')
        key = key.replace('&', '.').replace('=', '_')
        key = key.replace('/', '_').replace('~', '.')
        key = key.replace(' ', '')

        # special case for HGNC, e.g. "hgnc/10001"
        if len(components) >= 2 and components[-2] == 'hgnc':
            key = components[-2].upper() + '_' + components[-1]

        if key.replace('.', '').isnumeric():
            return None

        return key

    # Example of a restriction block:
    # <rdfs:subClassOf>
    #     <owl:Restriction>
    #         <owl:onProperty rdf:resource="http://purl.obolibrary.org/obo/RO_0001000"/>
    #         <owl:someValuesFrom rdf:resource="http://purl.obolibrary.org/obo/CL_0000056"/>
    #     </owl:Restriction>
    # </rdfs:subClassOf>
    # This block must be interpreted as the triple (s, p, o):
    # (parent object, http://purl.obolibrary.org/obo/RO_0001000, http://purl.obolibrary.org/obo/CL_0000056)

    def is_a_restriction_block(self, node):
        node_type = self.get_all_property_values_from_node(node, 'node_types')
        return node_type and node_type[0] == str(Ontology.RESTRICTION)

    def read_restriction_block(self, node):
        restricted_property = self.get_all_property_values_from_node(
            node, 'on_property')

        # assuming a restriction block will always contain only one `owl:onProperty` triple
        if restricted_property and restricted_property[0] not in str(Ontology.RESTRICTION_PREDICATES):
            return None, None

        restriction_predicate = str(restricted_property[0])

        # returning the pair (owl:onProperty value, owl:someValuesFrom or owl:allValuesFrom value)
        # assuming a owl:Restriction block in a rdf:subClassOf will contain only one `owl:someValuesFrom` or `owl:allValuesFrom` triple
        some_values_from = self.get_all_property_values_from_node(
            node, 'some_values_from')
        if some_values_from:
            return (restriction_predicate, some_values_from[0])

        all_values_from = self.get_all_property_values_from_node(
            node, 'all_values_from')
        if all_values_from:
            return (restriction_predicate, all_values_from[0])

        return (None, None)

    def find_go_nodes(self, graph):
        # subontologies are defined as `namespaces`
        nodes_in_namespaces = list(graph.subject_objects(
            predicate=Ontology.NAMESPACE))

        node_namespace_lookup = {}
        for n in nodes_in_namespaces:
            node = n[0]
            namespace = str(n[1])
            if namespace in Ontology.GO_SUBONTOLGIES:
                node_namespace_lookup[node] = namespace

        return node_namespace_lookup

    def is_blank(self, node):
        # a BNode according to rdflib is a general node (as a 'catch all' node) that doesn't have any type such as Class, Literal, etc.
        BLANK_NODE = rdflib.term.BNode

        return isinstance(node, BLANK_NODE)

    def arangodb(self, primary=True, type='node'):
        collection = self.collection
        if type == 'edge':
            collection = self.collection + '_' + self.collection

        if primary is False:
            return ArangoDB().generate_json_import_statement(self.outputs[type]['secondary'].name, collection, type=type)

        return ArangoDB().generate_json_import_statement(self.outputs[type]['primary'].name, collection, type=type, replace=True)

    def save_to_arango(self, type='node'):
        if self.dry_run:
            print(self.arangodb(primary=False, type=type)[0])
            print(self.arangodb(type=type)[0])
        else:
            os.system(self.arangodb(primary=False, type=type)[0])
            os.system(self.arangodb(type=type)[0])

    # it's faster to load all subject/objects beforehand
    def clear_cache(self):
        self.cache = {}

    def cache_edge_properties(self):
        self.cache['node_types'] = self.cache_predicate(Ontology.TYPE)
        self.cache['on_property'] = self.cache_predicate(Ontology.ON_PROPERTY)
        self.cache['some_values_from'] = self.cache_predicate(
            Ontology.SOME_VALUES_FROM)
        self.cache['all_values_from'] = self.cache_predicate(
            Ontology.ALL_VALUES_FROM)

    def cache_node_properties(self):
        self.cache['term_names'] = self.cache_predicate(Ontology.LABEL)
        self.cache['descriptions'] = self.cache_predicate(Ontology.DESCRIPTION)
        self.cache['related_synonyms'] = self.cache_predicate(
            Ontology.EXACT_SYNONYM)
        self.cache['exact_synonyms'] = self.cache_predicate(
            Ontology.RELATED_SYNONYM)

    def cache_predicate(self, predicate):
        return list(self.graph.subject_objects(predicate=predicate))

    def get_all_property_values_from_node(self, node, collection):
        values = []
        for subject_object in self.cache[collection]:
            subject, object = subject_object
            if subject == node:
                values.append(str(object))
        return values
