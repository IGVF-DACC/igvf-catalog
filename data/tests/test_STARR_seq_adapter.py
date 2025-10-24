import json
import pytest
from adapters.STARR_seq_adapter import STARRseqVariantBiosample
from adapters.writer import SpyWriter
from unittest.mock import patch
from unittest.mock import patch, mock_open

mock_tsv_data = ' \nchr1\t13833\t13834\tNC_000001.11:13833:C:T\t350\t+\t0.1053361347394244\t1.1178449514319324\t1.0921171037854174\t0\t0.2149853195124717\t \t \t0.35\t0.620196\t4.98262\t-1\tC\tT\n'


@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_igvf', return_value=(
    {
        'simple_sample_summaries': ['sample summary'],
        'samples': ['sample'],
        'treatments_term_ids': None,
        'method': 'STARR-seq'
    }, None, None
))
@patch('adapters.STARR_seq_adapter.bulk_check_variants_in_arangodb', return_value=set())
@patch('adapters.STARR_seq_adapter.load_variant', return_value=({
    '_key': 'NC_000001.11:13833:C:T',
    'name': 'NC_000001.11:13833:C:T',
    'chr': 'chr1',
    'pos': 13833,
    'ref': 'C',
    'alt': 'T',
    'variation_type': 'SNP',
    'spdi': 'NC_000001.11:13833:C:T',
    'hgvs': 'NC_000001.11:g.13834C>T',
    'organism': 'Homo sapiens',
    'rsid': [],
    'qual': '100',
    'filter': 'PASS',
    'annotations': {},
    'format': 'VCF',
    'vrs_digest': 'test_digest',
    'ca_id': 'CA1234567890'
}, None))
@patch('adapters.STARR_seq_adapter.SeqRepo', autospec=True)
@patch('adapters.STARR_seq_adapter.AlleleTranslator', autospec=True)
def test_process_file_variant(mock_translator, mock_seqrepo, mock_load_variant, mock_bulk_check, mock_query_props, mocker
                              ):
    writer = SpyWriter()

    adapter = STARRseqVariantBiosample(filepath='./samples/starr_seq.example.tsv', writer=writer,
                                       label='variant', source_url='https://data.igvf.org/tabular-files/IGVFFI7664HHXI/', validate=True)

    # 使用更精确的模拟，只影响数据文件的打开
    with patch('builtins.open', mock_open(read_data=mock_tsv_data)) as mock_file_open:
        adapter.process_file()

    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_key'] == 'NC_000001.11:13833:C:T'
    assert first_item['spdi'] == 'NC_000001.11:13833:C:T'
    assert first_item['hgvs'] == 'NC_000001.11:g.13834C>T'
    assert first_item['source'] == 'IGVF'
    assert first_item['source_url'] == 'https://data.igvf.org/tabular-files/IGVFFI7664HHXI/'
    assert first_item['files_filesets'] == 'files_filesets/IGVFFI7664HHXI'


@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_igvf', return_value=(
    {
        'simple_sample_summaries': ['K562'],
        'samples': ['ontology_terms/EFO_0002067'],
        'treatments_term_ids': None,
        'method': 'STARR-seq'
    }, None, None
))
@patch('adapters.STARR_seq_adapter.bulk_check_variants_in_arangodb', return_value={'NC_000001.11:13833:C:T'})
@patch(
    'adapters.STARR_seq_adapter.load_variant',
    return_value=({
        '_key': 'NC_000001.11:13833:C:T',
        'name': 'NC_000001.11:13833:C:T',
        'chr': 'chr1',
        'pos': 13833,
        'ref': 'C',
        'alt': 'T',
        'variation_type': 'SNP',
        'spdi': 'NC_000001.11:13833:C:T',
        'hgvs': 'NC_000001.11:g.13834C>T',
        'organism': 'Homo sapiens',
        'rsid': [],
        'qual': '100',
        'filter': 'PASS',
        'annotations': {},
        'format': 'VCF',
        'vrs_digest': 'test_digest',
        'ca_id': 'CA1234567890'
    }, None)
)
@patch('adapters.STARR_seq_adapter.SeqRepo', autospec=True)
@patch('adapters.STARR_seq_adapter.AlleleTranslator', autospec=True)
def test_process_file_variant_biosample(mock_query_props, mock_bulk_check, mock_load_variant, mock_translator, mock_seqrepo, mocker):
    writer = SpyWriter()

    adapter = STARRseqVariantBiosample(
        filepath='./samples/starr_seq.example.tsv', writer=writer, label='variant_biosample', source_url='https://data.igvf.org/tabular-files/IGVFFI7664HHXI/', validate=True)

    # 使用更精确的模拟，只影响数据文件的打开
    with patch('builtins.open', mock_open(read_data=mock_tsv_data)) as mock_file_open:
        adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item['_key'] == 'NC_000001.11:13833:C:T_EFO_0002067_IGVFFI7664HHXI'
    assert first_item['_from'] == 'variants/NC_000001.11:13833:C:T'
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
    assert first_item['source_url'] == 'https://data.igvf.org/tabular-files/IGVFFI7664HHXI/'
    assert first_item['files_filesets'] == 'files_filesets/IGVFFI7664HHXI'
    assert first_item['simple_sample_summaries'] == ['K562']
    assert first_item['biological_context'] == 'ontology_terms/EFO_0002067'
    assert first_item['treatments_term_ids'] == None


def test_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_label. Allowed values: variant, variant_biosample'):
        STARRseqVariantBiosample(
            filepath='./samples/starr_seq.example.tsv',
            label='invalid_label',
            source_url='https://data.igvf.org/tabular-files/IGVFFI7664HHXI/',
            writer=writer,
            validate=True
        )


@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_igvf', return_value=(
    {
        'simple_sample_summaries': ['sample summary'],
        'samples': ['sample'],
        'treatments_term_ids': None,
        'method': 'STARR-seq'
    }, None, None
))
@patch('adapters.STARR_seq_adapter.SeqRepo', autospec=True)
@patch('adapters.STARR_seq_adapter.AlleleTranslator', autospec=True)
def test_validate_doc_invalid(mock_translator, mock_seqrepo, mock_query_props):
    writer = SpyWriter()
    adapter = STARRseqVariantBiosample(
        filepath='./samples/starr_seq.example.tsv',
        label='variant',
        source_url='https://data.igvf.org/tabular-files/IGVFFI7664HHXI/',
        writer=writer,
        validate=True
    )
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
