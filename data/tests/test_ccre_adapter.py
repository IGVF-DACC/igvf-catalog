import json
import pytest
from adapters.ccre_adapter import CCRE
from adapters.writer import SpyWriter


@pytest.mark.external_dependency
def test_ccre_adapter():
    writer = SpyWriter()
    adapter = CCRE(filepath='./samples/ENCFF420VPZ.example.bed.gz',
                   label='genomic_element', writer=writer, validate=True)
    adapter.process_file()
    assert len(writer.contents) == 5510
    first_item = json.loads(writer.contents[0])
    assert first_item['_key'] == 'candidate_cis_regulatory_element_chr20_9550320_9550587_GRCh38_ENCFF420VPZ'
    assert first_item['chr'] == 'chr20'
    assert first_item['source_url'].startswith(
        'https://www.encodeproject.org/files/')


def test_ccre_adapter_initialization():
    adapter = CCRE(filepath='./samples/ENCFF167FJQ.example.bed.gz',
                   label='custom_label')
    assert adapter.filepath == './samples/ENCFF167FJQ.example.bed.gz'
    assert adapter.label == 'custom_label'
    assert adapter.dataset == 'custom_label'
    assert adapter.source_url.startswith(
        'https://www.encodeproject.org/files/')
    assert adapter.type == 'node'


def test_ccre_adapter_validate_doc_invalid():
    writer = SpyWriter()
    adapter = CCRE(filepath='./samples/ENCFF420VPZ.example.bed.gz',
                   label='genomic_element', writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
