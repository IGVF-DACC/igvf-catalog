import json
import pytest
from adapters.uniprot_protein_adapter import UniprotProtein
from adapters.writer import SpyWriter


def test_uniprot_protein_adapter_initialization():
    writer = SpyWriter()
    adapter = UniprotProtein(filepath='./samples/uniprot_sprot_human_sample.dat.gz',
                             source='UniProtKB/Swiss-Prot',
                             writer=writer)

    assert adapter.filepath == './samples/uniprot_sprot_human_sample.dat.gz'
    assert adapter.dataset == 'UniProtKB_protein'
    assert adapter.label == 'UniProtKB_protein'
    assert adapter.source == 'UniProtKB/Swiss-Prot'
    assert adapter.taxonomy_id == ['9606']
    assert adapter.organism == 'Homo sapiens'
    assert adapter.dry_run == True
    assert adapter.writer == writer


def test_uniprot_protein_adapter_process_file():
    writer = SpyWriter()
    adapter = UniprotProtein(filepath='./samples/uniprot_sprot_human_sample.dat.gz',
                             source='UniProtKB/Swiss-Prot',
                             writer=writer)

    adapter.process_file()

    assert len(writer.contents) > 0
    first_item = json.loads(writer.contents[0])

    assert '_key' in first_item
    assert 'name' in first_item
    assert 'organism' in first_item
    assert 'dbxrefs' in first_item
    assert 'source' in first_item
    assert 'source_url' in first_item

    assert first_item['organism'] == 'Homo sapiens'
    assert first_item['source'] == 'UniProtKB/Swiss-Prot'
    assert first_item['source_url'] == 'https://www.uniprot.org/help/downloads'
    assert isinstance(first_item['dbxrefs'], list)


def test_uniprot_protein_adapter_mouse():
    writer = SpyWriter()
    adapter = UniprotProtein(filepath='./samples/uniprot_sprot_human_sample.dat.gz',
                             source='UniProtKB/Swiss-Prot',
                             taxonomy_id='10090',
                             writer=writer)

    assert adapter.taxonomy_id == ['10090']
    assert adapter.organism == 'Mus musculus'


def test_uniprot_protein_adapter_trembl():
    writer = SpyWriter()
    adapter = UniprotProtein(filepath='./samples/uniprot_trembl_human_sample.dat.gz',
                             source='UniProtKB/TrEMBL',
                             writer=writer)

    assert adapter.source == 'UniProtKB/TrEMBL'


def test_uniprot_protein_adapter_invalid_source():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid source. Allowed values: UniProtKB/Swiss-Prot, UniProtKB/TrEMBL'):
        UniprotProtein(filepath='./samples/uniprot_sprot_human_sample.dat.gz',
                       source='Invalid_Source',
                       writer=writer)


def test_uniprot_protein_adapter_invalid_taxonomy():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid taxonomy id. Allowed values: 9606, 10090'):
        UniprotProtein(filepath='./samples/uniprot_sprot_human_sample.dat.gz',
                       source='UniProtKB/Swiss-Prot',
                       taxonomy_id='12345',
                       writer=writer)


def test_uniprot_protein_adapter_dry_run():
    writer = SpyWriter()
    adapter = UniprotProtein(filepath='./samples/uniprot_sprot_human_sample.dat.gz',
                             source='UniProtKB/Swiss-Prot',
                             dry_run=False,
                             writer=writer)

    assert adapter.dry_run == False


def test_uniprot_protein_adapter_get_dbxrefs():
    writer = SpyWriter()
    adapter = UniprotProtein(filepath='./samples/uniprot_sprot_human_sample.dat.gz',
                             source='UniProtKB/Swiss-Prot',
                             writer=writer)

    test_cross_references = [
        ('EMBL', 'X12345', 'Y67890', '-'),
        ('RefSeq', 'NP_001234.1', 'NP_005678.2'),
        ('Ensembl', 'ENST00000123456', 'ENSP00000234567'),
        ('MANE-Select', 'ENST00000987654.1', 'NM_001122334.2'),
        ('Other', 'ID12345')
    ]

    dbxrefs = adapter.get_dbxrefs(test_cross_references)

    assert len(dbxrefs) == 9
    assert {'name': 'EMBL', 'id': 'X12345'} in dbxrefs
    assert {'name': 'EMBL', 'id': 'Y67890'} in dbxrefs
    assert {'name': 'RefSeq', 'id': 'NP_001234.1'} in dbxrefs
    assert {'name': 'RefSeq', 'id': 'NP_005678.2'} in dbxrefs
    assert {'name': 'Ensembl', 'id': 'ENST00000123456'} in dbxrefs
    assert {'name': 'Ensembl', 'id': 'ENSP00000234567'} in dbxrefs
    assert {'name': 'MANE-Select', 'id': 'ENST00000987654.1'} in dbxrefs


def test_uniprot_protein_adapter_get_full_name():
    writer = SpyWriter()
    adapter = UniprotProtein(filepath='./samples/uniprot_sprot_human_sample.dat.gz',
                             source='UniProtKB/Swiss-Prot',
                             writer=writer)

    test_description = 'RecName: Full=Test protein; AltName: Full=Alternative name; Short=AN'
    full_name = adapter.get_full_name(test_description)

    assert full_name == 'Test protein'

    test_description_2 = 'SubName: Full=Uncharacterized protein'
    full_name_2 = adapter.get_full_name(test_description_2)

    assert full_name_2 == 'Uncharacterized protein'
