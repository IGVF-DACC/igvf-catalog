from unittest.mock import patch, mock_open
from adapters.writer import SpyWriter
from io import StringIO
import gzip
import json
from adapters.ESM_coding_variants_adapter import ESM1vCodingVariantsScores

SAMPLE_MAPPING_TSV = (
    'ENST00000370460.7\tp.Met1Ala\t'
    'AFF2_ENST00000370460.7_p.Met1Ala_c.1_3delinsGCA,AFF2_ENST00000370460.7_p.Met1Ala_c.1_3delinsGCC\t'
    'c.1_3delinsGCA,c.1_3delinsGCC\t'
    'NC_000023.11:148501097:ATG:GCA,NC_000023.11:148501097:ATG:GCC\t'
    'NC_000023.11:g.148501098_148501100delinsGCA,NC_000023.11:g.148501098_148501100delinsGCC\t'
    'GCA,GCC\t1,1\tATG\tENSP00000359489.2\tAFF2_HUMAN'
)

SAMPLE_ESM_TSV = (
    'GENCODE.v43.ENSG\tGENCODE.v43.ENST\tGENCODE.v43.ENSP\tHGVS.p\t'
    'esm1v_t33_650M_UR90S_1\tesm1v_t33_650M_UR90S_2\tcombined_score\n'
    'ENSG00000155966.14\tENST00000370460.7\tENSP00000359489.2\t'
    'ENSP00000359489.2:p.Met1Ala\t-5.354976177215576\t-4.247730731964111\t-5.950134754180908\n'
)


@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_MAPPING_TSV)
def test_load_from_mapping_file_variants(mock_gzip_open):
    writer = SpyWriter()
    adapter = ESM1vCodingVariantsScores(
        'dummy_accession.tsv.gz', label='variants', writer=writer)
    adapter.process_file()

    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_key'] == 'NC_000023.11:148501097:ATG:GCA'
    assert first_item['chr'] == 'chrX'
    assert first_item['pos'] == 148501097
    assert first_item['ref'] == 'ATG'
    assert first_item['alt'] == 'GCA'
    assert first_item['variation_type'] == 'deletion-insertion'
    assert first_item['source'] == 'IGVF'
    assert first_item['source_url'] == 'https://data.igvf.org/tabular-files/dummy_accession'


@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_MAPPING_TSV)
def test_load_from_mapping_file_variants_coding_variants(mock_gzip_open):
    writer = SpyWriter()
    adapter = ESM1vCodingVariantsScores(
        'dummy_accession.tsv.gz', label='variants_coding_variants', writer=writer)
    adapter.process_file()

    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_key'] == 'NC_000023.11:148501097:ATG:GCA_AFF2_ENST00000370460_p.Met1Ala_c.1_3delinsGCA'
    assert first_item['_from'] == 'variants/NC_000023.11:148501097:ATG:GCA'
    assert first_item['_to'] == 'coding_variants/AFF2_ENST00000370460_p.Met1Ala_c.1_3delinsGCA'
    assert first_item['chr'] == 'chrX'
    assert first_item['pos'] == 148501097
    assert first_item['ref'] == 'ATG'
    assert first_item['alt'] == 'GCA'


@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_MAPPING_TSV)
def test_load_from_mapping_file_coding_variants(mock_gzip_open):
    writer = SpyWriter()
    adapter = ESM1vCodingVariantsScores(
        'dummy_accession.tsv.gz', label='coding_variants', writer=writer)
    adapter.process_file()

    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_key'] == 'AFF2_ENST00000370460_p.Met1Ala_c.1_3delinsGCA'
    assert first_item['ref'] == 'M'
    assert first_item['alt'] == 'A'
    assert first_item['aapos'] == 1
    assert first_item['refcodon'] == 'ATG'
    assert first_item['gene_name'] == 'AFF2'
    assert first_item['protein_id'] == 'ENSP00000359489'
    assert first_item['transcript_id'] == 'ENST00000370460'
    assert first_item['protein_name'] == 'AFF2_HUMAN'
    assert first_item['hgvsp'] == 'p.Met1Ala'
    assert first_item['hgvsc'] == 'c.1_3delinsGCA'
    assert first_item['codonpos'] == 1


@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_igvf', return_value=[{'method': 'ESM1v'}])
@patch('gzip.open')
def test_process_file_coding_variants_phenotypes(mock_gzip_open, mock_fileset):
    def gzip_open_side_effect(filename, mode):
        if filename == 'ESM_1v_IGVFFI8105TNNO_mappings.tsv.gz':
            return mock_open(read_data=SAMPLE_MAPPING_TSV)(filename, mode)
        else:
            return mock_open(read_data=SAMPLE_ESM_TSV)(filename, mode)

    mock_gzip_open.side_effect = gzip_open_side_effect
    tsv_file = StringIO(SAMPLE_ESM_TSV)
    mock_gzip_open.return_value = tsv_file

    writer = SpyWriter()
    adapter = ESM1vCodingVariantsScores(
        'dummy_accession.tsv.gz',
        label='coding_variants_phenotypes',
        writer=writer
    )
    adapter.process_file()

    first_item = json.loads(writer.contents[0])
    assert first_item['_from'] == 'coding_variants/AFF2_ENST00000370460_p.Met1Ala_c.1_3delinsGCA'
    assert first_item['_to'] == 'ontology_terms/GO_0003674'
    assert first_item['esm_1v_score'] == -5.950134754180908
    assert first_item['esm1v_t33_650M_UR90S_1'] == -5.354976177215576
    assert first_item['method'] == 'ESM1v'
    assert first_item['files_filesets'] == 'files_filesets/dummy_accession'
