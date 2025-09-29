import json
import pytest
import tempfile
import gzip
import os
from unittest.mock import patch, MagicMock
from adapters.human_mouse_element_adapter import HumanMouseElementAdapter
from adapters.writer import SpyWriter


@pytest.fixture
def human_mouse_files():
    return './samples/element_mapping_example.txt.gz'


@pytest.fixture
def spy_writer():
    return SpyWriter()


def test_regulatory_region(human_mouse_files, spy_writer):
    adapter = HumanMouseElementAdapter(
        human_mouse_files, label='genomic_element', writer=spy_writer, validate=True)
    adapter.process_file()

    assert len(spy_writer.contents) > 0
    data = json.loads(spy_writer.contents[0])
    assert '_key' in data
    assert 'chr' in data
    assert 'start' in data
    assert 'end' in data
    assert 'type' in data
    assert data['type'] == 'accessible dna elements'
    assert 'source' in data
    assert 'source_url' in data


def test_mm_regulatory_region(human_mouse_files, spy_writer):
    adapter = HumanMouseElementAdapter(
        human_mouse_files, label='mm_genomic_element', writer=spy_writer, validate=True)
    adapter.process_file()

    assert len(spy_writer.contents) > 0
    data = json.loads(spy_writer.contents[0])
    assert '_key' in data
    assert 'chr' in data
    assert 'start' in data
    assert 'end' in data
    assert 'type' in data
    assert data['type'] == 'accessible dna elements (mouse)'
    assert 'source' in data
    assert 'source_url' in data


def test_regulatory_region_mm_regulatory_region(human_mouse_files, spy_writer):
    adapter = HumanMouseElementAdapter(
        human_mouse_files, label='genomic_element_mm_genomic_element', writer=spy_writer, validate=True)
    adapter.process_file()

    assert len(spy_writer.contents) > 0
    data = json.loads(spy_writer.contents[0])
    assert '_key' in data
    assert '_from' in data
    assert '_to' in data
    assert 'percent_identical_bp' in data
    assert 'phastCons4way' in data
    assert 'phyloP4way' in data
    assert 'cov_chromatin_accessibility' in data
    assert 'cov_chromatin_accessibility_pval' in data
    assert 'cov_chromatin_accessibility_fdr' in data
    assert 'cob_chromatin_accessibility' in data
    assert 'cob_chromatin_accessibility_pval' in data
    assert 'cob_chromatin_accessibility_fdr' in data
    assert 'cov_H3K27ac' in data
    assert 'cov_H3K27ac_pval' in data
    assert 'cov_H3K27ac_fdr' in data
    assert 'cob_H3K27ac' in data
    assert 'cob_H3K27ac_pval' in data
    assert 'cob_H3K27ac_fdr' in data
    assert 'cov_H3K4me1' in data
    assert 'cov_H3K4me1_pval' in data
    assert 'cov_H3K4me1_fdr' in data
    assert 'cob_H3K4me1' in data
    assert 'cob_H3K4me1_pval' in data
    assert 'cob_H3K4me1_fdr' in data
    assert 'cov_H3K4me3' in data
    assert 'cov_H3K4me3_pval' in data
    assert 'cov_H3K4me3_fdr' in data
    assert 'cob_H3K4me3' in data
    assert 'cob_H3K4me3_pval' in data
    assert 'cob_H3K4me3_fdr' in data
    assert 'source' in data
    assert 'source_url' in data


def test_human_mouse_element_adapter_initialization():
    """Test adapter initialization with different labels"""
    writer = SpyWriter()

    # Test default initialization
    adapter = HumanMouseElementAdapter('test_file.txt.gz', writer=writer)
    assert adapter.filepath == 'test_file.txt.gz'
    assert adapter.label == 'genomic_element_mm_genomic_element'
    assert adapter.type == 'edge'
    assert adapter.SOURCE == 'FUNCODE'
    assert adapter.file_accession == 'test_file'
    assert adapter.source_url == 'https://data.igvf.org/reference-files/test_file'

    # Test genomic_element label
    adapter = HumanMouseElementAdapter(
        'test_file.txt.gz', label='genomic_element', writer=writer)
    assert adapter.label == 'genomic_element'
    assert adapter.type == 'node'

    # Test mm_genomic_element label
    adapter = HumanMouseElementAdapter(
        'test_file.txt.gz', label='mm_genomic_element', writer=writer)
    assert adapter.label == 'mm_genomic_element'
    assert adapter.type == 'node'


def test_human_mouse_element_adapter_invalid_label():
    """Test error handling for invalid label"""
    writer = SpyWriter()

    with pytest.raises(ValueError, match='Invalid label. Allowed values: genomic_element,mm_genomic_element,genomic_element_mm_genomic_element'):
        HumanMouseElementAdapter(
            'test_file.txt.gz', label='invalid_label', writer=writer)


def test_human_mouse_element_adapter_validate_doc_invalid():
    writer = SpyWriter()
    adapter = HumanMouseElementAdapter(
        'test_file.txt.gz', label='genomic_element_mm_genomic_element', writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
