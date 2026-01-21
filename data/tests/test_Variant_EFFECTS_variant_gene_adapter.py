import json
import pytest
from adapters.Variant_EFFECTS_variant_gene_adapter import VariantEFFECTSAdapter
from adapters.writer import SpyWriter
from unittest.mock import patch, mock_open, MagicMock

# mock get_file_fileset_by_accession_in_arangodb so files_fileset data change will not affect the test


@pytest.fixture
def mock_file_fileset():
    """Fixture to mock get_file_fileset_by_accession_in_arangodb function."""
    with patch('adapters.Variant_EFFECTS_variant_gene_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'simple_sample_summaries': ['donor:human'],
            'samples': ['ontology_terms/EFO_0001253'],
            'treatments_term_ids': []
        }
        yield mock_get_file_fileset


mock_tsv_data = (
    'variant\tchr\tpos\tref\talt\teffect_allele\tother_allele\tgene\tgene_symbol\t'
    'effect_size\tlog2_fold_change\tp_nominal_nlog10\tfdr_nlog10\tfdr_method\tpower\tVariantID_h19\n'
    'NC_000010.11:79347444::CCTCCTCAGG\tchr10\t79347444\t\tCCTCCTCAGG\tCCTCCTCAGG\t\t'
    'ENSG00000108179\tPPIF\t-0.022\t-0.032\t1.86\t1.77\tBenjamini-Hochberg\t0.05\tchr10:81107199:A>ACCTCCTCAGG\n'
)


@patch('adapters.Variant_EFFECTS_variant_gene_adapter.GeneValidator', return_value=MagicMock(validate=MagicMock(return_value=True)))
@patch('adapters.Variant_EFFECTS_variant_gene_adapter.bulk_check_variants_in_arangodb', return_value=set())
@patch(
    'adapters.Variant_EFFECTS_variant_gene_adapter.load_variant',
    return_value=({
        '_key': 'NC_000010.11:79347444::CCTCCTCAGG',
        'name': 'NC_000010.11:79347444::CCTCCTCAGG',
        'chr': 'chr10',
        'pos': 79347444,
        'ref': '',
        'alt': 'CCTCCTCAGG',
        'variation_type': 'insertion',
        'spdi': 'NC_000010.11:79347444::CCTCCTCAGG',
        'hgvs': 'NC_000010.11:g.79347445dupCCTCCTCAGG',
        'organism': 'Homo sapiens',
        'rsid': [],
        'qual': '100',
        'filter': 'PASS',
        'annotations': {},
        'vrs_digest': 'test_digest',
        'ca_id': 'CA1234567890'
    }, None)
)
def test_process_file_variant(mock_load_variant, mock_bulk_check, mock_gene_validator, mock_file_fileset, mocker):
    writer = SpyWriter()
    adapter = VariantEFFECTSAdapter(
        filepath='./samples/variant_effects_variant_gene.example.tsv',
        writer=writer,
        label='variant',
        validate=True
    )

    with patch('builtins.open', mock_open(read_data=mock_tsv_data)) as mock_file_open:
        adapter.process_file()

    assert len(writer.contents) > 0
    first_item = json.loads(writer.contents[0])
    assert '_key' in first_item
    assert 'spdi' in first_item
    assert 'hgvs' in first_item
    assert 'variation_type' in first_item
    assert first_item['source_url'] == adapter.source_url

    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError):
        adapter.validate_doc(invalid_doc)


@patch('adapters.Variant_EFFECTS_variant_gene_adapter.GeneValidator', return_value=MagicMock(validate=MagicMock(return_value=True)))
@patch('adapters.Variant_EFFECTS_variant_gene_adapter.bulk_check_variants_in_arangodb', return_value={'NC_000010.11:79347444::CCTCCTCAGG'})
@patch(
    'adapters.Variant_EFFECTS_variant_gene_adapter.load_variant',
    return_value=({
        '_key': 'NC_000010.11:79347444::CCTCCTCAGG',
        'name': 'NC_000010.11:79347444::CCTCCTCAGG',
        'chr': 'chr10',
        'pos': 79347444,
        'ref': '',
        'alt': 'CCTCCTCAGG',
        'variation_type': 'insertion',
        'spdi': 'NC_000010.11:79347444::CCTCCTCAGG',
        'hgvs': 'NC_000010.11:g.79347445dupCCTCCTCAGG',
        'organism': 'Homo sapiens',
        'rsid': [],
        'qual': '100',
        'filter': 'PASS',
        'annotations': {},
        'vrs_digest': 'test_digest',
        'ca_id': 'CA1234567890'
    }, None)
)
def test_process_file_variant_gene(mock_load_variant, mock_bulk_check, mock_gene_validator, mock_file_fileset, mocker):
    writer = SpyWriter()
    adapter = VariantEFFECTSAdapter(
        filepath='./samples/variant_effects_variant_gene.example.tsv',
        writer=writer,
        label='variant_gene',
        validate=True
    )

    with patch('builtins.open', mock_open(read_data=mock_tsv_data)) as mock_file_open:
        adapter.process_file()

    assert len(writer.contents) > 0
    first_item = json.loads(writer.contents[0])
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert 'log2_fold_change' in first_item
    assert 'label' in first_item
    assert first_item['label'] == 'variant effect on gene expression'
    assert first_item['source_url'] == adapter.source_url
    assert first_item['method'] == 'Variant-EFFECTS'
    assert first_item['class'] == 'observed data'
    assert first_item['biological_context'] == 'donor:human'
    assert first_item['biosample_term'] == 'ontology_terms/EFO_0001253'


def test_invalid_label(mock_file_fileset):
    with pytest.raises(ValueError, match='Invalid label: invalid. Allowed values: variant, variant_gene'):
        VariantEFFECTSAdapter(
            filepath='./samples/variant_effects_variant_gene.example.tsv',
            writer=SpyWriter(),
            label='invalid'
        )
