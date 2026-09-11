import json
import math
import pytest
from unittest.mock import MagicMock, patch

from adapters.MORF_transcript_gene_adapter import MORFTranscriptGene
from adapters.writer import SpyWriter

DESEQ_PATH = './samples/morf_transcript_gene_deseq2.example.tsv'
ORF_PATH = './samples/morf_orf_transcripts.example.tsv'
SOURCE_URL = 'https://api.data.igvf.org/tabular-files/IGVFFI6734IWRB/'
REFERENCE_SOURCE_URL = 'https://api.data.igvf.org/tabular-files/IGVFFI2373SYJW/'


@pytest.fixture
def mock_file_fileset():
    with patch('adapters.MORF_transcript_gene_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'method': 'MORF screen',
            'class': 'observed data',
            'crispr_modality': None,
            'simple_sample_summaries': ['CD8-positive, alpha-beta T cell'],
            'samples': ['ontology_terms/CL_0000625'],
            'treatments_term_ids': None,
            'file_set_id': 'IGVFDS0859PLSS',
        }
        yield mock_get_file_fileset


@pytest.fixture
def mock_gene_validator():
    with patch('adapters.MORF_transcript_gene_adapter.GeneValidator') as mock_validator:
        mock_validator.return_value = MagicMock(
            validate=MagicMock(return_value=True)
        )
        yield mock_validator


def _build_adapter(writer, **kwargs):
    return MORFTranscriptGene(
        filepath=kwargs.get('filepath', DESEQ_PATH),
        label=kwargs.get('label', 'transcript_gene'),
        source_url=kwargs.get('source_url', SOURCE_URL),
        writer=writer,
        validate=kwargs.get('validate', True),
        reference_filepath=kwargs.get('reference_filepath', ORF_PATH),
        reference_source_url=kwargs.get(
            'reference_source_url', REFERENCE_SOURCE_URL),
    )


def _parsed_docs(writer):
    return [json.loads(item) for item in writer.contents]


def test_morf_transcript_gene_writes_ensembl_edges(mock_file_fileset, mock_gene_validator):
    writer = SpyWriter()
    adapter = _build_adapter(writer)
    adapter.process_file()

    docs = _parsed_docs(writer)
    keys = {doc['_key'] for doc in docs}
    assert keys == {
        'ENST00000619387_ENSG00000198846_IGVFFI6734IWRB_AATF_1',
        'ENST00000450518_ENSG00000198846_IGVFFI6734IWRB_ACTL6A_1',
        'ENST00000392662_ENSG00000198846_IGVFFI6734IWRB_ACTL6A_1',
        'ENST00000511061_ENSG00000198846_IGVFFI6734IWRB_NKX2_1_1',
        'ENST00000403290_ENSG00000198846_IGVFFI6734IWRB_ARNTL_1',
    }

    aatf = next(doc for doc in docs if doc['morf_id'] == 'AATF_1')
    assert aatf['_from'] == 'transcripts/ENST00000619387'
    assert aatf['_to'] == 'genes/ENSG00000198846'
    assert aatf['log2FC'] == pytest.approx(-0.786997515211818)
    assert aatf['log2FC_se'] == pytest.approx(0.699309113088129)
    assert aatf['p_value'] == pytest.approx(0.260422575712608)
    assert aatf['p_value_adj'] == pytest.approx(0.997637901873519)
    assert aatf['neg_log10_pvalue'] == pytest.approx(
        -math.log10(0.260422575712608))
    assert aatf['significant'] is False
    assert aatf['orf_gene'] == 'ENSG00000275700'
    assert aatf['ensembl_transcript_ids'] == ['ENST00000619387']
    assert aatf['refseq_transcript_ids'] == ['NM_012138']
    assert aatf['method'] == 'MORF screen'
    assert aatf['crispr_modality'] is None
    assert aatf['label'] == 'transcript effect on gene expression'
    assert aatf['name'] == 'modulates expression of'
    assert aatf['source_url'] == 'https://data.igvf.org/tabular-files/IGVFFI6734IWRB/'
    assert aatf['files_filesets'] == 'files_filesets/IGVFFI6734IWRB'
    assert aatf['biosample_term'] == 'ontology_terms/CL_0000625'
    assert aatf['biological_context'] == 'CD8-positive, alpha-beta T cell'


