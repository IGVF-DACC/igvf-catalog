import pytest
import json
from unittest.mock import patch, MagicMock

from adapters.scorpion_adapter import ScorpionAdapter


@pytest.fixture
def mock_writer():
    return MagicMock()


@pytest.fixture
def mock_file_metadata():
    return {
        'catalog_class': 'regulatory_interaction',
        'catalog_method': 'scorpion'
    }


@pytest.fixture
def sample_data():
    # Simulate a gzipped TSV file as lines
    return [
        'ZNF250\tENSG00000196150\tWNK1\tENSG00000060237\t2.79614395634379\t2.23950511461299e-22\t2.2770944348533403e-19\n',
        'ZNF770\tENSG00000198146\tIL32\tENSG00000008517\t2.68504180081855\t1.80943850543389e-22\t1.8921041491990902e-19\n'
    ]


@patch('adapters.scorpion_adapter.requests.get')
@patch('adapters.scorpion_adapter.gzip.open')
def test_process_file_writes_json(mock_gzip_open, mock_requests_get, mock_writer, mock_file_metadata, sample_data):
    # Mock requests.get to return file metadata
    mock_resp = MagicMock()
    mock_resp.json.return_value = mock_file_metadata
    mock_requests_get.return_value = mock_resp

    # Mock gzip.open to return sample data as a file-like object
    mock_gzip_open.return_value.__enter__.return_value = sample_data

    # Patch DictReader to use correct fieldnames
    with patch('csv.DictReader', autospec=True) as mock_dictreader_cls:
        # Simulate DictReader yielding dicts for each row
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

        adapter = ScorpionAdapter(
            filepath='dummy.gz', writer=mock_writer, validate=False)
        adapter.process_file()

        # Check that write was called for each row
        assert mock_writer.write.call_count > 0
        # Check that the output contains expected keys
        written = [json.loads(
            call.args[0]) for call in mock_writer.write.call_args_list if call.args[0].strip().startswith('{')]
        for doc in written:
            assert '_key' in doc
            assert '_from' in doc
            assert '_to' in doc
            assert 'beta' in doc
            assert 'p_value' in doc
            assert 'fdr' in doc
            assert 'files_filesets' in doc
            assert doc['label'] == 'predicted gene regulatory networks'
            assert doc['source'] == 'IGVF'
            assert doc['class'] == 'regulatory_interaction'
            assert doc['method']
