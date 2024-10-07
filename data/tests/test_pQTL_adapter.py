import json

from adapters.pQTL_adapter import pQTL
from adapters.writer import SpyWriter


def test_pQTL_adapter():
    writer = SpyWriter()
    adapter = pQTL(filepath='./samples/pQTL_UKB_example.csv',
                   label='pqtl', writer=writer)
    adapter.process_file()
    assert len(writer.contents) == 200
    first_item = json.loads(writer.contents[0])
    assert first_item['_key'] == '7c956a1b8ed65d87dd710feb0e7614683e8a65eb83306daee6be58cdf8b17b01_P04217_UKB'
    assert first_item['name'] == 'associated with levels of'
    assert first_item['label'] == 'pQTL'
    assert first_item['log10pvalue'] == 79.2