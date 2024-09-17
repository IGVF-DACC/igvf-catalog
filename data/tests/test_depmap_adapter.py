import json
from adapters.depmap_adapter import DepMap
from adapters.writer import SpyWriter


def test_depmap_adapter_process_file():
    writer = SpyWriter()
    adapter = DepMap(
        filepath='./samples/DepMap/CRISPRGeneDependency_transposed_example.csv',
        type='edge',
        label='gene_term',
        writer=writer
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
        type='edge',
        label='depmap'
    )
    assert adapter.filepath == './samples/DepMap/CRISPRGeneDependency_transposed_example.csv'
    assert adapter.type == 'edge'
    assert adapter.label == 'depmap'
    assert adapter.dataset == 'depmap'
    assert adapter.dry_run == True
    assert adapter.writer is None, 'Writer should be None by default.'


def test_depmap_adapter_missing_gene_id_mapping():
    writer = SpyWriter()
    adapter = DepMap(
        filepath='./samples/DepMap/CRISPRGeneDependency_transposed_example.csv',
        type='edge',
        label='depmap',
        writer=writer
    )
    adapter.process_file()

    assert len(
        writer.contents) > 0, 'No records were parsed despite missing gene mappings.'
    for item in writer.contents:
        if item.startswith('{'):
            data = json.loads(item)
            # Ensure that records with missing gene IDs are skipped
            assert 'gene_dependency' in data, "Record should contain 'gene_dependency'."
            assert data['gene_dependency'] >= DepMap.CUTOFF, 'Dependency score below cutoff.'


def test_depmap_adapter_dependency_cutoff():
    writer = SpyWriter()
    adapter = DepMap(
        filepath='./samples/DepMap/CRISPRGeneDependency_transposed_example.csv',
        type='edge',
        label='depmap',
        writer=writer
    )
    adapter.process_file()

    for item in writer.contents:
        if item.startswith('{'):
            data = json.loads(item)
            assert data['gene_dependency'] >= DepMap.CUTOFF, (
                f"Dependency score {data['gene_dependency']} below cutoff."
            )
