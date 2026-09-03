import json
from adapters.gvatdb_asb_adapter import ASB_GVATDB
from adapters.writer import SpyWriter
import pytest
from unittest.mock import patch


FILE_ACCESSION = 'GVATdb_sample'
SAMPLE_PROTEIN_MAP = {
    'Q15699': ['ENSP00000320447'],  # ALX1
}


@pytest.fixture
def mock_file_fileset():
    """Mock get_file_fileset_by_accession_in_arangodb so ArangoDB is not required."""
    with patch('adapters.gvatdb_asb_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'class': 'observed data',
            'method': 'GVATdb'
        }
        yield mock_get_file_fileset


@pytest.fixture
def mock_protein_map():
    with patch('adapters.protein_map.get_protein_map_from_arangodb') as mock_get:
        mock_get.return_value = SAMPLE_PROTEIN_MAP
        yield mock_get


def test_asb_gvatdb_adapter_process(mock_file_fileset, mock_protein_map, mocker):
    writer = SpyWriter()
    adapter = ASB_GVATDB(filepath='./samples/GVATdb_sample.tsv',
                         writer=writer, validate=True)
    adapter.process_file()
    mock_protein_map.assert_called_once_with(
        field='uniprot_ids',
        organism='Homo sapiens',
        dbxref_name=None,
    )
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_from'] == 'variants/NC_000010.11:112626979:C:T'
    assert first_item['_to'] == 'proteins/ENSP00000320447'
    assert 'neg_log10_pvalue' in first_item
    assert 'p_value' in first_item
    assert 'hg19_coordinate' in first_item
    assert 'experiment' in first_item
    assert 'oligo_auc' in first_item
    assert 'oligo_pval' in first_item
    assert 'ref_auc' in first_item
    assert 'alt_auc' in first_item
    assert 'pbs' in first_item
    assert 'neg_log10_pvalue_adj' in first_item
    assert first_item['source'] == ASB_GVATDB.SOURCE
    assert first_item['source_url'] == ASB_GVATDB.SOURCE_URL
    assert first_item['label'] == 'allele-specific binding'
    assert first_item['method'] == 'GVATdb'
    assert first_item['class'] == 'observed data'
    assert first_item['files_filesets'] == f'files_filesets/{FILE_ACCESSION}'
    assert first_item['name'] == 'modulates binding of'
    assert first_item['inverse_name'] == 'binding modulated by'
    assert first_item['biological_process'] == 'ontology_terms/GO_0051101'


def test_asb_gvatdb_adapter_initialization():
    writer = SpyWriter()
    adapter = ASB_GVATDB(filepath='./samples/GVATdb_sample.tsv',
                         writer=writer)
    assert adapter.filepath == './samples/GVATdb_sample.tsv'
    assert adapter.writer == writer


def test_asb_gvatdb_adapter_load_tf_uniprot_id_mapping():
    adapter = ASB_GVATDB(filepath='./samples/GVATdb_sample.tsv')
    adapter.load_tf_uniprot_id_mapping()
    assert hasattr(adapter, 'tf_uniprot_id_mapping')
    assert isinstance(adapter.tf_uniprot_id_mapping, dict)
    assert len(adapter.tf_uniprot_id_mapping) > 0


def test_asb_gvatdb_adapter_validate_doc_invalid(mock_file_fileset):
    writer = SpyWriter()
    adapter = ASB_GVATDB(filepath='./samples/GVATdb_sample.tsv',
                         writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc({})
