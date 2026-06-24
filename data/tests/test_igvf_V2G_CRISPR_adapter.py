import json
import math
import pytest
from adapters.igvf_V2G_CRISPR_adapter import IGVFV2GCRISPR
from adapters.writer import SpyWriter
from unittest.mock import patch, mock_open, MagicMock

SOURCE_URL = 'https://data.igvf.org/tabular-files/IGVFFI9602ILPC/'


@pytest.mark.parametrize('effect_size, log2_fold_change', [
    (-0.718599966, -1.8293055920000934),
    (-0.592074958, -1.2936240198229567),
    (-0.940403039, -4.0686174238861454),
])
def test_fractional_effect_size_to_log2_fold_change(effect_size, log2_fold_change):
    assert IGVFV2GCRISPR._fractional_effect_size_to_log2_fold_change(
        effect_size) == pytest.approx(log2_fold_change)


@pytest.fixture
def mock_file_fileset():
    """Fixture to mock get_file_fileset_by_accession_in_arangodb function."""
    with patch('adapters.igvf_V2G_CRISPR_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'method': 'Variant-EFFECTS',
            'simple_sample_summaries': ['donor:human'],
            'samples': ['ontology_terms/EFO_0001253'],
            'treatments_term_ids': [],
            'crispr_modality': 'prime editing'
        }
        yield mock_get_file_fileset


mock_tsv_data = (
    'variant\tchr\tpos\tref\talt\teffect_allele\tother_allele\tgene\tgene_symbol\t'
    'effect_size\tlog2_fold_change\tp_nominal_nlog10\tfdr_nlog10\tfdr_method\tpower\tVariantID_h19\n'
    'NC_000010.11:79347444::CCTCCTCAGG\tchr10\t79347444\t\tCCTCCTCAGG\tCCTCCTCAGG\t\t'
    'ENSG00000108179\tPPIF\t-0.022\t-0.032\t1.86\t1.77\tBenjamini-Hochberg\t0.05\tchr10:81107199:A>ACCTCCTCAGG\n'
)


