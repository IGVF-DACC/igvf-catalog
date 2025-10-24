from unittest.mock import patch
from adapters.writer import SpyWriter
import json
from adapters.cV2F_variant_phenotype_adapter import cV2F
import pytest


@patch('adapters.cV2F_variant_phenotype_adapter.bulk_check_variants_in_arangodb', return_value={'NC_000001.11:10203:T:G'})
@patch('adapters.cV2F_variant_phenotype_adapter.load_variant')
def test_process_variants_chunk(mock_load_variant, mock_bulk_check, mocker):
    # Create a complete mock variant that satisfies the schema requirements
    mock_variant = {
        '_key': 'NC_000001.11:10202:C:A',
        'name': 'NC_000001.11:10202:C:A',
        'chr': 'chr1',
        'pos': 10202,
        'rsid': ['rs1234567890'],
        'ref': 'C',
        'alt': 'A',
        'qual': '60',
        'filter': None,
        'variation_type': 'SNP',
        'annotations': {},
        'format': 'GT:DP',
        'spdi': 'NC_000001.11:10202:C:A',
        'hgvs': 'NC_000001.11:g.10203C>A',
        'vrs_digest': 'fake_vrs_digest',
        'ca_id': 'CA1234567890',
        'organism': 'Homo sapiens'
    }
    mock_load_variant.return_value = (mock_variant, None)

    writer = SpyWriter()
    chunk = [
        ['chr1', '10203', '10203', 'A', 'C', 'NC_000001.11:10202:C:A',
            'GO:0003674', 'AGNOSTIC', '', 'continuous score', '0.85'],
        ['chr1', '10204', '10204', 'T', 'G', 'NC_000001.11:10203:T:G',
            'GO:0003674', 'AGNOSTIC', '', 'continuous score', '0.76']
    ]

    adapter = cV2F('dummy_accession.tsv.gz', label='variants',
                   writer=writer, validate=True)
    adapter.process_variants_chunk(chunk)
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_key'] == 'NC_000001.11:10202:C:A'
    assert first_item['source'] == 'IGVF'
    assert first_item['source_url'] == 'https://data.igvf.org/tabular-files/dummy_accession'
    assert first_item['files_filesets'] == 'files_filesets/dummy_accession'


@patch('adapters.cV2F_variant_phenotype_adapter.bulk_check_variants_in_arangodb', return_value={'NC_000001.11:10202:C:A'})
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
                   label='variants_phenotypes', writer=writer, validate=True)
    adapter.process_variants_phenotypes_chunk(chunk)
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 1
    assert first_item['_key'] == 'NC_000001.11:10202:C:A_' + \
        cV2F.PHENOTYPE_TERM + '_dummy_accession'
    assert first_item['source'] == 'IGVF'
    assert first_item['source_url'] == 'https://data.igvf.org/tabular-files/dummy_accession'
    assert first_item['files_filesets'] == 'files_filesets/dummy_accession'


def test_cV2F_adapter_validate_doc_invalid():
    writer = SpyWriter()
    adapter = cV2F('dummy_accession.tsv.gz',
                   label='variants_phenotypes', writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)


def test_cV2F_adapter_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_label. Allowed values: variants, variants_phenotypes'):
        cV2F('dummy_accession.tsv.gz', label='invalid_label',
             writer=writer, validate=True)


@patch('adapters.cV2F_variant_phenotype_adapter.bulk_check_variants_in_arangodb', return_value=set())
@patch('adapters.cV2F_variant_phenotype_adapter.load_variant', return_value=(None, None))
@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_igvf', return_value=[{
    'simple_sample_summaries': ['lung'],
    'method': 'cV2F',
    'samples': ['K562']
}])
def test_cV2F_adapter_process_file(mock_fileset, mock_load_variant, mock_bulk_check):
    writer = SpyWriter()

    # Create a temporary test file
    import tempfile
    import gzip
    with tempfile.NamedTemporaryFile(suffix='.tsv.gz', delete=False) as temp_file:
        with gzip.open(temp_file.name, 'wt') as f:
            f.write('VariantChr\tVariantStart\tVariantEnd\tEffectAllele\tOtherAllele\tSPDI_ID\tGOOntology\tBiosampleTermName\tBiosampleTerm\tPredictionType\tPredictionValue\n')
            f.write('VariantChr\tVariantStart\tVariantEnd\tEffectAllele\tOtherAllele\tSPDI_ID\tGOOntology\tBiosampleTermName\tBiosampleTerm\tPredictionType\tPredictionValue\n')
            f.write(
                'chr1\t10203\t10203\tA\tC\tNC_000001.11:10202:C:A\tGO:0003674\tAGNOSTIC\t\tcontinuous score\t0.85\n')
        temp_file_path = temp_file.name

    try:
        adapter = cV2F(temp_file_path, label='variants_phenotypes',
                       writer=writer, validate=True)
        adapter.process_file()
        assert len(writer.contents) > 0
        adapter = cV2F(temp_file_path, label='variants',
                       writer=writer, validate=True)
        adapter.process_file()
        assert len(writer.contents) > 0
    finally:
        import os
        os.unlink(temp_file_path)
