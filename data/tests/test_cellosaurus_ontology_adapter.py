import json

from adapters.cellosaurus_ontology_adapter import Cellosaurus
from adapters.writer import SpyWriter


def test_cellosaurus_adapter_node():
    writer = SpyWriter()
    adapter = Cellosaurus(filepath='./samples/cellosaurus_example.obo.txt',
                          type='node', writer=writer)
    adapter.process_file()
    assert len(writer.contents) > 0
    first_item = json.loads(writer.contents[0])
    assert first_item['_key'].startswith('CVCL_')
    assert 'name' in first_item
    assert 'uri' in first_item
    assert first_item['source'] == 'Cellosaurus'


def test_cellosaurus_adapter_edge():
    writer = SpyWriter()
    adapter = Cellosaurus(filepath='./samples/cellosaurus_example.obo.txt',
                          type='edge', writer=writer)
    adapter.process_file()
    assert len(writer.contents) > 0
    first_item = json.loads(writer.contents[0])
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert 'name' in first_item
    assert 'inverse_name' in first_item
    assert first_item['source'] == 'Cellosaurus'


def test_cellosaurus_adapter_species_filter():
    writer = SpyWriter()
    adapter = Cellosaurus(filepath='./samples/cellosaurus_example.obo.txt',
                          type='node', species_filter=True, writer=writer)
    adapter.process_file()
    filtered_count = len(writer.contents)

    writer = SpyWriter()
    adapter = Cellosaurus(filepath='./samples/cellosaurus_example.obo.txt',
                          type='node', species_filter=False, writer=writer)
    adapter.process_file()
    unfiltered_count = len(writer.contents)

    assert filtered_count < unfiltered_count


def test_cellosaurus_adapter_to_key():
    adapter = Cellosaurus(filepath='./samples/cellosaurus_example.obo.txt')
    assert adapter.to_key('NCBI_TaxID:9606') == 'NCBITaxon_9606'
    assert adapter.to_key('ORDO:Orphanet_102') == 'Orphanet_102'
    assert adapter.to_key('CLO:CLO_0001001') == 'CLO_0001001'


def test_cellosaurus_adapter_initialization():
    adapter = Cellosaurus(
        filepath='./samples/cellosaurus_example.obo.txt', type='node')
    assert adapter.filepath == './samples/cellosaurus_example.obo.txt'
    assert adapter.type == 'node'
    assert adapter.dataset == 'ontology_term'
    assert adapter.label == 'ontology_term'

    adapter = Cellosaurus(
        filepath='./samples/cellosaurus_example.obo.txt', type='edge')
    assert adapter.type == 'edge'
    assert adapter.dataset == 'ontology_relationship'
    assert adapter.label == 'ontology_relationship'
