import json
from unittest.mock import patch
import pytest

from adapters.clingen_variant_disease_adapter import ClinGen
from adapters.writer import SpyWriter


def test_clingen_adapter_variant_disease():
    writer = SpyWriter()
    with patch('adapters.clingen_variant_disease_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True

        adapter = ClinGen(filepath='./samples/clinGen_variant_pathogenicity_example.csv',
                          label='variant_disease', writer=writer, validate=True)
        adapter.process_file()

        assert len(writer.contents) > 0
        first_item = json.loads(writer.contents[0])

        assert '_key' in first_item
        assert '_from' in first_item
        assert '_to' in first_item
        assert first_item['name'] == 'associated with'
        assert first_item['inverse_name'] == 'associated with'
        assert 'gene_id' in first_item
        assert 'assertion' in first_item
        assert 'pmids' in first_item
        assert first_item['source'] == 'ClinGen'
        assert first_item['source_url'] == 'https://search.clinicalgenome.org/kb/downloads'


def test_clingen_adapter_variant_disease_gene():
    writer = SpyWriter()
    with patch('adapters.clingen_variant_disease_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True
        adapter = ClinGen(filepath='./samples/clinGen_variant_pathogenicity_example.csv',
                          label='variant_disease_gene', writer=writer, validate=True)
        adapter.process_file()

        assert len(writer.contents) > 0
        first_item = json.loads(writer.contents[0])

        assert '_key' in first_item
        assert '_from' in first_item
        assert '_to' in first_item
        assert first_item['name'] == 'associated with'
        assert first_item['inverse_name'] == 'associated with'
        assert 'inheritance_mode' in first_item
        assert first_item['source'] == 'ClinGen'
        assert first_item['source_url'] == 'https://search.clinicalgenome.org/kb/downloads'


def test_clingen_adapter_invalid_label():
    with pytest.raises(ValueError, match='Invalid label: invalid_label. Allowed values: variant_disease, variant_disease_gene'):
        ClinGen(filepath='./samples/clinGen_variant_pathogenicity_example.csv',
                label='invalid_label')


def test_clingen_adapter_initialization():
    with patch('adapters.clingen_variant_disease_adapter.GeneValidator') as MockGeneValidator:
        adapter = ClinGen(
            filepath='./samples/clinGen_variant_pathogenicity_example.csv', label='variant_disease')
        assert adapter.filepath == './samples/clinGen_variant_pathogenicity_example.csv'
        assert adapter.label == 'variant_disease'
        assert adapter.gene_validator is not None


def test_clingen_adapter_validate_doc_invalid():
    writer = SpyWriter()
    adapter = ClinGen(filepath='./samples/clinGen_variant_pathogenicity_example.csv',
                      label='variant_disease', writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)


def test_clingen_adapter_invalid_gene_id():
    writer = SpyWriter()

    # Mock GeneValidator before creating the adapter
    with patch('adapters.clingen_variant_disease_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = False

        adapter = ClinGen(filepath='./samples/clinGen_variant_pathogenicity_example.csv',
                          label='variant_disease', writer=writer, validate=True)
        adapter.process_file()
        assert len(writer.contents) == 0