def test_morf_transcript_gene_joins_hyphenated_row_ids(mock_file_fileset, mock_gene_validator):
    writer = SpyWriter()
    adapter = _build_adapter(writer)
    adapter.process_file()

    nkx = next(
        doc for doc in _parsed_docs(writer) if doc['morf_id'] == 'NKX2_1_1')
    assert nkx['significant'] is True
    assert nkx['log2FC'] == pytest.approx(1.2)
    assert nkx['_from'] == 'transcripts/ENST00000511061'


def test_morf_transcript_gene_emits_one_edge_per_ensembl_transcript(mock_file_fileset, mock_gene_validator):
    writer = SpyWriter()
    adapter = _build_adapter(writer)
    adapter.process_file()

    actl = [
        doc for doc in _parsed_docs(writer) if doc['morf_id'] == 'ACTL6A_1']
    assert {doc['_from'] for doc in actl} == {
        'transcripts/ENST00000450518',
        'transcripts/ENST00000392662',
    }
    assert all(
        doc['ensembl_transcript_ids'] == [
            'ENST00000450518', 'ENST00000392662']
        for doc in actl
    )


def test_morf_transcript_gene_allows_null_orf_gene(mock_file_fileset, mock_gene_validator):
    writer = SpyWriter()
    adapter = _build_adapter(writer)
    adapter.process_file()

    arntl = next(
        doc for doc in _parsed_docs(writer) if doc['morf_id'] == 'ARNTL_1')
    assert arntl['orf_gene'] is None
    assert arntl['_from'] == 'transcripts/ENST00000403290'


def test_morf_transcript_gene_flags_refseq_only_orfs(mock_file_fileset, mock_gene_validator, caplog):
    writer = SpyWriter()
    adapter = _build_adapter(writer)
    adapter.process_file()

    docs = _parsed_docs(writer)
    assert all(doc['morf_id'] not in {'ACTL6A_2', 'GFP_1'} for doc in docs)
    assert 'Flagged 2 ORF(s)' in caplog.text
    assert 'ACTL6A_2' in caplog.text
    assert 'GFP_1' in caplog.text
    assert 'NM_004301.4' in caplog.text


def test_morf_transcript_gene_skips_na_deseq_stats(mock_file_fileset, mock_gene_validator, caplog):
    caplog.set_level('INFO')
    writer = SpyWriter()
    adapter = _build_adapter(writer)
    adapter.process_file()

    assert all(doc['morf_id'] != 'ARID1B_1' for doc in _parsed_docs(writer))
    assert 'NA DESeq2 log2FoldChange/p-value' in caplog.text


def test_morf_transcript_gene_chronic_accession(mock_file_fileset, mock_gene_validator):
    writer = SpyWriter()
    adapter = _build_adapter(
        writer,
        source_url='https://data.igvf.org/tabular-files/IGVFFI6032GREJ/',
    )
    adapter.process_file()

    first = _parsed_docs(writer)[0]
    assert first['files_filesets'] == 'files_filesets/IGVFFI6032GREJ'
    assert '_IGVFFI6032GREJ_' in first['_key']


def test_morf_transcript_gene_invalid_label(mock_file_fileset, mock_gene_validator):
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label'):
        _build_adapter(writer, label='invalid_label')


def test_morf_transcript_gene_unsupported_accession(mock_file_fileset):
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Unsupported file accession'):
        MORFTranscriptGene(
            filepath=DESEQ_PATH,
            label='transcript_gene',
            source_url='https://data.igvf.org/tabular-files/IGVFFI0000AAAA/',
            writer=writer,
            reference_filepath=ORF_PATH,
        )


def test_morf_transcript_gene_requires_reference_filepath(mock_file_fileset):
    writer = SpyWriter()
    with pytest.raises(ValueError, match='reference_filepath is required'):
        MORFTranscriptGene(
            filepath=DESEQ_PATH,
            label='transcript_gene',
            source_url=SOURCE_URL,
            writer=writer,
        )


def test_morf_transcript_gene_invalid_readout_gene(mock_file_fileset):
    writer = SpyWriter()
    with patch('adapters.MORF_transcript_gene_adapter.GeneValidator') as mock_validator:
        mock_validator.return_value = MagicMock(
            validate=MagicMock(return_value=False)
        )
        adapter = MORFTranscriptGene(
            filepath=DESEQ_PATH,
            label='transcript_gene',
            source_url=SOURCE_URL,
            writer=writer,
            validate=False,
            reference_filepath=ORF_PATH,
        )
        with pytest.raises(ValueError, match='ENSG00000198846 is not a valid gene'):
            adapter.process_file()
