import json
from unittest.mock import patch, mock_open
from adapters.writer import SpyWriter
from adapters.VAMP_coding_variant_scores_adapter import VAMPAdapter
import pytest


SAMPLE_TSV = (
    'variant\tscore\tstandard_error\trep1_score\trep2_score\trep3_score\n'
    'ENSP00000360372.3:p.Ala103Cys\t0.902654998066618\t0.0551255935523091\t0.79741948771822\t0.983743944202336\t0.926801562279298\n'
    'ENSP00000218099.2:p.Ile334Val\t1.0288110839938078\t0.07662282613325597\t\t0.9878924294091088\t1.1771665419319868\n'
)

MOCKED_CODING_VARIANTS = {
    ('ENSP00000360372', 'p.Ala103Cys'): ['coding_var_1', 'coding_var_2'],
    ('ENSP00000218099', 'p.Ile334Val'): ['coding_var_3']
}

MOCKED_CODING_VARIANTS_hgvsc = {
    ('ENST00000371321', 'c.447C>A'): ['coding_var_4']
}

MOCKED_GET_FILES_FILESET_ARANGO_RETURN = {
    'method': 'VAMP-seq',
    'class': 'observed data',
    'label': 'mutational effect',
    'simple_sample_summaries': ['test_summaries'],
    'samples': ['test_sample']
}


@patch('adapters.VAMP_coding_variant_scores_adapter.get_file_fileset_by_accession_in_arangodb', return_value=MOCKED_GET_FILES_FILESET_ARANGO_RETURN)
@patch('adapters.VAMP_coding_variant_scores_adapter.bulk_query_coding_variants_in_arangodb', return_value=MOCKED_CODING_VARIANTS)
@patch('adapters.VAMP_coding_variant_scores_adapter.bulk_query_coding_variants_from_hgvsc_in_arangodb', return_value=MOCKED_CODING_VARIANTS_hgvsc)
@patch('adapters.VAMP_coding_variant_scores_adapter.bulk_query_coding_variants_Met1_in_arangodb', return_value={})
@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_TSV)
def test_process_file_coding_variants_phenotypes(mock_file_fileset, mock_gzip_open, mock_bulk_query, mock_bulk_query_hgvsc, mock_bulk_query_Met1):
    writer = SpyWriter()
    phenotype_term = 'test_phenotype'
    adapter = VAMPAdapter(
        'IGVFFI0629IIQU.tsv.gz',
        label='coding_variants_phenotypes',
        phenotype_term=phenotype_term,
        writer=writer,
        validate=True
    )
    adapter.process_file()

    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_key'] == 'coding_var_1_test_phenotype_IGVFFI0629IIQU'
    assert first_item['_from'] == 'coding_variants/coding_var_1'
    assert first_item['_to'] == 'ontology_terms/test_phenotype'
    assert first_item['name'] == 'mutational effect'
    assert first_item['inverse_name'] == 'altered due to mutation'
    assert first_item['score'] == 0.902654998066618
    assert first_item['standard_error'] == 0.0551255935523091
    assert first_item['source'] == 'IGVF'
    assert first_item['source_url'] == 'https://data.igvf.org/tabular-files/IGVFFI0629IIQU'
    assert first_item['method'] == 'VAMP-seq'
    assert first_item['biological_context'] == 'test_summaries'
    assert first_item['biosample_term'] == 'test_sample'


def test_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_label. Allowed values: coding_variants_phenotypes'):
        VAMPAdapter(
            './samples/VAMP_CYP2C19_example.tsv.gz',
            label='invalid_label',
            writer=writer,
            validate=True
        )


@patch('adapters.VAMP_coding_variant_scores_adapter.get_file_fileset_by_accession_in_arangodb', return_value=MOCKED_GET_FILES_FILESET_ARANGO_RETURN)
@patch('adapters.VAMP_coding_variant_scores_adapter.bulk_query_coding_variants_in_arangodb', return_value=MOCKED_CODING_VARIANTS)
@patch('adapters.VAMP_coding_variant_scores_adapter.bulk_query_coding_variants_from_hgvsc_in_arangodb', return_value=MOCKED_CODING_VARIANTS_hgvsc)
@patch('adapters.VAMP_coding_variant_scores_adapter.bulk_query_coding_variants_Met1_in_arangodb', return_value={})
@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_TSV)
def test_validate_doc_invalid(mock_file_fileset, mock_gzip_open, mock_bulk_query, mock_bulk_query_hgvsc, mock_bulk_query_Met1):
    writer = SpyWriter()
    phenotype_term = 'test_phenotype'
    adapter = VAMPAdapter(
        'IGVFFI0629IIQU.tsv.gz',
        label='coding_variants_phenotypes',
        phenotype_term=phenotype_term,
        writer=writer,
        validate=True
    )
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
