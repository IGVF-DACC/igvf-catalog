import json

from adapters.AFGR_caqtl_adapter import AFGRCAQtl
from adapters.writer import SpyWriter


def test_AFGR_caqtl_adapter():
    writer = SpyWriter()
    adapter = AFGRCAQtl(filepath='./samples/AFGR/sorted.dist.hwe.af.AFR.caQTL.example.txt.gz',
                        label='regulatory_region', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) == 200
    assert len(first_item) == 8
    assert first_item['_key'] == 'accessible_dna_element_1_906596_907043_GRCh38'
