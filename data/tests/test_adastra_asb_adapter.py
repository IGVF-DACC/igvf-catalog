import json
from unittest.mock import patch
from adapters.adastra_asb_adapter import ASB
from adapters.writer import SpyWriter
import pytest


def test_adastra_asb_adapter_invalid_label():
    """Test invalid label handling"""
    with pytest.raises(ValueError, match='Invalid label'):
        ASB(filepath='./samples/allele_specific_binding', label='invalid_label')


@patch('adapters.adastra_asb_adapter.build_variant_id')
def test_adastra_asb_adapter_process_file_asb(mock_build_variant_id):
    """Test processing file with asb label"""
    # Set up mock data
    mock_build_variant_id.return_value = 'NC_000019.10:9435653:C:A'

    adapter = ASB(filepath='./samples/allele_specific_binding',
                  label='asb', writer=SpyWriter(), validate=True)

    # Actually call process_file to test the full functionality
    adapter.process_file()

    # Verify that some output was generated
    assert len(adapter.writer.contents) > 0

    # Parse the first output item
    first_item = json.loads(adapter.writer.contents[0])

    # Verify the structure of the output
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert first_item['_from'].startswith('variants/')
    assert first_item['_to'].startswith('proteins/')
    assert 'chr' in first_item
    assert 'rsid' in first_item
    assert 'motif_fc' in first_item
    assert 'motif_pos' in first_item
    assert 'motif_orient' in first_item
    assert 'motif_conc' in first_item
    assert first_item['source'] == ASB.SOURCE
    assert first_item['label'] == 'allele-specific binding'
    assert first_item['name'] == 'modulates binding of'
    assert first_item['inverse_name'] == 'binding modulated by'
    assert first_item['biological_process'] == 'ontology_terms/GO_0051101'

    invalid_doc = {
        '_key': 'NC_000019.10:9435653:C:A',
        '_from': 'variants/NC_000019.10:9435653:C:A',
        '_to': 'proteins/ENSP00000383070',
        'chr': 'chr10',
        'rsid': 'rs1234567890',
    }
    with pytest.raises(ValueError, match='Document validation failed'):
        adapter.validate_doc(invalid_doc)


@patch('adapters.adastra_asb_adapter.build_variant_id')
def test_adastra_asb_adapter_process_file_asb_cell_ontology(mock_build_variant_id):
    """Test processing file with asb_cell_ontology label"""
    # Set up mock data
    mock_build_variant_id.return_value = 'NC_000019.10:9435653:C:A'

    adapter = ASB(filepath='./samples/allele_specific_binding',
                  label='asb_cell_ontology', writer=SpyWriter(), validate=True)

    # Actually call process_file to test the full functionality
    adapter.process_file()

    # Verify that some output was generated
    assert len(adapter.writer.contents) > 0

    # Parse the first output item
    first_item = json.loads(adapter.writer.contents[0])

    # Verify the structure of the output for cell ontology edges
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert first_item['_from'].startswith('variants_proteins/')
    assert first_item['_to'].startswith('ontology_terms/')
    assert 'es_mean_ref' in first_item
    assert 'es_mean_alt' in first_item
    assert 'fdrp_bh_ref' in first_item
    assert 'fdrp_bh_alt' in first_item
    assert 'biological_context' in first_item
    assert 'source_url' in first_item
    assert first_item['name'] == 'occurs in'
    assert first_item['inverse_name'] == 'has measurement'


@patch('adapters.adastra_asb_adapter.build_variant_id')
def test_adastra_asb_adapter_process_file_with_mock_unmatched_ensembl(mock_build_variant_id):
    """Test process_file method with mocked ensembl mapping"""
    # Set up mock data
    mock_build_variant_id.return_value = 'NC_000019.10:9435653:C:A'

    # Mock the ensembl mapping to return specific protein IDs
    mock_ensembl_mapping = {
        'P18846': ['ENSP00000383070', 'ENSP00000412345']  # ATF1_HUMAN
    }

    with patch('adapters.adastra_asb_adapter.pickle.load', return_value=mock_ensembl_mapping):
        adapter = ASB(filepath='./samples/allele_specific_binding',
                      label='asb', writer=SpyWriter())

        # Call process_file
        adapter.process_file()

        # Filter out empty lines and verify output was generated
        non_empty_contents = [
            content for content in adapter.writer.contents if content.strip()]
        assert len(non_empty_contents) > 0

        # Verify the structure of outputs
        for content in non_empty_contents:
            item = json.loads(content)
            assert '_key' in item
            assert '_from' in item
            assert '_to' in item
            assert item['_from'] == 'variants/NC_000019.10:9435653:C:A'
            assert item['_to'].startswith('proteins/ENSP')
            assert item['source'] == ASB.SOURCE


@patch('adapters.adastra_asb_adapter.build_variant_id')
def test_adastra_asb_adapter_process_file_skip_unmatched_tf(mock_build_variant_id, caplog):
    """Test process_file skips files with unmatched TF uniprot ID"""
    # Set up mock data
    mock_build_variant_id.return_value = 'NC_000019.10:9435653:C:A'

    adapter = ASB(filepath='./samples/allele_specific_binding',
                  label='asb', writer=SpyWriter())

    # Mock the TF mapping loading to return a mapping that doesn't include ATF1_HUMAN
    def mock_load_tf_mapping():
        adapter.tf_uniprot_id_mapping = {
            'UNKNOWN_TF': 'P12345'  # Different from ATF1_HUMAN
        }

    # Load the cell mapping normally first
    adapter.load_cell_ontology_id_mapping()

    with patch.object(adapter, 'load_tf_uniprot_id_mapping', side_effect=mock_load_tf_mapping):
        # Call process_file
        adapter.process_file()

    # Check that the skip message was logged
    assert 'TF uniprot id unavailable, skipping: ATF1_HUMAN@HepG2__hepatoblastoma_.tsv' in caplog.text

    # Verify no output was generated since the TF was skipped
    assert len(adapter.writer.contents) == 0


@patch('adapters.adastra_asb_adapter.build_variant_id')
def test_adastra_asb_adapter_process_file_skip_unmatched_cell(mock_build_variant_id, caplog):
    """Test process_file skips files with unmatched cell ontology ID"""
    # Set up mock data
    mock_build_variant_id.return_value = 'NC_000019.10:9435653:C:A'

    adapter = ASB(filepath='./samples/allele_specific_binding',
                  label='asb', writer=SpyWriter())

    # Load the TF mapping normally first
    adapter.load_tf_uniprot_id_mapping()

    # Mock the cell mapping loading to return a mapping that doesn't include HepG2__hepatoblastoma_
    def mock_load_cell_mapping():
        adapter.cell_ontology_id_mapping = {
            'unknown_cell': ('CL:0000001', 'GTRD123', 'Unknown Cell')
        }

    with patch.object(adapter, 'load_cell_ontology_id_mapping', side_effect=mock_load_cell_mapping):
        # Call process_file
        adapter.process_file()

    # Check that the skip message was logged
    assert 'Cell ontology id unavailable, skipping: ATF1_HUMAN@HepG2__hepatoblastoma_.tsv' in caplog.text

    # Verify no output was generated since the cell was skipped
    assert len(adapter.writer.contents) == 0
