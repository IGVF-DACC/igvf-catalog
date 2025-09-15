import json
import pytest
from adapters.ebi_complex_adapter import EBIComplex
from adapters.writer import SpyWriter


def test_ebi_complex_initialization():
    sample_filepath = './samples/EBI_complex_example.tsv'
    for label in EBIComplex.ALLOWED_LABELS:
        writer = SpyWriter()
        adapter = EBIComplex(sample_filepath, label=label, writer=writer)
        assert adapter.filepath == sample_filepath
        assert adapter.label == label
        assert adapter.dataset == label
        assert adapter.dry_run == True
        assert adapter.writer == writer

        if label == 'complex':
            assert adapter.type == 'node'
        else:
            assert adapter.type == 'edge'


def test_ebi_complex_invalid_label():
    sample_filepath = './samples/EBI_complex_example.tsv'
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label. Allowed values: complex,complex_protein,complex_term'):
        EBIComplex(sample_filepath, label='invalid_label', writer=writer)


def test_ebi_complex_process_file():
    sample_filepath = './samples/EBI_complex_example.tsv'
    for label in EBIComplex.ALLOWED_LABELS:
        writer = SpyWriter()
        adapter = EBIComplex(sample_filepath, label=label,
                             writer=writer, validate=True)
        adapter.process_file()

        # Check that some data was written
        assert len(writer.contents) > 0

        # Check the structure of the first item
        first_item = json.loads(writer.contents[0])
        if label == 'complex':
            assert '_key' in first_item
            assert 'name' in first_item
        elif label == 'complex_protein':
            assert '_key' in first_item
            assert '_from' in first_item
            assert '_to' in first_item
        elif label == 'complex_term':
            assert '_key' in first_item
            assert '_from' in first_item
            assert '_to' in first_item


def test_ebi_complex_get_chain_id():
    adapter = EBIComplex('./samples/EBI_complex_example.tsv', label='complex')

    assert adapter.get_chain_id('P12345') == None
    assert adapter.get_chain_id('P12345-1') == None
    assert adapter.get_chain_id('P12345-PRO_0000123456') == 'PRO_0000123456'


def test_ebi_complex_get_isoform_id():
    adapter = EBIComplex('./samples/EBI_complex_example.tsv', label='complex')

    assert adapter.get_isoform_id('P12345') == None
    assert adapter.get_isoform_id('P12345-1') == '1'
    assert adapter.get_isoform_id('P12345-PRO_0000123456') == None


def test_ebi_complex_load_linked_features_dict():
    sample_filepath = './samples/EBI_complex_example.tsv'
    writer = SpyWriter()
    adapter = EBIComplex(
        sample_filepath, label='complex_protein', writer=writer)
    adapter.load_linked_features_dict()
    assert hasattr(adapter, 'linked_features_dict')
    assert isinstance(adapter.linked_features_dict, dict)


def test_ebi_complex_load_subontologies():
    sample_filepath = './samples/EBI_complex_example.tsv'
    writer = SpyWriter()
    adapter = EBIComplex(sample_filepath, label='complex', writer=writer)
    adapter.load_subontologies()
    assert hasattr(adapter, 'subontologies')
    assert isinstance(adapter.subontologies, dict)


def test_ebi_complex_validate_doc_invalid():
    sample_filepath = './samples/EBI_complex_example.tsv'
    writer = SpyWriter()
    adapter = EBIComplex(sample_filepath, label='complex',
                         writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
