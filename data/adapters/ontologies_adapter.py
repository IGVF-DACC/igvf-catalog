import json
from typing import Optional
from rdflib import RDF, BNode, Literal, URIRef
from rdflib.collection import Collection

from owlready2 import *

from adapters.writer import Writer


class Ontology:

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

    SOURCE_LINKS = {
        'go': 'https://geneontology.org/',
        'clo': 'https://obofoundry.org/ontology/clo.html',
        'chebi': 'https://www.ebi.ac.uk/chebi/',
        'cl': 'https://obophenotype.github.io/cell-ontology/',
        'efo': 'https://www.ebi.ac.uk/efo/',
        'mondo': 'https://mondo.monarchinitiative.org/',
        'ncit': 'https://github.com/NCI-Thesaurus/thesaurus-obo-edition',
        'oncotree': 'https://github.com/cBioPortal/oncotree',
        'uberon': 'https://obophenotype.github.io/uberon/',
        'vario': 'http://variationontology.org/',
        'hpo': 'https://hpo.jax.org/',
        'encode': 'https://encodeproject.org',
        'bao': 'http://bioassayontology.org/',
        'oba': 'https://github.com/obophenotype/bio-attribute-ontology',
        'orphanet': 'https://www.orpha.net/'
    }

    GO_SUBONTOLGIES = ['molecular_function',
                       'cellular_component', 'biological_process']

    HAS_PART = URIRef('http://purl.obolibrary.org/obo/BFO_0000051')
    PART_OF = URIRef('http://purl.obolibrary.org/obo/BFO_0000050')
    SUBCLASS = URIRef(
        'http://www.w3.org/2000/01/rdf-schema#subClassOf')
    DB_XREF = URIRef(
        'http://www.geneontology.org/formats/oboInOwl#hasDbXref')
    DERIVES_FROM = URIRef(
        'http://purl.obolibrary.org/obo/RO_0001000')
    INTERSECTION_OF = URIRef(
        'http://www.w3.org/2002/07/owl#intersectionOf')

    LABEL = URIRef('http://www.w3.org/2000/01/rdf-schema#label')
    RESTRICTION = URIRef(
        'http://www.w3.org/2002/07/owl#Restriction')
    TYPE = URIRef(
        'http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
    ON_PROPERTY = URIRef(
        'http://www.w3.org/2002/07/owl#onProperty')
    SOME_VALUES_FROM = URIRef(
        'http://www.w3.org/2002/07/owl#someValuesFrom')
    ALL_VALUES_FROM = URIRef(
        'http://www.w3.org/2002/07/owl#allValuesFrom')
    NAMESPACE = URIRef(
        'http://www.geneontology.org/formats/oboInOwl#hasOBONamespace')
    EXACT_SYNONYM = URIRef(
        'http://www.geneontology.org/formats/oboInOwl#hasExactSynonym')
    RELATED_SYNONYM = URIRef(
        'http://www.geneontology.org/formats/oboInOwl#hasRelatedSynonym')
    DESCRIPTION = URIRef(
        'http://purl.obolibrary.org/obo/IAO_0000115')

    PREDICATES = [SUBCLASS, DB_XREF]
    RESTRICTION_PREDICATES = [HAS_PART, PART_OF, DERIVES_FROM]

    EXCLUDED_URIS = {
        # Add other properties you want to exclude when finding all nodes from an intersectionOf
        URIRef('http://www.w3.org/2002/07/owl#Restriction'),
        URIRef('http://www.w3.org/2002/07/owl#Class'),
        URIRef('http://purl.obolibrary.org/obo/BFO_0000050'),
        URIRef('http://purl.obolibrary.org/obo/RO_0000052')
    }

    def __init__(
        self,
        filepath,
        ontology,
        node_primary_writer: Optional[Writer] = None,
        node_secondary_writer: Optional[Writer] = None,
        edge_primary_writer: Optional[Writer] = None,
        edge_secondary_writer: Optional[Writer] = None,
        **kwargs
    ):
        self.filepath = filepath
        self.ontology = ontology
        self.node_primary_writer = node_primary_writer
        self.node_secondary_writer = node_secondary_writer
        self.edge_primary_writer = edge_primary_writer
        self.edge_secondary_writer = edge_secondary_writer

    def process_file(self):
        self.node_primary_writer.open()
        self.node_secondary_writer.open()
        self.edge_primary_writer.open()
        self.edge_secondary_writer.open()

        # primary: for example, Go ontology defining a Go term
        # secondary: for example, HPO ontology defining a Go term
        # primary data will replace secondary data when loading into DB
        self.outputs = {
            'node': {
                'primary': self.node_primary_writer,
                'secondary': self.node_secondary_writer
            },
            'edge': {
                'primary': self.edge_primary_writer,
                'secondary': self.edge_secondary_writer
            }
        }

        self.process_ontology()

        for t in self.outputs.keys():
            self.outputs[t]['primary'].close()
            self.outputs[t]['secondary'].close()

    def process_ontology(self):
        onto = get_ontology(self.filepath).load()
        with onto:
            self.graph = default_world.as_rdflib_graph()
            print('Processing {}...'.format(self.ontology))
            self.clear_cache()
            self.cache_edge_properties()
            self.cache_node_properties()

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
            to_nodes = [to_node]
            restriction_predicate = None
            restriction_nodes = None
            if self.is_blank(to_node):
                if self.is_a_restriction_block(to_node):
                    restriction_predicate, restriction_nodes = self.read_restriction_block(
                        to_node)
                    if restriction_predicate is None or restriction_nodes is None:
                        continue
                    to_nodes = restriction_nodes

            nodes.add(from_node)
            nodes.update(to_nodes)
            predicate_for_props = restriction_predicate if restriction_predicate else predicate
            from_node_key = Ontology.to_key(from_node)
            predicate_key = Ontology.to_key(predicate_for_props)

            if from_node_key is None or predicate_key is None:
                continue
            for to_node in to_nodes:
                # Ignore literal nodes such as numeric values and strings. Example: BNode('397')
                if isinstance(to_node, BNode):
                    continue
                to_node_key = Ontology.to_key(to_node)
                if to_node_key is None:
                    continue
                if predicate == Ontology.DB_XREF:
                    if to_node.__class__ == Literal:
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
                    'name': self.predicate_name(predicate_for_props),
                    'type_uri': str(predicate_for_props),
                    'source': self.ontology.upper(),
                    'source_url': Ontology.SOURCE_LINKS.get(self.ontology.lower())
                }

                inverse_name = 'type of'  # for name = subclass
                if props['name'] == 'database cross-reference':
                    inverse_name = 'database cross-reference'
                elif props['name'] == 'derives from':
                    inverse_name = 'derives'
                elif props['name'] == 'has part':
                    inverse_name = 'part of'
                elif props['name'] == 'part of':
                    inverse_name = 'has part'
                elif props['name'] == 'originate from same individual as':
                    inverse_name = 'originate from same individual as'
                props['inverse_name'] = inverse_name
                self.save_props(props, True, 'edge')

        return nodes

    def process_nodes(self, nodes, go_namespaces={}):
        for node in nodes:
            # avoiding blank nodes and other arbitrary node types
            if not isinstance(node, URIRef):
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
                'source_url': Ontology.SOURCE_LINKS.get(self.ontology.lower()),
                'subontology': go_namespaces.get(node, None)
            }

            self.save_props(props, primary=(
                self.ontology in term_id.lower()), prop_type='node')

    def save_props(self, props, primary=True, prop_type='node'):
        save_to = self.outputs[prop_type]['primary']
        if not primary:
            save_to = self.outputs[prop_type]['secondary']
        save_to.write(json.dumps(props) + '\n')

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
        elif predicate == str(Ontology.DERIVES_FROM):
            return 'derives from'
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

    def get_all_nodes_from_intersection_of(self, node, visited=None, depth=0, max_depth=10):
        """
        Recursively extract non-BNode URIs from a node, avoiding cycles
        and optionally limiting max recursion depth.
        """
        if visited is None:
            visited = set()
        if node in visited or depth > max_depth:
            return []

        visited.add(node)
        found = []

        if isinstance(node, URIRef):
            if node not in self.EXCLUDED_URIS:
                return [node]
            else:
                return []

        # If this is a list (owl:intersectionOf, etc.)
        if (node, RDF.first, None) in self.graph:
            try:
                items = Collection(self.graph, node)
                for item in items:
                    found.extend(self.get_all_nodes_from_intersection_of(
                        item, visited, depth + 1, max_depth))
            except Exception as e:
                print(f'Collection parse error: {e}')
            return found

        # Otherwise, walk predicate-objects
        for _, o in self.graph.predicate_objects(node):
            found.extend(self.get_all_nodes_from_intersection_of(
                o, visited, depth + 1, max_depth))

        return found

    def read_restriction_block(self, node):
        restricted_property = self.get_all_property_values_from_node(
            node, 'on_property')
        # assuming a restriction block will always contain only one `owl:onProperty` triple
        if restricted_property and restricted_property[0] not in str(Ontology.RESTRICTION_PREDICATES):
            return None, None

        restriction_predicate = str(restricted_property[0])
        if restriction_predicate == str(self.DERIVES_FROM) and self.ontology.lower() in ['uberon', 'efo', 'obi', 'doid', 'hpo', 'mondo', 'oba']:
            some_values_from = self.get_all_property_nodes_from_node(
                node, 'some_values_from')

            # get intersectionOf from this blank node
            intersection_of = self.get_all_property_nodes_from_node(
                some_values_from[0], 'intersection_of')
            all_nodes = self.get_all_nodes_from_intersection_of(
                intersection_of[0])
            all_nodes_uris = [
                node for node in all_nodes if isinstance(node, URIRef)]
            return (restriction_predicate, all_nodes_uris)

        # returning the pair (owl:onProperty value, owl:someValuesFrom or owl:allValuesFrom value)
        # assuming a owl:Restriction block in a rdf:subClassOf will contain only one `owl:someValuesFrom` or `owl:allValuesFrom` triple
        some_values_from = self.get_all_property_values_from_node(
            node, 'some_values_from')
        if some_values_from:
            return (restriction_predicate, some_values_from)

        all_values_from = self.get_all_property_values_from_node(
            node, 'all_values_from')
        if all_values_from:
            return (restriction_predicate, all_values_from)

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
        BLANK_NODE = BNode

        return isinstance(node, BLANK_NODE)

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
        self.cache['intersection_of'] = self.cache_predicate(
            Ontology.INTERSECTION_OF)

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

    def get_all_property_nodes_from_node(self, node, collection):
        values = []
        for subject_object in self.cache[collection]:
            subject, object = subject_object

            if subject == node:
                values.append(object)

        return values
