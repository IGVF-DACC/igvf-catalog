from unittest.mock import patch, mock_open
from adapters.writer import SpyWriter
import json
from adapters.ESM_coding_variants_adapter import ESM1vCodingVariantsScores
import pytest

SAMPLE_MAPPING_TSV = (
    'ENST00000370460.7\tp.Met1Ala\t'
    'AFF2_ENST00000370460.7_p.Met1Ala_c.1_3delinsGCA,AFF2_ENST00000370460.7_p.Met1Ala_c.1_3delinsGCC\t'
    'c.1_3delinsGCA,c.1_3delinsGCC\t'
    'NC_000023.11:148501097:ATG:GCA,NC_000023.11:148501097:ATG:GCC\t'
    'NC_000023.11:g.148501098_148501100delinsGCA,NC_000023.11:g.148501098_148501100delinsGCC\t'
    'GCA,GCC\t1,1\tATG\tENSP00000359489.2\tAFF2_HUMAN\t-5.354976177215576\t-4.247730731964111\t-5.950134754180908\t-5.966752052307129\t-5.39961051940918\t\t\t\t\t\t-5.383840847015381\n'
)


# mock get_file_fileset_by_accession_in_arangodb so files_fileset data change will not affect the test
@pytest.fixture
def mock_file_fileset():
    """Fixture to mock get_file_fileset_by_accession_in_arangodb function."""
    with patch('adapters.ESM_coding_variants_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'method': 'ESM-1v',
            'class': 'prediction',
            'samples': ['ontology_terms/CL_0000679'],
            'simple_sample_summaries': ['glutamatergic neuron differentiated cell specimen, pooled cell']
        }
        yield mock_get_file_fileset


@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_MAPPING_TSV)
def test_load_from_mapping_file_variants(mock_gzip_open):
    writer = SpyWriter()
    adapter = ESM1vCodingVariantsScores(
        None, label='variants', writer=writer, validate=True)
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
    assert first_item['source_url'] == 'https://data.igvf.org/tabular-files/IGVFFI8105TNNO'


@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_MAPPING_TSV)
def test_load_from_mapping_file_variants_coding_variants(mock_gzip_open, mock_file_fileset):
    writer = SpyWriter()
    adapter = ESM1vCodingVariantsScores(
        None, label='variants_coding_variants', writer=writer, validate=True)
    # Initialize igvf_metadata_props for variants_coding_variants label
    adapter.igvf_metadata_props = mock_file_fileset.return_value
    adapter.process_file()

    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_key'] == 'NC_000023.11:148501097:ATG:GCA_AFF2_ENST00000370460_p.Met1!_c.1_3delinsGCA'
    assert first_item['_from'] == 'variants/NC_000023.11:148501097:ATG:GCA'
    assert first_item['_to'] == 'coding_variants/AFF2_ENST00000370460_p.Met1!_c.1_3delinsGCA'
    assert first_item['chr'] == 'chrX'
    assert first_item['pos'] == 148501097
    assert first_item['ref'] == 'ATG'
    assert first_item['alt'] == 'GCA'
    assert first_item['method'] == 'ESM-1v'
    assert first_item['class'] == 'prediction'
    assert first_item['biosample_term'] == 'ontology_terms/CL_0000679'
    assert first_item['biological_context'] == 'glutamatergic neuron differentiated cell specimen, pooled cell'
    assert first_item['source'] == 'IGVF'
    assert first_item['source_url'] == 'https://data.igvf.org/tabular-files/IGVFFI8105TNNO'
    assert first_item['label'] == 'codes for'
    assert first_item['name'] == 'codes for'
    assert first_item['inverse_name'] == 'encoded by'


@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_MAPPING_TSV)
def test_load_from_mapping_file_coding_variants(mock_gzip_open):
    writer = SpyWriter()
    adapter = ESM1vCodingVariantsScores(
        None, label='coding_variants', writer=writer, validate=True)
    adapter.process_file()

    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_key'] == 'AFF2_ENST00000370460_p.Met1!_c.1_3delinsGCA'
    assert first_item['ref'] == 'M'
    assert first_item['alt'] == 'A'
    assert first_item['aapos'] == 1
    assert first_item['refcodon'] == 'ATG'
    assert first_item['gene_name'] == 'AFF2'
    assert first_item['protein_id'] == 'ENSP00000359489'
    assert first_item['transcript_id'] == 'ENST00000370460'
    assert first_item['protein_name'] == 'AFF2_HUMAN'
    assert first_item['hgvsp'] == 'p.Met1?'
    assert first_item['hgvsc'] == 'c.1_3delinsGCA'
    assert first_item['codonpos'] == 1


@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_MAPPING_TSV)
def test_process_file_coding_variants_phenotypes(mock_gzip_open, mock_file_fileset):
    writer = SpyWriter()
    adapter = ESM1vCodingVariantsScores(
        None,
        label='coding_variants_phenotypes',
        writer=writer,
        validate=True
    )
    adapter.process_file()

    first_item = json.loads(writer.contents[0])
    assert first_item['_from'] == 'coding_variants/AFF2_ENST00000370460_p.Met1!_c.1_3delinsGCA'
    assert first_item['_to'] == 'ontology_terms/GO_0003674'
    assert first_item['esm_1v_score'] == -5.383840847015381
    assert first_item['esm1v_t33_650M_UR90S_1'] == -5.354976177215576
    assert first_item['method'] == 'ESM-1v'
    assert first_item['class'] == 'prediction'
    assert first_item['biosample_term'] == 'ontology_terms/CL_0000679'
    assert first_item['biological_context'] == 'glutamatergic neuron differentiated cell specimen, pooled cell'
    assert first_item['files_filesets'] == 'files_filesets/IGVFFI8105TNNO'
    assert first_item['source'] == 'IGVF'
    assert first_item['source_url'] == 'https://data.igvf.org/tabular-files/IGVFFI8105TNNO'
    assert first_item['name'] == 'mutational effect'
    assert first_item['inverse_name'] == 'altered due to mutation'
    assert first_item['label'] == 'predicted protein variant effect'


def test_validate_doc_invalid():
    writer = SpyWriter()
    adapter = ESM1vCodingVariantsScores(
        None,
        label='coding_variants_phenotypes',
        writer=writer,
        validate=True
    )
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)


def test_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_label. Allowed values: coding_variants, variants, variants_coding_variants, coding_variants_phenotypes'):
        ESM1vCodingVariantsScores(
            None,
            label='invalid_label',
            writer=writer,
            validate=True
        )
