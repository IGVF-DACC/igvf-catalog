import json
from unittest.mock import patch
from adapters.depmap_adapter import DepMap
from adapters.ontology_term_validator import OntologyTermValidator
from adapters.writer import SpyWriter
import pytest

CRISPR_SAMPLE = './samples/DepMap/CRISPRGeneDependency_transposed_example.csv'
MODEL_SAMPLE = './samples/DepMap/DepMap_model_example.csv'


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


@pytest.fixture(autouse=True)
def mock_file_fileset():
    """Fixture to mock get_file_fileset_by_accession_in_arangodb function."""
    with patch('adapters.depmap_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get:
        mock_get.return_value = {
            'class': 'observed data',
            'method': 'DepMap'
        }
        yield mock_get


@pytest.fixture(autouse=True)
def mock_ontology_term_validator():
    with patch('adapters.depmap_adapter.OntologyTermValidator') as MockValidator:
        MockValidator.normalize_term_key = staticmethod(
            OntologyTermValidator.normalize_term_key)
        mock_validator = MockValidator.return_value
        mock_validator.resolve.side_effect = (
            lambda term_key: OntologyTermValidator.normalize_term_key(term_key)
        )
        mock_validator.validate.return_value = True
        mock_validator.ensure.return_value = True
        yield mock_validator


def _make_adapter(**kwargs):
    defaults = {
        'filepath': CRISPR_SAMPLE,
        'reference_filepath': MODEL_SAMPLE,
        'label': 'depmap',
    }
    defaults.update(kwargs)
    return DepMap(**defaults)


def test_depmap_adapter_process_file(mock_file_fileset):
    writer = SpyWriter()
    adapter = _make_adapter(writer=writer, validate=True)
    adapter.file_accession = 'IGVFFI8832ZBCC'
    adapter.model_file_accession = 'IGVFFI6415FDRI'
    adapter.process_file()

    mock_file_fileset.assert_called_once_with('IGVFFI8832ZBCC')
    assert len(writer.contents) > 1, 'No records were parsed.'
    first_item = json.loads(writer.contents[0])

    # Check for presence of essential keys
    expected_keys = [
        '_key', '_from', '_to', 'biological_context',
        'model_id', 'model_type', 'cancer_term',
        'gene_dependency', 'source', 'source_url',
        'source_file', 'name', 'inverse_name',
        'class', 'method', 'label', 'files_filesets'
    ]
    for key in expected_keys:
        assert key in first_item, f'Missing key: {key}'

    # Additional specific assertions
    assert first_item['source'] == 'DepMap'
    assert first_item['source_url'] == 'https://depmap.org/portal/'
    assert first_item['source_file'] == 'CRISPRGeneDependency.csv'
    assert first_item['name'] == 'essential in'
    assert first_item['inverse_name'] == 'dependent on'
    assert first_item['class'] == 'observed data'
    assert first_item['method'] == 'DepMap'
    assert first_item['label'] == first_item['method']
    assert first_item['files_filesets'] == 'files_filesets/IGVFFI8832ZBCC'
    assert first_item['_to'].startswith('ontology_terms/CVCL_')
    assert first_item['cancer_term'].startswith('ontology_terms/Oncotree_')
    assert first_item['cancer_term'].count('/') == 1


def test_depmap_adapter_sanitizes_oncotree_slash_in_cancer_term(mocker):
    """Oncotree codes with '/' must match sanitized ontology_terms _key (e.g. MDS/MPN → MDS_MPN)."""
    mocker.patch(
        'adapters.depmap_adapter.get_gene_map_from_arangodb',
        return_value={'FAKEGENE': ['ENSG00000000001']},
    )

    import tempfile
    import os

    with open(CRISPR_SAMPLE, 'r') as sample_file:
        header = sample_file.readline().strip().split(',')

    model_id = header[1]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(','.join(header) + '\n')
        row = ['FAKEGENE (0)'] + ['0.9'] + [''] * (len(header) - 2)
        f.write(','.join(row) + '\n')
        temp_file_path = f.name

    try:
        writer = SpyWriter()
        adapter = _make_adapter(filepath=temp_file_path, writer=writer)
        adapter.file_accession = 'IGVFFI8832ZBCC'

        original_load = adapter.load_cell_ontology_id_mapping

        def load_with_slash_code():
            original_load()
            adapter.cell_ontology_id_mapping[model_id]['oncotree_code'] = 'MDS/MPN'

        adapter.load_cell_ontology_id_mapping = load_with_slash_code
        adapter.process_file()

        items = [json.loads(item)
                 for item in writer.contents if item.startswith('{')]
        assert items
        assert all(
            item['cancer_term'] == 'ontology_terms/Oncotree_MDS_MPN'
            for item in items
        )
    finally:
        os.unlink(temp_file_path)


def test_depmap_adapter_initialization():
    adapter = _make_adapter()
    assert adapter.filepath == CRISPR_SAMPLE
    assert adapter.reference_filepath == MODEL_SAMPLE
    assert adapter.label == 'depmap'
    assert adapter.writer is None, 'Writer should be None by default.'
    assert adapter.file_accession == 'CRISPRGeneDependency_transposed_example'
    assert adapter.model_file_accession == 'DepMap_model_example'


def test_depmap_adapter_requires_reference_filepath():
    with pytest.raises(TypeError):
        DepMap(filepath=CRISPR_SAMPLE, label='depmap')


def test_depmap_adapter_missing_gene_id_mapping():
    writer = SpyWriter()
    adapter = _make_adapter(writer=writer)
    adapter.file_accession = 'IGVFFI8832ZBCC'
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

    with open(CRISPR_SAMPLE, 'r') as sample_file:
        header = sample_file.readline().strip().split(',')

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(','.join(header) + '\n')
        row = ['FAKEGENE (0)'] + ['0.9'] + [''] * (len(header) - 2)
        f.write(','.join(row) + '\n')
        temp_file_path = f.name

    try:
        writer = SpyWriter()
        adapter = _make_adapter(filepath=temp_file_path, writer=writer)
        adapter.file_accession = 'IGVFFI8832ZBCC'
        adapter.process_file()

        gene_ids = {json.loads(item)['_from']
                    for item in writer.contents if item.startswith('{')}
        assert gene_ids == {'genes/ENSG00000000001', 'genes/ENSG00000000002'}
    finally:
        os.unlink(temp_file_path)


def test_depmap_adapter_synonym_fallback(mocker):
    """A gene symbol not found by name should be resolved via its synonym."""
    def fake_gene_map(field):
        if field == 'synonyms':
            return {'FAKEGENE': ['ENSG00000000099']}
        return {}

    mocker.patch(
        'adapters.depmap_adapter.get_gene_map_from_arangodb',
        side_effect=fake_gene_map
    )

    import tempfile
    import os

    with open(CRISPR_SAMPLE, 'r') as sample_file:
        header = sample_file.readline().strip().split(',')

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(','.join(header) + '\n')
        row = ['FAKEGENE (0)'] + ['0.9'] + [''] * (len(header) - 2)
        f.write(','.join(row) + '\n')
        temp_file_path = f.name

    try:
        writer = SpyWriter()
        adapter = _make_adapter(filepath=temp_file_path, writer=writer)
        adapter.file_accession = 'IGVFFI8832ZBCC'
        adapter.process_file()

        gene_ids = {json.loads(item)['_from']
                    for item in writer.contents if item.startswith('{')}
        assert gene_ids == {'genes/ENSG00000000099'}
    finally:
        os.unlink(temp_file_path)


def test_depmap_adapter_maps_by_entrez_not_shared_synonym(mocker):
    """CFAP90 and WBP11 share a synonym hit but have distinct Entrez ids."""
    def fake_gene_map(field):
        if field == 'entrez':
            return {
                'ENTREZ:134121': ['ENSG00000215217'],
                'ENTREZ:51729': ['ENSG00000084463'],
            }
        if field == 'name':
            return {'WBP11': ['ENSG00000084463']}
        if field == 'synonyms':
            return {'CFAP90': ['ENSG00000215217', 'ENSG00000084463']}
        return {}

    mock_get_gene_map = mocker.patch(
        'adapters.depmap_adapter.get_gene_map_from_arangodb',
        side_effect=fake_gene_map,
    )

    import tempfile
    import os

    with open(CRISPR_SAMPLE, 'r') as sample_file:
        header = sample_file.readline().strip().split(',')

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(','.join(header) + '\n')
        empty_tail = [''] * (len(header) - 2)
        f.write(','.join(['CFAP90 (134121)', '0.9'] + empty_tail) + '\n')
        f.write(','.join(['WBP11 (51729)', '0.9'] + empty_tail) + '\n')
        temp_file_path = f.name

    try:
        writer = SpyWriter()
        adapter = _make_adapter(filepath=temp_file_path, writer=writer)
        adapter.file_accession = 'IGVFFI8832ZBCC'
        adapter.process_file()

        gene_ids = {json.loads(item)['_from']
                    for item in writer.contents if item.startswith('{')}
        assert gene_ids == {
            'genes/ENSG00000215217',
            'genes/ENSG00000084463',
        }
        assert mock_get_gene_map.call_args_list == [mocker.call('entrez')]
    finally:
        os.unlink(temp_file_path)


def test_depmap_adapter_skips_synonym_lookup_when_all_matched(mocker):
    """The synonyms lookup should not run when every still-unmapped symbol matches by name."""
    def fake_gene_map(field):
        if field == 'name':
            return {'FAKEGENE': ['ENSG00000000001']}
        return {}

    mock_get_gene_map = mocker.patch(
        'adapters.depmap_adapter.get_gene_map_from_arangodb',
        side_effect=fake_gene_map,
    )

    import tempfile
    import os

    with open(CRISPR_SAMPLE, 'r') as sample_file:
        header = sample_file.readline().strip().split(',')

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(','.join(header) + '\n')
        row = ['FAKEGENE (0)'] + ['0.9'] + [''] * (len(header) - 2)
        f.write(','.join(row) + '\n')
        temp_file_path = f.name

    try:
        writer = SpyWriter()
        adapter = _make_adapter(filepath=temp_file_path, writer=writer)
        adapter.file_accession = 'IGVFFI8832ZBCC'
        adapter.process_file()

        assert [call.args[0] for call in mock_get_gene_map.call_args_list] == [
            'entrez', 'name']
    finally:
        os.unlink(temp_file_path)


def test_depmap_adapter_dependency_cutoff():
    writer = SpyWriter()
    adapter = _make_adapter(writer=writer)
    adapter.file_accession = 'IGVFFI8832ZBCC'
    adapter.process_file()

    first_item = json.loads(writer.contents[0])
    assert first_item['gene_dependency'] >= DepMap.CUTOFF, (
        f"Dependency score {first_item['gene_dependency']} below cutoff."
    )


def test_depmap_adapter_validate_doc_invalid():
    writer = SpyWriter()
    adapter = _make_adapter(writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)


def test_depmap_adapter_loads_model_columns_by_header():
    adapter = _make_adapter()
    adapter.load_cell_ontology_id_mapping()
    props = adapter.cell_ontology_id_mapping['ACH-000001']
    assert props['cell_ontology_id'] == 'CVCL_0465'
    assert props['biological_context'] == 'NIH:OVCAR-3'
    assert props['model_type'] == 'HGSOC'
    assert props['oncotree_code'] == 'HGSOC'
