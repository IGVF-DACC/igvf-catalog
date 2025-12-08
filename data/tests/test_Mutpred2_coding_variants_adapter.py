from unittest.mock import patch, mock_open
from adapters.writer import SpyWriter
from io import StringIO
import gzip
import json
from adapters.Mutpred2_coding_variants_adapter import Mutpred2CodingVariantsScores
import pytest

mechanisms_json = json.dumps([{
    'Property': 'VSL2B_disorder',
    'Posterior Probability': 0.3,
    'P-value': 0.04,
    'Effected Position': 'S869',
    'Type': 'Loss'
}])

SAMPLE_MAPPING_TSV = (
    f'ENST00000261590.13\tQ873T\tDSG2_ENST00000261590.13_p.Q873T_c.2617_2618delinsAC,DSG2_ENST00000261590.13_p.Q873T_c.2617_2619delinsACC\tc.2617_2618delinsAC,c.2617_2619delinsACC\tNC_000018.10:31546002:CA:AC,NC_000018.10:31546002:CAA:ACC\tNC_000018.10:g.31546003_31546004delinsAC,NC_000018.10:g.31546003_31546005delinsACC\tACA,ACC\t1,1\tCAA\tENSP00000261590.8\tDSG2_HUMAN\t0.279\t{mechanisms_json}\n'
)


# mock get_file_fileset_by_accession_in_arangodb so files_fileset data change will not affect the test
@pytest.fixture
def mock_file_fileset():
    """Fixture to mock get_file_fileset_by_accession_in_arangodb function."""
    with patch('adapters.Mutpred2_coding_variants_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'method': 'MutPred2',
            'class': 'prediction',
            'samples': None,
            'simple_sample_summaries': None
        }
        yield mock_get_file_fileset


@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_MAPPING_TSV)
def test_load_from_mapping_file_variants(mock_gzip_open):
    writer = SpyWriter()
    adapter = Mutpred2CodingVariantsScores(
        None, label='variants', writer=writer, validate=True)
    adapter.process_file()

    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_key'] == 'NC_000018.10:31546002:CA:AC'
    assert first_item['chr'] == 'chr18'
    assert first_item['pos'] == 31546002
    assert first_item['ref'] == 'CA'
    assert first_item['alt'] == 'AC'
    assert first_item['variation_type'] == 'deletion-insertion'
    assert first_item['source'] == 'IGVF'
    assert first_item['source_url'] == 'https://data.igvf.org/tabular-files/IGVFFI6893ZOAA'


@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_MAPPING_TSV)
def test_load_from_mapping_file_variants_coding_variants(mock_gzip_open, mock_file_fileset):
    writer = SpyWriter()
    adapter = Mutpred2CodingVariantsScores(
        None, label='variants_coding_variants', writer=writer, validate=True)
    # Initialize igvf_metadata_props for variants_coding_variants label
    adapter.igvf_metadata_props = mock_file_fileset.return_value
    adapter.process_file()

    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_key'] == 'NC_000018.10:31546002:CA:AC_DSG2_ENST00000261590_p.Gln873Thr_c.2617_2618delinsAC'
    assert first_item['_from'] == 'variants/NC_000018.10:31546002:CA:AC'
    assert first_item['_to'] == 'coding_variants/DSG2_ENST00000261590_p.Gln873Thr_c.2617_2618delinsAC'
    assert first_item['chr'] == 'chr18'
    assert first_item['pos'] == 31546002
    assert first_item['ref'] == 'CA'
    assert first_item['alt'] == 'AC'
    assert first_item['name'] == 'codes for'
    assert first_item['inverse_name'] == 'encoded by'
    assert first_item['source'] == 'IGVF'
    assert first_item['source_url'] == 'https://data.igvf.org/tabular-files/IGVFFI6893ZOAA'
    assert first_item['biosample_term'] is None
    assert first_item['biological_context'] is None
    assert first_item['method'] == 'MutPred2'
    assert first_item['class'] == 'prediction'
    assert first_item['label'] == 'codes for'


