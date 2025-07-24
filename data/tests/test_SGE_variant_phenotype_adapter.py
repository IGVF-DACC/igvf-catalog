import unittest
from unittest.mock import patch, MagicMock, mock_open
from adapters.writer import SpyWriter
import csv
import json
from io import StringIO
from adapters.SGE_variant_phenotype_adapter import SGE


def create_mock_writer():
    mock_writer = MagicMock()
    mock_writer.open = MagicMock()
    mock_writer.write = MagicMock()
    mock_writer.close = MagicMock()
    return mock_writer


SAMPLE_TSV = (
    'chrom\tpos\tref\talt\texon\ttarget\tconsequence\tscore\tstandard_error\t95_ci_upper\t95_ci_lower\tamino_acid_change\thgvs_p\tfunctional_consequence\tfunctional_consequence_zscore\tvariant_qc_flag\tsnvlib_lib1\n'
    'chr16\t23603562\tG\tA\tPALB2_X13\tPALB2_X13A\tmissense_variant\t-0.140561\t0.0469519\t-0.0485354\t-0.232587\tP1153L\tENSP00000261584.4:p.Pro1153Leu\tfunctionally_abnormal\t-4.24559\tPASS\t1155\n'
)


@patch('adapters.SGE_variant_phenotype_adapter.load_variant', return_value=({'_key': 'NC_000016.10:23603561:G:A'}, None))
@patch('adapters.SGE_variant_phenotype_adapter.bulk_check_spdis_in_arangodb', return_value=[])
@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_TSV)
def test_process_file_variants(mock_gzip_open, mock_bulk_check, mock_load_variant):
    writer = SpyWriter()
    adapter = SGE('dummy_accession.tsv.gz', label='variants', writer=writer)
    adapter.process_file()

    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_key'] == 'NC_000016.10:23603561:G:A'
    assert first_item['source'] == 'IGVF'
    assert first_item['source_url'] == 'https://data.igvf.org/tabular-files/dummy_accession'
    assert first_item['files_filesets'] == 'files_filesets/dummy_accession'


@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_igvf', return_value=[{}])
@patch('adapters.SGE_variant_phenotype_adapter.load_variant', return_value=({'_key': 'NC_000016.10:23603561:G:A'}, None))
@patch('adapters.SGE_variant_phenotype_adapter.bulk_check_spdis_in_arangodb', return_value=[])
@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_TSV)
def test_process_file_variants_phenotypes(mock_file_fileset, mock_gzip_open, mock_bulk_check, mock_load_variant):
    writer = SpyWriter()
    adapter = SGE('dummy_accession.tsv.gz',
                  label='variants_phenotypes', writer=writer)
    adapter.process_file()

    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_key'] == 'NC_000016.10:23603561:G:A_' + \
        SGE.PHENOTYPE_TERM + '_dummy_accession'
    assert first_item['source'] == 'IGVF'
    assert first_item['source_url'] == 'https://data.igvf.org/tabular-files/dummy_accession'
    assert first_item['files_filesets'] == 'files_filesets/dummy_accession'


@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_igvf', return_value=[{}])
@patch('adapters.SGE_variant_phenotype_adapter.load_variant', return_value=({'_key': 'NC_000016.10:23603561:G:A'}, None))
@patch('adapters.SGE_variant_phenotype_adapter.bulk_check_spdis_in_arangodb', return_value=[])
@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_TSV)
def test_process_file_coding_variants_label(mock_file_fileset, mock_gzip_open, mock_bulk_check, mock_load_variant, mocker):
    mocker.patch.object(
        SGE,
        'validate_coding_variant',
        return_value='dummy_coding_variant_key'  # Mocked coding variant ID
    )
    writer = SpyWriter()
    adapter = SGE('dummy_accession.tsv.gz',
                  label='variants_phenotypes_coding_variants', writer=writer)
    adapter.process_file()

    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_key'] == 'NC_000016.10:23603561:G:A_' + \
        SGE.PHENOTYPE_TERM + '_dummy_accession' + '_dummy_coding_variant_key'
    assert first_item['source'] == 'IGVF'
    assert first_item['source_url'] == 'https://data.igvf.org/tabular-files/dummy_accession'
    assert first_item['files_filesets'] == 'files_filesets/dummy_accession'
