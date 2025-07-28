import json
import pytest
from adapters.Variant_EFFECTS_variant_gene_adapter import VariantEFFECTSAdapter
from adapters.writer import SpyWriter
from unittest.mock import patch, mock_open, MagicMock

mock_tsv_data = (
    'variant\tchr\tpos\tref\talt\teffect_allele\tother_allele\tgene\tgene_symbol\t'
    'effect_size\tlog2_fold_change\tp_nominal_nlog10\tfdr_nlog10\tfdr_method\tpower\tVariantID_h19\n'
    'NC_000010.11:79347444::CCTCCTCAGG\tchr10\t79347444\t\tCCTCCTCAGG\tCCTCCTCAGG\t\t'
    'ENSG00000108179\tPPIF\t-0.022\t-0.032\t1.86\t1.77\tBenjamini-Hochberg\t0.05\tchr10:81107199:A>ACCTCCTCAGG\n'
)


@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_igvf', return_value=(
    {
        'simple_sample_summaries': ['donor:human'],
        'samples': 'sample',
        'treatments_term_ids': [],
        'method': 'CRISPR'
    }, None, None
))
@patch('adapters.Variant_EFFECTS_variant_gene_adapter.GeneValidator', return_value=MagicMock(validate=MagicMock(return_value=True)))
@patch('adapters.Variant_EFFECTS_variant_gene_adapter.bulk_check_variants_in_arangodb', return_value=set())
@patch('builtins.open', new_callable=mock_open, read_data=mock_tsv_data)
@patch(
    'adapters.Variant_EFFECTS_variant_gene_adapter.load_variant',
    return_value=({
        '_key': 'NC_000010.11:79347444::CCTCCTCAGG',
        'spdi': 'NC_000010.11:79347444::CCTCCTCAGG',
        'hgvs': 'NC_000010.11:g.79347445dupCCTCCTCAGG',
        'variation_type': 'insertion',
    }, None)
)
def test_process_file_variant(mock_query_props, mock_gene_validator, mock_bulk_check, mock_file, mock_load_variant, mocker):
    writer = SpyWriter()
    adapter = VariantEFFECTSAdapter(
        filepath='./samples/variant_effects_variant_gene.example.tsv',
        writer=writer,
        label='variant',
        source_url='https://api.data.igvf.org/files/IGVFFI9602ILPC/'
    )
    adapter.process_file()
    assert len(writer.contents) > 0
    first_item = json.loads(writer.contents[0])
    assert '_key' in first_item
    assert 'spdi' in first_item
    assert 'hgvs' in first_item
    assert 'variation_type' in first_item
    assert first_item['source_url'] == adapter.source_url


@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_igvf', return_value=(
    {
        'simple_sample_summaries': ['donor:human'],
        'samples': 'sample',
        'treatments_term_ids': [],
        'method': 'CRISPR'
    }, None, None
))
@patch('adapters.Variant_EFFECTS_variant_gene_adapter.GeneValidator', return_value=MagicMock(validate=MagicMock(return_value=True)))
@patch('adapters.Variant_EFFECTS_variant_gene_adapter.bulk_check_variants_in_arangodb', return_value={'NC_000010.11:79347444::CCTCCTCAGG'})
@patch('builtins.open', new_callable=mock_open, read_data=mock_tsv_data)
@patch(
    'adapters.Variant_EFFECTS_variant_gene_adapter.load_variant',
    return_value=({
        '_key': 'NC_000010.11:79347444::CCTCCTCAGG',
        'spdi': 'NC_000010.11:79347444::CCTCCTCAGG',
        'hgvs': 'NC_000010.11:g.79347445dupCCTCCTCAGG',
        'variation_type': 'insertion',
    }, None)
)
def test_process_file_variant_gene(mock_query_props, mock_gene_validator, mock_bulk_check, mock_file, mock_load_variant, mocker):
    writer = SpyWriter()
    adapter = VariantEFFECTSAdapter(
        filepath='./samples/variant_effects_variant_gene.example.tsv',
        writer=writer,
        label='variant_gene',
        source_url='https://api.data.igvf.org/files/IGVFFI9602ILPC/'
    )
    adapter.process_file()
    assert len(writer.contents) > 0
    first_item = json.loads(writer.contents[0])
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert 'log2_fold_change' in first_item
    assert 'label' in first_item
    assert first_item['label'] == 'variant effect on gene expression of ENSG00000108179'
    assert first_item['source_url'] == adapter.source_url
    assert first_item['method'] == 'CRISPR'
    assert first_item['simple_sample_summaries'] == ['donor:human']
    assert first_item['biological_context'] == 'sample'
