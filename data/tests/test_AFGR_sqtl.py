import json

from adapters.AFGR_sqtl_adapter import AFGRSQtl
from adapters.writer import SpyWriter


def test_AFGR_sqtl_adapter_AFGR_sqtl():
    writer = SpyWriter()
    adapter = AFGRSQtl(filepath='./samples/AFGR/sorted.all.AFR.Meta.sQTL.example.txt.gz',
                       label='AFGR_sqtl', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) == 214
    assert len(first_item) == 17
    assert first_item['intron_chr'].startswith('chr')


def test_AFGR_sqtl_adapter_AFGR_sqtl_term():
    writer = SpyWriter()
    adapter = AFGRSQtl(filepath='./samples/AFGR/sorted.all.AFR.Meta.sQTL.example.txt.gz',
                       label='AFGR_sqtl_term', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) == 214
    assert len(first_item) == 8
    assert first_item['inverse_name'] == 'has measurement'
