import json
import pytest
from adapters.STARR_seq_adapter import STARRseqVariantOntologyTerm
from adapters.writer import SpyWriter
from unittest.mock import patch
from unittest.mock import patch, mock_open


@patch('adapters.STARR_seq_adapter.get_ref_seq_by_spdi', return_value='T')
@patch('adapters.STARR_seq_adapter.bulk_check_spdis_in_arangodb', return_value=set())
@patch('gzip.open', new_callable=mock_open, read_data=' \nchr1\t13833\t13834\tNC_000001.11:13833:C:T\t350\t+\t0.1053361347394244\t1.1178449514319324\t1.0921171037854174\t0\t0.2149853195124717\t \t \t0.35\t0.620196\t4.98262\t-1\tC\tT\n')
def test_process_file_variant(mock_file, mock_bulk_check, mock_validate, mocker):
    mocker.patch('adapters.STARR_seq_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    adapter = STARRseqVariantOntologyTerm(filepath='./samples/starr_seq.example.tsv.gz', writer=writer,
                                          label='variant', source_url='https://api.data.igvf.org/tabular-files/IGVFFI7664HHXI/')
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert 1 == 2
    print(first_item)


@patch('adapters.STARR_seq_adapter.get_ref_seq_by_spdi', return_value='T')
@patch('adapters.STARR_seq_adapter.bulk_check_spdis_in_arangodb', return_value={'NC_000001.11:13833:C:T'})
@patch('gzip.open', new_callable=mock_open, read_data=' \nchr1\t13833\t13834\tNC_000001.11:13833:C:T\t350\t+\t0.1053361347394244\t1.1178449514319324\t1.0921171037854174\t0\t0.2149853195124717\t \t \t0.35\t0.620196\t4.98262\t-1\tC\tT\n')
def test_process_file_variant_ontology_term(mock_file, mock_bulk_check, mock_validate, mocker):
    mocker.patch('adapters.STARR_seq_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    adapter = STARRseqVariantOntologyTerm(
        filepath='./samples/starr_seq.example.tsv.gz', writer=writer, label='variant_ontology_term', source_url='https://api.data.igvf.org/tabular-files/IGVFFI7664HHXI/')
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert 1 == 2
    print(first_item)


def test_invalid_label_raises_error():
    with pytest.raises(ValueError, match='Invalid label. Allowed values: variant,variant_ontology_term'):
        STARRseqVariantOntologyTerm(
            filepath='./samples/starr_seq.example.tsv.gz', label='invalid_label', source_url='https://api.data.igvf.org/tabular-files/IGVFFI7664HHXI/')


@patch('adapters.STARR_seq_adapter.get_ref_seq_by_spdi', return_value='T')
@patch('adapters.STARR_seq_adapter.bulk_check_spdis_in_arangodb', return_value=set())
@patch('gzip.open', new_callable=mock_open, read_data=' \nchr1\t13833\t13834\tNC_000001.11:13833:C:T\t350\t+\t0.1053361347394244\t1.1178449514319324\t1.0921171037854174\t0\t0.2149853195124717\t \t \t0.35\t0.620196\t4.98262\t-1\tC\tT\n')
def test_process_file_handles_empty_chunk(mock_file, mock_bulk_check, mock_validate, mocker):
    mocker.patch('adapters.STARR_seq_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    adapter = STARRseqVariantOntologyTerm(
        filepath='./samples/starr_seq.example.tsv.gz', writer=writer, label='variant', source_url='https://api.data.igvf.org/tabular-files/IGVFFI7664HHXI/')
    adapter.process_file()
    # Ensure no errors occur with a single chunk
    assert len(writer.contents) > 0


@patch('adapters.STARR_seq_adapter.get_ref_seq_by_spdi', return_value='T')
@patch('adapters.STARR_seq_adapter.bulk_check_spdis_in_arangodb', return_value={'NC_000001.11:13833:C:T'})
@patch('gzip.open', new_callable=mock_open, read_data=' \nchr1\t13833\t13834\tNC_000001.11:13833:C:T\t350\t+\t0.1053361347394244\t1.1178449514319324\t1.0921171037854174\t0\t0.2149853195124717\t \t \t0.35\t0.620196\t4.98262\t-1\tC\tT\n')
def test_process_file_skips_loaded_variants(mock_file, mock_bulk_check, mock_validate):
    writer = SpyWriter()
    adapter = STARRseqVariantOntologyTerm(
        filepath='./samples/starr_seq.example.tsv.gz', writer=writer, label='variant', source_url='https://api.data.igvf.org/tabular-files/IGVFFI7664HHXI/')
    adapter.process_file()
    # No unloaded variants should be processed
    assert len(writer.contents) == 0
