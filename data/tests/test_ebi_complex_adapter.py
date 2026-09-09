import json
import pytest
from unittest.mock import patch
from adapters.ebi_complex_adapter import EBIComplex
from adapters.protein_map import ProteinMap
from adapters.writer import SpyWriter


FILE_ACCESSION = 'EBI_complex_example'

SAMPLE_PROTEIN_MAP = {
    'P84022': ['ENSP00000341551'],
    'Q13485': ['ENSP00000341551'],
    'Q15796': ['ENSP00000341551'],
    'P16220': ['ENSP00000341551'],
    'P18848': ['ENSP00000341551'],
}


@pytest.fixture
def mock_file_fileset():
    """Mock get_file_fileset_by_accession_in_arangodb so ArangoDB is not required."""
    with patch('adapters.ebi_complex_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'class': 'observed data',
            'method': None
        }
        yield mock_get_file_fileset


@pytest.fixture
def mock_protein_map():
    with patch('adapters.protein_map.get_protein_map_from_arangodb') as mock_get:
        mock_get.return_value = SAMPLE_PROTEIN_MAP
        yield mock_get


def test_ebi_complex_initialization():
    sample_filepath = './samples/EBI_complex_example.tsv'
    for label in EBIComplex.ALLOWED_LABELS:
        writer = SpyWriter()
        adapter = EBIComplex(sample_filepath, label=label, writer=writer)
        assert adapter.filepath == sample_filepath
        assert adapter.label == label
        assert adapter.writer == writer
        assert adapter.file_accession == FILE_ACCESSION


def test_ebi_complex_invalid_label():
    sample_filepath = './samples/EBI_complex_example.tsv'
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_label. Allowed values: complex, complex_protein, complex_term'):
        EBIComplex(sample_filepath, label='invalid_label', writer=writer)


def test_ebi_complex_process_file(mock_file_fileset, mock_protein_map):
    sample_filepath = './samples/EBI_complex_example.tsv'
    for label in EBIComplex.ALLOWED_LABELS:
        writer = SpyWriter()
        adapter = EBIComplex(sample_filepath, label=label,
                             writer=writer, validate=True)
        adapter.process_file()

        # Check that some data was written
        assert len(writer.contents) > 0

        # Check the structure of the first item
        first_item = json.loads(writer.contents[0])
        assert first_item['class'] == 'observed data'
        assert first_item['method'] is None
        assert first_item['label'] is None
        assert first_item['files_filesets'] == f'files_filesets/{FILE_ACCESSION}'
        if label == 'complex':
            assert '_key' in first_item
            assert 'name' in first_item
        elif label == 'complex_protein':
            mock_protein_map.assert_called_once_with(
                field='uniprot_ids',
                organism='Homo sapiens',
                dbxref_name=None,
            )
            assert first_item['_from'] == 'complexes/CPX-1'
            assert first_item['_to'] == 'proteins/ENSP00000341551'
        elif label == 'complex_term':
            assert '_key' in first_item
            assert '_from' in first_item
            assert '_to' in first_item


def test_ebi_complex_get_chain_id():
    adapter = EBIComplex('./samples/EBI_complex_example.tsv', label='complex')

    assert adapter.get_chain_id('P12345') == None
    assert adapter.get_chain_id('P12345-1') == None
    assert adapter.get_chain_id('P12345-PRO_0000123456') == 'PRO_0000123456'


def test_ebi_complex_get_isoform_id():
    adapter = EBIComplex('./samples/EBI_complex_example.tsv', label='complex')

    assert adapter.get_isoform_id('P12345') == None
    assert adapter.get_isoform_id('P12345-1') == '1'
    assert adapter.get_isoform_id('P12345-PRO_0000123456') == None


def test_ebi_complex_load_linked_features_dict(mock_protein_map):
    sample_filepath = './samples/EBI_complex_example.tsv'
    writer = SpyWriter()
    adapter = EBIComplex(
        sample_filepath, label='complex_protein', writer=writer)
    adapter.protein_map = ProteinMap(organism='Homo sapiens')
    adapter.load_linked_features_dict()
    assert hasattr(adapter, 'linked_features_dict')
    assert isinstance(adapter.linked_features_dict, dict)


def test_ebi_complex_load_subontologies():
    sample_filepath = './samples/EBI_complex_example.tsv'
    writer = SpyWriter()
    adapter = EBIComplex(sample_filepath, label='complex', writer=writer)
    adapter.load_subontologies()
    assert hasattr(adapter, 'subontologies')
    assert isinstance(adapter.subontologies, dict)


def test_ebi_complex_validate_doc_invalid():
    sample_filepath = './samples/EBI_complex_example.tsv'
    writer = SpyWriter()
    adapter = EBIComplex(sample_filepath, label='complex',
                         writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
