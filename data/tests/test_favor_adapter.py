import pytest
import json
from unittest.mock import MagicMock, patch, mock_open
from adapters.writer import SpyWriter

from adapters.favor_adapter import Favor


@pytest.fixture
def mock_writer():
    return MagicMock()


@patch('adapters.favor_adapter.build_spdi', return_value='21:5025532:G:C')
@patch('adapters.favor_adapter.build_hgvs_from_spdi', return_value='chr21:g.5025533G>C')
@patch('adapters.favor_adapter.SeqRepo')
@patch('adapters.favor_adapter.create_dataproxy')
@patch('adapters.favor_adapter.AlleleTranslator')
def test_process_file_writes_json(
    mock_translator_cls,
    mock_create_dp,
    mock_seqrepo,
    mock_build_hgvs,
    mock_build_spdi,
    mock_writer,
):
    # Setup mocks for translator and allele
    mock_translator = MagicMock()
    mock_allele = MagicMock()
    mock_allele.digest = 'digest123'
    mock_translator.translate_from.return_value = mock_allele
    mock_translator_cls.return_value = mock_translator

    # Mock container
    mock_container = MagicMock()
    mock_container.contains.return_value = False

    # Mock ca_ids
    mock_ca_ids = MagicMock()
    mock_ca_ids.get.return_value = b'CA123'

    # Patch get_container and Rdict
    with patch('adapters.favor_adapter.get_container', return_value=mock_container), \
            patch('adapters.favor_adapter.Rdict', return_value=mock_ca_ids), \
            patch('builtins.open', mock_open(read_data='#CHROM\tPOS\tID\tREF\tALT\tQUAL\tNA\tINFO\tGT\n21\t5025532\trs1\tG\tC\t.\tNA\tFREQ=Korea1K:0.9545,0.04545;FAVORFullDB/variant_annovar=21-5025532-5025532-G-C;FAVORFullDB/cadd_phred=2.753\t0/1\n')):
        favor = Favor(filepath='dummy.vcf',
                      ca_ids_path='dummy.rdict', writer=mock_writer)
        favor.process_file()

    # Writer should be opened, written to, and closed
    assert mock_writer.open.called
    assert mock_writer.write.call_count > 0
    assert mock_writer.close.called

    # Check that the output JSON contains expected keys
    written_json = None
    for call in mock_writer.write.call_args_list:
        arg = call[0][0]
        if arg.strip().startswith('{'):
            written_json = json.loads(arg)
            break
    assert written_json is not None
    assert written_json['chr'] == 'chr21'
    assert written_json['ref'] == 'G'
    assert written_json['alt'] == 'C'
    assert written_json['spdi'] == '21:5025532:G:C'
    assert written_json['vrs_digest'] == 'digest123'
    assert written_json['ca_id'] == 'CA123'
    assert written_json['source'] == 'FAVOR'


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
