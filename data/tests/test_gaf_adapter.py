import json
import pytest
from adapters.gaf_adapter import GAF
from adapters.writer import SpyWriter


def test_gaf_adapter_human():
    writer = SpyWriter()
    adapter = GAF(filepath='./samples/goa_human_sample.gaf.gz',
                  gaf_type='human', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert first_item['organism'] == 'Homo sapiens'
    assert first_item['source'] == 'Gene Ontology'
    assert first_item['source_url'] == GAF.SOURCES['human']


def test_gaf_adapter_mouse():
    writer = SpyWriter()
    adapter = GAF(filepath='./samples/mgi_sample.gaf.gz',
                  gaf_type='mouse', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert first_item['organism'] == 'Mus musculus'
    assert first_item['source'] == 'Gene Ontology'
    assert first_item['source_url'] == GAF.SOURCES['mouse']


def test_gaf_adapter_rna():
    writer = SpyWriter()
    adapter = GAF(filepath='./samples/goa_human_rna.gaf.gz',
                  gaf_type='rna', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert first_item['organism'] == 'Homo sapiens'
    assert first_item['source'] == 'Gene Ontology'
    assert first_item['source_url'] == GAF.SOURCES['rna']


def test_gaf_adapter_invalid_type():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid type. Allowed values: human, human_isoform, mouse, rna'):
        GAF(filepath='./samples/goa_human_sample.gaf.gz',
            gaf_type='invalid_type', writer=writer)


def test_gaf_adapter_load_rnacentral_mapping():
    writer = SpyWriter()
    adapter = GAF(filepath='./samples/goa_human_rna.gaf.gz',
                  gaf_type='rna', writer=writer)
    adapter.load_rnacentral_mapping()
    assert hasattr(adapter, 'rnacentral_mapping')
    assert isinstance(adapter.rnacentral_mapping, dict)
    assert len(adapter.rnacentral_mapping) > 0


def test_gaf_adapter_load_mouse_mgi_to_uniprot():
    writer = SpyWriter()
    adapter = GAF(filepath='./samples/mgi_sample.gaf.gz',
                  gaf_type='mouse', writer=writer)
    adapter.load_mouse_mgi_to_uniprot()
    assert hasattr(adapter, 'mouse_mgi_mapping')
    assert isinstance(adapter.mouse_mgi_mapping, dict)
    assert len(adapter.mouse_mgi_mapping) > 0
