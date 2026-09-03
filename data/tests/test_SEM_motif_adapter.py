import gzip
import json
import pytest
from unittest.mock import patch
from adapters.SEM_motif_adapter import SEMMotif
from adapters.writer import SpyWriter


FILE_ACCESSION = 'SEM_model_file'

# real uniprot -> ENSP mapping for P15923 (TCF3), used by the sample provenance file
SAMPLE_PROTEIN_MAP = {
    'P15923': ['ENSP00000262965', 'ENSP00000378813', 'ENSP00000468487']
}


@pytest.fixture
def mock_file_fileset():
    """Mock get_file_fileset_by_accession_in_arangodb so ArangoDB is not required."""
    with patch('adapters.SEM_motif_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'class': 'observed data',
            'method': 'SEMpl'
        }
        yield mock_get_file_fileset


@pytest.fixture
def mock_protein_map():
    """Mock get_protein_map_from_arangodb so ArangoDB is not required."""
    with patch('adapters.protein_map.get_protein_map_from_arangodb') as mock_get_protein_map:
        mock_get_protein_map.return_value = SAMPLE_PROTEIN_MAP
        yield mock_get_protein_map


def test_sem_motif_adapter_motif(mock_file_fileset, mock_protein_map):
    writer = SpyWriter()
    adapter = SEMMotif(filepath='./samples/SEM/SEM_model_file.tsv.gz',
                       sem_provenance_path='./samples/SEM/provenance_file.tsv.gz', label='motif', writer=writer, validate=True)
    adapter.process_file()
    # the 'motif' label never touches self.protein_map, so the protein map should not be fetched
    mock_protein_map.assert_not_called()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert 'name' in first_item
    assert 'tf_name' in first_item
    assert 'source' in first_item
    assert 'source_url' in first_item
    assert 'pwm' in first_item
    assert 'length' in first_item
    assert first_item['class'] == 'observed data'
    assert first_item['method'] == 'SEMpl'
    assert first_item['files_filesets'] == f'files_filesets/{FILE_ACCESSION}'


