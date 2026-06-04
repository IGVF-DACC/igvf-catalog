import pytest
import json
from unittest.mock import patch, MagicMock

from adapters.scorpion_adapter import ScorpionAdapter


@pytest.fixture
def mock_writer():
    return MagicMock()


@patch('adapters.scorpion_adapter.gzip.open')
@patch('adapters.scorpion_adapter.csv.DictReader')
@patch('adapters.scorpion_adapter.get_file_fileset_by_accession_in_arangodb')
def test_process_file_writes_json(mock_get_file_fileset, mock_dictreader_cls, mock_gzip_open, mock_writer):
    # Setup file_fileset metadata returned by arangodb lookup
    mock_get_file_fileset.return_value = {
        'method': 'scorpion',
        'class': 'regulatory_interaction',
        'files_filesets': 'files_filesets/IGVFTEST'
    }

    # Simulate DictReader yielding two rows with tf_ensembl present
    mock_dictreader_cls.return_value = [
        {
            'tf': 'ZNF250',
            'tf_ensembl': 'ENSG00000196150',
            'target': 'WNK1',
            'target_ensembl': 'ENSG00000060237',
            'beta': '2.79614395634379',
            'P': '2.23950511461299e-22',
            'FDR': '2.2770944348533403e-19'
        },
        {
            'tf': 'ZNF770',
            'tf_ensembl': 'ENSG00000198146',
            'target': 'IL32',
            'target_ensembl': 'ENSG00000008517',
            'beta': '2.68504180081855',
            'P': '1.80943850543389e-22',
            'FDR': '1.8921041491990902e-19'
        }
    ]

    # gzip.open is used by the adapter but csv.DictReader is patched to return rows,
    # so gzip.open can return any context manager; provide a dummy
    mock_ctx = MagicMock()
    mock_gzip_open.return_value.__enter__.return_value = mock_ctx

    adapter = ScorpionAdapter(
        filepath='path/to/IGVFTEST.gz', writer=mock_writer, validate=False)
    adapter.process_file()

    assert mock_writer.open.called
    assert mock_writer.write.call_count > 0
    assert mock_writer.close.called

    written = [
        json.loads(call.args[0])
        for call in mock_writer.write.call_args_list
        if isinstance(call.args[0], str) and call.args[0].strip().startswith('{')
    ]
    assert len(written) == 2
    for doc in written:
        assert '_key' in doc
        assert '_from' in doc
        assert '_to' in doc
        assert 'effect_size' in doc
        assert 'p_value' in doc
        assert 'p_value_adj' in doc
        assert 'nlog10_p_value' in doc
        assert 'files_filesets' in doc
        assert doc['label'] == ScorpionAdapter.LABEL
        assert doc['source'] == ScorpionAdapter.SOURCE
        assert doc['class'] == 'regulatory_interaction'
        assert doc['method'] == 'scorpion'


@patch('adapters.scorpion_adapter.gzip.open')
@patch('adapters.scorpion_adapter.csv.DictReader')
@patch('adapters.scorpion_adapter.get_file_fileset_by_accession_in_arangodb')
@patch('adapters.scorpion_adapter.gene_synonym_to_ensembl_id')
def test_process_file_resolves_tf_synonym(
    mock_gene_synonym,
    mock_get_file_fileset,
    mock_dictreader_cls,
    mock_gzip_open,
    mock_writer
):
    mock_get_file_fileset.return_value = {
        'method': 'scorpion',
        'class': 'regulatory_interaction',
        'files_filesets': 'files_filesets/IGVFTEST'
    }

    # First row missing tf_ensembl; second row has it
    mock_dictreader_cls.return_value = [
        {
            'tf': 'ZNF250',
            'tf_ensembl': '',
            'target': 'WNK1',
            'target_ensembl': 'ENSG00000060237',
            'beta': '2.79614395634379',
            'P': '2.23950511461299e-22',
            'FDR': '2.2770944348533403e-19'
        },
        {
            'tf': 'ZNF770',
            'tf_ensembl': 'ENSG00000198146',
            'target': 'IL32',
            'target_ensembl': 'ENSG00000008517',
            'beta': '2.68504180081855',
            'P': '1.80943850543389e-22',
            'FDR': '1.8921041491990902e-19'
        }
    ]

    # gene_synonym_to_ensembl_id should be called for the first row
    mock_gene_synonym.return_value = 'ENSG00000196150'

    mock_ctx = MagicMock()
    mock_gzip_open.return_value.__enter__.return_value = mock_ctx

    adapter = ScorpionAdapter(
        filepath='path/to/IGVFTEST.gz', writer=mock_writer, validate=False)
    adapter.process_file()

    # ensure synonym lookup was attempted
    mock_gene_synonym.assert_called_with('ZNF250')

    written = [
        json.loads(call.args[0])
        for call in mock_writer.write.call_args_list
        if isinstance(call.args[0], str) and call.args[0].strip().startswith('{')
    ]
    assert len(written) == 2
    # ensure files_filesets was injected from file_fileset metadata
    for doc in written:
        assert doc['files_filesets']