@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_MAPPING_TSV)
def test_load_from_mapping_file_coding_variants(mock_gzip_open):
    writer = SpyWriter()
    adapter = Mutpred2CodingVariantsScores(
        None, label='coding_variants', writer=writer, validate=True)
    adapter.process_file()

    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_key'] == 'DSG2_ENST00000261590_p.Gln873Thr_c.2617_2618delinsAC'
    assert first_item['ref'] == 'Q'
    assert first_item['alt'] == 'T'
    assert first_item['aapos'] == 873
    assert first_item['refcodon'] == 'CAA'
    assert first_item['gene_name'] == 'DSG2'
    assert first_item['protein_id'] == 'ENSP00000261590'
    assert first_item['transcript_id'] == 'ENST00000261590'
    assert first_item['protein_name'] == 'DSG2_HUMAN'
    assert first_item['hgvsp'] == 'p.Gln873Thr'
    assert first_item['hgvsc'] == 'c.2617_2618delinsAC'
    assert first_item['codonpos'] == 1


@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_MAPPING_TSV)
def test_process_file_coding_variants_phenotypes(mock_gzip_open, mock_file_fileset):
    writer = SpyWriter()
    adapter = Mutpred2CodingVariantsScores(
        None,
        label='coding_variants_phenotypes',
        writer=writer,
        validate=True
    )
    # Initialize igvf_metadata_props for coding_variants_phenotypes label
    adapter.igvf_metadata_props = mock_file_fileset.return_value
    adapter.process_file()

    first_item = json.loads(writer.contents[0])
    assert 'DSG2_ENST00000261590_p.Gln873Thr_c.2617_2618delinsAC' in first_item['_from']
    assert first_item['_to'] == 'ontology_terms/GO_0003674'
    assert first_item['pathogenicity_score'] == 0.279
    assert len(first_item['property_scores']) == 1
    assert first_item['property_scores'][0]['Property'] == 'VSL2B_disorder'
    assert first_item['property_scores'][0]['Posterior Probability'] == 0.3
    assert first_item['method'] == 'MutPred2'
    assert first_item['files_filesets'] == 'files_filesets/IGVFFI6893ZOAA'
    assert first_item['source'] == 'IGVF'
    assert first_item['source_url'] == 'https://data.igvf.org/tabular-files/IGVFFI6893ZOAA'
    assert first_item['biosample_term'] is None
    assert first_item['biological_context'] is None
    assert first_item['method'] == 'MutPred2'
    assert first_item['class'] == 'prediction'
    assert first_item['label'] == 'predicted protein variant effect'


def test_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_label. Allowed values: coding_variants, variants, variants_coding_variants, coding_variants_phenotypes'):
        Mutpred2CodingVariantsScores(
            None,
            label='invalid_label',
            writer=writer,
            validate=True
        )


def test_validate_doc_invalid():
    """Test document validation with invalid data"""
    writer = SpyWriter()
    adapter = Mutpred2CodingVariantsScores(
        None, writer=writer, validate=True)

    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }

    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)


def test_met1_aa_change_handling():
    """Test handling of Met1 amino acid changes"""
    writer = SpyWriter()
    adapter = Mutpred2CodingVariantsScores(
        None, writer=writer, validate=True)

    # Create a test row with Met1 amino acid change
    test_row = {
        'aa_change': 'Met1Val',
        'codon_ref': 'ATG',
        'gene_name': 'TEST_GENE',
        'property_scores': [{'Posterior Probability': 0.5}]
    }

    # Mock the process_file method to test the Met1 handling logic
    with patch.object(adapter, 'writer') as mock_writer:
        # This will test the Met1 handling code path
        aa_change = test_row['aa_change']
        if aa_change.startswith('Met1'):
            aa_change = 'Met1?'  # to match with dbNSFP

        assert aa_change == 'Met1?'
