import json
import pytest
from unittest.mock import patch
from adapters.gtex_eqtl_adapter import GtexEQtl
from adapters.writer import SpyWriter
import os


def test_gtex_eqtl_adapter_eqtl(mocker):
    mocker.patch('adapters.gtex_eqtl_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    with patch('adapters.gtex_eqtl_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True
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
        assert first_item['name'] == 'modulates expression of'
        assert first_item['inverse_name'] == 'expression modulated by'
        assert first_item['biological_process'] == 'ontology_terms/GO_0010468'


def test_gtex_eqtl_adapter_eqtl_term(mocker):
    mocker.patch('adapters.gtex_eqtl_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    with patch('adapters.gtex_eqtl_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True
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
        with patch('adapters.gtex_eqtl_adapter.GeneValidator'):
            adapter = GtexEQtl(filepath='./samples/GTEx_eQTL',
                               label=label, writer=writer)
            assert adapter.filepath == './samples/GTEx_eQTL'
            assert adapter.label == label
            assert adapter.dataset == label
            assert adapter.dry_run == True
            assert adapter.type == 'edge'
            assert adapter.writer == writer


def test_gtex_eqtl_adapter_load_ontology_mapping():
    with patch('adapters.gtex_eqtl_adapter.GeneValidator'):
        adapter = GtexEQtl(filepath='./samples/GTEx_eQTL')
        adapter.load_ontology_mapping()
        assert hasattr(adapter, 'ontology_id_mapping')
        assert isinstance(adapter.ontology_id_mapping, dict)
        assert len(adapter.ontology_id_mapping) > 0
        assert hasattr(adapter, 'ontology_term_mapping')
        assert isinstance(adapter.ontology_term_mapping, dict)
        assert len(adapter.ontology_term_mapping) > 0
