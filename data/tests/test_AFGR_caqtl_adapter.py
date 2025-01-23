import json

from adapters.AFGR_caqtl_adapter import AFGRCAQtl
from adapters.writer import SpyWriter


def test_AFGR_caqtl_adapter_regulatory_region():
    writer = SpyWriter()
    adapter = AFGRCAQtl(filepath='./samples/AFGR/sorted.dist.hwe.af.AFR.caQTL.example.txt.gz',
                        label='genomic_element', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) == 200
    assert len(first_item) == 9
    assert first_item['_key'] == 'accessible_dna_element_1_906596_907043_GRCh38_AFGR'


def test_AFGR_caqtl_adapter_AFGR_caqtl():
    writer = SpyWriter()
    adapter = AFGRCAQtl(filepath='./samples/AFGR/sorted.dist.hwe.af.AFR.caQTL.example.txt.gz',
                        label='AFGR_caqtl', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) == 200
    assert len(first_item) == 13
    assert '_from' in first_item
    assert first_item['_key'] == '701f175a69d51e1e7c526f8c8ca2b2165ba7a58aadfa797dfa737916120b8ce5_accessible_dna_element_1_906596_907043_GRCh38_AFGR'
