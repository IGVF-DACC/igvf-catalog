import gzip
import json
from unittest.mock import patch

import pytest

from adapters.overexpression_ATAC_adapter import OverexpressionATAC
from adapters.writer import SpyWriter


MODULE = 'adapters.overexpression_ATAC_adapter'
HEADER = 'rowID\tbaseMean\tlog2FoldChange\tlfcSE\tstat\tpvalue\tpadj\n'
METADATA = {
    'method': 'ATAC-seq', 'class': 'observed data',
    'perturbation': 'ORF overexpression', 'file_set_id': 'IGVFDS6344XBAV',
    'simple_sample_summaries': ['CD8-positive memory T cell'],
    'samples': ['ontology_terms/CL_0000909'], 'treatments_term_ids': None,
}


@pytest.fixture(autouse=True)
def catalog():
    with patch(f'{MODULE}.get_file_fileset_by_accession_in_arangodb', return_value=METADATA) as metadata, \
            patch(f'{MODULE}.ArangoDB') as arango:
        arango.return_value.get_igvf_connection.return_value.collection.return_value.get.return_value = {
            '_from': 'genes/ENSG00000123685', '_to': 'transcripts/ENST00000243440'}
        yield metadata, arango


def parse(tmp_path, rows, label='gene_transcript_genomic_element', accession='IGVFFI2320OTYL', compressed=False):
    path = tmp_path / (accession + '.tsv' + ('.gz' if compressed else ''))
    opener = gzip.open if compressed else open
    with opener(path, 'wt') as stream:
        stream.write(HEADER + rows)
    writer = SpyWriter()
    OverexpressionATAC(str(path), label, writer, validate=True).process_file()
    return [json.loads(doc) for doc in writer.contents]


@pytest.mark.parametrize('accession', sorted(OverexpressionATAC.FILE_ACCESSIONS))
@pytest.mark.parametrize('compressed', [False, True])
def test_nodes_and_edges_share_exact_half_open_intervals(tmp_path, accession, compressed):
    rows = 'chr1_0_10616\t55.37700577\t-0.344752844\t0.360178503\t-0.957172185\t0.338480354\t0.539344977\n'
    node, = parse(tmp_path, rows, 'genomic_element', accession, compressed)
    edge, = parse(tmp_path, rows, accession=accession, compressed=compressed)
    assert (node['chr'], node['start'], node['end']) == ('chr1', 0, 10616)
    assert node['_key'] == f'ATAC_chr1_0_10616_GRCh38_{accession}'
    assert edge['_to'] == f'genomic_elements/{node["_key"]}'
    assert edge['_from'] == 'genes_transcripts/ENSG00000123685_ENST00000243440'
    assert edge['files_filesets'] == f'files_filesets/{accession}'
    assert edge['perturbation'] == 'ORF overexpression'
    assert edge['log2FC'] == pytest.approx(-0.344752844)
    assert edge['standard_error'] == pytest.approx(0.360178503)
    assert edge['base_mean'] == pytest.approx(55.37700577)
    assert edge['significant'] is False


def test_zero_missing_pvalues_and_significance_boundary(tmp_path):
    docs = parse(tmp_path, 'chr1_0_10\t1\t2\t1\t2\t0\t0\n'
                 'chr1_10_20\t1\tNA\tNA\tNA\tNA\tNA\n'
                 'chr1_20_30\t1\t2\t1\t2\t0.01\t0.05\n')
    assert docs[0]['significant'] is True
    assert docs[0]['neg_log10_pvalue'] == 240
    assert docs[0]['neg_log10_pvalue_adj'] == 240
    assert docs[1]['log2FC'] is None
    assert docs[1]['p_value_adj'] is None
    assert docs[1]['neg_log10_pvalue_adj'] is None
    assert docs[1]['significant'] is False
    assert docs[2]['significant'] is False
    assert docs[2]['neg_log10_pvalue'] == 2


@pytest.mark.parametrize('row, message', [
    ('chr1_10_10\t1\t2\t1\t2\t0.1\t0.1\n', 'Invalid peak interval'),
    ('chr1_-1_10\t1\t2\t1\t2\t0.1\t0.1\n', 'Invalid peak identifier'),
    ('chr1_0_10\t1\tinf\t1\t2\t0.1\t0.1\n', 'finite number'),
    ('chr1_0_10\t1\t2\t1\t2\t1.1\t0.1\n', 'between 0 and 1'),
    ('chr1_0_10\t1\t2\t-1\t2\t0.1\t0.1\n', 'nonnegative'),
])
def test_invalid_rows_fail_with_line_number(tmp_path, row, message):
    with pytest.raises(ValueError, match=f'line 2: .*{message}'):
        parse(tmp_path, row)


def test_duplicate_peaks_fail(tmp_path):
    with pytest.raises(ValueError, match='Duplicate peak'):
        parse(tmp_path, 'chr1_0_10\t1\t2\t1\t2\t0.1\t0.1\n' * 2)


def test_missing_columns_fail(tmp_path):
    path = tmp_path / 'IGVFFI2320OTYL.tsv'
    path.write_text('rowID\tlog2FoldChange\nchr1_0_10\t1\n')
    with pytest.raises(ValueError, match='missing columns'):
        OverexpressionATAC(
            str(path), 'gene_transcript_genomic_element', SpyWriter()).process_file()


def test_missing_catalog_dependencies_fail(tmp_path, catalog):
    metadata, arango = catalog
    metadata.return_value = None
    with pytest.raises(ValueError, match='Load files_filesets'):
        parse(tmp_path, '')
    metadata.return_value = METADATA
    arango.return_value.get_igvf_connection.return_value.collection.return_value.get.return_value = None
    with pytest.raises(ValueError, match='Missing or inconsistent genes_transcripts'):
        parse(tmp_path, '')


def test_raw_counts_are_not_supported():
    with pytest.raises(ValueError, match='Unsupported file accession'):
        OverexpressionATAC('IGVFFI4762WUEH.tsv.gz', 'genomic_element')
