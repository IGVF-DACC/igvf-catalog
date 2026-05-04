import json
import pytest
from adapters.ColocBoost_variants_biosamples_adapter import ColocBoostVariantBiosample
from adapters.writer import SpyWriter
from unittest.mock import patch, mock_open

MOCK_SPDI = 'NC_000001.11:100:G:A'
MOCK_VARIANT_ID = 'NC_000001.11:100:G:A'
FILE_ACCESSION = 'IGVFFI1234ABCD'
FILEPATH = f'./samples/{FILE_ACCESSION}.tsv.gz'

mock_tsv_header = (
    'VariantChr\tVariantStart\tVariantEnd\tEffectAllele\tOtherAllele\t'
    'SPDI_ID\tBiosampleTerm\tOntologyTerm\tVCP\tGeneEnsembl\tGeneName\tTraitName\n'
)
mock_tsv_row = (
    f'chr1\t100\t101\tA\tG\t{MOCK_SPDI}\t'
    'UBERON_0001323\tEFO_0006340\t0.85\tENSG00000123456\tCLU\tAlzheimer disease\n'
)
mock_tsv_data = mock_tsv_header + mock_tsv_row

mock_tsv_row_multi_biosample = (
    f'chr1\t100\t101\tA\tG\t{MOCK_SPDI}\t'
    'UBERON_0001323,UBERON_0002097\tEFO_0006340\t0.85\tENSG00000123456\tCLU\tAlzheimer disease\n'
)
mock_tsv_data_multi_biosample = mock_tsv_header + mock_tsv_row_multi_biosample

mock_tsv_row_no_phenotype = (
    f'chr1\t100\t101\tA\tG\t{MOCK_SPDI}\t'
    'UBERON_0001323\t\t0.85\tENSG00000123456\tCLU\tAlzheimer disease\n'
)
mock_tsv_data_no_phenotype = mock_tsv_header + mock_tsv_row_no_phenotype


