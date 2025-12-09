from unittest.mock import patch, mock_open
from adapters.writer import SpyWriter
import json
from adapters.SGE_variant_phenotype_adapter import SGE
import pytest


# mock get_file_fileset_by_accession_in_arangodb so files_fileset data change will not affect the test
@pytest.fixture
def mock_file_fileset():
    """Fixture to mock get_file_fileset_by_accession_in_arangodb function."""
    with patch('adapters.SGE_variant_phenotype_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'method': 'SGE',
            'class': 'observed data',
            'simple_sample_summaries': ['HAP-1'],
            'samples': ['ontology_terms/EFO_0007598']
        }
        yield mock_get_file_fileset


SAMPLE_TSV = (
    'chrom\tpos\tref\talt\texon\ttarget\tconsequence\tscore\tstandard_error\t95_ci_upper\t95_ci_lower\tamino_acid_change\thgvs_p\tfunctional_consequence\tfunctional_consequence_zscore\tvariant_qc_flag\tsnvlib_lib1\tsnvlib_lib2\tD05_R1_lib1\tD05_R1_lib2\tD05_R2_lib1\tD05_R2_lib2\tD05_R3_lib1\tD05_R3_lib2\tD13_R1_lib1\tD13_R1_lib2\tD13_R2_lib1\tD13_R2_lib2\tD13_R3_lib1\tD13_R3_lib2\n'
    'chr16\t23603562\tG\tA\tPALB2_X13\tPALB2_X13A\tmissense_variant\t-0.140561\t0.0469519\t-0.0485354\t-0.232587\tP1153L\tENSP00000261584.4:p.Pro1153Leu\tfunctionally_abnormal\t-4.24559\tPASS\t1155\t1156\t1001\t1002\t1003\t1004\t1005\t1006\t2001\t2002\t2003\t2004\t2005\t2006\n'
)

# Complete variant object for mocking
COMPLETE_VARIANT = {
    '_key': 'NC_000016.10:23603561:G:A',
    'name': 'NC_000016.10:23603561:G:A',
    'chr': 'chr16',
    'pos': 23603561,
    'ref': 'G',
    'alt': 'A',
    'variation_type': 'SNP',
    'spdi': 'NC_000016.10:23603561:G:A',
    'hgvs': 'NC_000016.10:g.23603562G>A',
    'organism': 'Homo sapiens',
    'rsid': [],
    'qual': '100',
    'filter': 'PASS',
    'annotations': {},
    'vrs_digest': 'test_digest',
    'ca_id': 'CA1234567890'
}


@patch('adapters.SGE_variant_phenotype_adapter.load_variant', return_value=(COMPLETE_VARIANT, None))
@patch('adapters.SGE_variant_phenotype_adapter.bulk_check_variants_in_arangodb', return_value=[])
@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_TSV)
def test_process_file_variants(mock_gzip_open, mock_bulk_check, mock_load_variant):
    writer = SpyWriter()
    adapter = SGE('dummy_accession.tsv.gz', label='variants',
                  writer=writer, validate=True)
    adapter.process_file()

    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_key'] == 'NC_000016.10:23603561:G:A'
    assert first_item['source'] == 'IGVF'
    assert first_item['source_url'] == 'https://data.igvf.org/tabular-files/dummy_accession'
    assert first_item['files_filesets'] == 'files_filesets/dummy_accession'


@patch('adapters.SGE_variant_phenotype_adapter.load_variant', return_value=(COMPLETE_VARIANT, None))
@patch('adapters.SGE_variant_phenotype_adapter.bulk_check_variants_in_arangodb', return_value=[])
@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_TSV)
def test_process_file_variants_phenotypes(mock_gzip_open, mock_bulk_check, mock_load_variant, mock_file_fileset):
    writer = SpyWriter()
    adapter = SGE('dummy_accession.tsv.gz',
                  label='variants_phenotypes', writer=writer, validate=True)
    adapter.process_file()

    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_key'] == 'NC_000016.10:23603561:G:A_' + \
        SGE.PHENOTYPE_TERM + '_dummy_accession'
    assert first_item['source'] == 'IGVF'
    assert first_item['source_url'] == 'https://data.igvf.org/tabular-files/dummy_accession'
    assert first_item['files_filesets'] == 'files_filesets/dummy_accession'


@patch('adapters.SGE_variant_phenotype_adapter.load_variant', return_value=(COMPLETE_VARIANT, None))
@patch('adapters.SGE_variant_phenotype_adapter.bulk_check_variants_in_arangodb', return_value=[])
@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_TSV)
def test_process_file_coding_variants_label(mock_gzip_open, mock_bulk_check, mock_load_variant, mock_file_fileset, mocker):
    mocker.patch.object(
        SGE,
        'validate_coding_variant',
        return_value='dummy_coding_variant_key'  # Mocked coding variant ID
    )
    writer = SpyWriter()
    adapter = SGE('dummy_accession.tsv.gz',
                  label='variants_phenotypes_coding_variants', writer=writer, validate=True)
    adapter.process_file()

    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_key'] == 'NC_000016.10:23603561:G:A_' + \
        SGE.PHENOTYPE_TERM + '_dummy_accession' + '_dummy_coding_variant_key'
    assert first_item['source'] == 'IGVF'
    assert first_item['source_url'] == 'https://data.igvf.org/tabular-files/dummy_accession'
    assert first_item['files_filesets'] == 'files_filesets/dummy_accession'


def test_invalid_label(mock_file_fileset):
    writer = SpyWriter()
    with pytest.raises(ValueError):
        adapter = SGE('dummy_accession.tsv.gz',
                      label='invalid_label', writer=writer, validate=True)


def test_validate_doc_invalid(mock_file_fileset):
    writer = SpyWriter()
    adapter = SGE('dummy_accession.tsv.gz',
                  label='variants_phenotypes', writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError):
        adapter.validate_doc(invalid_doc)