@patch('adapters.igvf_V2G_CRISPR_adapter.GeneValidator', return_value=MagicMock(validate=MagicMock(return_value=True)))
@patch('adapters.igvf_V2G_CRISPR_adapter.bulk_check_variants_in_arangodb', return_value=set())
@patch(
    'adapters.igvf_V2G_CRISPR_adapter.load_variant',
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
        'annotations': {},
        'vrs_digest': 'test_digest',
        'ca_id': 'CA1234567890'
    }, None)
)
def test_process_file_variant(mock_load_variant, mock_bulk_check, mock_gene_validator, mock_file_fileset, mocker):
    writer = SpyWriter()
    adapter = IGVFV2GCRISPR(
        filepath='./samples/igvf_v2g_crispr.example.tsv',
        source_url=SOURCE_URL,
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


@patch('adapters.igvf_V2G_CRISPR_adapter.GeneValidator', return_value=MagicMock(validate=MagicMock(return_value=True)))
@patch('adapters.igvf_V2G_CRISPR_adapter.bulk_check_variants_in_arangodb', return_value={'NC_000010.11:79347444::CCTCCTCAGG'})
@patch(
    'adapters.igvf_V2G_CRISPR_adapter.load_variant',
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
        'annotations': {},
        'vrs_digest': 'test_digest',
        'ca_id': 'CA1234567890'
    }, None)
)
def test_process_file_variant_gene(mock_load_variant, mock_bulk_check, mock_gene_validator, mock_file_fileset, mocker):
    writer = SpyWriter()
    adapter = IGVFV2GCRISPR(
        filepath='./samples/igvf_v2g_crispr.example.tsv',
        source_url=SOURCE_URL,
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
    assert first_item['crispr_modality'] == 'prime editing'
    assert first_item['class'] == 'observed data'
    assert first_item['biological_context'] == 'donor:human'
    assert first_item['biosample_term'] == 'ontology_terms/EFO_0001253'
    assert first_item['neg_log10_pvalue'] == 1.86


def test_invalid_label(mock_file_fileset):
    with pytest.raises(ValueError, match='Invalid label: invalid. Allowed values: variant, variant_gene'):
        IGVFV2GCRISPR(
            filepath='./samples/igvf_v2g_crispr.example.tsv',
            source_url=SOURCE_URL,
            writer=SpyWriter(),
            label='invalid'
        )


MILLIPEDE_SOURCE_URL = 'https://data.igvf.org/tabular-files/IGVFFI8101RHSC/'
mock_millipede_data = (
    'variants,PIP,Betas,Coefficient StdDev\n'
    'NC_000016.10:28930710:G:A,0.0284163262526425,-0.0116633875205405,0.0699744682130392\n'
    'intercept_exp0_rep0,,0.00290135882130573,0.0273268245689704\n'
    'intercept_exp0_rep1,,-0.00718843152560525,0.0273936838403644\n'
    'intercept_exp0_rep2,,0.00561260332647456,0.0286117416190804\n'
    'Intercept,,0.182835156419124,2.26084488707795\n'
)


@pytest.fixture
def mock_millipede_file_fileset():
    with patch('adapters.igvf_V2G_CRISPR_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'method': 'CRISPR screen',
            'simple_sample_summaries': ['human NALM-6 cell line'],
            'samples': ['ontology_terms/CLO_0007938'],
            'treatments_term_ids': None,
            'crispr_modality': 'base editing'
        }
        yield mock_get_file_fileset


@patch('adapters.igvf_V2G_CRISPR_adapter.GeneValidator', return_value=MagicMock(validate=MagicMock(return_value=True)))
@patch('adapters.igvf_V2G_CRISPR_adapter.bulk_check_variants_in_arangodb', return_value={'NC_000016.10:28930710:G:A'})
@patch(
    'adapters.igvf_V2G_CRISPR_adapter.load_variant',
    return_value=({
        '_key': 'NC_000016.10:28930710:G:A',
        'name': 'NC_000016.10:28930710:G:A',
        'chr': 'chr16',
        'pos': 28930710,
        'ref': 'G',
        'alt': 'A',
        'variation_type': 'SNV',
        'spdi': 'NC_000016.10:28930710:G:A',
        'hgvs': 'NC_000016.10:g.28930710G>A',
        'organism': 'Homo sapiens',
        'rsid': [],
        'qual': '100',
        'annotations': {},
        'vrs_digest': 'test_digest',
        'ca_id': 'CA1234567890'
    }, None)
)
def test_millipede_file_uses_hardcoded_cd19_gene(
    mock_load_variant, mock_bulk_check, mock_gene_validator, mock_millipede_file_fileset, caplog
):
    writer = SpyWriter()
    adapter = IGVFV2GCRISPR(
        filepath='./samples/igvf_v2g_crispr_millipede.example.csv',
        source_url=MILLIPEDE_SOURCE_URL,
        writer=writer,
        label='variant_gene',
        validate=True
    )

    with patch('builtins.open', mock_open(read_data=mock_millipede_data)):
        with caplog.at_level('INFO'):
            adapter.process_file()

    assert (
        'Skipping 4 Millipede intercept model term row(s) in IGVFFI8101RHSC '
        '(not variants): intercept_exp0_rep0, intercept_exp0_rep1, '
        'intercept_exp0_rep2, Intercept'
    ) in caplog.text
    assert mock_load_variant.call_count == 1
    assert len(writer.contents) == 1
    first_item = json.loads(writer.contents[0])
    assert first_item['_to'] == 'genes/ENSG00000177455'
    assert first_item['_key'] == 'NC_000016.10:28930710:G:A_ENSG00000177455_IGVFFI8101RHSC'
    assert first_item['effect_size'] == -0.0116633875205405
    assert first_item['power'] == 0.0284163262526425
    assert first_item['log2_fold_change'] == pytest.approx(
        math.log2(1 + first_item['effect_size']))
    assert first_item['neg_log10_pvalue'] is None
    assert first_item['neg_log10_pvalue_adj'] is None
    assert first_item['method'] == 'CRISPR screen'
    assert first_item['crispr_modality'] == 'base editing'
