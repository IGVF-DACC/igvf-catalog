import json
from unittest.mock import patch

import pytest

from adapters.gencc_diseases_genes_adapter import GenccDiseasesGenes
from adapters.writer import SpyWriter


SAMPLE_TSV = './samples/gencc_submissions.example.tsv'
MOCK_GENE_MAP = {'HGNC:10896': ['ENSG00000123456', 'ENSG00000654321']}


def _parsed_docs(spy_writer: SpyWriter):
    """Collect JSON objects from SpyWriter (ignores newline-only writes)."""
    return [json.loads(c) for c in spy_writer.contents if c.strip().startswith('{')]


@pytest.fixture
def mock_gene_map():
    with patch('adapters.gencc_diseases_genes_adapter.get_gene_map_from_arangodb') as m:
        m.return_value = MOCK_GENE_MAP
        yield m


def test_gencc_process_file_writes_edge(mock_gene_map):
    writer = SpyWriter()
    adapter = GenccDiseasesGenes(
        filepath=SAMPLE_TSV,
        writer=writer,
        validate=True,
    )
    adapter.process_file()

    docs = _parsed_docs(writer)
    assert len(docs) == 2
    doc = next(d for d in docs if d['_to'] == 'genes/ENSG00000123456')

    assert doc['_key'] == 'SGC-TEST001_ENSG00000123456'
    assert doc['_from'] == 'ontology_terms/MONDO_0008426'
    assert doc['_to'] == 'genes/ENSG00000123456'
    assert doc['sgc_id'] == 'SGC-TEST001.1'
    assert doc['name'] == 'associated_with'
    assert doc['inverse_name'] == 'associated_with'
    assert doc['hgnc'] == 'HGNC:10896'
    assert doc['gene_symbol'] == 'SKI'
    assert doc['term_name'] == 'Shprintzen-Goldberg syndrome'
    assert doc['classification'] == 'Definitive'
    assert doc['moi_id'] == 'HP:0000006'
    assert doc['moi_name'] == 'Autosomal dominant'
    assert doc['submitter'] == 'Ambry Genetics'
    assert doc['pmids'] == ['28106320', '12345678']
    assert doc['source'] == GenccDiseasesGenes.SOURCE
    assert doc['source_url'] == 'https://thegencc.org/submissions/SGC-TEST001.1'


def test_gencc_process_file_one_row_per_gene_ensembl(mock_gene_map):
    writer = SpyWriter()
    adapter = GenccDiseasesGenes(
        filepath=SAMPLE_TSV,
        writer=writer,
        validate=True,
    )
    adapter.process_file()

    docs = _parsed_docs(writer)
    assert len(docs) == 2
    keys = {d['_key'] for d in docs}
    assert keys == {
        'SGC-TEST001_ENSG00000123456',
        'SGC-TEST001_ENSG00000654321',
    }
    assert {d['_to'] for d in docs} == {
        'genes/ENSG00000123456',
        'genes/ENSG00000654321',
    }


def test_gencc_skips_row_when_hgnc_not_in_gene_map(mock_gene_map):
    writer = SpyWriter()
    adapter = GenccDiseasesGenes(
        filepath=SAMPLE_TSV,
        writer=writer,
        validate=False,
    )
    adapter.process_file()
    docs = _parsed_docs(writer)
    assert len(docs) == 2
    assert all(doc['hgnc'] != 'HGNC:99999999' for doc in docs)


def test_gencc_invalid_label():
    with pytest.raises(
        ValueError,
        match='Invalid label: invalid_label. Allowed values: disease_gene',
    ):
        GenccDiseasesGenes(filepath=SAMPLE_TSV, label='invalid_label')


def test_gencc_validate_doc_invalid(mock_gene_map):
    adapter = GenccDiseasesGenes(
        filepath=SAMPLE_TSV,
        validate=True,
    )
    invalid_doc = {'invalid_field': 'x'}
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)


def test_gencc_initialization():
    adapter = GenccDiseasesGenes(filepath=SAMPLE_TSV, label='disease_gene')
    assert adapter.filepath == SAMPLE_TSV
    assert adapter.label == 'disease_gene'
