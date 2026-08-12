import json
import pytest
from unittest.mock import patch

from adapters.mgi_human_mouse_ortholog_adapter import MGIHumanMouseOrthologAdapter
from adapters.writer import SpyWriter


FILE_ACCESSION = 'IGVFFI9177QQPS'


@pytest.fixture
def sample_filepath():
    return './samples/IGVFFI9177QQPS.HOM_MouseHumanSequence_sample.rpt'


@pytest.fixture
def spy_writer():
    return SpyWriter()


@pytest.fixture
def mock_file_fileset():
    """Mock get_file_fileset_by_accession_in_arangodb so ArangoDB is not required."""
    with patch('adapters.mgi_human_mouse_ortholog_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'class': 'observed data',
            'method': 'Homology'
        }
        yield mock_get_file_fileset


def _collect_sample_entrez_and_mgi_ids(filepath):
    entrez_ids = set()
    mgi_ids = set()
    for line in open(filepath, 'r'):
        if line.startswith('DB'):
            continue
        data_line = line.strip().split('\t')
        if data_line[1].startswith('mouse'):
            mgi_ids.add(data_line[5])
        elif data_line[1].startswith('human'):
            entrez_ids.add(data_line[4])
    return entrez_ids, mgi_ids


def mock_human_entrez_gene_map(filepath='./samples/IGVFFI9177QQPS.HOM_MouseHumanSequence_sample.rpt'):
    entrez_ids, _ = _collect_sample_entrez_and_mgi_ids(filepath)
    return {
        f'ENTREZ:{entrez_id}': [f'ENSG{int(entrez_id):011d}']
        for entrez_id in entrez_ids
    }


def mock_mouse_mgi_gene_map(filepath='./samples/IGVFFI9177QQPS.HOM_MouseHumanSequence_sample.rpt'):
    _, mgi_ids = _collect_sample_entrez_and_mgi_ids(filepath)
    return {
        mgi_id: [f'ENSMUSG{int(mgi_id.split(":")[1]):011d}']
        for mgi_id in mgi_ids
    }


def mock_get_gene_map_from_arangodb(field, collection='genes'):
    if collection == 'mm_genes':
        return mock_mouse_mgi_gene_map()
    if field == 'entrez':
        return mock_human_entrez_gene_map()
    return {}


@patch('adapters.mgi_human_mouse_ortholog_adapter.get_gene_map_from_arangodb')
def test_process_file(mock_gene_map, sample_filepath, spy_writer, mock_file_fileset):
    mock_gene_map.side_effect = mock_get_gene_map_from_arangodb
    adapter = MGIHumanMouseOrthologAdapter(
        sample_filepath, writer=spy_writer, validate=True)
    adapter.process_file()

    assert len(spy_writer.contents) > 0
    data = json.loads(spy_writer.contents[0])
    assert '_key' in data
    assert '_from' in data
    assert '_to' in data
    assert data['_from'].startswith('genes/')
    assert data['_to'].startswith('mm_genes/')
    assert data['name'] == 'homologous to'
    assert data['inverse_name'] == 'homologous to'
    assert data['relationship'] == 'ontology_terms/NCIT_C79968'
    assert data['source'] == 'MGI'
    assert data['source_url'] == 'https://www.informatics.jax.org/downloads/reports/HOM_MouseHumanSequence.rpt'
    assert data['class'] == 'observed data'
    assert data['method'] == 'Homology'
    assert data['files_filesets'] == f'files_filesets/{FILE_ACCESSION}'


@patch('adapters.mgi_human_mouse_ortholog_adapter.get_gene_map_from_arangodb')
def test_load_mappings(mock_gene_map, sample_filepath, spy_writer, mock_file_fileset):
    mock_gene_map.side_effect = mock_get_gene_map_from_arangodb
    adapter = MGIHumanMouseOrthologAdapter(sample_filepath, writer=spy_writer)
    adapter.parse()

    assert len(adapter.mm_gene_mapping) > 0
    assert len(adapter.gene_mapping) > 0
    assert isinstance(next(iter(adapter.gene_mapping.values())), list)
    assert isinstance(next(iter(adapter.mm_gene_mapping.values())), list)
    mock_gene_map.assert_any_call('entrez')
    mock_gene_map.assert_any_call('mgi', collection='mm_genes')


@patch('adapters.mgi_human_mouse_ortholog_adapter.get_gene_map_from_arangodb')
def test_emits_edges_for_all_ensembl_ids(mock_gene_map, sample_filepath, spy_writer, mock_file_fileset):
    def mock_multi_ensembl(field, collection='genes'):
        if collection == 'mm_genes':
            return {
                'MGI:107430': ['ENSMUSG00000022144', 'ENSMUSG00000888888'],
                'MGI:96176': ['ENSMUSG00000000942'],
            }
        if field == 'entrez':
            return {
                'ENTREZ:2668': ['ENSG00000168621', 'ENSG00000999999'],
                'ENTREZ:3201': ['ENSG00000006015'],
            }
        return {}

    mock_gene_map.side_effect = mock_multi_ensembl

    adapter = MGIHumanMouseOrthologAdapter(
        sample_filepath, writer=spy_writer, validate=True)
    adapter.process_file()

    edges = [json.loads(item)
             for item in spy_writer.contents if item.startswith('{')]
    gdnf_mouse_edges = [
        edge for edge in edges
        if edge['_from'] == 'genes/ENSG00000168621'
        and edge['_to'] == 'mm_genes/ENSMUSG00000022144'
    ]
    assert len(gdnf_mouse_edges) == 1
    assert any(
        edge['_from'] == 'genes/ENSG00000999999'
        and edge['_to'] == 'mm_genes/ENSMUSG00000022144'
        for edge in edges
    )
    assert any(
        edge['_from'] == 'genes/ENSG00000168621'
        and edge['_to'] == 'mm_genes/ENSMUSG00000888888'
        for edge in edges
    )


def test_validate_doc_invalid(sample_filepath, spy_writer):
    adapter = MGIHumanMouseOrthologAdapter(
        sample_filepath, writer=spy_writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
