from adapters import Adapter
from owlready2 import *
import rdflib


class Ontology(Adapter):
  UBERON = 'http://purl.obolibrary.org/obo/uberon.owl'
  CLO = 'http://purl.obolibrary.org/obo/clo.owl'
  CL = 'http://purl.obolibrary.org/obo/cl.owl'
  HPO = 'http://purl.obolibrary.org/obo/hpo.owl'
  MONDO = 'https://github.com/monarch-initiative/mondo/releases/download/v2023-02-06/mondo.owl'
  GO = 'http://purl.obolibrary.org/obo/go.owl'

  BLANK_NODE = rdflib.term.BNode
  HAS_PART = rdflib.term.URIRef('http://purl.obolibrary.org/obo/BFO_0000051')
  PART_OF = rdflib.term.URIRef('http://purl.obolibrary.org/obo/BFO_0000050')

  SUBCLASS = rdflib.term.URIRef('http://www.w3.org/2000/01/rdf-schema#subClassOf')
  LABEL = rdflib.term.URIRef('http://www.w3.org/2000/01/rdf-schema#label')
  RESTRICTION = rdflib.term.URIRef('http://www.w3.org/2002/07/owl#Restriction')
  TYPE = rdflib.term.URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
  ON_PROPERTY = rdflib.term.URIRef('http://www.w3.org/2002/07/owl#onProperty')
  SOME_VALUES_FROM = rdflib.term.URIRef('http://www.w3.org/2002/07/owl#someValuesFrom')
  ALL_VALUES_FROM = rdflib.term.URIRef('http://www.w3.org/2002/07/owl#allValuesFrom')

  PREDICATES = [SUBCLASS]
  RESTRICTION_PREDICATES = [HAS_PART, PART_OF]


  def __init__(self, ontology, type='node'):
    ontologies = vars(Ontology).keys()
    if ontology.upper() not in ontologies:
      raise ValueError('Ontology not supported.')

    self.ontology_url = getattr(Ontology, ontology)
    self.ontology = ontology.lower()
    self.type = type

    self.dataset = '{}_class'.format(self.ontology)
    if self.type == 'edge':
      self.dataset = '{}_relationship'.format(self.ontology)

    super(Ontology, self).__init__()


  # "http://purl.obolibrary.org/obo/CLO_0027762#subclass" => "obo:CLO_0027762.subclass"
  @classmethod
  def to_key(cls, node):
    return ':'.join(str(node).split('/')[-2:]).replace('#', '.')


  # Example:
  # <rdfs:subClassOf>
  #     <owl:Restriction>
  #         <owl:onProperty rdf:resource="http://purl.obolibrary.org/obo/RO_0001000"/>
  #         <owl:someValuesFrom rdf:resource="http://purl.obolibrary.org/obo/CL_0000056"/>
  #     </owl:Restriction>
  # </rdfs:subClassOf>
  def read_restriction_block(self, graph, node):
    node_type = list(graph.objects(node, Ontology.TYPE))

    if node_type and node_type[0] != Ontology.RESTRICTION:
      return None

    restricted_property = list(graph.objects(node, Ontology.ON_PROPERTY))
    
    if restricted_property and restricted_property[0] not in Ontology.RESTRICTION_PREDICATES:
      return None

    values = []
    for predicate in [Ontology.SOME_VALUES_FROM, Ontology.ALL_VALUES_FROM]:
      values += [(str(restricted_property[0]), value) for value in graph.objects(node, predicate)]

    # assuming a owl:Restriction block in a rdf:subClassOf will contain only one triple
    return values[0] if values else None


  def process_file(self):
    print('Downloading {}...'.format(self.ontology))
    onto = get_ontology(self.ontology_url).load()
    graph = default_world.as_rdflib_graph()
    
    nodes = set()

    for predicate in Ontology.PREDICATES:
      relationships = list(graph.subject_objects(predicate=predicate, unique=True))

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

        if self.type == 'node':
          nodes.add(from_node)
          nodes.add(to_node)

        if self.type == 'edge':
          id = Ontology.to_key(from_node) + '_' + Ontology.to_key(to_node) + '_' + Ontology.to_key(predicate)
          source = '{}/{}'.format(self.collection_from, Ontology.to_key(from_node))
          target = '{}/{}'.format(self.collection_from, Ontology.to_key(to_node))
          label = '{}_relationship'.format(self.ontology)
          props = {
            'type': str(predicate)
          }
          yield(id, source, target, label, props)

    if self.type == 'node':
      for node in nodes:
        id = Ontology.to_key(node)
        label = '{}_class'.format(self.ontology)
        props = {
          'uri': str(node),
          'label': ', '.join([o.value for o in graph.objects(subject=node, predicate=Ontology.LABEL)])
        }

        yield(id, label, props)
