import json
import pytest
from adapters.uniprot_adapter import Uniprot
from adapters.writer import SpyWriter


def test_uniprot_adapter_initialization():
    writer = SpyWriter()
    adapter = Uniprot(filepath='./samples/uniprot_sprot_human_sample.dat.gz',
                      label='UniProtKB_Translates_To',
                      source='UniProtKB/Swiss-Prot',
                      writer=writer)

    assert adapter.filepath == './samples/uniprot_sprot_human_sample.dat.gz'
    assert adapter.label == 'UniProtKB_Translates_To'
    assert adapter.source == 'UniProtKB/Swiss-Prot'
    assert adapter.organism == 'HUMAN'
    assert adapter.transcript_endpoint == 'transcripts/'
    assert adapter.ensembl_prefix == 'ENST'
    assert adapter.dataset == 'UniProtKB_Translates_To'
    assert adapter.dry_run == True
    assert adapter.type == 'edge'
    assert adapter.writer == writer


def test_uniprot_adapter_process_file():
    writer = SpyWriter()
    adapter = Uniprot(filepath='./samples/uniprot_sprot_human_sample.dat.gz',
                      label='UniProtKB_Translates_To',
                      source='UniProtKB/Swiss-Prot',
                      writer=writer)

    adapter.process_file()

    assert len(writer.contents) > 0
    first_item = json.loads(writer.contents[0])

    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert 'source' in first_item
    assert 'source_url' in first_item
    assert 'name' in first_item
    assert 'inverse_name' in first_item
    assert 'biological_process' in first_item

    assert first_item['source'] == 'UniProtKB/Swiss-Prot'
    assert first_item['source_url'] == 'https://www.uniprot.org/help/downloads'
    assert first_item['name'] == 'translates to'
    assert first_item['inverse_name'] == 'translated from'
    assert first_item['biological_process'] == 'ontology_terms/GO_0006412'
    assert first_item['_from'].startswith('transcripts/')
    assert first_item['_to'].startswith('proteins/')


def test_uniprot_adapter_translation_to():
    writer = SpyWriter()
    adapter = Uniprot(filepath='./samples/uniprot_sprot_human_sample.dat.gz',
                      label='UniProtKB_Translates_To',
                      source='UniProtKB/Swiss-Prot',
                      writer=writer)

    adapter.process_file()

    assert len(writer.contents) > 0
    first_item = json.loads(writer.contents[0])

    assert first_item['_from'].startswith('transcripts/')
    assert first_item['_to'].startswith('proteins/')


def test_uniprot_adapter_mouse():
    writer = SpyWriter()
    adapter = Uniprot(filepath='./samples/uniprot_sprot_human_sample.dat.gz',
                      label='UniProtKB_Translates_To',
                      source='UniProtKB/Swiss-Prot',
                      organism='MOUSE',
                      writer=writer)

    assert adapter.organism == 'MOUSE'
    assert adapter.transcript_endpoint == 'mm_transcripts/'
    assert adapter.ensembl_prefix == 'ENSMUST'


def test_uniprot_adapter_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label. Allowed values: UniProtKB_Translates_To'):
        Uniprot(filepath='./samples/uniprot_sprot_human_sample.dat.gz',
                label='Invalid_Label',
                source='UniProtKB/Swiss-Prot',
                writer=writer)


def test_uniprot_adapter_invalid_organism():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid organism. Allowed values: HUMAN, MOUSE'):
        Uniprot(filepath='./samples/uniprot_sprot_human_sample.dat.gz',
                label='UniProtKB_Translates_To',
                source='UniProtKB/Swiss-Prot',
                organism='UNICORN',
                writer=writer)
