import json
import pytest
from adapters.STARR_seq_adapter import STARRseqVariantOntologyTerm
from adapters.writer import SpyWriter
from unittest.mock import patch
from unittest.mock import patch, mock_open


@patch('adapters.STARR_seq_adapter.get_ref_seq_by_spdi', return_value='C')
@patch('adapters.STARR_seq_adapter.bulk_check_spdis_in_arangodb', return_value=set())
@patch('builtins.open', new_callable=mock_open, read_data=' \nchr1\t13833\t13834\tNC_000001.11:13833:C:T\t350\t+\t0.1053361347394244\t1.1178449514319324\t1.0921171037854174\t0\t0.2149853195124717\t \t \t0.35\t0.620196\t4.98262\t-1\tC\tT\n')
def test_process_file_variant(mock_file, mock_bulk_check, mock_validate, mocker):
    mocker.patch('adapters.STARR_seq_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    adapter = STARRseqVariantOntologyTerm(filepath='./samples/starr_seq.example.tsv', writer=writer,
                                          label='variant', source_url='https://api.data.igvf.org/tabular-files/IGVFFI7664HHXI/')
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_key'] == 'fake_variant_id'
    assert first_item['name'] == 'NC_000001.11:13833:C:T'
    assert first_item['chr'] == 'chr1'
    assert first_item['pos'] == 13833
    assert first_item['ref'] == 'C'
    assert first_item['alt'] == 'T'
    assert first_item['variation_type'] == 'SNP'
    assert first_item['spdi'] == 'NC_000001.11:13833:C:T'
    assert first_item['hgvs'] == 'NC_000001.11:g.13834C>T'
    assert first_item['organism'] == 'Homo sapiens'
    assert first_item['source'] == 'IGVF'
    assert first_item['source_url'] == 'https://api.data.igvf.org/tabular-files/IGVFFI7664HHXI/'
    assert first_item['files_filesets'] == 'files_filesets/IGVFFI7664HHXI'


@patch('adapters.STARR_seq_adapter.get_ref_seq_by_spdi', return_value='C')
@patch('adapters.STARR_seq_adapter.bulk_check_spdis_in_arangodb', return_value={'NC_000001.11:13833:C:T'})
@patch('builtins.open', new_callable=mock_open, read_data=' \nchr1\t13833\t13834\tNC_000001.11:13833:C:T\t350\t+\t0.1053361347394244\t1.1178449514319324\t1.0921171037854174\t0\t0.2149853195124717\t \t \t0.35\t0.620196\t4.98262\t-1\tC\tT\n')
def test_process_file_variant_ontology_term(mock_file, mock_bulk_check, mock_validate, mocker):
    mocker.patch('adapters.STARR_seq_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    adapter = STARRseqVariantOntologyTerm(
        filepath='./samples/starr_seq.example.tsv', writer=writer, label='variant_ontology_term', source_url='https://api.data.igvf.org/tabular-files/IGVFFI7664HHXI/')
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item['_key'] == 'fake_variant_id_EFO_0002067_IGVFFI7664HHXI'
    assert first_item['_from'] == 'variants/fake_variant_id'
    assert first_item['_to'] == 'ontology_terms/EFO_0002067'
    assert first_item['name'] == 'modulates expression in'
    assert first_item['inverse_name'] == 'regulatory activity modulated by'
    assert first_item['log2FoldChange'] == 0.1053361347394244
    assert first_item['inputCountRef'] == 1.1178449514319324
    assert first_item['outputCountRef'] == 1.0921171037854174
    assert first_item['inputCountAlt'] == 0.0
    assert first_item['outputCountAlt'] == 0.2149853195124717
    assert first_item['postProbEffect'] == 0.35
    assert first_item['CI_lower_95'] == 0.620196
    assert first_item['CI_upper_95'] == 4.98262
    assert first_item['label'] == 'variant effect on gene expression'
    assert first_item['method'] == 'STARR-seq'
    assert first_item['source'] == 'IGVF'
    assert first_item['source_url'] == 'https://api.data.igvf.org/tabular-files/IGVFFI7664HHXI/'
    assert first_item['files_filesets'] == 'files_filesets/IGVFFI7664HHXI'
    assert first_item['simple_sample_summaries'] == ['K562']
    assert first_item['biological_context'] == ['ontology_terms/EFO_0002067']
    assert first_item['treatments_term_ids'] == None


def test_invalid_label_raises_error():
    with pytest.raises(ValueError, match='Invalid label. Allowed values: variant,variant_ontology_term'):
        STARRseqVariantOntologyTerm(
            filepath='./samples/starr_seq.example.tsv', label='invalid_label', source_url='https://api.data.igvf.org/tabular-files/IGVFFI7664HHXI/')


@patch('adapters.STARR_seq_adapter.get_ref_seq_by_spdi', return_value='C')
@patch('adapters.STARR_seq_adapter.bulk_check_spdis_in_arangodb', return_value=set())
@patch('builtins.open', new_callable=mock_open, read_data=' \nchr1\t13833\t13834\tNC_000001.11:13833:C:T\t350\t+\t0.1053361347394244\t1.1178449514319324\t1.0921171037854174\t0\t0.2149853195124717\t \t \t0.35\t0.620196\t4.98262\t-1\tC\tT\n')
def test_process_file_handles_empty_chunk(mock_file, mock_bulk_check, mock_validate, mocker):
    mocker.patch('adapters.STARR_seq_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    adapter = STARRseqVariantOntologyTerm(
        filepath='./samples/starr_seq.example.tsv', writer=writer, label='variant', source_url='https://api.data.igvf.org/tabular-files/IGVFFI7664HHXI/')
    adapter.process_file()
    # Ensure no errors occur with a single chunk
    assert len(writer.contents) > 0


@patch('adapters.STARR_seq_adapter.get_ref_seq_by_spdi', return_value='C')
@patch('adapters.STARR_seq_adapter.bulk_check_spdis_in_arangodb', return_value={'NC_000001.11:13833:C:T'})
@patch('builtins.open', new_callable=mock_open, read_data=' \nchr1\t13833\t13834\tNC_000001.11:13833:C:T\t350\t+\t0.1053361347394244\t1.1178449514319324\t1.0921171037854174\t0\t0.2149853195124717\t \t \t0.35\t0.620196\t4.98262\t-1\tC\tT\n')
def test_process_file_skips_loaded_variants(mock_file, mock_bulk_check, mock_validate):
    writer = SpyWriter()
    adapter = STARRseqVariantOntologyTerm(
        filepath='./samples/starr_seq.example.tsv', writer=writer, label='variant', source_url='https://api.data.igvf.org/tabular-files/IGVFFI7664HHXI/')
    adapter.process_file()
    # No unloaded variants should be processed
    assert len(writer.contents) == 0
