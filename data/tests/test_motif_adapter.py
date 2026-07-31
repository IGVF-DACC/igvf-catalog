import json
import tarfile

import pytest
from unittest.mock import patch

from adapters.motif_adapter import Motif
from adapters.writer import SpyWriter


FILE_ACCESSION = 'IGVFFI9678CVIS'
SAMPLE_DIR = './samples/motifs'


@pytest.fixture
def sample_archive(tmp_path):
    archive_filepath = tmp_path / f'{FILE_ACCESSION}.tar.gz'
    with tarfile.open(archive_filepath, 'w:gz') as archive:
        archive.add(SAMPLE_DIR, arcname='.')
    return str(archive_filepath)


@pytest.fixture
def spy_writer():
    return SpyWriter()


@pytest.fixture
def mock_file_fileset():
    """Mock get_file_fileset_by_accession_in_arangodb so ArangoDB is not required."""
    with patch('adapters.motif_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'class': 'observed data',
            'method': 'HOCOMOCO'
        }
        yield mock_get_file_fileset


def test_motif_node(sample_archive, spy_writer, mock_file_fileset):
    motif = Motif(sample_archive, label='motif',
                  writer=spy_writer, validate=True)
    motif.process_file()

    assert motif.file_accession == FILE_ACCESSION
    assert len(spy_writer.contents) > 0
    data = json.loads(spy_writer.contents[0])
    assert '_key' in data
    assert 'name' in data
    assert 'tf_name' in data
    assert 'source' in data
    assert 'source_url' in data
    assert 'pwm' in data
    assert 'length' in data
    assert data['source'] == Motif.SOURCE
    assert data['source_url'].startswith(Motif.SOURCE_URL)
    assert data['class'] == 'observed data'
    assert data['method'] == 'HOCOMOCO'
    assert data['files_filesets'] == f'files_filesets/{FILE_ACCESSION}'


def test_motif_accepts_archive_and_derives_accession(tmp_path, spy_writer, mock_file_fileset):
    input_directory = tmp_path / 'pwm'
    input_directory.mkdir()
    (input_directory / 'TEST_HUMAN.H11MO.0.A.pwm').write_text(
        '>TEST_HUMAN.H11MO.0.A\n1\t2\t3\t4\n'
    )
    archive_filepath = tmp_path / f'{FILE_ACCESSION}.tar.gz'
    with tarfile.open(archive_filepath, 'w:gz') as archive:
        archive.add(input_directory, arcname='pwm')

    motif = Motif(str(archive_filepath), label='motif', writer=spy_writer)
    motif.process_file()

    assert motif.file_accession == FILE_ACCESSION
    assert json.loads(spy_writer.contents[0])['tf_name'] == 'TEST_HUMAN'


def test_motif_protein_link(sample_archive, spy_writer, mock_file_fileset):
    motif = Motif(sample_archive, label='motif_protein_link',
                  writer=spy_writer, validate=True)
    motif.process_file()

    assert len(spy_writer.contents) > 0
    data = json.loads(spy_writer.contents[0])
    assert '_key' in data
    assert '_from' in data
    assert '_to' in data
    assert 'name' in data
    assert 'inverse_name' in data
    assert 'biological_process' in data
    assert 'source' in data
    assert data['name'] == 'is used by'
    assert data['inverse_name'] == 'uses'
    assert data['biological_process'] == 'ontology_terms/GO_0003677'
    assert data['source'] == Motif.SOURCE
    assert data['class'] == 'observed data'
    assert data['method'] == 'HOCOMOCO'
    assert data['files_filesets'] == f'files_filesets/{FILE_ACCESSION}'


def test_invalid_label(sample_archive, spy_writer):
    with pytest.raises(ValueError):
        Motif(sample_archive, label='invalid_label', writer=spy_writer)


def test_load_tf_uniprot_id_mapping(sample_archive, spy_writer):
    motif = Motif(sample_archive, label='motif_protein_link',
                  writer=spy_writer)
    motif.load_tf_ensembl_id_mapping()

    assert hasattr(motif, 'tf_ensembl_id_mapping')
    assert len(motif.tf_ensembl_id_mapping) > 0


def test_validate_doc_invalid(sample_archive, spy_writer):
    motif = Motif(sample_archive, label='motif_protein_link',
                  writer=spy_writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        motif.validate_doc(invalid_doc)