@pytest.fixture
def mock_file_fileset():
    with patch('adapters.ColocBoost_variants_biosamples_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get:
        mock_get.return_value = {
            'method': 'ColocBoost',
            'class': 'prediction'
        }
        yield mock_get


@pytest.fixture
def mock_load_variant():
    with patch('adapters.ColocBoost_variants_biosamples_adapter.load_variant') as mock_load:
        mock_load.return_value = ({
            '_key': MOCK_VARIANT_ID,
            'name': MOCK_VARIANT_ID,
            'chr': 'chr1',
            'pos': 100,
            'ref': 'G',
            'alt': 'A',
            'variation_type': 'SNP',
            'spdi': MOCK_SPDI,
            'hgvs': 'NC_000001.11:g.101G>A',
            'organism': 'Homo sapiens',
            'rsid': [],
            'qual': '100',
            'annotations': {},
            'vrs_digest': 'test_digest',
            'ca_id': 'CA1234567890'
        }, None)
        yield mock_load


@patch('adapters.ColocBoost_variants_biosamples_adapter.bulk_check_variants_in_arangodb', return_value=set())
def test_process_file_variant(mock_bulk_check, mock_file_fileset, mock_load_variant):
    writer = SpyWriter()
    adapter = ColocBoostVariantBiosample(
        filepath=FILEPATH,
        label='variant',
        writer=writer,
        validate=True
    )
    with patch('gzip.open', mock_open(read_data=mock_tsv_data)):
        adapter.process_file()

    assert len(writer.contents) == 1
    first_item = json.loads(writer.contents[0])
    assert first_item['_key'] == MOCK_VARIANT_ID
    assert first_item['spdi'] == MOCK_SPDI
    assert first_item['source'] == 'IGVF'
    assert first_item[
        'source_url'] == f'https://data.igvf.org/tabular-files/{FILE_ACCESSION}/'
    assert first_item['files_filesets'] == f'files_filesets/{FILE_ACCESSION}'


@patch('adapters.ColocBoost_variants_biosamples_adapter.bulk_check_variants_in_arangodb', return_value=set())
def test_process_file_variant_already_loaded_skipped(mock_bulk_check, mock_file_fileset, mock_load_variant):
    # When variant is already in DB (loaded_spdis is not empty but doesn't include our spdi),
    # and our spdi IS in the set, the variant is skipped for loading.
    mock_bulk_check.return_value = {MOCK_SPDI}
    writer = SpyWriter()
    adapter = ColocBoostVariantBiosample(
        filepath=FILEPATH,
        label='variant',
        writer=writer,
        validate=False
    )
    with patch('gzip.open', mock_open(read_data=mock_tsv_data)):
        adapter.process_file()

    assert len(writer.contents) == 0


@patch('adapters.ColocBoost_variants_biosamples_adapter.build_variant_id', return_value=MOCK_VARIANT_ID)
@patch('adapters.ColocBoost_variants_biosamples_adapter.split_spdi', return_value=('chr1', 100, 'G', 'A'))
@patch('adapters.ColocBoost_variants_biosamples_adapter.bulk_check_variants_in_arangodb', return_value={MOCK_SPDI})
def test_process_file_variant_biosample(mock_bulk_check, mock_split_spdi, mock_build_id, mock_file_fileset, mock_load_variant):
    writer = SpyWriter()
    adapter = ColocBoostVariantBiosample(
        filepath=FILEPATH,
        label='variant_biosample',
        writer=writer,
        validate=True
    )
    with patch('gzip.open', mock_open(read_data=mock_tsv_data)):
        adapter.process_file()

    assert len(writer.contents) == 1
    item = json.loads(writer.contents[0])
    assert item['_key'] == f'{MOCK_VARIANT_ID}_UBERON_0001323_{FILE_ACCESSION}'
    assert item['_from'] == f'variants/{MOCK_VARIANT_ID}'
    assert item['_to'] == 'ontology_terms/UBERON_0001323'
    assert item['biosample_term'] == 'ontology_terms/UBERON_0001323'
    assert item['phenotype'] == 'ontology_terms/EFO_0006340'
    assert item['vcp'] == 0.85
    assert item['gene_ensembl'] == 'ENSG00000123456'
    assert item['gene_name'] == 'CLU'
    assert item['trait_name'] == 'Alzheimer disease'
    assert item['label'] == 'variant colocalization with molecular trait'
    assert item['method'] == 'ColocBoost'
    assert item['class'] == 'prediction'
    assert item['name'] == 'colocalizes with'
    assert item['inverse_name'] == 'colocalized by variant'
    assert item['source'] == 'IGVF'
    assert item['source_url'] == f'https://data.igvf.org/tabular-files/{FILE_ACCESSION}/'
    assert item['files_filesets'] == f'files_filesets/{FILE_ACCESSION}'


@patch('adapters.ColocBoost_variants_biosamples_adapter.build_variant_id', return_value=MOCK_VARIANT_ID)
@patch('adapters.ColocBoost_variants_biosamples_adapter.split_spdi', return_value=('chr1', 100, 'G', 'A'))
@patch('adapters.ColocBoost_variants_biosamples_adapter.bulk_check_variants_in_arangodb', return_value={MOCK_SPDI})
def test_multiple_biosamples_per_row(mock_bulk_check, mock_split_spdi, mock_build_id, mock_file_fileset, mock_load_variant):
    writer = SpyWriter()
    adapter = ColocBoostVariantBiosample(
        filepath=FILEPATH,
        label='variant_biosample',
        writer=writer,
        validate=False
    )
    with patch('gzip.open', mock_open(read_data=mock_tsv_data_multi_biosample)):
        adapter.process_file()

    assert len(writer.contents) == 2
    keys = {json.loads(item)['_key'] for item in writer.contents}
    assert f'{MOCK_VARIANT_ID}_UBERON_0001323_{FILE_ACCESSION}' in keys
    assert f'{MOCK_VARIANT_ID}_UBERON_0002097_{FILE_ACCESSION}' in keys
    tos = {json.loads(item)['_to'] for item in writer.contents}
    assert 'ontology_terms/UBERON_0001323' in tos
    assert 'ontology_terms/UBERON_0002097' in tos


@patch('adapters.ColocBoost_variants_biosamples_adapter.build_variant_id', return_value=MOCK_VARIANT_ID)
@patch('adapters.ColocBoost_variants_biosamples_adapter.split_spdi', return_value=('chr1', 100, 'G', 'A'))
@patch('adapters.ColocBoost_variants_biosamples_adapter.bulk_check_variants_in_arangodb', return_value={MOCK_SPDI})
def test_missing_ontology_term_sets_phenotype_none(mock_bulk_check, mock_split_spdi, mock_build_id, mock_file_fileset, mock_load_variant):
    writer = SpyWriter()
    adapter = ColocBoostVariantBiosample(
        filepath=FILEPATH,
        label='variant_biosample',
        writer=writer,
        validate=False
    )
    with patch('gzip.open', mock_open(read_data=mock_tsv_data_no_phenotype)):
        adapter.process_file()

    assert len(writer.contents) == 1
    item = json.loads(writer.contents[0])
    assert item['phenotype'] is None


@patch('adapters.ColocBoost_variants_biosamples_adapter.bulk_check_variants_in_arangodb', return_value={MOCK_SPDI})
def test_variant_not_in_db_skips_edge(mock_bulk_check, mock_file_fileset, mock_load_variant):
    mock_bulk_check.return_value = set()
    writer = SpyWriter()
    adapter = ColocBoostVariantBiosample(
        filepath=FILEPATH,
        label='variant_biosample',
        writer=writer,
        validate=False
    )
    with patch('gzip.open', mock_open(read_data=mock_tsv_data)):
        adapter.process_file()

    assert len(writer.contents) == 0


def test_invalid_label(mock_file_fileset, mock_load_variant):
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_label. Allowed values: variant, variant_biosample'):
        ColocBoostVariantBiosample(
            filepath=FILEPATH,
            label='invalid_label',
            writer=writer,
            validate=True
        )