def test_sem_motif_adapter_motif_with_description_header(mock_file_fileset, mock_protein_map, tmp_path):
    # regression test: some real SEMpl model files include a leading
    # '#Description: ...' line before '#BASELINE:', which used to break
    # the naive two-line header parsing (see: ValueError could not convert
    # string to float when 'baseline' picked up the description text)
    model_file = tmp_path / 'SEM_model_file_with_description.tsv.gz'
    with gzip.open(model_file, 'wt') as f:
        f.write(
            '#Description: Predictions of variant effects on transcription factor binding\n')
        f.write('#BASELINE:-1.5347609999406169\n')
        f.write('TCF3\tA\tC\tG\tT\n')
        f.write('1\t-0.525692\t0.146994\t-0.162952\t-0.298346\n')
        f.write('2\t-0.800987\t-0.703454\t-1.167276\t0.016788\n')

    writer = SpyWriter()
    adapter = SEMMotif(filepath=str(model_file),
                       sem_provenance_path='./samples/SEM/provenance_file.tsv.gz', label='motif', writer=writer, validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item['tf_name'] == 'TCF3'
    assert first_item['baseline'] == -1.5347609999406169
    assert len(first_item['pwm']) == 2


def test_sem_motif_adapter_raises_clear_error_for_non_model_file(mock_file_fileset, mock_protein_map, tmp_path):
    # regression test: if the wrong file (e.g. the provenance file, which has
    # no '#BASELINE:' header at all) is mistakenly passed as the model file,
    # the adapter should fail with a clear message instead of a TypeError
    # from float(None) deep inside parse()
    not_a_model_file = tmp_path / 'not_a_model_file.tsv.gz'
    with gzip.open(not_a_model_file, 'wt') as f:
        f.write('transcription_factor\tensembl_id\tebi_complex_ac\tuniprot_ac\n')
        f.write('AHR\tENSG00000106546\t\tP35869\n')

    writer = SpyWriter()
    adapter = SEMMotif(filepath=str(not_a_model_file),
                       sem_provenance_path='./samples/SEM/provenance_file.tsv.gz', label='motif', writer=writer, validate=True)
    with pytest.raises(ValueError, match='does not look like a SEMpl motif model file'):
        adapter.process_file()


def test_sem_motif_adapter_complex_protein_without_sem_provenance_path(mock_protein_map):
    # regression test: 'complex'/'complex_protein' labels don't use
    # sem_provenance_path (see load_complexes/load_tf_id_mapping), and the
    # documented CLI usage for them omits --sem_provenance_path entirely.
    # The adapter must not require it.
    writer = SpyWriter()
    adapter = SEMMotif(filepath='./samples/SEM/provenance_file.tsv.gz',
                       label='complex_protein', writer=writer)
    adapter.process_file()
    assert adapter.sem_provenance_path is None
    assert adapter.sem_provenance_accession is None
    assert len(writer.contents) > 0


def test_sem_motif_adapter_motif_protein_link(mock_file_fileset, mock_protein_map):
    writer = SpyWriter()
    adapter = SEMMotif(filepath='./samples/SEM/SEM_model_file.tsv.gz', sem_provenance_path='./samples/SEM/provenance_file.tsv.gz',
                       label='motif_protein', writer=writer, validate=True)
    adapter.process_file()
    mock_protein_map.assert_called_once_with(
        field='uniprot_ids',
        organism='Homo sapiens',
        dbxref_name=None,
    )
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert first_item['_to'] == 'proteins/ENSP00000262965'
    assert 'name' in first_item
    assert 'inverse_name' in first_item
    assert 'biological_process' in first_item
    assert 'source' in first_item
    assert 'source_url' in first_item
    assert first_item['name'] == 'is used by'
    assert first_item['inverse_name'] == 'uses'
    assert first_item['biological_process'] == 'ontology_terms/GO_0003677'
    assert first_item['class'] == 'observed data'
    assert first_item['method'] == 'SEMpl'
    assert first_item['files_filesets'] == f'files_filesets/{FILE_ACCESSION}'


def test_sem_motif_adapter_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_label. Allowed values: motif, motif_protein, complex, complex_protein'):
        SEMMotif(filepath='./samples/SEM/SEM_model_file.tsv.gz', sem_provenance_path='./samples/SEM/provenance_file.tsv.gz',
                 label='invalid_label', writer=writer)


def test_sem_motif_adapter_load_tf_id_mapping():
    adapter = SEMMotif(filepath='./samples/SEM/SEM_model_file.tsv.gz',
                       sem_provenance_path='./samples/SEM/provenance_file.tsv.gz')
    adapter.load_tf_id_mapping()
    assert hasattr(adapter, 'tf_id_mapping')
    assert isinstance(adapter.tf_id_mapping, dict)
    assert len(adapter.tf_id_mapping) > 0


def test_protein_map_is_fetched_only_once(mock_protein_map):
    adapter = SEMMotif(filepath='./samples/SEM/SEM_model_file.tsv.gz',
                       sem_provenance_path='./samples/SEM/provenance_file.tsv.gz', label='motif_protein')
    assert adapter.protein_map.get('P15923') == SAMPLE_PROTEIN_MAP['P15923']
    assert adapter.protein_map.get('P15923') == SAMPLE_PROTEIN_MAP['P15923']
    mock_protein_map.assert_called_once_with(
        field='uniprot_ids',
        organism='Homo sapiens',
        dbxref_name=None,
    )


def test_validate_doc_invalid():
    writer = SpyWriter()
    adapter = SEMMotif(filepath='./samples/SEM/SEM_model_file.tsv.gz',
                       sem_provenance_path='./samples/SEM/provenance_file.tsv.gz', label='motif', writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
