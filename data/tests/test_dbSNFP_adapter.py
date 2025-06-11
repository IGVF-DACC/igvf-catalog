import json
from adapters.dbSNFP_adapter import DbSNFP
from adapters.writer import SpyWriter


def test_dbSNFP_adapter_coding_variants():
    writer = SpyWriter()
    adapter = DbSNFP(
        filepath='./samples/dbNSFP4.5a_variant.chrY_sample', writer=writer)
    adapter.process_file()

    assert len(writer.contents) > 1
    first_item = json.loads(writer.contents[0])

    assert '_key' in first_item
    assert 'name' in first_item
    assert 'gene_name' in first_item
    assert 'transcript_id' in first_item
    assert 'source' in first_item
    assert first_item['source'] == 'dbSNFP 5.1a'


def test_dbSNFP_adapter_variants_coding_variants():
    writer = SpyWriter()
    adapter = DbSNFP(filepath='./samples/dbNSFP4.5a_variant.chrY_sample',
                     collection='variants_coding_variants', writer=writer)
    adapter.process_file()

    assert len(writer.contents) > 1
    first_item = json.loads(writer.contents[0])

    assert '_from' in first_item
    assert '_to' in first_item
    assert 'name' in first_item
    assert 'inverse_name' in first_item
    assert 'source' in first_item
    assert first_item['source'] == 'dbSNFP 5.1a'


def test_dbSNFP_adapter_coding_variants_proteins():
    writer = SpyWriter()
    adapter = DbSNFP(filepath='./samples/dbNSFP4.5a_variant.chrY_sample',
                     collection='coding_variants_proteins', writer=writer)
    adapter.process_file()

    assert len(writer.contents) > 1
    first_item = json.loads(writer.contents[0])

    assert '_from' in first_item
    assert '_to' in first_item
    assert 'name' in first_item
    assert 'inverse_name' in first_item
    assert 'type' in first_item
    assert 'source' in first_item
    assert first_item['source'] == 'dbSNFP 5.1a'


def test_dbSNFP_adapter_multiple_records():
    adapter = DbSNFP(filepath='./samples/dbNSFP4.5a_variant.chrY_sample')
    data_line = ['Y', '2786989', 'C', 'A', 'X', 'Y', '.', 'Y', '2655030', 'Y', '2715030', '205;206', 'SRY;SRY',
                 'ENSG00000184895;ENSG00000184895', 'ENST00000383070;ENST00000383070', 'ENSP00000372547;ENSP00000372547']

    assert adapter.multiple_records(data_line) == True


def test_dbSNFP_adapter_breakdown_line():
    adapter = DbSNFP(filepath='./samples/dbNSFP4.5a_variant.chrY_sample')
    original_data_line = ['Y', '2786989', 'C', 'A', 'X', 'Y', '.', 'Y', '2655030', 'Y', '2715030', '205;206', 'SRY;SRY',
                          'ENSG00000184895;ENSG00000184895', 'ENST00000383070;ENST00000383070', 'ENSP00000372547;ENSP00000372547']

    broken_down_lines = adapter.breakdown_line(original_data_line)

    assert len(broken_down_lines) == 2
    assert broken_down_lines[0][11] == '205'
    assert broken_down_lines[1][11] == '206'
    assert broken_down_lines[0][12] == 'SRY'
    assert broken_down_lines[1][12] == 'SRY'


def test_dbSNFP_adapter_initialization():
    adapter = DbSNFP(filepath='./samples/dbNSFP4.5a_variant.chrY_sample',
                     collection='custom_collection')

    assert adapter.filepath == './samples/dbNSFP4.5a_variant.chrY_sample'
    assert adapter.collection_name == 'custom_collection'
