import json
import pytest
from adapters.gtex_eqtl_adapter import GtexEQtl
from adapters.writer import SpyWriter
import os


def test_gtex_eqtl_adapter_eqtl():
    writer = SpyWriter()
    adapter = GtexEQtl(filepath='./samples/GTEx_eQTL',
                       label='GTEx_eqtl', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert 'biological_context' in first_item
    assert 'chr' in first_item
    assert 'p_value' in first_item
    assert 'log10pvalue' in first_item
    assert 'effect_size' in first_item
    assert 'pval_beta' in first_item
    assert first_item['label'] == 'eQTL'
    assert first_item['source'] == GtexEQtl.SOURCE
    assert first_item['source_url'].startswith(GtexEQtl.SOURCE_URL_PREFIX)


def test_gtex_eqtl_adapter_eqtl_term():
    writer = SpyWriter()
    adapter = GtexEQtl(filepath='./samples/GTEx_eQTL',
                       label='GTEx_eqtl_term', writer=writer)
    adapter.process_file()

    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert 'biological_context' in first_item
    assert first_item['source'] == GtexEQtl.SOURCE
    assert first_item['source_url'].startswith(GtexEQtl.SOURCE_URL_PREFIX)
    assert first_item['name'] == 'occurs in'
    assert first_item['inverse_name'] == 'has measurement'


def test_gtex_eqtl_adapter_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label. Allowed values: GTEx_eqtl,GTEx_eqtl_term'):
        GtexEQtl(filepath='./samples/GTEx_eQTL',
                 label='invalid_label', writer=writer)


def test_gtex_eqtl_adapter_initialization():
    writer = SpyWriter()
    for label in GtexEQtl.ALLOWED_LABELS:
        adapter = GtexEQtl(filepath='./samples/GTEx_eQTL',
                           label=label, writer=writer)
        assert adapter.filepath == './samples/GTEx_eQTL'
        assert adapter.label == label
        assert adapter.dataset == label
        assert adapter.dry_run == True
        assert adapter.type == 'edge'
        assert adapter.writer == writer


def test_gtex_eqtl_adapter_load_ontology_mapping():
    adapter = GtexEQtl(filepath='./samples/GTEx_eQTL')
    adapter.load_ontology_mapping()
    assert hasattr(adapter, 'ontology_id_mapping')
    assert isinstance(adapter.ontology_id_mapping, dict)
    assert len(adapter.ontology_id_mapping) > 0
    assert hasattr(adapter, 'ontology_term_mapping')
    assert isinstance(adapter.ontology_term_mapping, dict)
    assert len(adapter.ontology_term_mapping) > 0
