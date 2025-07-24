from unittest.mock import patch
from adapters.writer import SpyWriter
import json
from adapters.cV2F_variant_phenotype_adapter import cV2F


@patch('adapters.cV2F_variant_phenotype_adapter.bulk_check_spdis_in_arangodb', return_value={'NC_000001.11:10203:T:G'})
@patch('adapters.cV2F_variant_phenotype_adapter.load_variant', return_value=({'_key': 'NC_000001.11:10202:C:A'}, None))
def test_process_variants_chunk(mock_bulk_check_spdis_in_arangodb, mock_load_variant, mocker):
    writer = SpyWriter()
    chunk = [
        ['chr1', '10203', '10203', 'A', 'C', 'NC_000001.11:10202:C:A',
            'GO:0003674', 'AGNOSTIC', '', 'continuous score', '0.85'],
        ['chr1', '10204', '10204', 'T', 'G', 'NC_000001.11:10203:T:G',
            'GO:0003674', 'AGNOSTIC', '', 'continuous score', '0.76']
    ]

    adapter = cV2F('dummy_accession.tsv.gz', label='variants', writer=writer)
    adapter.process_variants_chunk(chunk)
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_key'] == 'NC_000001.11:10202:C:A'
    assert first_item['source'] == 'IGVF'
    assert first_item['source_url'] == 'https://data.igvf.org/tabular-files/dummy_accession'
    assert first_item['files_filesets'] == 'files_filesets/dummy_accession'


@patch('adapters.cV2F_variant_phenotype_adapter.bulk_check_spdis_in_arangodb', return_value={'NC_000001.11:10202:C:A'})
@patch('adapters.cV2F_variant_phenotype_adapter.load_variant', return_value=({'_key': 'NC_000001.11:10203:T:G'}, None))
@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_igvf', return_value=[{}])
def test_process_variants_phenotypes_chunk(mock_bulk_check, mock_load_variant, mocker):
    writer = SpyWriter()
    chunk = [
        ['chr1', '10203', '10203', 'A', 'C', 'NC_000001.11:10202:C:A',
            'GO:0003674', 'AGNOSTIC', '', 'continuous score', '0.85'],
        ['chr1', '10204', '10204', 'T', 'G', 'NC_000001.11:10203:T:G',
            'GO:0003674', 'AGNOSTIC', '', 'continuous score', '0.76']
    ]
    adapter = cV2F('dummy_accession.tsv.gz',
                   label='variants_phenotypes', writer=writer)
    adapter.process_variants_phenotypes_chunk(chunk)
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 1
    assert first_item['_key'] == 'NC_000001.11:10202:C:A_' + \
        cV2F.PHENOTYPE_TERM + '_dummy_accession'
    assert first_item['source'] == 'IGVF'
    assert first_item['source_url'] == 'https://data.igvf.org/tabular-files/dummy_accession'
    assert first_item['files_filesets'] == 'files_filesets/dummy_accession'
