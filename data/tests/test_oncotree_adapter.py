import json
from unittest.mock import MagicMock, patch

import pytest
from adapters.oncotree_adapter import Oncotree
from adapters.writer import SpyWriter

SAMPLE_FILEPATH = './samples/IGVFFI4975UFZM.example.tar.gz'
SAMPLE_ACCESSION = 'IGVFFI4975UFZM'


@pytest.fixture
def mock_file_fileset():
    """Mock get_file_fileset_by_accession_in_arangodb so ArangoDB is not required."""
    with patch('adapters.oncotree_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'class': 'biological relationship',
            'method': None
        }
        yield mock_get_file_fileset


def _docs(writer):
    return [json.loads(item) for item in writer.contents if item.strip()]


def test_oncotree_adapter(mock_file_fileset):
    writer = SpyWriter()
    adapter = Oncotree(
        filepath=SAMPLE_FILEPATH, label='node', writer=writer, validate=True)
    adapter.process_file()
    docs = _docs(writer)
    assert adapter.file_accession == SAMPLE_ACCESSION
    assert len(docs) == 4
    mock_file_fileset.assert_called_once_with(SAMPLE_ACCESSION)

    tissue = next(doc for doc in docs if doc['_key'] == 'Oncotree_TISSUE')
    assert tissue['term_id'] == 'Oncotree_TISSUE'
    assert tissue['name'] == 'Tissue'
    assert tissue['source'] == 'Oncotree'
    assert tissue['source_url'] == 'https://oncotree.mskcc.org/api/tumorTypes'
    assert tissue['class'] == 'biological relationship'
    assert tissue['method'] is None
    assert tissue['files_filesets'] == f'files_filesets/{SAMPLE_ACCESSION}'

    mds_mpn = next(doc for doc in docs if doc['_key'] == 'Oncotree_MDS_MPN')
    assert mds_mpn['term_id'] == 'Oncotree_MDS/MPN'
    assert mds_mpn['name'] == 'Myelodysplastic/Myeloproliferative Neoplasms'
    assert mds_mpn['files_filesets'] == f'files_filesets/{SAMPLE_ACCESSION}'


def test_oncotree_adapter_edges(mock_file_fileset):
    writer = SpyWriter()
    adapter = Oncotree(
        filepath=SAMPLE_FILEPATH, label='edge', writer=writer, validate=True)
    adapter.process_file()
    docs = _docs(writer)
    assert len(docs) > 1
    mock_file_fileset.assert_called_once_with(SAMPLE_ACCESSION)

    keys = {doc['_key'] for doc in docs}
    assert 'Oncotree_SKIN_rdf-schema.subClassOf_Oncotree_TISSUE' in keys
    assert 'Oncotree_MDS_MPN_rdf-schema.subClassOf_Oncotree_EMBT' in keys
    assert 'Oncotree_TISSUE_oboInOwl.hasDbXref_NCIT_C12801' in keys
    assert 'Oncotree_MDS_MPN_oboInOwl.hasDbXref_NCIT_C27238' in keys

    first_item = docs[0]
    assert 'type' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert first_item['source'] == 'Oncotree'
    assert first_item['class'] == 'biological relationship'
    assert first_item['method'] is None
    assert first_item['files_filesets'] == f'files_filesets/{SAMPLE_ACCESSION}'


def test_process_file_writer_closed_on_finish(mock_file_fileset):
    writer = MagicMock()
    oncotree = Oncotree(filepath=SAMPLE_FILEPATH, label='node', writer=writer)
    oncotree.process_file()
    writer.add_tag.assert_called_once_with(
        'portal_accessions', SAMPLE_ACCESSION)
    # process_file drives the writer through the context-manager protocol,
    # so the writer is exited (closed) rather than having close() called directly.
    assert writer.__exit__.called
