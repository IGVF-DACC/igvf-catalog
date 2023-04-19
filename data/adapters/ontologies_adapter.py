from adapters import Adapter
from owlready2 import *
import rdflib


class Ontology(Adapter):
    # Temporary URLs. They will be moved to igvfd.
    # this file has an OWL error
    UBERON = 'http://purl.obolibrary.org/obo/uberon.owl'
    CLO = 'http://purl.obolibrary.org/obo/clo.owl'
    CL = 'http://purl.obolibrary.org/obo/cl.owl'
    HPO = 'https://github.com/obophenotype/human-phenotype-ontology/releases/download/v2023-01-27/hp.owl'
    MONDO = 'https://github.com/monarch-initiative/mondo/releases/download/v2023-02-06/mondo.owl'
    GO = 'http://purl.obolibrary.org/obo/go.owl'
    EFO = 'https://github.com/EBISPOT/efo/releases/download/current/efo.owl'

    GO_SUBONTOLGIES = ['molecular_function',
                       'cellular_component', 'biological_process']

    # a BNode according to rdflib is a general node (as a 'catch all' node) that doesn't have any predetermined type such as class, literal, etc.
    BLANK_NODE = rdflib.term.BNode
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

    PREDICATES = [SUBCLASS]
    RESTRICTION_PREDICATES = [HAS_PART, PART_OF]

    def __init__(self, ontology, type='node', subontology=None):
        self.type = type

        ontologies = vars(Ontology).keys()
        if ontology.upper() not in ontologies:
            raise ValueError('Ontology not supported.')

        self.ontology_url = getattr(Ontology, ontology)
        self.ontology = ontology.lower()

        self.subontology = None
        if self.ontology == 'go':
            if subontology not in Ontology.GO_SUBONTOLGIES:
                raise ValueError('Subontology not supported.')

            self.subontology = rdflib.term.Literal(subontology)
            self.ontology += '_{}'.format(str(self.subontology))

        self.dataset = '{}_class'.format(self.ontology)
        if self.type == 'edge':
            self.dataset = '{}_relationship'.format(self.ontology)

        super(Ontology, self).__init__()

    # "http://purl.obolibrary.org/obo/CLO_0027762#subclass?id=123" => "obo:CLO_0027762.subclass_id=123"
    # "12345" => "number_12345" - there are cases where URIs are just numbers, e.g. HPO

    @classmethod
    def to_key(cls, node):
        key = ':'.join(str(node).split('/')[-2:])
        key = key.replace('#', '.').replace('?', '_')

        if key.replace('.', '').isnumeric():
            key = '{}_{}'.format('number', key)

        return key

    # Example:
    # <rdfs:subClassOf>
    #     <owl:Restriction>
    #         <owl:onProperty rdf:resource="http://purl.obolibrary.org/obo/RO_0001000"/>
    #         <owl:someValuesFrom rdf:resource="http://purl.obolibrary.org/obo/CL_0000056"/>
    #     </owl:Restriction>
    # </rdfs:subClassOf>
    # This block will be interpreted as the triple (s, p, o):
    # (parent object, http://purl.obolibrary.org/obo/RO_0001000, http://purl.obolibrary.org/obo/CL_0000056)

    def read_restriction_block(self, graph, node):
        node_type = list(graph.objects(node, Ontology.TYPE))

        # every node contains only one basic type.
        if node_type and node_type[0] != Ontology.RESTRICTION:
            return None

        restricted_property = list(graph.objects(node, Ontology.ON_PROPERTY))

        # assuming a restriction block will always contain only one `owl:onProperty` triple
        if restricted_property and restricted_property[0] not in Ontology.RESTRICTION_PREDICATES:
            return None

        values = []
        for predicate in [Ontology.SOME_VALUES_FROM, Ontology.ALL_VALUES_FROM]:
            values += [(str(restricted_property[0]), value)
                       for value in graph.objects(node, predicate)]

        # returning the pair (owl:onProperty value, owl:someValuesFrom or owl:allValuesFrom value)
        # assuming a owl:Restriction block in a rdf:subClassOf will contain only one `owl:someValuesFrom` or `owl:allValuesFrom` triple
        return values[0] if values else None

    def process_file(self):
        print('Downloading {}...'.format(self.ontology))
        onto = get_ontology(self.ontology_url).load()
        graph = default_world.as_rdflib_graph()

        nodes = set()

        if self.subontology:
            all_namespaces = list(graph.subject_objects(
                predicate=Ontology.NAMESPACE))

            namespace_lookup = {}
            go_namespaces = [n for n in all_namespaces if str(
                n[1]) in Ontology.GO_SUBONTOLGIES]
            for node_namespace_pair in go_namespaces:
                namespace_lookup[str(node_namespace_pair[0])] = str(
                    node_namespace_pair[1])

            nodes_in_current_namespace = set(
                [n[0] for n in all_namespaces if n[1] == self.subontology])

            nodes = nodes_in_current_namespace

        print('Processing ontology...')
        for predicate in Ontology.PREDICATES:
            if self.subontology and self.type == 'node':
                # list of nodes is just nodes in subontology namespace already calculated above
                break

            relationships = list(graph.subject_objects(
                predicate=predicate, unique=True))

            for relationship in relationships:
                from_node, to_node = relationship

                if isinstance(from_node, Ontology.BLANK_NODE):
                    continue

                if isinstance(to_node, Ontology.BLANK_NODE):
                    restriction = self.read_restriction_block(graph, to_node)

                    if not restriction:
                        continue

                    restriction_type, restriction_class = restriction

                    predicate = restriction_type
                    to_node = restriction_class

                # relationships to other namespaces are valid, but at least one node must be part of this namespace
                if self.subontology and from_node not in nodes and to_node not in nodes:
                    continue

                if self.type == 'node':
                    nodes.add(from_node)
                    nodes.add(to_node)

                if self.type == 'edge':
                    if self.subontology:
                        source_collection = 'go_{}_classes'.format(
                            namespace_lookup[str(from_node)])
                        target_collection = 'go_{}_classes'.format(
                            namespace_lookup[str(to_node)])
                    else:
                        source_collection = self.collection_from
                        target_collection = self.collection_to

                    source = '{}/{}'.format(source_collection,
                                            Ontology.to_key(from_node))
                    target = '{}/{}'.format(target_collection,
                                            Ontology.to_key(to_node))

                    id = Ontology.to_key(
                        from_node) + '_' + Ontology.to_key(to_node) + '_' + Ontology.to_key(predicate)
                    label = '{}_relationship'.format(self.ontology)
                    props = {
                        'type': str(predicate)
                    }
                    yield(id, source, target, label, props)

        if self.type == 'node':
            print('Processing nodes...')
            all_labels = list(graph.subject_objects(predicate=Ontology.LABEL))
            for node in nodes:
                id = Ontology.to_key(node)
                label = '{}_class'.format(self.ontology)
                props = {
                    'uri': str(node),
                    'term_id': str(node).split('/')[-1],
                    'term_name': ', '.join([t[1].value for t in all_labels if t[0] == node])
                }

                yield(id, label, props)
