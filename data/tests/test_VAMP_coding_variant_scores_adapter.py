import json
import pytest
from adapters.VAMP_coding_variant_scores_adapter import VAMPAdapter
from adapters.writer import SpyWriter


def test_vamp_adapter():
    writer = SpyWriter()
    adapter = VAMPAdapter(
        filepath='./samples/vamp_coding_variants.example.csv', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert 'abundance_score:long' in first_item
    assert 'abundance_sd:long' in first_item
    assert 'abundance_se:long' in first_item
    assert 'ci_upper:long' in first_item
    assert 'ci_lower:long' in first_item
    assert 'abundance_Rep1:long' in first_item
    assert 'abundance_Rep2:long' in first_item
    assert 'abundance_Rep3:long' in first_item
    assert 'source' in first_item
    assert 'source_url' in first_item
    assert first_item['source'] == VAMPAdapter.SOURCE
    assert first_item['source_url'] == VAMPAdapter.SOURCE_URL
    assert first_item['_to'] == f'ontology_terms/{VAMPAdapter.PHENOTYPE_TERM}'


def test_vamp_adapter_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label. Allowed values: vamp_coding_variants_phenotypes'):
        VAMPAdapter(filepath='./samples/vamp_coding_variants.example.csv',
                    label='invalid_label', writer=writer)


def test_vamp_adapter_initialization():
    writer = SpyWriter()
    adapter = VAMPAdapter(
        filepath='./samples/vamp_coding_variants.example.csv', writer=writer)
    assert adapter.filepath == './samples/vamp_coding_variants.example.csv'
    assert adapter.label == 'vamp_coding_variants_phenotypes'
    assert adapter.dataset == 'vamp_coding_variants_phenotypes'
    assert adapter.type == 'edge'
    assert adapter.dry_run == True
    assert adapter.writer == writer


def test_vamp_adapter_load_coding_variant_id():
    adapter = VAMPAdapter(
        filepath='./samples/vamp_coding_variants.example.csv')
    adapter.load_coding_variant_id()
    assert hasattr(adapter, 'coding_variant_id')
    assert isinstance(adapter.coding_variant_id, dict)
    assert len(adapter.coding_variant_id) > 0
