"""Tests for base adapter class."""

import pytest
import json
from unittest.mock import patch, MagicMock
from adapters.base import BaseAdapter
from adapters.writer import SpyWriter


# Test implementation of BaseAdapter
class TestAdapter(BaseAdapter):
    """Concrete implementation for testing BaseAdapter."""
    ALLOWED_LABELS = ['test_nodes', 'test_edges']

    def __init__(self, filepath, label, writer, validate=False, schema_type='nodes'):
        self.schema_type = schema_type
        super().__init__(filepath, label, writer, validate)
        self.source = 'TestSource'

    def _get_schema_type(self):
        """Return schema type (nodes or edges)."""
        return self.schema_type

    def _get_collection_name(self):
        """Return collection name."""
        if self.label == 'test_nodes':
            return 'test_collection'
        else:
            return 'test_edge_collection'

    def process_file(self):
        self.writer.open()
        doc = {'_key': 'test1', 'name': 'Test',
               'source': self.source, 'source_url': 'http://test'}
        if self.validate:
            self.validate_doc(doc)
        self.writer.write(json.dumps(doc))
        self.writer.close()


# Basic tests
def test_adapter_initialization():
    """Test BaseAdapter initializes correctly."""
    writer = SpyWriter()
    adapter = TestAdapter(
        filepath='./dummy.txt',
        label='test_nodes',
        writer=writer,
        validate=False
    )

    assert adapter.filepath == './dummy.txt'
    assert adapter.label == 'test_nodes'
    assert adapter.writer == writer
    assert adapter.validate is False
    assert adapter.source == 'TestSource'


def test_adapter_invalid_label():
    """Test BaseAdapter raises error for invalid label."""
    writer = SpyWriter()

    with pytest.raises(ValueError, match='Invalid label'):
        TestAdapter(
            filepath='./dummy.txt',
            label='invalid_label',
            writer=writer
        )


def test_adapter_process_file():
    """Test BaseAdapter can process file."""
    writer = SpyWriter()
    adapter = TestAdapter(
        filepath='./dummy.txt',
        label='test_nodes',
        writer=writer
    )

    adapter.process_file()

    assert len(writer.contents) == 1
    doc = json.loads(writer.contents[0])
    assert doc['_key'] == 'test1'
    assert doc['source'] == 'TestSource'


@patch('adapters.base.base_adapter.get_schema')
def test_adapter_with_validation(mock_get_schema):
    """Test BaseAdapter with validation enabled."""
    # Mock schema and validator
    mock_schema = {'type': 'object', 'properties': {}}
    mock_get_schema.return_value = mock_schema

    writer = SpyWriter()
    adapter = TestAdapter(
        filepath='./dummy.txt',
        label='test_nodes',
        writer=writer,
        validate=True
    )

    assert adapter.validate is True
    assert hasattr(adapter, 'schema')
    assert hasattr(adapter, 'validator')
    mock_get_schema.assert_called_once()


# Test schema collection methods
def test_adapter_node_schema_collection():
    """Test adapter uses correct schema type for nodes."""
    writer = SpyWriter()

    with patch('adapters.base.base_adapter.get_schema') as mock_get_schema:
        mock_get_schema.return_value = {}
        adapter = TestAdapter(
            filepath='./dummy.txt',
            label='test_nodes',
            writer=writer,
            validate=True,
            schema_type='nodes'
        )

        # Verify it called get_schema with correct type
        call_args = mock_get_schema.call_args[0]
        assert call_args[0] == 'nodes'
        assert call_args[1] == 'test_collection'


def test_adapter_edge_schema_collection():
    """Test adapter uses correct schema type for edges."""
    writer = SpyWriter()

    with patch('adapters.base.base_adapter.get_schema') as mock_get_schema:
        mock_get_schema.return_value = {}
        adapter = TestAdapter(
            filepath='./dummy.txt',
            label='test_edges',
            writer=writer,
            validate=True,
            schema_type='edges'
        )

        # Verify it called get_schema with 'edges' type
        call_args = mock_get_schema.call_args[0]
        assert call_args[0] == 'edges'
        assert call_args[1] == 'test_edge_collection'


# Tests for validation
@patch('adapters.base.base_adapter.get_schema')
def test_validate_doc_success(mock_get_schema):
    """Test validate_doc with valid document."""
    mock_schema = {
        'type': 'object',
        'properties': {
            '_key': {'type': 'string'},
            'name': {'type': 'string'}
        },
        'required': ['_key', 'name']
    }
    mock_get_schema.return_value = mock_schema

    writer = SpyWriter()
    adapter = TestAdapter(
        filepath='./dummy.txt',
        label='test_nodes',
        writer=writer,
        validate=True
    )

    valid_doc = {'_key': 'test', 'name': 'Test',
                 'source': 'Test', 'source_url': 'http://test'}

    # Should not raise
    adapter.validate_doc(valid_doc)


@patch('adapters.base.base_adapter.get_schema')
def test_validate_doc_failure(mock_get_schema):
    """Test validate_doc with invalid document."""
    mock_schema = {
        'type': 'object',
        'properties': {
            '_key': {'type': 'string'},
            'name': {'type': 'string'}
        },
        'required': ['_key', 'name']
    }
    mock_get_schema.return_value = mock_schema

    writer = SpyWriter()
    adapter = TestAdapter(
        filepath='./dummy.txt',
        label='test_nodes',
        writer=writer,
        validate=True
    )

    invalid_doc = {'_key': 'test'}  # Missing 'name'

    with pytest.raises(ValueError, match='Document validation failed'):
        adapter.validate_doc(invalid_doc)


# Tests for logging
def test_adapter_has_logger():
    """Test adapter has logger configured."""
    writer = SpyWriter()
    adapter = TestAdapter(
        filepath='./dummy.txt',
        label='test_nodes',
        writer=writer
    )

    assert hasattr(adapter, 'logger')
    assert adapter.logger.name == 'TestAdapter'


# Tests for configuration paths
def test_get_config_path():
    """Test get_config_path helper method."""
    writer = SpyWriter()
    adapter = TestAdapter(
        filepath='./dummy.txt',
        label='test_nodes',
        writer=writer
    )

    path = adapter.get_config_path('test_file.txt')

    assert 'test_file.txt' in str(path)
    assert path.is_absolute()


# Tests for abstract methods
def test_base_adapter_abstract_methods():
    """Test BaseAdapter cannot be instantiated directly."""
    writer = SpyWriter()

    with pytest.raises(TypeError):
        BaseAdapter(
            filepath='./dummy.txt',
            label='test',
            writer=writer
        )


def test_adapter_without_collection_name():
    """Test BaseAdapter requires _get_collection_name implementation."""

    class IncompleteAdapter(BaseAdapter):
        ALLOWED_LABELS = ['test']

        def process_file(self):
            pass

    writer = SpyWriter()

    with patch('adapters.base.base_adapter.get_schema') as mock_get_schema:
        mock_get_schema.return_value = {}
        with pytest.raises(NotImplementedError, match='must implement'):
            IncompleteAdapter(
                filepath='./dummy.txt',
                label='test',
                writer=writer,
                validate=True
            )
