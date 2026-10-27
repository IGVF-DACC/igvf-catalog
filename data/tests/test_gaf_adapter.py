import json
import pytest
from unittest.mock import patch
from adapters.gaf_adapter import GAF
from adapters.ontology_term_validator import OntologyTermValidator
from adapters.writer import SpyWriter


@pytest.fixture(autouse=True)
def mock_file_fileset():
    with patch('adapters.gaf_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get:
        mock_get.return_value = {
            'class': 'biological relationship',
            'method': None
        }
        yield mock_get


@pytest.fixture
def mock_protein_map():
    with patch('adapters.protein_map.get_protein_map_from_arangodb') as mock_get:
        mock_get.return_value = {
            'A0A024RBG1': ['ENSP00000263100'],
            'MGI:1915609': ['ENSMUSP00000000001'],
        }
        yield mock_get


@pytest.fixture
def mock_ontology_term_validator():
    with patch('adapters.gaf_adapter.OntologyTermValidator') as MockValidator:
        MockValidator.normalize_term_key = staticmethod(
            OntologyTermValidator.normalize_term_key)
        mock_validator = MockValidator.return_value
        mock_validator.validate.return_value = True
        mock_validator.ensure.return_value = True
        mock_validator.resolve.side_effect = (
            lambda term_key: OntologyTermValidator.normalize_term_key(term_key)
        )
        yield mock_validator


def test_gaf_adapter_human(mock_file_fileset, mock_protein_map, mock_ontology_term_validator):
    writer = SpyWriter()
    adapter = GAF(filepath='./tests/fixtures/goa_human_sample.gaf.gz',
                  label='human', writer=writer, validate=True)
    adapter.file_accession = 'IGVFFI4899LHFM'
    adapter.process_file()
    mock_file_fileset.assert_called_once_with('IGVFFI4899LHFM')
    _, preload_kwargs = mock_ontology_term_validator.preload.call_args
    assert preload_kwargs.get('resolve_via_ols') is True
    mock_protein_map.assert_called_once_with(
        field='uniprot_ids',
        organism='Homo sapiens',
        dbxref_name=None,
    )
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_from'] == 'proteins/ENSP00000263100'
    assert '_to' in first_item
    assert first_item['organism'] == 'Homo sapiens'
    assert first_item['source'] == 'Gene Ontology'
    assert first_item['source_url'] == GAF.SOURCES['human']
    assert first_item['class'] == 'biological relationship'
    assert first_item['method'] is None
    assert first_item['label'] is None
    assert first_item['files_filesets'] == 'files_filesets/IGVFFI4899LHFM'


def test_gaf_adapter_uses_remapped_go_term(
        mock_file_fileset, mock_protein_map, mock_ontology_term_validator):
    mock_ontology_term_validator.resolve.side_effect = (
        lambda term_key: 'GO_0003674'
        if OntologyTermValidator.normalize_term_key(term_key) == 'GO_0003723'
        else OntologyTermValidator.normalize_term_key(term_key)
    )
    writer = SpyWriter()
    adapter = GAF(filepath='./samples/goa_human_sample.gaf.gz',
                  label='human', writer=writer, validate=False)
    adapter.file_accession = 'IGVFFI4899LHFM'
    adapter.process_file()

    docs = [json.loads(c)
            for c in writer.contents if c.strip().startswith('{')]
    remapped = [d for d in docs if d['gene_product_id'] == 'A0A024RBG1'
                and d['_to'] == 'ontology_terms/GO_0003674']
    assert remapped
    assert all(d['go_id'] == 'GO:0003674' for d in remapped)


def test_gaf_adapter_mouse(mock_file_fileset, mock_protein_map, mock_ontology_term_validator):
    writer = SpyWriter()
    adapter = GAF(filepath='./tests/fixtures/mgi_sample.gaf.gz',
                  label='mouse', writer=writer, validate=True)
    adapter.file_accession = 'IGVFFI0062EMMC'
    adapter.process_file()
    mock_file_fileset.assert_called_once_with('IGVFFI0062EMMC')
    mock_protein_map.assert_called_once_with(
        field='uniprot_ids',
        organism='Mus musculus',
        dbxref_name='MGI',
    )
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_from'] == 'proteins/ENSMUSP00000000001'
    assert '_to' in first_item
    assert first_item['organism'] == 'Mus musculus'
    assert first_item['source'] == 'Gene Ontology'
    assert first_item['source_url'] == GAF.SOURCES['mouse']
    assert first_item['class'] == 'biological relationship'
    assert first_item['method'] is None
    assert first_item['label'] is None
    assert first_item['files_filesets'] == 'files_filesets/IGVFFI0062EMMC'


def test_gaf_adapter_rna(mock_file_fileset, mock_ontology_term_validator):
    writer = SpyWriter()
    adapter = GAF(filepath='./tests/fixtures/goa_human_rna.gaf.gz',
                  label='rna', writer=writer, validate=True,
                  reference_filepath='./data_loading_support_files/rnacentral_ensembl_gencode.tsv.gz')
    adapter.file_accession = 'IGVFFI6197DHVQ'
    adapter.process_file()
    mock_file_fileset.assert_called_once_with('IGVFFI6197DHVQ')
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_from'].startswith('transcripts/')
    assert '_to' in first_item
    assert first_item['organism'] == 'Homo sapiens'
    assert first_item['source'] == 'Gene Ontology'
    assert first_item['source_url'] == GAF.SOURCES['rna']
    assert first_item['class'] == 'biological relationship'
    assert first_item['method'] is None
    assert first_item['label'] is None
    assert first_item['files_filesets'] == 'files_filesets/IGVFFI6197DHVQ'


def test_gaf_adapter_invalid_type():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_type. Allowed values: human, human_isoform, mouse, rna'):
        GAF(filepath='./tests/fixtures/goa_human_sample.gaf.gz',
            label='invalid_type', writer=writer, validate=True)


def test_gaf_adapter_rna_requires_reference_filepath():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='reference_filepath is required'):
        GAF(filepath='./samples/goa_human_rna.gaf.gz',
            label='rna', writer=writer, validate=False)


def test_gaf_adapter_load_rnacentral_mapping():
    writer = SpyWriter()
    adapter = GAF(filepath='./tests/fixtures/goa_human_rna.gaf.gz',
                  label='rna', writer=writer, validate=True,
                  reference_filepath='./data_loading_support_files/rnacentral_ensembl_gencode.tsv.gz')
    adapter.load_rnacentral_mapping()
    assert hasattr(adapter, 'rnacentral_mapping')
    assert isinstance(adapter.rnacentral_mapping, dict)
    assert len(adapter.rnacentral_mapping) > 0


def test_gaf_adapter_validate_doc_invalid():
    writer = SpyWriter()
    adapter = GAF(filepath='./tests/fixtures/goa_human_sample.gaf.gz',
                  label='human', writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)


def test_gaf_adapter_initialization():
    adapter = GAF(
        filepath='./tests/fixtures/goa_human_sample.gaf.gz', label='human')
    assert adapter.filepath == './tests/fixtures/goa_human_sample.gaf.gz'
    assert adapter.label == 'human'
    assert adapter.file_accession == 'goa_human_sample'
