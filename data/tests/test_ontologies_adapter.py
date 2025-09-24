import pytest
from unittest.mock import MagicMock, patch
from rdflib import URIRef, BNode, Literal
from adapters.ontologies_adapter import Ontology


@pytest.fixture
def mock_writers():
    return {
        'node_primary_writer': MagicMock(),
        'node_secondary_writer': MagicMock(),
        'edge_primary_writer': MagicMock(),
        'edge_secondary_writer': MagicMock(),
    }


@pytest.fixture
def ontology_instance(mock_writers):
    with patch('adapters.ontologies_adapter.get_ontology') as mock_get_ontology, \
            patch('adapters.ontologies_adapter.default_world') as mock_default_world:
        mock_graph = MagicMock()
        mock_default_world.as_rdflib_graph.return_value = mock_graph
        mock_onto = MagicMock()
        mock_get_ontology.return_value.load.return_value = mock_onto
        return Ontology(
            filepath='dummy.owl',
            ontology='go',
            node_primary_writer=mock_writers['node_primary_writer'],
            node_secondary_writer=mock_writers['node_secondary_writer'],
            edge_primary_writer=mock_writers['edge_primary_writer'],
            edge_secondary_writer=mock_writers['edge_secondary_writer'],
        )


def test_init_sets_attributes(mock_writers):
    ont = Ontology(
        filepath='dummy.owl',
        ontology='uberon',
        node_primary_writer=mock_writers['node_primary_writer'],
        node_secondary_writer=mock_writers['node_secondary_writer'],
        edge_primary_writer=mock_writers['edge_primary_writer'],
        edge_secondary_writer=mock_writers['edge_secondary_writer'],
    )
    assert ont.filepath == 'dummy.owl'
    assert ont.ontology == 'uberon'
    assert ont.node_primary_writer is mock_writers['node_primary_writer']


@patch('adapters.ontologies_adapter.get_ontology')
@patch('adapters.ontologies_adapter.default_world')
def test_process_file_opens_and_closes_writers(mock_default_world, mock_get_ontology, mock_writers):
    mock_graph = MagicMock()
    mock_default_world.as_rdflib_graph.return_value = mock_graph
    mock_onto = MagicMock()
    mock_get_ontology.return_value.load.return_value = mock_onto

    ont = Ontology(
        filepath='dummy.owl',
        ontology='uberon',
        node_primary_writer=mock_writers['node_primary_writer'],
        node_secondary_writer=mock_writers['node_secondary_writer'],
        edge_primary_writer=mock_writers['edge_primary_writer'],
        edge_secondary_writer=mock_writers['edge_secondary_writer'],
    )
    with patch.object(ont, 'process_ontology') as mock_process_ontology:
        ont.process_file()
    for w in mock_writers.values():
        assert w.open.called
        assert w.close.called


def test_predicate_name_returns_expected_strings():
    ont = Ontology('dummy.owl', 'uberon', None, None, None, None)
    assert ont.predicate_name(Ontology.HAS_PART) == 'has part'
    assert ont.predicate_name(Ontology.PART_OF) == 'part of'
    assert ont.predicate_name(Ontology.SUBCLASS) == 'subclass'
    assert ont.predicate_name(Ontology.DB_XREF) == 'database cross-reference'
    assert ont.predicate_name(Ontology.DERIVES_FROM) == 'derives from'
    assert ont.predicate_name('unknown') == ''


def test_to_key_handles_various_cases():
    assert Ontology.to_key(URIRef(
        'http://purl.obolibrary.org/obo/CLO_0027762#subclass?id=123')) == 'CLO_0027762.subclass_id_123'
    assert Ontology.to_key(
        URIRef('http://example.org/hgnc/10001')) == 'HGNC_10001'
    assert Ontology.to_key(URIRef('http://example.org/12345')) is None
    assert Ontology.to_key(URIRef('http://example.org/abc def')) == 'abcdef'


def test_is_blank_and_clear_cache(ontology_instance):
    bnode = BNode()
    assert ontology_instance.is_blank(bnode)
    ontology_instance.clear_cache()
    assert hasattr(ontology_instance, 'cache')


def test_save_props_primary_and_secondary(ontology_instance, mock_writers):
    props = {'_key': 'A', 'uri': 'uri', 'term_id': 'A', 'name': 'name', 'description': '',
             'synonyms': [], 'source': 'GO', 'source_url': '', 'subontology': None}
    ontology_instance.outputs = {
        'node': {'primary': mock_writers['node_primary_writer'], 'secondary': mock_writers['node_secondary_writer']},
        'edge': {'primary': mock_writers['edge_primary_writer'], 'secondary': mock_writers['edge_secondary_writer']},
    }
    ontology_instance.save_props(props, primary=True, prop_type='node')
    ontology_instance.save_props(props, primary=False, prop_type='node')
    assert mock_writers['node_primary_writer'].write.called
    assert mock_writers['node_secondary_writer'].write.called


def test_get_all_property_values_and_nodes_from_node(ontology_instance):
    ontology_instance.cache = {
        'term_names': [(URIRef('A'), Literal('NameA')), (URIRef('B'), Literal('NameB'))],
        'descriptions': [(URIRef('A'), Literal('DescA'))],
        'related_synonyms': [],
        'exact_synonyms': [],
        'node_types': [],
        'on_property': [],
        'some_values_from': [],
        'all_values_from': [],
        'intersection_of': [],
    }
    assert ontology_instance.get_all_property_values_from_node(
        URIRef('A'), 'term_names') == ['NameA']
    assert ontology_instance.get_all_property_nodes_from_node(
        URIRef('A'), 'term_names') == [Literal('NameA')]


def test_is_a_restriction_block(ontology_instance):
    ontology_instance.cache = {'node_types': [
        (BNode('x'), Ontology.RESTRICTION)]}
    assert ontology_instance.is_a_restriction_block(BNode('x'))


def test_find_go_nodes_returns_namespace_dict(ontology_instance):
    mock_graph = MagicMock()
    mock_graph.subject_objects.return_value = [
        (URIRef('A'), 'molecular_function'), (URIRef('B'), 'other')]
    result = ontology_instance.find_go_nodes(mock_graph)
    assert result[URIRef('A')] == 'molecular_function'
    assert URIRef('B') not in result
