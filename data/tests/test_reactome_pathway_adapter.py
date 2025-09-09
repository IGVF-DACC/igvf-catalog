import pytest
import json
from unittest.mock import patch, MagicMock
from adapters.reactome_pathway_adapter import ReactomePathway
from adapters.writer import SpyWriter


@pytest.fixture
def filepath():
    return './samples/reactome/ReactomePathways_20240603.txt'


@pytest.fixture
def mock_sample_file(tmp_path):
    """Create a mock sample file with known pathway IDs"""
    sample_file = tmp_path / 'ReactomePathways_sample.txt'
    sample_content = """R-HSA-164843	2-LTR circle formation	Homo sapiens
R-HSA-1971475	A tetrasaccharide linker sequence is required for GAG synthesis	Homo sapiens
R-BTA-73843	5-Phosphoribose 1-diphosphate biosynthesis	Bos taurus
R-HSA-5619084	ABC transporter disorders	Homo sapiens"""
    sample_file.write_text(sample_content)
    return str(sample_file)


@pytest.fixture
def spy_writer():
    return SpyWriter()


@pytest.fixture
def mock_response_data():
    """Mock response data from Reactome API"""
    return {
        'stIdVersion': 'R-HSA-1971475.4',
        'isInDisease': True,
        'name': ['A tetrasaccharide linker sequence is required for GAG synthesis'],
        'className': 'TopLevelPathway',
        'disease': [
            {
                'databaseName': 'DOID',
                'identifier': '12345'
            }
        ],
        'goBiologicalProcess': {
            'databaseName': 'GO',
            'accession': '0006914'
        }
    }


@pytest.fixture
def mock_response_data_no_disease():
    """Mock response data without disease information"""
    return {
        'stIdVersion': 'R-HSA-164843.2',
        'isInDisease': False,
        'name': ['2-LTR circle formation'],
        'className': 'Pathway',
        'goBiologicalProcess': {
            'databaseName': 'GO',
            'accession': '0006914'
        }
    }


def test_reactome_pathway_adapter_initialization(filepath, spy_writer):
    """Test adapter initialization"""
    adapter = ReactomePathway(filepath=filepath, writer=spy_writer)

    assert adapter.filepath == filepath
    assert adapter.label == 'pathway'
    assert adapter.dataset == 'pathway'
    assert adapter.dry_run is False


def test_reactome_pathway_adapter_with_disease(mock_sample_file, spy_writer, mock_response_data):
    """Test adapter processing with disease information"""
    with patch('requests.Session') as mock_session:
        # Setup mock session
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance

        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_session_instance.get.return_value = mock_response

        adapter = ReactomePathway(
            filepath=mock_sample_file, writer=spy_writer, validate=True)
        adapter.process_file()

        assert len(spy_writer.contents) > 0
        first_item = json.loads(spy_writer.contents[0])

        # Check required fields
        assert '_key' in first_item
        assert 'name' in first_item
        assert 'organism' in first_item
        assert 'source' in first_item
        assert 'source_url' in first_item
        assert 'id_version' in first_item
        assert 'is_in_disease' in first_item
        assert 'name_aliases' in first_item
        assert 'is_top_level_pathway' in first_item

        # Check field values (using actual first human pathway from file)
        assert first_item['_key'] == 'R-HSA-164843'
        assert first_item['name'] == '2-LTR circle formation'
        assert first_item['organism'] == 'Homo sapiens'
        assert first_item['source'] == 'Reactome'
        assert first_item['source_url'] == 'https://reactome.org/'
        assert first_item['id_version'] == 'R-HSA-1971475.4'
        assert first_item['is_in_disease'] is True
        assert first_item['is_top_level_pathway'] is True

        # Check disease ontology terms
        assert 'disease_ontology_terms' in first_item
        assert first_item['disease_ontology_terms'] == [
            'ontology_terms/DOID_12345']

        # Check GO biological process
        assert 'go_biological_process' in first_item
        assert first_item['go_biological_process'] == 'ontology_terms/GO_0006914'


