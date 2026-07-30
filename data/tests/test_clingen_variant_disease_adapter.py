import csv
import json
from unittest.mock import patch
import pytest

from adapters.clingen_variant_disease_adapter import ClinGen
from adapters.writer import SpyWriter

SAMPLE_PATH = './samples/clinGen_variant_pathogenicity_example.csv'
SAMPLE_VARIANT_KEY = 'NC_000012.12:102917129:T:C'


def _sample_hgvs_map():
    """Build hgvs -> [key] for every GRCh38 genomic HGVS in the sample file."""
    hgvs_map = {}
    with open(SAMPLE_PATH) as f:
        for row in csv.DictReader(f):
            hgvs = ClinGen.extract_grch38_genomic_hgvs(
                row.get('HGVS Expressions'))
            if hgvs:
                # Use a deterministic SPDI-like key for tests; first row matches real catalog key.
                if hgvs == 'NC_000012.12:g.102917130T>C':
                    hgvs_map[hgvs] = [SAMPLE_VARIANT_KEY]
                else:
                    hgvs_map[hgvs] = [f'test_key_for_{hgvs}']
    return hgvs_map


@pytest.fixture
def mock_file_fileset():
    with patch('adapters.clingen_variant_disease_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get:
        mock_get.return_value = {
            'class': 'biological relationship',
            'method': 'ClinGen'
        }
        yield mock_get


@pytest.fixture
def mock_variant_lookup():
    hgvs_map = _sample_hgvs_map()

    def _side_effect(identifiers, check_by='ca_id', chunk_size=500):
        if check_by == 'hgvs':
            return {i: hgvs_map[i] for i in identifiers if i in hgvs_map}
        if check_by == 'ca_id':
            return {}
        return {}

    with patch(
        'adapters.clingen_variant_disease_adapter.bulk_query_variant_keys_by_identifier',
        side_effect=_side_effect,
    ) as mock_bulk:
        yield mock_bulk


def test_clingen_adapter_variant_disease(mock_file_fileset, mock_variant_lookup):
    writer = SpyWriter()
    with patch('adapters.clingen_variant_disease_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True

        adapter = ClinGen(filepath=SAMPLE_PATH,
                          label='variant_disease', writer=writer, validate=True)
        adapter.file_accession = 'IGVFFI5852GYTT'
        adapter.process_file()

        mock_file_fileset.assert_called_once_with('IGVFFI5852GYTT')
        assert mock_variant_lookup.called
        assert len(writer.contents) > 0
        first_item = json.loads(writer.contents[0])

        assert '_key' in first_item
        assert first_item['_from'] == f'variants/{SAMPLE_VARIANT_KEY}'
        assert '_to' in first_item
        assert first_item['name'] == 'associated with'
        assert first_item['inverse_name'] == 'associated with'
        assert 'gene_id' in first_item
        assert 'assertion' in first_item
        assert 'pmids' in first_item
        assert first_item['source'] == 'ClinGen'
        assert first_item['source_url'] == 'https://search.clinicalgenome.org/kb/downloads'
        assert first_item['class'] == 'biological relationship'
        assert first_item['method'] == 'ClinGen'
        assert first_item['label'] == first_item['method']
        assert first_item['files_filesets'] == 'files_filesets/IGVFFI5852GYTT'


def test_clingen_adapter_variant_disease_gene(mock_file_fileset, mock_variant_lookup):
    writer = SpyWriter()
    with patch('adapters.clingen_variant_disease_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True
        adapter = ClinGen(filepath=SAMPLE_PATH,
                          label='variant_disease_gene', writer=writer, validate=True)
        adapter.file_accession = 'IGVFFI5852GYTT'
        adapter.process_file()

        mock_file_fileset.assert_called_once_with('IGVFFI5852GYTT')
        assert len(writer.contents) > 0
        first_item = json.loads(writer.contents[0])

        assert '_key' in first_item
        assert '_from' in first_item
        assert '_to' in first_item
        assert first_item['name'] == 'associated with'
        assert first_item['inverse_name'] == 'associated with'
        assert 'inheritance_mode' in first_item
        assert first_item['source'] == 'ClinGen'
        assert first_item['source_url'] == 'https://search.clinicalgenome.org/kb/downloads'
        assert first_item['class'] == 'biological relationship'
        assert first_item['method'] == 'ClinGen'
        assert first_item['label'] == first_item['method']
        assert first_item['files_filesets'] == 'files_filesets/IGVFFI5852GYTT'


def test_clingen_adapter_invalid_label():
    with pytest.raises(ValueError, match='Invalid label: invalid_label. Allowed values: variant_disease, variant_disease_gene'):
        ClinGen(filepath=SAMPLE_PATH, label='invalid_label')


def test_clingen_adapter_initialization():
    with patch('adapters.clingen_variant_disease_adapter.GeneValidator') as MockGeneValidator:
        adapter = ClinGen(filepath=SAMPLE_PATH, label='variant_disease')
        assert adapter.filepath == SAMPLE_PATH
        assert adapter.label == 'variant_disease'
        assert adapter.gene_validator is not None
        assert adapter.file_accession == 'clinGen_variant_pathogenicity_example'


def test_clingen_adapter_validate_doc_invalid():
    writer = SpyWriter()
    adapter = ClinGen(filepath=SAMPLE_PATH,
                      label='variant_disease', writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)


def test_clingen_adapter_invalid_gene_id(mock_file_fileset, mock_variant_lookup):
    writer = SpyWriter()

    with patch('adapters.clingen_variant_disease_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = False

        adapter = ClinGen(filepath=SAMPLE_PATH,
                          label='variant_disease', writer=writer, validate=True)
        adapter.file_accession = 'IGVFFI5852GYTT'
        adapter.process_file()
        assert len(writer.contents) == 0


def test_clingen_adapter_skips_unmatched_variants(mock_file_fileset):
    writer = SpyWriter()

    def _no_matches(identifiers, check_by='ca_id', chunk_size=500):
        return {}

    with patch('adapters.clingen_variant_disease_adapter.GeneValidator') as MockGeneValidator, \
            patch('adapters.clingen_variant_disease_adapter.bulk_query_variant_keys_by_identifier', side_effect=_no_matches):
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True

        adapter = ClinGen(filepath=SAMPLE_PATH,
                          label='variant_disease', writer=writer, validate=True)
        adapter.file_accession = 'IGVFFI5852GYTT'
        adapter.process_file()
        assert len(writer.contents) == 0


def test_extract_grch38_genomic_hgvs():
    exprs = (
        'NM_000277.2:c.1A>G, NC_000012.12:g.102917130T>C, '
        'NC_000012.11:g.103310908T>C'
    )
    assert ClinGen.extract_grch38_genomic_hgvs(
        exprs) == 'NC_000012.12:g.102917130T>C'
    assert ClinGen.extract_grch38_genomic_hgvs('') is None
    assert ClinGen.normalize_identifier('-') is None
    assert ClinGen.normalize_identifier('CA114360') == 'CA114360'
