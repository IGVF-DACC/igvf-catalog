import json

from adapters.coxpresdb_adapter import Coxpresdb
from adapters.writer import SpyWriter


def test_coxpresdb_adapter():
    writer = SpyWriter()
    adapter = Coxpresdb(filepath='./samples/coxpresdb/', writer=writer)
    adapter.process_file()

    assert len(writer.contents) > 0
    first_item = json.loads(writer.contents[0])

    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert 'z_score' in first_item
    assert first_item['source'] == 'CoXPresdb'
    assert first_item['source_url'] == 'https://coxpresdb.jp/'
    assert first_item['name'] == 'coexpressed with'
    assert first_item['inverse_name'] == 'coexpressed with'
    assert first_item['associated process'] == 'ontology_terms/GO_0010467'


def test_coxpresdb_adapter_z_score_filter():
    writer = SpyWriter()
    adapter = Coxpresdb(filepath='./samples/coxpresdb/', writer=writer)
    adapter.process_file()

    for item in writer.contents:
        if item.startswith('{'):
            data = json.loads(item)
            assert abs(float(data['z_score'])) >= 3


def test_coxpresdb_adapter_initialization():
    adapter = Coxpresdb(filepath='foobarbaz')
    assert adapter.filepath == 'foobarbaz'
    assert adapter.label == 'coxpresdb'
    assert adapter.source == 'CoXPresdb'
    assert adapter.source_url == 'https://coxpresdb.jp/'