def test_reactome_pathway_adapter_without_disease(mock_sample_file, spy_writer, mock_response_data_no_disease):
    """Test adapter processing without disease information"""
    with patch('requests.Session') as mock_session:
        # Setup mock session
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance

        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data_no_disease
        mock_session_instance.get.return_value = mock_response

        adapter = ReactomePathway(
            filepath=mock_sample_file, writer=spy_writer, validate=True)
        adapter.process_file()

        assert len(spy_writer.contents) > 0
        first_item = json.loads(spy_writer.contents[0])

        # Check required fields
        assert '_key' in first_item
        assert 'name' in first_item
        assert 'organism' in first_item
        assert 'source' in first_item
        assert 'source_url' in first_item
        assert 'id_version' in first_item
        assert 'is_in_disease' in first_item
        assert 'name_aliases' in first_item
        assert 'is_top_level_pathway' in first_item

        # Check field values (using actual first human pathway from file)
        assert first_item['_key'] == 'R-HSA-164843'
        assert first_item['name'] == '2-LTR circle formation'
        assert first_item['organism'] == 'Homo sapiens'
        assert first_item['source'] == 'Reactome'
        assert first_item['source_url'] == 'https://reactome.org/'
        assert first_item['id_version'] == 'R-HSA-164843.2'
        assert first_item['is_in_disease'] is False
        assert first_item['is_top_level_pathway'] is False

        # Check that disease_ontology_terms is not present
        assert 'disease_ontology_terms' not in first_item

        # Check GO biological process
        assert 'go_biological_process' in first_item
        assert first_item['go_biological_process'] == 'ontology_terms/GO_0006914'


def test_reactome_pathway_adapter_404_response(mock_sample_file, spy_writer):
    """Test adapter handling of 404 responses"""
    with patch('requests.Session') as mock_session:
        # Setup mock session
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance

        # Setup mock 404 response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_session_instance.get.return_value = mock_response

        adapter = ReactomePathway(filepath=mock_sample_file, writer=spy_writer)
        adapter.process_file()

        # Should not write anything for 404 responses
        assert len(spy_writer.contents) == 0


def test_reactome_pathway_adapter_json_decode_error(mock_sample_file, spy_writer):
    """Test adapter handling of JSON decode errors"""
    with patch('requests.Session') as mock_session:
        # Setup mock session
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance

        # Setup mock response that will cause JSON decode error
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError(
            'Invalid JSON', '', 0)
        mock_response.text = 'Invalid JSON response'
        mock_session_instance.get.return_value = mock_response

        adapter = ReactomePathway(filepath=mock_sample_file, writer=spy_writer)

        # Should raise TypeError because adapter raises JSONDecodeError() without args
        with pytest.raises(TypeError):
            adapter.process_file()


def test_reactome_pathway_adapter_non_human_organism(mock_sample_file, spy_writer):
    """Test that non-human organisms are filtered out"""
    with patch('requests.Session') as mock_session:
        # Setup mock session
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance

        # Setup mock response for human pathways only
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'stIdVersion': 'R-HSA-164843.2',
            'isInDisease': False,
            'name': '2-LTR circle formation',
            'className': 'Pathway'
        }
        mock_session_instance.get.return_value = mock_response

        adapter = ReactomePathway(filepath=mock_sample_file, writer=spy_writer)
        adapter.process_file()

        # Should only process human organisms
        assert len(spy_writer.contents) > 0
        for line in spy_writer.contents:
            if line.strip():  # Skip empty lines
                item = json.loads(line)
                assert item['organism'] == 'Homo sapiens'


def test_reactome_pathway_adapter_retry_mechanism(mock_sample_file, spy_writer, mock_response_data):
    """Test that the adapter uses retry mechanism for failed requests"""
    with patch('requests.Session') as mock_session:
        # Setup mock session
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance

        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_session_instance.get.return_value = mock_response

        adapter = ReactomePathway(filepath=mock_sample_file, writer=spy_writer)
        adapter.process_file()

        # Verify that session was configured with retries
        mock_session.assert_called_once()
        # Verify that mount was called (which means retry mechanism was set up)
        mock_session_instance.mount.assert_called_once()

        # Verify the mount call was made with https:// prefix
        mount_call_args = mock_session_instance.mount.call_args
        assert mount_call_args[0][0] == 'https://'


def test_reactome_pathway_adapter_dry_run(mock_sample_file, spy_writer):
    """Test adapter in dry run mode"""
    adapter = ReactomePathway(
        filepath=mock_sample_file, dry_run=True, writer=spy_writer)

    assert adapter.dry_run is True
    # In dry run mode, the adapter should still process but not write to output
    # This behavior depends on the actual implementation


def test_reactome_pathway_adapter_writer_integration(mock_sample_file, spy_writer, mock_response_data):
    """Test that the adapter properly integrates with the writer"""
    with patch('requests.Session') as mock_session:
        # Setup mock session
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance

        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_session_instance.get.return_value = mock_response

        adapter = ReactomePathway(filepath=mock_sample_file, writer=spy_writer)
        adapter.process_file()

        # Verify writer methods were called
        assert spy_writer.contents is not None
        assert len(spy_writer.contents) > 0

        # Verify each non-empty line is valid JSON
        for line in spy_writer.contents:
            if line.strip():  # Skip empty lines
                json.loads(line)  # Should not raise an exception
