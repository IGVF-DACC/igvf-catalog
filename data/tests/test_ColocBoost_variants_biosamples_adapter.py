import json
import pytest
from adapters.ColocBoost_variants_biosamples_adapter import ColocBoostVariantBiosample
from adapters.writer import SpyWriter
from unittest.mock import patch, mock_open, MagicMock

MOCK_SPDI = 'NC_000001.11:112503772:T:C'
MOCK_VARIANT_ID = 'NC_000001.11:112503772:T:C'
FILE_ACCESSION = 'IGVFFI7493PNOA'
FILEPATH = f'./samples/{FILE_ACCESSION}.tsv.gz'

mock_tsv_header = (
    'VariantChr\tVariantStart\tVariantEnd\tEffectAllele\tOtherAllele\t'
    'SPDI_ID\tVCP\tGeneEnsembl\tGeneName\tTraitName\tOntologyTerm\tBiosampleTermName\tUBERONTerm\n'
)
mock_tsv_row = (
    f'chr1\t112503772\t112503773\tT\tC\t{MOCK_SPDI}\t'
    '0.9993\tENSG00000134245\tWNT2B\tmean arterial pressure\tEFO_0006340\ttibial nerve\tUBERON_0001323\n'
)
mock_tsv_data = mock_tsv_header + mock_tsv_row

mock_tsv_row_multi_biosample = (
    f'chr1\t112691075\t112691076\tT\tC\t{MOCK_SPDI}\t'
    '0.1056\tENSG00000155363\tMOV10\tmean arterial pressure\tEFO_0006340\t'
    'tibial artery;tibial nerve\tUBERON_0007610;UBERON_0001323\n'
)
mock_tsv_data_multi_biosample = mock_tsv_header + mock_tsv_row_multi_biosample


@pytest.fixture
def mock_file_fileset():
    with patch('adapters.ColocBoost_variants_biosamples_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get:
        mock_get.return_value = {
            'method': 'ColocBoost',
            'class': 'prediction'
        }
        yield mock_get


@pytest.fixture(autouse=True)
def mock_gene_validator():
    with patch('adapters.ColocBoost_variants_biosamples_adapter.GeneValidator') as mock_cls:
        instance = MagicMock()
        instance.validate.return_value = True
        mock_cls.return_value = instance
        yield instance


@pytest.fixture
def mock_load_variant():
    with patch('adapters.ColocBoost_variants_biosamples_adapter.load_variant') as mock_load:
        mock_load.return_value = ({
            '_key': MOCK_VARIANT_ID,
            'name': MOCK_VARIANT_ID,
            'chr': 'chr1',
            'pos': 112503772,
            'ref': 'T',
            'alt': 'C',
            'variation_type': 'SNP',
            'spdi': MOCK_SPDI,
            'hgvs': 'NC_000001.11:g.112503773T>C',
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


@patch('adapters.ColocBoost_variants_biosamples_adapter.bulk_check_variants_in_arangodb', return_value={MOCK_SPDI})
def test_process_file_variant_already_loaded_skipped(mock_bulk_check, mock_file_fileset, mock_load_variant):
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
@patch('adapters.ColocBoost_variants_biosamples_adapter.split_spdi', return_value=('chr1', 112503772, 'T', 'C'))
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
    assert item['_key'] == f'{MOCK_VARIANT_ID}_UBERON_0001323_ENSG00000134245_EFO_0006340_{FILE_ACCESSION}'
    assert item['_from'] == f'variants/{MOCK_VARIANT_ID}'
    assert item['_to'] == 'ontology_terms/UBERON_0001323'
    assert item['biosample_term'] == 'ontology_terms/UBERON_0001323'
    assert item['biological_context'] == 'tibial nerve'
    assert item['phenotype'] == 'ontology_terms/EFO_0006340'
    assert item['vcp'] == 0.9993
    assert item['gene'] == 'genes/ENSG00000134245'
    assert item['trait_name'] == 'mean arterial pressure'
    assert item['label'] == 'predicted variant effect on phenotype'
    assert item['method'] == 'ColocBoost'
    assert item['class'] == 'prediction'
    assert item['name'] == 'colocalizes with'
    assert item['inverse_name'] == 'colocalized by variant'
    assert item['source'] == 'IGVF'
    assert item['source_url'] == f'https://data.igvf.org/tabular-files/{FILE_ACCESSION}/'
    assert item['files_filesets'] == f'files_filesets/{FILE_ACCESSION}'


@patch('adapters.ColocBoost_variants_biosamples_adapter.build_variant_id', return_value=MOCK_VARIANT_ID)
@patch('adapters.ColocBoost_variants_biosamples_adapter.split_spdi', return_value=('chr1', 112691075, 'T', 'C'))
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
    items = [json.loads(item) for item in writer.contents]
    by_key = {item['_key']: item for item in items}
    assert f'{MOCK_VARIANT_ID}_UBERON_0007610_ENSG00000155363_EFO_0006340_{FILE_ACCESSION}' in by_key
    assert f'{MOCK_VARIANT_ID}_UBERON_0001323_ENSG00000155363_EFO_0006340_{FILE_ACCESSION}' in by_key
    assert by_key[f'{MOCK_VARIANT_ID}_UBERON_0007610_ENSG00000155363_EFO_0006340_{FILE_ACCESSION}']['biological_context'] == 'tibial artery'
    assert by_key[f'{MOCK_VARIANT_ID}_UBERON_0001323_ENSG00000155363_EFO_0006340_{FILE_ACCESSION}']['biological_context'] == 'tibial nerve'


@patch('adapters.ColocBoost_variants_biosamples_adapter.bulk_check_variants_in_arangodb', return_value=set())
def test_variant_not_in_db_skips_edge(mock_bulk_check, mock_file_fileset, mock_load_variant):
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
