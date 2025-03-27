import json
import pytest
from adapters.VAMP_coding_variant_scores_adapter import VAMPAdapter
from adapters.writer import SpyWriter


def test_vamp_adapter():
    writer = SpyWriter()
    adapter = VAMPAdapter(
        filepath='./samples/bluestarr_variant_element.example.tsv', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert 'abundance_score' in first_item
    assert 'abundance_sd' in first_item
    assert 'abundance_se' in first_item
    assert 'ci_upper' in first_item
    assert 'ci_lower' in first_item
    assert 'abundance_Rep1' in first_item
    assert 'abundance_Rep2' in first_item
    assert 'abundance_Rep3' in first_item
    assert 'source' in first_item
    assert 'source_url' in first_item
    assert first_item['source'] == VAMPAdapter.SOURCE
    assert first_item['source_url'] == VAMPAdapter.SOURCE_URL
    assert first_item['_to'] == f'ontology_terms/{VAMPAdapter.PHENOTYPE_TERM}'
