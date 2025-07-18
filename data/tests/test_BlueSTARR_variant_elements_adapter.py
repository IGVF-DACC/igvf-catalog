import json
import pytest
from adapters.BlueSTARR_variant_elements_adapter import BlueSTARRVariantElement
from adapters.writer import SpyWriter
from unittest.mock import patch
from unittest.mock import patch, mock_open


@patch('adapters.BlueSTARR_variant_elements_adapter.bulk_check_spdis_in_arangodb', return_value=set())
@patch('builtins.open', new_callable=mock_open, read_data='chr5\t1778763\t1779094\t0.131\tNC_000005.10:1778862:T:G\n')
def test_process_file_variant(mock_file, mock_bulk_check, mocker):
    mocker.patch(
        'adapters.BlueSTARR_variant_elements_adapter.load_variant',
        return_value=({'_key': 'NC_000005.10:1778862:T:G', 'spdi': 'NC_000005.10:1778862:T:G', 'hgvs': 'NC_000005.10:g.1778863T>G',
                      'variation_type': 'SNP'}, None)
    )
    writer = SpyWriter()
    adapter = BlueSTARRVariantElement(
        filepath='./samples/bluestarr_variant_element.example.tsv', writer=writer, label='variant')
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert 'spdi' in first_item
    assert 'hgvs' in first_item
    assert 'variation_type' in first_item
    assert first_item['source'] == BlueSTARRVariantElement.SOURCE
    assert first_item['source_url'] == BlueSTARRVariantElement.SOURCE_URL


@patch('adapters.helpers.get_ref_seq_by_spdi', return_value='T')
@patch('adapters.BlueSTARR_variant_elements_adapter.bulk_check_spdis_in_arangodb', return_value={'NC_000005.10:1778862:T:G'})
@patch('builtins.open', new_callable=mock_open, read_data='chr5\t1778763\t1779094\t0.131\tNC_000005.10:1778862:T:G\n')
def test_process_file_variant_genomic_element(mock_file, mock_bulk_check, mock_validate, mocker):
    mocker.patch('adapters.BlueSTARR_variant_elements_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    adapter = BlueSTARRVariantElement(
        filepath='./samples/bluestarr_variant_element.example.tsv', writer=writer, label='variant_genomic_element')
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert 'log2FC' in first_item
    assert 'label' in first_item
    assert first_item['source'] == BlueSTARRVariantElement.SOURCE
    assert first_item['source_url'] == BlueSTARRVariantElement.SOURCE_URL


def test_invalid_label_raises_error():
    with pytest.raises(ValueError, match='Invalid label. Allowed values: variant,variant_genomic_element'):
        BlueSTARRVariantElement(
            filepath='./samples/bluestarr_variant_element.example.tsv', label='invalid_label')


@patch('adapters.BlueSTARR_variant_elements_adapter.bulk_check_spdis_in_arangodb', return_value=set())
@patch('builtins.open', new_callable=mock_open, read_data='chr5\t1778763\t1779094\t0.131\tNC_000005.10:1778862:T:G\n')
def test_process_file_handles_empty_chunk(mock_file, mock_bulk_check, mocker):
    mocker.patch(
        'adapters.BlueSTARR_variant_elements_adapter.load_variant',
        return_value=({'_key': 'NC_000005.10:1778862:T:G', 'spdi': 'NC_000005.10:1778862:T:G', 'hgvs': 'NC_000005.10:g.1778863T>G',
                      'variation_type': 'SNP'}, None)
    )
    writer = SpyWriter()
    adapter = BlueSTARRVariantElement(
        filepath='./samples/bluestarr_variant_element.example.tsv', writer=writer, label='variant')
    adapter.process_file()
    # Ensure no errors occur with a single chunk
    assert len(writer.contents) > 0


@patch('adapters.BlueSTARR_variant_elements_adapter.bulk_check_spdis_in_arangodb', return_value={'NC_000005.10:1778862:T:G'})
@patch('builtins.open', new_callable=mock_open, read_data='chr5\t1778763\t1779094\t0.131\tNC_000005.10:1778862:T:G\n')
def test_process_file_skips_loaded_variants(mock_file, mock_bulk_check, mocker):
    mocker.patch(
        'adapters.BlueSTARR_variant_elements_adapter.load_variant',
        return_value=({'_key': 'NC_000005.10:1778862:T:G', 'spdi': 'NC_000005.10:1778862:T:G', 'hgvs': 'NC_000005.10:g.1778863T>G',
                      'variation_type': 'SNP'}, None)
    )
    writer = SpyWriter()
    adapter = BlueSTARRVariantElement(
        filepath='./samples/bluestarr_variant_element.example.tsv', writer=writer, label='variant')
    adapter.process_file()
    # No unloaded variants should be processed
    assert len(writer.contents) == 0


@patch('adapters.BlueSTARR_variant_elements_adapter.bulk_check_spdis_in_arangodb', return_value=set())
@patch('builtins.open', new_callable=mock_open, read_data='chr5\t1778763\t1779094\t0.131\tNC_000005.10:1778862:T:G\n')
def test_process_file_skips_variant_on_ref_mismatch(mock_file, mock_bulk_check, mocker):
    mocker.patch(
        'adapters.BlueSTARR_variant_elements_adapter.load_variant',
        return_value=({}, {'variant_id': 'NC_000005.10:1778862:T:G',
                      'reason': 'Ref allele mismatch'})
    )
    writer = SpyWriter()
    adapter = BlueSTARRVariantElement(
        filepath='./samples/bluestarr_variant_element.example.tsv',
        writer=writer,
        label='variant'
    )
    adapter.process_file()
    # Since ref != 'T' from SPDI, variant should be skipped
    assert len(writer.contents) == 0
