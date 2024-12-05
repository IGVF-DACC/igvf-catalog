import json

from adapters.ccre_adapter import CCRE
from adapters.writer import SpyWriter


def test_ccre_adapter():
    writer = SpyWriter()
    adapter = CCRE(filepath='./samples/ccre_example.bed.gz',
                   label='regulatory_region', writer=writer)
    adapter.process_file()
    assert len(writer.contents) == 5510
    first_item = json.loads(writer.contents[0])
    assert first_item['_key'] == 'EH38E4255188'
    assert first_item['chr'] == 'chr20'
    assert first_item['source_url'].startswith(
        'https://www.encodeproject.org/files/')


def test_ccre_adapter_initialization():
    adapter = CCRE(filepath='./samples/ccre_example.bed.gz',
                   label='custom_label')
    assert adapter.filepath == './samples/ccre_example.bed.gz'
    assert adapter.label == 'custom_label'
    assert adapter.dataset == 'custom_label'
    assert adapter.source_url.startswith(
        'https://www.encodeproject.org/files/')
    assert adapter.type == 'node'
