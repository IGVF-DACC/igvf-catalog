import json

from adapters.clingen_variant_disease_adapter import ClinGen
from adapters.writer import SpyWriter


def test_clingen_adapter_variant_disease():
    writer = SpyWriter()
    adapter = ClinGen(filepath='./samples/clinGen_variant_pathogenicity_example.csv',
                      label='variant_disease', writer=writer)
    adapter.process_file()

    assert len(writer.contents) > 0
    first_item = json.loads(writer.contents[0])

    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert first_item['name'] == 'associated with'
    assert first_item['inverse_name'] == 'associated with'
    assert 'gene_id' in first_item
    assert 'assertion' in first_item
    assert 'pmids' in first_item
    assert first_item['source'] == 'ClinGen'
    assert first_item['source_url'] == 'https://search.clinicalgenome.org/kb/downloads'


def test_clingen_adapter_variant_disease_gene():
    writer = SpyWriter()
    adapter = ClinGen(filepath='./samples/clinGen_variant_pathogenicity_example.csv',
                      label='variant_disease_gene', writer=writer)
    adapter.process_file()

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


def test_clingen_adapter_invalid_label():
    try:
        ClinGen(filepath='./samples/clinGen_variant_pathogenicity_example.csv',
                label='invalid_label')
    except ValueError as e:
        assert str(e).startswith('Invalid label. Allowed values:')
    else:
        assert False, 'Expected ValueError was not raised'


def test_clingen_adapter_initialization():
    adapter = ClinGen(
        filepath='./samples/clinGen_variant_pathogenicity_example.csv', label='variant_disease')
    assert adapter.filepath == './samples/clinGen_variant_pathogenicity_example.csv'
    assert adapter.label == 'variant_disease'
    assert adapter.dataset == 'variant_disease'
    assert adapter.type == 'edge'
