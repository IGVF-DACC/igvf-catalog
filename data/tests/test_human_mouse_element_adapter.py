import json
import pytest
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
        human_mouse_files, label='genomic_element', writer=spy_writer)
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
        human_mouse_files, label='mm_genomic_element', writer=spy_writer)
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
        human_mouse_files, label='genomic_element_mm_genomic_element', writer=spy_writer)
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
