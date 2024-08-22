import json

from adapters.biogrid_gene_gene_adapter import GeneGeneBiogrid
from adapters.writer import SpyWriter


def test_biogrid_gene_gene_adapter_gene_gene_biogrid():
    writer = SpyWriter()
    adapter = GeneGeneBiogrid(
        filepath='./samples/merged_PPI.UniProt.example.csv', label='biogrid_gene_gene', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    print(first_item)
    assert len(writer.contents) == 4
    assert len(first_item) == 15
    assert first_item['source'] == 'BioGRID'
    assert first_item['confidence_value_biogrid:long'] is None
    assert first_item['interaction_type'] == [
        'negative genetic interaction (sensu BioGRID)']


def test_biogrid_gene_gene_adapter_mouse_gene_gene_biogrid():
    writer = SpyWriter()
    adapter = GeneGeneBiogrid(filepath='./samples/merged_PPI_mouse.UniProt.example.csv',
                              label='mouse_gene_gene_biogrid', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) == 14
    assert len(first_item) == 15
    assert first_item['source'] == 'BioGRID'
    assert first_item['interaction_type'] == [
        'positive genetic interaction (sensu BioGRID)']
