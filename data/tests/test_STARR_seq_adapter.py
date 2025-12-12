import json
import pytest
from adapters.STARR_seq_adapter import STARRseqVariantBiosample
from adapters.writer import SpyWriter
from unittest.mock import patch, mock_open

mock_tsv_data = ' \nchr1\t13833\t13834\tNC_000001.11:13833:C:T\t350\t+\t0.1053361347394244\t1.1178449514319324\t1.0921171037854174\t0\t0.2149853195124717\t \t \t0.35\t0.620196\t4.98262\t-1\tC\tT\n'


# mock get_file_fileset_by_accession_in_arangodb so files_fileset data change will not affect the test
@pytest.fixture
def mock_file_fileset():
    """Fixture to mock get_file_fileset_by_accession_in_arangodb function."""
    with patch('adapters.STARR_seq_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'simple_sample_summaries': ['K562'],
            'samples': ['ontology_terms/EFO_0002067'],
            'treatments_term_ids': None,
            'method': 'STARR-seq',
            'class': 'observed data'
        }
        yield mock_get_file_fileset


# mock load_variant to avoid repeated setup
@pytest.fixture
def mock_load_variant():
    """Fixture to mock load_variant function."""
    with patch('adapters.STARR_seq_adapter.load_variant') as mock_load:
        mock_load.return_value = ({
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
            'vrs_digest': 'test_digest',
            'ca_id': 'CA1234567890'
        }, None)
        yield mock_load


# mock SeqRepo and AlleleTranslator to avoid repeated setup
@pytest.fixture
def mock_seqrepo_and_translator():
    """Fixture to mock SeqRepo and AlleleTranslator."""
    with patch('adapters.STARR_seq_adapter.SeqRepo', autospec=True), \
            patch('adapters.STARR_seq_adapter.AlleleTranslator', autospec=True):
        yield


@patch('adapters.STARR_seq_adapter.bulk_check_variants_in_arangodb', return_value=set())
def test_process_file_variant(mock_bulk_check, mock_file_fileset, mock_load_variant, mock_seqrepo_and_translator, mocker):
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


@patch('adapters.STARR_seq_adapter.bulk_check_variants_in_arangodb', return_value={'NC_000001.11:13833:C:T'})
def test_process_file_variant_biosample(mock_bulk_check, mock_file_fileset, mock_load_variant, mock_seqrepo_and_translator, mocker):

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
    assert first_item['label'] == 'variant effect on regulatory element activity'
    assert first_item['method'] == 'STARR-seq'
    assert first_item['class'] == 'observed data'
    assert first_item['source'] == 'IGVF'
    assert first_item['source_url'] == 'https://data.igvf.org/tabular-files/IGVFFI7664HHXI/'
    assert first_item['files_filesets'] == 'files_filesets/IGVFFI7664HHXI'
    assert first_item['biological_context'] == 'K562'
    assert first_item['biosample_term'] == 'ontology_terms/EFO_0002067'
    assert first_item['treatments_term_ids'] == None


def test_invalid_label(mock_file_fileset, mock_load_variant, mock_seqrepo_and_translator):
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_label. Allowed values: variant, variant_biosample'):
        STARRseqVariantBiosample(
            filepath='./samples/starr_seq.example.tsv',
            label='invalid_label',
            source_url='https://data.igvf.org/tabular-files/IGVFFI7664HHXI/',
            writer=writer,
            validate=True
        )


def test_validate_doc_invalid(mock_file_fileset, mock_load_variant, mock_seqrepo_and_translator):
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
