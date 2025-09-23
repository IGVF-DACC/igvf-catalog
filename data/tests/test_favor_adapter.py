import json
from adapters.favor_adapter import Favor
from adapters.writer import SpyWriter
from unittest.mock import MagicMock, patch, mock_open


@patch('adapters.favor_adapter.build_hgvs_from_spdi', return_value='chr21:g.5025533G>C')
@patch('adapters.favor_adapter.SeqRepo')
def test_favor_adapter(
    mock_seqrepo,
    mock_build_hgvs
):
    writer = SpyWriter()

    adapter = Favor(
        filepath='./samples/favor_sample.vcf', ca_ids_path='./samples/ca_ids.rdict', writer=writer)
    adapter.process_file()
    assert len(writer.contents) > 1
    first_item = json.loads(writer.contents[0])
    assert '_key' in first_item
    assert 'name' in first_item
    assert 'source' in first_item
    assert 'chr' in first_item
    assert 'pos' in first_item
    assert 'ref' in first_item
    assert 'alt' in first_item
    assert first_item['organism'] == 'Homo sapiens'
    assert first_item['source'] == 'FAVOR'


def test_convert_freq_value_handles_dot_and_float():
    writer = SpyWriter()
    adapter = Favor(
        filepath='./samples/favor_sample.vcf', ca_ids_path='./samples/ca_ids.rdict', writer=writer)
    assert adapter.convert_freq_value('.') == 0
    assert adapter.convert_freq_value('1.23') == 1.23
    assert adapter.convert_freq_value('abc') == 'abc'


def test_parse_metadata_freq_and_favor_fields():
    writer = SpyWriter()
    adapter = Favor(
        filepath='./samples/favor_sample.vcf', ca_ids_path='./samples/ca_ids.rdict', writer=writer)

    info = 'FREQ=Korea1K:0.9545,0.04545|TOPMED:0.8587|dbGaP_PopFreq:0.9243,0.07566;FAVORFullDB/variant_annovar=21-5025532-5025532-G-C;FAVORFullDB/cadd_phred=2.753'
    result = adapter.parse_metadata(info)
    assert 'freq' in result
    assert 'variant_annovar' in result
    assert 'cadd_phred' in result
    assert result['freq']['korea1k']['ref'] == 0.9545
    assert result['freq']['korea1k']['alt'] == 0.04545
    assert result['freq']['topmed']['ref'] == 0.8587
    assert result['variant_annovar'].startswith('21-5025532')
    assert isinstance(result['cadd_phred'], float)


def test_parse_metadata_handles_missing_value():
    writer = SpyWriter()
    adapter = Favor(
        filepath='./samples/favor_sample.vcf', ca_ids_path='./samples/ca_ids.rdict', writer=writer)

    info = 'FREQ=Korea1K:1.0'
    result = adapter.parse_metadata(info)
    assert result['freq']['korea1k']['ref'] == 1.0
    assert result['freq']['korea1k']['alt'] == 0.0


def test_parse_metadata_ignores_unknown_favor_fields():
    writer = SpyWriter()
    adapter = Favor(
        filepath='./samples/favor_sample.vcf', ca_ids_path='./samples/ca_ids.rdict', writer=writer)

    info = 'FAVORFullDB/unknown_field=foo'
    result = adapter.parse_metadata(info)
    assert 'unknown_field' not in result
