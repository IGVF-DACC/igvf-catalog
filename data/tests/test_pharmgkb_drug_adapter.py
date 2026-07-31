import pytest
import json
import tarfile
from unittest.mock import patch
from adapters.pharmgkb_drug_adapter import PharmGKB
from adapters.writer import SpyWriter


FILE_ACCESSION = 'IGVFFI8835SMSP'
DRUG_FILE_ACCESSION = 'IGVFFI2997DUKO'
SAMPLE_DIR = './samples/pharmGKB'


@pytest.fixture
def filepath(tmp_path):
    archive_filepath = tmp_path / f'{FILE_ACCESSION}.tar.gz'
    with tarfile.open(archive_filepath, 'w:gz') as archive:
        archive.add(SAMPLE_DIR, arcname='.')
    return str(archive_filepath)


@pytest.fixture
def mock_file_fileset():
    """Mock get_file_fileset_by_accession_in_arangodb so ArangoDB is not required."""
    with patch('adapters.pharmgkb_drug_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'class': 'observed data',
            'method': 'PharmGKB'
        }
        yield mock_get_file_fileset


@pytest.fixture
def reference_kwargs():
    # Use full support tables for edge labels so sample annotation rows resolve
    return {
        'drug_reference_filepath': './data_loading_support_files/IGVFFI2997DUKO.pharmGKB_chemicals.tsv',
        'variant_reference_filepath': './data_loading_support_files/pharmGKB_variants.tsv',
        'study_reference_filepath': './data_loading_support_files/pharmGKB_study_parameters.tsv',
        'gene_reference_filepath': './data_loading_support_files/pharmGKB_genes.tsv',
    }


@pytest.fixture
def drug_filepath(reference_kwargs):
    return reference_kwargs['drug_reference_filepath']


@pytest.fixture
def spy_writer():
    return SpyWriter()


def test_drug_label(drug_filepath, spy_writer, mocker, mock_file_fileset):
    mocker.patch('adapters.pharmgkb_drug_adapter.build_variant_id_from_hgvs',
                 return_value='fake_variant_id')
    pharmgkb = PharmGKB(filepath=drug_filepath, label='drug',
                        writer=spy_writer, validate=True)
    assert pharmgkb.label == 'drug'
    assert pharmgkb.file_accession == DRUG_FILE_ACCESSION

    pharmgkb.process_file()

    assert len(spy_writer.contents) > 0
    first_item = json.loads(spy_writer.contents[0])
    assert isinstance(first_item, dict)
    assert set(first_item.keys()) == {
        '_key', 'name', 'drug_ontology_terms', 'source', 'source_url', 'class', 'method', 'files_filesets'}
    assert first_item['source'] == 'pharmGKB'
    assert first_item['source_url'].startswith(
        'https://www.pharmgkb.org/chemical/')
    assert first_item['_key'] == 'PA166250381'
    assert first_item['name'] == '10-desmethyl alpha-dihydrotetrabenazine'
    assert first_item['drug_ontology_terms'] == []
    assert first_item['class'] == 'observed data'
    assert first_item['method'] == 'PharmGKB'
    assert first_item['files_filesets'] == f'files_filesets/{DRUG_FILE_ACCESSION}'


def test_variant_drug_label(filepath, reference_kwargs, spy_writer, mocker, mock_file_fileset):
    mocker.patch('adapters.pharmgkb_drug_adapter.build_variant_id_from_hgvs',
                 return_value='fake_variant_id')
    pharmgkb = PharmGKB(filepath=filepath, label='variant_drug',
                        writer=spy_writer, validate=True, **reference_kwargs)
    assert pharmgkb.label == 'variant_drug'
    assert pharmgkb.file_accession == FILE_ACCESSION

    pharmgkb.process_file()

    assert len(spy_writer.contents) > 0
    first_item = json.loads(spy_writer.contents[0])
    assert isinstance(first_item, dict)
    assert set(first_item.keys()) == {'_key', '_from', '_to', 'gene_symbol', 'pmid',
                                      'study_parameters', 'phenotype_categories', 'name', 'inverse_name', 'source', 'source_url',
                                      'class', 'method', 'files_filesets'}
    assert first_item['_from'].startswith('variants/')
    assert first_item['_to'].startswith('drugs/')
    assert first_item['source'] == 'pharmGKB'
    assert first_item['source_url'].startswith(
        'https://www.pharmgkb.org/variantAnnotation/')
    assert first_item['class'] == 'observed data'
    assert first_item['method'] == 'PharmGKB'
    assert first_item['files_filesets'] == f'files_filesets/{FILE_ACCESSION}'


def test_variant_drug_gene_label(filepath, reference_kwargs, spy_writer, mocker, mock_file_fileset):
    mocker.patch('adapters.pharmgkb_drug_adapter.build_variant_id_from_hgvs',
                 return_value='fake_variant_id')
    pharmgkb = PharmGKB(filepath=filepath, label='variant_drug_gene',
                        writer=spy_writer, validate=True, **reference_kwargs)
    assert pharmgkb.label == 'variant_drug_gene'

    pharmgkb.process_file()

    assert len(spy_writer.contents) > 0
    first_item = json.loads(spy_writer.contents[0])
    assert isinstance(first_item, dict)
    assert set(first_item.keys()) == {
        '_key', '_from', '_to', 'name', 'inverse_name', 'gene_symbol', 'source', 'source_url',
        'class', 'method', 'files_filesets'}
    assert first_item['_from'].startswith('variants_drugs/')
    assert first_item['_to'].startswith('genes/')
    assert first_item['source'] == 'pharmGKB'
    assert first_item['source_url'].startswith(
        'https://www.pharmgkb.org/variantAnnotation/')
    assert first_item['class'] == 'observed data'
    assert first_item['method'] == 'PharmGKB'
    assert first_item['files_filesets'] == f'files_filesets/{FILE_ACCESSION}'


def test_variant_drug_requires_reference_filepaths(filepath, spy_writer):
    with pytest.raises(ValueError, match='drug_reference_filepath'):
        PharmGKB(filepath=filepath, label='variant_drug', writer=spy_writer)


def test_invalid_label(filepath, spy_writer):
    with pytest.raises(ValueError):
        PharmGKB(filepath=filepath, label='invalid_label', writer=spy_writer)


def test_validate_doc_invalid(filepath, reference_kwargs, spy_writer):
    pharmgkb = PharmGKB(filepath=filepath, label='variant_drug',
                        writer=spy_writer, validate=True, **reference_kwargs)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        pharmgkb.validate_doc(invalid_doc)
