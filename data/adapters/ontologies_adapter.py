import os
import json
import rdflib
from owlready2 import *

from db.arango_db import ArangoDB
from adapters import Adapter


class Ontology(Adapter):
    SKIP_BIOCYPHER = True
    OUTPUT_PATH = './parsed-data'

    ONTOLOGIES = {
        'uberon': 'http://purl.obolibrary.org/obo/uberon.owl',
        'clo': 'http://purl.obolibrary.org/obo/clo.owl',
        'cl': 'http://purl.obolibrary.org/obo/cl.owl',
        'hpo': 'https://github.com/obophenotype/human-phenotype-ontology/releases/download/v2023-01-27/hp.owl',
        'mondo': 'https://github.com/monarch-initiative/mondo/releases/download/v2023-02-06/mondo.owl',
        'go': 'http://purl.obolibrary.org/obo/go.owl',
        'efo': 'https://github.com/EBISPOT/efo/releases/download/current/efo.owl',
        'chebi': 'https://ftp.ebi.ac.uk/pub/databases/chebi/ontology/chebi.owl',
        'vario': 'http://purl.obolibrary.org/obo/vario.owl'
    }

    GO_SUBONTOLGIES = ['molecular_function',
                       'cellular_component', 'biological_process']

    HAS_PART = rdflib.term.URIRef('http://purl.obolibrary.org/obo/BFO_0000051')
    PART_OF = rdflib.term.URIRef('http://purl.obolibrary.org/obo/BFO_0000050')
    SUBCLASS = rdflib.term.URIRef(
        'http://www.w3.org/2000/01/rdf-schema#subClassOf')

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

    PREDICATES = [SUBCLASS]
    RESTRICTION_PREDICATES = [HAS_PART, PART_OF]

    def __init__(self, type='node', dry_run=True):
        self.type = type
        self.dry_run = dry_run
        if type == 'node':
            self.dataset = 'ontology_term'
        else:
            self.dataset = 'ontology_relationship'

        super(Ontology, self).__init__()

    def process_file(self):
        for ontology in Ontology.ONTOLOGIES.keys():
            self.ontology = ontology

            path = '{}/{}-{}-'.format(Ontology.OUTPUT_PATH,
                                      ontology, self.type)

            # source of truth:
            # primary: for example, Go ontology defining a Go term
            # secondary: for example, HPO ontology defining a Go term
            output_filepath_primary = path + 'primary.json'
            output_filepath_secondary = path + 'secondary.json'

            self.primary_output = open(output_filepath_primary, 'w')
            self.secondary_output = open(output_filepath_secondary, 'w')

            self.process_ontology()

            self.primary_output.close()
            self.secondary_output.close()

            self.save_to_arango()

    def process_ontology(self):
        print('Processing {}...'.format(self.ontology))

        onto = get_ontology(Ontology.ONTOLOGIES[self.ontology]).load()
        self.graph = default_world.as_rdflib_graph()

        self.clear_cache()

        if self.ontology == 'go' and self.type == 'node':
            nodes_in_go_namespaces = self.find_go_nodes(self.graph)
            nodes = nodes_in_go_namespaces.keys()
            self.process_nodes(nodes, nodes_in_go_namespaces)
            return

        for predicate in Ontology.PREDICATES:
            nodes = self.process_edges(predicate)

            if self.type == 'node' and self.ontology != 'go':
                self.process_nodes(nodes)

    def process_edges(self, predicate):
        self.cache_edge_properties()

        nodes = set()

        edges = list(self.graph.subject_objects(
            predicate=predicate, unique=True))
        for edge in edges:
            from_node, to_node = edge

            if self.is_blank(from_node):
                continue

            if self.is_blank(to_node) and self.is_a_restriction_block(to_node):
                restriction_predicate, restriction_node = self.read_restriction_block(
                    to_node)
                if restriction_predicate is None or restriction_node is None:
                    continue

                predicate = restriction_predicate
                to_node = restriction_node

            if self.type == 'node':
                nodes.add(from_node)
                nodes.add(to_node)

            if self.type == 'edge':
                key = '{}_{}_{}'.format(
                    Ontology.to_key(from_node),
                    Ontology.to_key(predicate),
                    Ontology.to_key(to_node)
                )
                props = {
                    '_key': key,
                    '_from': 'ontology_terms/' + Ontology.to_key(from_node),
                    '_to': 'ontology_terms/' + Ontology.to_key(to_node),
                    'type': self.predicate_name(predicate),
                    'type_ontology': str(predicate),
                    'source': self.ontology.upper()
                }

                self.save_props(props)

        return nodes

    def process_nodes(self, nodes, go_namespaces={}):
        self.cache_node_properties()

        for node in nodes:
            # avoiding blank nodes and other arbitrary node types
            if not isinstance(node, rdflib.term.URIRef):
                continue

            term_id = str(node).split('/')[-1]

            props = {
                '_key': Ontology.to_key(node),
                'uri': str(node),
                'term_id': str(node).split('/')[-1],
                'term_name': ', '.join(self.get_all_property_values_from_node(node, 'term_names')),
                'description': ' '.join(self.get_all_property_values_from_node(node, 'descriptions')),
                'synonyms': self.get_all_property_values_from_node(node, 'related_synonyms') +
                self.get_all_property_values_from_node(node, 'exact_synonyms'),
                'source': self.ontology.upper(),
                'subontology': go_namespaces.get(node, None)
            }

            self.save_props(props, primary=(self.ontology in term_id.lower()))

    def save_props(self, props, primary=True):
        save_to = self.primary_output
        if not primary:
            save_to = self.secondary_output

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
        return ''

    # "http://purl.obolibrary.org/obo/CLO_0027762#subclass?id=123" => "obo:CLO_0027762.subclass_id=123"
    # "12345" => "number_12345" - there are cases where URIs are just numbers, e.g. HPO

    @classmethod
    def to_key(cls, node):
        key = ':'.join(str(node).split('/')[-2:])
        key = key.replace('#', '.').replace('?', '_')

        if key.replace('.', '').isnumeric():
            key = '{}_{}'.format('number', key)

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
        return node_type and node_type[0] == Ontology.RESTRICTION

    def read_restriction_block(self, node):
        restricted_property = self.get_all_property_values_from_node(
            node, 'on_property')

        # assuming a restriction block will always contain only one `owl:onProperty` triple
        if restricted_property and restricted_property[0] not in Ontology.RESTRICTION_PREDICATES:
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

    def arangodb(self, primary=True):
        if primary is False:
            return ArangoDB().generate_json_import_statement(self.secondary_output.name, self.collection, type=self.type)

        return ArangoDB().generate_json_import_statement(self.primary_output.name, self.collection, type=self.type, replace=True)

    def save_to_arango(self):
        if self.dry_run:
            print(self.arangodb(primary=False)[0])
            print(self.arangodb()[0])
        else:
            os.system(self.arangodb(primary=False)[0])
            os.system(self.arangodb()[0])

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
                values.append(object)
        return values
