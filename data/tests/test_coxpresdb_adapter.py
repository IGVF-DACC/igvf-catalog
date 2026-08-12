import json
import os
import tarfile
from unittest.mock import patch

import pytest

from adapters.coxpresdb_adapter import Coxpresdb
from adapters.writer import SpyWriter


FILE_ACCESSION = 'IGVFFI3321YNBP'
SAMPLE_DIR = './samples/coxpresdb/'


@pytest.fixture
def sample_archive(tmp_path):
    archive_filepath = tmp_path / f'{FILE_ACCESSION}.tar.gz'
    with tarfile.open(archive_filepath, 'w:gz') as archive:
        archive.add(SAMPLE_DIR, arcname='.')
    return str(archive_filepath)


@pytest.fixture
def mock_file_fileset():
    """Mock get_file_fileset_by_accession_in_arangodb so ArangoDB is not required."""
    with patch('adapters.coxpresdb_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'class': 'observed data',
            'method': 'COXPRESdb'
        }
        yield mock_get_file_fileset


def mock_entrez_gene_map():
    entrez_ids = set()
    for filename in os.listdir(SAMPLE_DIR):
        if not filename.isdigit():
            continue
        entrez_ids.add(filename)
        with open(os.path.join(SAMPLE_DIR, filename), 'r') as input:
            for line in input:
                co_entrez_id, score = line.strip().split()
                if abs(float(score)) >= 3:
                    entrez_ids.add(co_entrez_id)
    return {
        f'ENTREZ:{entrez_id}': [f'ENSG{int(entrez_id):011d}']
        for entrez_id in entrez_ids
    }


@patch('adapters.coxpresdb_adapter.get_gene_map_from_arangodb')
def test_coxpresdb_adapter(mock_gene_map, mock_file_fileset, sample_archive):
    mock_gene_map.return_value = mock_entrez_gene_map()
    writer = SpyWriter()
    adapter = Coxpresdb(filepath=sample_archive,
                        writer=writer, validate=True)
    adapter.process_file()

    assert adapter.file_accession == FILE_ACCESSION
    assert len(writer.contents) > 0
    first_item = json.loads(writer.contents[0])

    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert 'z_score' in first_item
    assert first_item['source'] == adapter.source
    assert first_item['source_url'] == 'https://coxpresdb.jp/'
    assert first_item['name'] == 'coexpressed with'
    assert first_item['inverse_name'] == 'coexpressed with'
    assert first_item['associated_process'] == 'ontology_terms/GO_0010467'
    assert first_item['class'] == 'observed data'
    assert first_item['method'] == 'COXPRESdb'
    assert first_item['label'] == adapter.collection_label
    assert first_item['files_filesets'] == f'files_filesets/{FILE_ACCESSION}'


@patch('adapters.coxpresdb_adapter.get_gene_map_from_arangodb')
def test_coxpresdb_adapter_z_score_filter(mock_gene_map, mock_file_fileset, sample_archive):
    mock_gene_map.return_value = mock_entrez_gene_map()
    writer = SpyWriter()
    adapter = Coxpresdb(filepath=sample_archive, writer=writer)
    adapter.process_file()

    for item in writer.contents:
        if item.startswith('{'):
            data = json.loads(item)
            assert abs(float(data['z_score'])) >= 3


@patch('adapters.coxpresdb_adapter.get_gene_map_from_arangodb')
def test_coxpresdb_adapter_deduplicates_gene_pairs(mock_gene_map, mock_file_fileset, sample_archive):
    mock_gene_map.return_value = mock_entrez_gene_map()
    writer = SpyWriter()
    adapter = Coxpresdb(filepath=sample_archive, writer=writer)
    adapter.process_file()

    edges = [json.loads(item)
             for item in writer.contents if item.startswith('{')]
    entrez_pairs = set()
    for edge in edges:
        key_body = edge['_key'].removesuffix('_coxpresdb')
        if key_body.startswith('ENSG'):
            pair = tuple(sorted(
                [key_body.split('_')[0], key_body.split('_', 1)[1]],
                key=lambda ens: ens,
            ))
        else:
            entrez_a, entrez_b = key_body.split('_', 1)
            pair = tuple(sorted([entrez_a, entrez_b], key=int))
        assert pair not in entrez_pairs
        entrez_pairs.add(pair)
        assert edge['_key'].endswith('_coxpresdb')


def test_coxpresdb_adapter_initialization():
    adapter = Coxpresdb(filepath=f'{FILE_ACCESSION}.tar.gz')
    assert adapter.filepath == f'{FILE_ACCESSION}.tar.gz'
    assert adapter.file_accession == FILE_ACCESSION
    assert adapter.label == 'coxpresdb'
    assert adapter.source == 'COXPRESdb'
    assert adapter.source_url == 'https://coxpresdb.jp/'


def test_coxpresdb_adapter_validate_doc_invalid(sample_archive):
    writer = SpyWriter()
    adapter = Coxpresdb(filepath=sample_archive,
                        writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
