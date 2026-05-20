import json
from unittest.mock import patch, mock_open
from adapters.writer import SpyWriter
from adapters.DUAL_IPA_coding_variant_scores_adapter import DUALIPAAdapter
import pytest


SAMPLE_TSV = (
    'spdi\tsymbol\tensembl_gene_id\tccsb_mutation_id\tCCSB_referenece_orf_id\thgvs_orf\thgvs_protein\t'
    'avg_gfp\tavg_mcherry\tavg_GFP_mCherry_ratio\twt_GFP_mCherry_ratio\tallele_wt_ratio\tdualipa_abun_score\tdualipa_abun_change\n'
    'NC_000016.10:89100729:G:C\tACSF3\tENSG00000176715\tCCSBVarC008268\tCCSBORF71337\t49G>C\t'
    'ENSP00000320646.4:p.Ala17Pro\t795.99\t4593.57\t0.2886\t0.3983\t0.7247\t-1.2568\tUncertain\n'
    'NC_000016.10:89101036:G:A\tACSF3\tENSG00000176715\tCCSBVarC008269\tCCSBORF71337\t356G>A\t'
    'ENSP00000320646.4:p.Gly119Asp\t716.73\t3870.44\t0.3261\t0.3983\t0.8188\t-0.8149\tN\n'
    'NC_000016.10:89101264:A:G\tACSF3\tENSG00000176715\tCCSBVarC008270\tCCSBORF71337\t584A>G\t'
    'ENSP00000320646.4:p.Lys195Arg\t883.26\t4664.60\t0.3395\t0.3983\t0.8523\t-0.6695\tY\n'
)

MOCKED_CODING_VARIANTS = {
    ('NC_000016.10:89100729:G:C', 'ENSP00000320646', 'p.Ala17Pro'): ['ACSF3_ENST00000317447_p.Ala17Pro_c.49G-C'],
    ('NC_000016.10:89101036:G:A', 'ENSP00000320646', 'p.Gly119Asp'): ['ACSF3_ENST00000317447_p.Gly119Asp_c.356G-A'],
    ('NC_000016.10:89101264:A:G', 'ENSP00000320646', 'p.Lys195Arg'): ['ACSF3_ENST00000317447_p.Lys195Arg_c.584A-G'],
}

MOCKED_FILE_FILESET = {
    'method': 'DUAL-IPA',
    'class': 'observed data',
    'label': 'protein variant effect',
    'simple_sample_summaries': ['HEK293 cell line, female, Homo sapiens'],
    'samples': ['ontology_terms/EFO_0001182']
}


@patch('adapters.DUAL_IPA_coding_variant_scores_adapter.get_file_fileset_by_accession_in_arangodb', return_value=MOCKED_FILE_FILESET)
@patch('adapters.DUAL_IPA_coding_variant_scores_adapter.bulk_query_coding_variants_from_spdi_in_arangodb', return_value=MOCKED_CODING_VARIANTS)
@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_TSV)
def test_process_file_coding_variants_phenotypes(mock_gzip_open, mock_bulk_query, mock_file_fileset):
    writer = SpyWriter()
    adapter = DUALIPAAdapter(
        'IGVFFI6224HZMG.tsv.gz',
        label='coding_variants_phenotypes',
        phenotype_term='BAO:0040014',
        writer=writer,
        validate=True
    )
    adapter.process_file()

    records = [json.loads(c) for c in writer.contents if c != '\n']
    assert len(records) == 3

    first = records[0]
    assert first['_key'] == 'ACSF3_ENST00000317447_p.Ala17Pro_c.49G-C_BAO:0040014_IGVFFI6224HZMG'
    assert first['_from'] == 'coding_variants/ACSF3_ENST00000317447_p.Ala17Pro_c.49G-C'
    assert first['_to'] == 'ontology_terms/BAO:0040014'
    assert first['name'] == 'mutational effect'
    assert first['inverse_name'] == 'altered due to mutation'
    assert first['source'] == 'IGVF'
    assert first['source_url'] == 'https://data.igvf.org/tabular-files/IGVFFI6224HZMG'
    assert first['label'] == 'protein variant effect'
    assert first['method'] == 'DUAL-IPA'
    assert first['class'] == 'observed data'
    assert first['biological_context'] == 'HEK293 cell line, female, Homo sapiens'
    assert first['biosample_term'] == 'ontology_terms/EFO_0001182'
    assert first['files_filesets'] == 'files_filesets/IGVFFI6224HZMG'
    assert first['avg_gfp'] == 795.99
    assert first['avg_mcherry'] == 4593.57
    assert first['avg_GFP_mCherry_ratio'] == 0.2886
    assert first['wt_GFP_mCherry_ratio'] == 0.3983
    assert first['allele_wt_ratio'] == 0.7247
    assert first['dualipa_abun_score'] == -1.2568
    assert first['dualipa_abun_change'] == 'Uncertain'

    # check all three categorical values appear
    assert set(r['dualipa_abun_change']
               for r in records) == {'Uncertain', 'N', 'Y'}


@patch('adapters.DUAL_IPA_coding_variant_scores_adapter.get_file_fileset_by_accession_in_arangodb', return_value=MOCKED_FILE_FILESET)
@patch('adapters.DUAL_IPA_coding_variant_scores_adapter.bulk_query_coding_variants_from_spdi_in_arangodb', return_value=MOCKED_CODING_VARIANTS)
@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_TSV)
def test_missing_variant_is_skipped(mock_gzip_open, mock_bulk_query, mock_file_fileset):
    writer = SpyWriter()
    # return empty mapping — all variants will be skipped
    mock_bulk_query.return_value = {}
    adapter = DUALIPAAdapter(
        'IGVFFI6224HZMG.tsv.gz',
        label='coding_variants_phenotypes',
        phenotype_term='BAO:0040014',
        writer=writer,
        validate=True
    )
    adapter.process_file()
    records = [c for c in writer.contents if c != '\n']
    assert len(records) == 0


def test_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_label. Allowed values: coding_variants_phenotypes'):
        DUALIPAAdapter(
            'IGVFFI6224HZMG.tsv.gz',
            label='invalid_label',
            writer=writer,
        )


@patch('adapters.DUAL_IPA_coding_variant_scores_adapter.get_file_fileset_by_accession_in_arangodb', return_value=MOCKED_FILE_FILESET)
@patch('adapters.DUAL_IPA_coding_variant_scores_adapter.bulk_query_coding_variants_from_spdi_in_arangodb', return_value=MOCKED_CODING_VARIANTS)
@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_TSV)
def test_validate_doc_invalid(mock_gzip_open, mock_bulk_query, mock_file_fileset):
    writer = SpyWriter()
    adapter = DUALIPAAdapter(
        'IGVFFI6224HZMG.tsv.gz',
        label='coding_variants_phenotypes',
        phenotype_term='BAO:0040014',
        writer=writer,
        validate=True
    )
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc({'invalid_field': 'bad'})
