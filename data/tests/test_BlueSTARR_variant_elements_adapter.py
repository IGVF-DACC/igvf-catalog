import json
import pytest
from adapters.BlueSTARR_variant_elements_adapter import BlueSTARRVariantElement
from adapters.writer import SpyWriter


def test_bluestarr_adapter():
    writer = SpyWriter()
    adapter = BlueSTARRVariantElement(
        filepath='./samples/bluestarr_variant_element.example.tsv', writer=writer, write_missing_variants=False)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert 'log2FC' in first_item
    assert 'label' in first_item
    assert 'method' in first_item
    assert 'biosample_context' in first_item
    assert 'biosample_term' in first_item
    assert 'name' in first_item
    assert 'inverse_name' in first_item
    assert 'source' in first_item
    assert 'source_url' in first_item
    assert first_item['source'] == BlueSTARRVariantElement.SOURCE
    assert first_item['source_url'] == BlueSTARRVariantElement.SOURCE_URL
    assert first_item['_to'] == f'genomic_elements/candidate_cis_regulatory_element_chr10_100005234_100005491_GRCh38_IGVFFI7195KIHI'
