import pytest
import json
from adapters.pharmgkb_drug_adapter import PharmGKB
from adapters.writer import SpyWriter


@pytest.fixture
def filepath():
    return './samples/pharmGKB'


@pytest.fixture
def spy_writer():
    return SpyWriter()


def test_drug_label(filepath, spy_writer, mocker):
    mocker.patch('adapters.pharmgkb_drug_adapter.build_variant_id_from_hgvs',
                 return_value='fake_variant_id')
    pharmgkb = PharmGKB(filepath=filepath, label='drug',
                        writer=spy_writer, validate=True)
    assert pharmgkb.label == 'drug'

    pharmgkb.process_file()

    assert len(spy_writer.contents) > 0
    first_item = json.loads(spy_writer.contents[0])
    assert isinstance(first_item, dict)
    assert set(first_item.keys()) == {
        '_key', 'name', 'drug_ontology_terms', 'source', 'source_url'}
    assert first_item['source'] == 'pharmGKB'
    assert first_item['source_url'].startswith(
        'https://www.pharmgkb.org/chemical/')


def test_variant_drug_label(filepath, spy_writer, mocker):
    mocker.patch('adapters.pharmgkb_drug_adapter.build_variant_id_from_hgvs',
                 return_value='fake_variant_id')
    pharmgkb = PharmGKB(filepath=filepath,
                        label='variant_drug', writer=spy_writer, validate=True)
    assert pharmgkb.label == 'variant_drug'

    pharmgkb.process_file()

    assert len(spy_writer.contents) > 0
    first_item = json.loads(spy_writer.contents[0])
    assert isinstance(first_item, dict)
    assert set(first_item.keys()) == {'_key', '_from', '_to', 'gene_symbol', 'pmid',
                                      'study_parameters', 'phenotype_categories', 'name', 'inverse_name', 'source', 'source_url'}
    assert first_item['_from'].startswith('variants/')
    assert first_item['_to'].startswith('drugs/')
    assert first_item['source'] == 'pharmGKB'
    assert first_item['source_url'].startswith(
        'https://www.pharmgkb.org/variantAnnotation/')


def test_variant_drug_gene_label(filepath, spy_writer, mocker):
    mocker.patch('adapters.pharmgkb_drug_adapter.build_variant_id_from_hgvs',
                 return_value='fake_variant_id')
    pharmgkb = PharmGKB(filepath=filepath,
                        label='variant_drug_gene', writer=spy_writer, validate=True)
    assert pharmgkb.label == 'variant_drug_gene'

    pharmgkb.process_file()

    assert len(spy_writer.contents) > 0
    first_item = json.loads(spy_writer.contents[0])
    assert isinstance(first_item, dict)
    assert set(first_item.keys()) == {
        '_key', '_from', '_to', 'name', 'inverse_name', 'gene_symbol', 'source', 'source_url'}
    assert first_item['_from'].startswith('variants_drugs/')
    assert first_item['_to'].startswith('genes/')
    assert first_item['source'] == 'pharmGKB'
    assert first_item['source_url'].startswith(
        'https://www.pharmgkb.org/variantAnnotation/')


def test_invalid_label(filepath, spy_writer):
    with pytest.raises(ValueError):
        PharmGKB(filepath=filepath, label='invalid_label', writer=spy_writer)


def test_validate_doc_invalid(filepath, spy_writer):
    pharmgkb = PharmGKB(filepath=filepath, label='variant_drug',
                        writer=spy_writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        pharmgkb.validate_doc(invalid_doc)
