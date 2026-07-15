import json
from unittest.mock import patch
from adapters.depmap_adapter import DepMap
from adapters.writer import SpyWriter
import pytest


# mock get_gene_map_from_arangodb so gene collection data change will not affect the test
@pytest.fixture(autouse=True)
def mock_gene_map():
    """Fixture to mock get_gene_map_from_arangodb function."""
    with patch('adapters.depmap_adapter.get_gene_map_from_arangodb') as mock_get_gene_map:
        mock_get_gene_map.return_value = {
            'A1BG': ['ENSG00000121410'],
            'A1CF': ['ENSG00000148584'],
            'A2M': ['ENSG00000175899'],
            'A2ML1': ['ENSG00000166535'],
            'A3GALT2': ['ENSG00000184389']
        }
        yield mock_get_gene_map


def test_depmap_adapter_process_file():
    writer = SpyWriter()
    adapter = DepMap(
        filepath='./samples/DepMap/CRISPRGeneDependency_transposed_example.csv',
        label='depmap',
        writer=writer,
        validate=True
    )
    adapter.process_file()

    assert len(writer.contents) > 1, 'No records were parsed.'
    first_item = json.loads(writer.contents[0])

    # Check for presence of essential keys
    expected_keys = [
        '_key', '_from', '_to', 'biology_context',
        'model_id', 'model_type', 'cancer_term',
        'gene_dependency', 'source', 'source_url',
        'source_file', 'name', 'inverse_name'
    ]
    for key in expected_keys:
        assert key in first_item, f'Missing key: {key}'

    # Additional specific assertions
    assert first_item['source'] == 'DepMap'
    assert first_item['source_url'] == 'https://depmap.org/portal/'
    assert first_item['source_file'] == 'CRISPRGeneDependency.csv'
    assert first_item['name'] == 'essential in'
    assert first_item['inverse_name'] == 'dependent on'


def test_depmap_adapter_initialization():
    adapter = DepMap(
        filepath='./samples/DepMap/CRISPRGeneDependency_transposed_example.csv',
        label='depmap'
    )
    assert adapter.filepath == './samples/DepMap/CRISPRGeneDependency_transposed_example.csv'
    assert adapter.label == 'depmap'
    assert adapter.writer is None, 'Writer should be None by default.'


def test_depmap_adapter_missing_gene_id_mapping():
    writer = SpyWriter()
    adapter = DepMap(
        filepath='./samples/DepMap/CRISPRGeneDependency_transposed_example.csv',
        label='depmap',
        writer=writer
    )
    adapter.process_file()

    assert len(
        writer.contents) > 0, 'No records were parsed despite missing gene mappings.'
    first_item = json.loads(writer.contents[0])
    assert 'gene_dependency' in first_item, "Record should contain 'gene_dependency'."
    assert first_item['gene_dependency'] >= DepMap.CUTOFF, 'Dependency score below cutoff.'


def test_depmap_adapter_multiple_gene_ids(mocker):
    """A gene symbol mapping to multiple Ensembl ids should produce an edge for each id, not just the first."""
    mocker.patch(
        'adapters.depmap_adapter.get_gene_map_from_arangodb',
        return_value={
            'FAKEGENE': ['ENSG00000000001', 'ENSG00000000002'],
        }
    )

    import tempfile
    import os

    with open('./samples/DepMap/CRISPRGeneDependency_transposed_example.csv', 'r') as sample_file:
        header = sample_file.readline().strip().split(',')

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(','.join(header) + '\n')
        row = ['FAKEGENE (0)'] + ['0.9'] + [''] * (len(header) - 2)
        f.write(','.join(row) + '\n')
        temp_file_path = f.name

    try:
        writer = SpyWriter()
        adapter = DepMap(filepath=temp_file_path,
                         label='depmap', writer=writer)
        adapter.process_file()

        gene_ids = {json.loads(item)['_from']
                    for item in writer.contents if item.startswith('{')}
        assert gene_ids == {'genes/ENSG00000000001', 'genes/ENSG00000000002'}
    finally:
        os.unlink(temp_file_path)


def test_depmap_adapter_dependency_cutoff():
    writer = SpyWriter()
    adapter = DepMap(
        filepath='./samples/DepMap/CRISPRGeneDependency_transposed_example.csv',
        label='depmap',
        writer=writer
    )
    adapter.process_file()

    first_item = json.loads(writer.contents[0])
    assert first_item['gene_dependency'] >= DepMap.CUTOFF, (
        f"Dependency score {first_item['gene_dependency']} below cutoff."
    )


def test_depmap_adapter_validate_doc_invalid():
    writer = SpyWriter()
    adapter = DepMap(
        filepath='./samples/DepMap/CRISPRGeneDependency_transposed_example.csv',
        label='depmap',
        writer=writer,
        validate=True
    )
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
