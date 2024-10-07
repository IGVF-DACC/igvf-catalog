import json
import pytest
from adapters.encode_E2G_CRISPR_adapter import ENCODE2GCRISPR
from adapters.writer import SpyWriter


def test_encode2gcrispr_adapter_regulatory_region():
    writer = SpyWriter()
    adapter = ENCODE2GCRISPR(
        filepath='./samples/ENCODE_E2G_CRISPR_example.tsv', label='regulatory_region', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert 'chr' in first_item
    assert 'start' in first_item
    assert 'end' in first_item
    assert 'type' in first_item
    assert first_item['source'] == ENCODE2GCRISPR.SOURCE
    assert first_item['source_url'] == ENCODE2GCRISPR.SOURCE_URL


def test_encode2gcrispr_adapter_regulatory_region_gene():
    writer = SpyWriter()
    adapter = ENCODE2GCRISPR(filepath='./samples/ENCODE_E2G_CRISPR_example.tsv',
                             label='regulatory_region_gene', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert 'score' in first_item
    assert 'p_value' in first_item
    assert 'log10pvalue' in first_item
    assert 'significant' in first_item
    assert first_item['source'] == ENCODE2GCRISPR.SOURCE
    assert first_item['source_url'] == ENCODE2GCRISPR.SOURCE_URL
    assert first_item['biological_context'] == f'ontology_terms/{ENCODE2GCRISPR.BIOLOGICAL_CONTEXT}'


def test_encode2gcrispr_adapter_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label. Allowed values: regulatory_region,regulatory_region_gene'):
        ENCODE2GCRISPR(filepath='./samples/ENCODE_E2G_CRISPR_example.tsv',
                       label='invalid_label', writer=writer)


def test_encode2gcrispr_adapter_initialization():
    writer = SpyWriter()
    for label in ENCODE2GCRISPR.ALLOWED_LABELS:
        adapter = ENCODE2GCRISPR(
            filepath='./samples/ENCODE_E2G_CRISPR_example.tsv', label=label, writer=writer)
        assert adapter.filepath == './samples/ENCODE_E2G_CRISPR_example.tsv'
        assert adapter.label == label
        assert adapter.dataset == label
        assert adapter.dry_run == True
        assert adapter.writer == writer

        if label == 'regulatory_region':
            assert adapter.type == 'node'
        else:
            assert adapter.type == 'edge'


def test_encode2gcrispr_adapter_load_regulatory_region():
    writer = SpyWriter()
    adapter = ENCODE2GCRISPR(
        filepath='./samples/ENCODE_E2G_CRISPR_example.tsv', label='regulatory_region', writer=writer)
    adapter.load_regulatory_region()
    assert hasattr(adapter, 'regulatory_region_nodes')
    assert isinstance(adapter.regulatory_region_nodes, dict)
    assert len(adapter.regulatory_region_nodes) > 0


def test_encode2gcrispr_adapter_load_gene_id_mapping():
    writer = SpyWriter()
    adapter = ENCODE2GCRISPR(filepath='./samples/ENCODE_E2G_CRISPR_example.tsv',
                             label='regulatory_region_gene', writer=writer)
    adapter.load_gene_id_mapping()
    assert hasattr(adapter, 'gene_id_mapping')
    assert isinstance(adapter.gene_id_mapping, dict)
    assert len(adapter.gene_id_mapping) > 0