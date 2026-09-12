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
    assert 'Flagged 1 ORF(s)' in caplog.text
    assert 'ACTL6A_2' in caplog.text
    assert 'GFP_1' not in caplog.text
    assert 'NM_004301.4' in caplog.text


def test_morf_transcript_gene_skips_na_deseq_stats(mock_file_fileset, mock_gene_validator, caplog):
    caplog.set_level('INFO')
    writer = SpyWriter()
    adapter = _build_adapter(writer)
    adapter.process_file()

    assert all(doc['morf_id'] != 'ARID1B_1' for doc in _parsed_docs(writer))
    assert 'missing DESeq2 log2FoldChange' in caplog.text


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
            reference_source_url=REFERENCE_SOURCE_URL,
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
            reference_source_url=REFERENCE_SOURCE_URL,
        )
        with pytest.raises(ValueError, match='ENSG00000198846 is not a valid gene'):
            adapter.process_file()


@pytest.fixture(autouse=True)
def mock_gene_maps():
    with patch('adapters.MORF_transcript_gene_adapter.get_gene_map_from_arangodb', return_value={}) as mapping:
        yield mapping


def test_missing_gene_name_then_synonym(mock_gene_maps):
    mock_gene_maps.side_effect = [
        {'CURRENT': ['ENSG00000000001']}, {'OLD': ['ENSG00000000002']}]
    orfs = {name: {'morf_id': name, 'orf_gene': None, 'orf_gene_symbol': name,
                   'ensembl_transcript_ids': []} for name in ['CURRENT', 'OLD', 'GFP_1', 'mCherry_1']}
    adapter = MORFTranscriptGene.__new__(MORFTranscriptGene)
    adapter._resolve_missing_orf_genes(orfs)
    assert orfs['CURRENT']['orf_gene'] == 'ENSG00000000001'
    assert orfs['OLD']['orf_gene'] == 'ENSG00000000002'
    assert orfs['GFP_1']['orf_gene'] is None
    assert orfs['mCherry_1']['orf_gene'] is None


@pytest.mark.parametrize('parents, expected', [
    (['ENSG00000000001', 'ENSG00000000001'], 'ENSG00000000001'),
    (['ENSG00000000001', 'ENSG00000000002'], None),
    (['ENSG00000000001'], None),
    (['ENSG00000000003', 'ENSG00000000003'], None),
])
def test_ambiguous_gene_requires_consistent_transcripts(mock_gene_maps, parents, expected):
    mock_gene_maps.side_effect = [
        {}, {'OLD': ['ENSG00000000001', 'ENSG00000000002']}]
    orf = {'morf_id': 'OLD_1', 'orf_gene': None, 'orf_gene_symbol': 'OLD',
           'ensembl_transcript_ids': ['ENST00000000001', 'ENST00000000002']}
    adapter = MORFTranscriptGene.__new__(MORFTranscriptGene)
    with patch('adapters.MORF_transcript_gene_adapter.ArangoDB') as db, patch.object(
        MORFTranscriptGene, 'logger', create=True
    ):
        db.return_value.get_igvf_connection.return_value.aql.execute.return_value = [
            {'transcript': 'transcripts/' + t, 'gene': 'genes/' + g}
            for t, g in zip(orf['ensembl_transcript_ids'], parents)]
        adapter._resolve_missing_orf_genes({'OLD_1': orf})
    assert orf['orf_gene'] == expected


def test_reference_provenance_uses_input(mock_file_fileset, mock_gene_validator):
    writer = SpyWriter()
    writer.add_tag = MagicMock()
    adapter = _build_adapter(
        writer, reference_source_url='https://data.igvf.org/tabular-files/IGVFFI0000AAAA/?format=json')
    adapter.process_file()
    assert adapter.reference_accession == 'IGVFFI0000AAAA'
    tags = [call.args[1] for call in writer.add_tag.call_args_list]
    assert 'IGVFFI0000AAAA' in tags
    assert 'IGVFFI2373SYJW' not in tags


@pytest.mark.parametrize('url', [None, '', 'IGVFFI2373SYJW', 'https://data.igvf.org/tabular-files/bad/'])
def test_reference_url_required(mock_file_fileset, mock_gene_validator, url):
    with pytest.raises(ValueError, match='reference_source_url'):
        _build_adapter(SpyWriter(), reference_source_url=url)


def test_transcript_parser_rejects_partial_ids():
    assert MORFTranscriptGene._parse_transcript_ids(
        'ENST000000000010,xENST00000000001,ENST00000000001.bad,'
        'ENST00000000002.3,ENST00000000002.4,NM_123.1,NM_123.1'
    ) == (['ENST00000000002'], ['NM_123.1'])


@pytest.mark.parametrize('field,value', [('pvalue', '-0.1'), ('padj', '1.1'),
                                         ('baseMean', '-1'), ('lfcSE', '-1'),
                                         ('log2FoldChange', 'inf')])
def test_invalid_statistics_have_row_context(tmp_path, mock_file_fileset, mock_gene_validator, field, value):
    import csv
    with open(DESEQ_PATH) as f:
        reader = csv.DictReader(f, delimiter='\t')
        columns = reader.fieldnames
        row = next(reader)
    row[field] = value
    path = tmp_path / 'bad.tsv'
    with path.open('w') as f:
        writer = csv.DictWriter(f, fieldnames=columns, delimiter='\t')
        writer.writeheader()
        writer.writerow(row)
    adapter = _build_adapter(SpyWriter(), filepath=str(path))
    with pytest.raises(ValueError, match='AATF_1'):
        adapter.process_file()


def test_missing_columns_fail(tmp_path, mock_file_fileset, mock_gene_validator):
    path = tmp_path / 'bad.tsv'
    path.write_text('rowID\nAATF_1\n')
    adapter = _build_adapter(SpyWriter(), filepath=str(path))
    with pytest.raises(ValueError, match='missing required columns'):
        adapter.process_file()


def test_duplicate_screen_rows_fail(tmp_path, mock_file_fileset, mock_gene_validator):
    lines = open(DESEQ_PATH).readlines()
    path = tmp_path / 'duplicate.tsv'
    path.write_text(''.join([lines[0], lines[1], lines[1]]))
    adapter = _build_adapter(SpyWriter(), filepath=str(path))
    with pytest.raises(ValueError, match='duplicate rowID'):
        adapter.process_file()


def test_null_pvalues_are_preserved(tmp_path, mock_file_fileset, mock_gene_validator):
    path = tmp_path / 'null.tsv'
    path.write_text(
        'rowID\tbaseMean\tlog2FoldChange\tlfcSE\tpvalue\tpadj\nAATF_1\t1\t2\t0.1\tNA\tNA\n')
    writer = SpyWriter()
    _build_adapter(writer, filepath=str(path)).process_file()
    doc = _parsed_docs(writer)[0]
    assert doc['p_value'] is None
    assert doc['neg_log10_pvalue'] is None
    assert doc['significant'] is False


@pytest.fixture(autouse=True)
def mock_transcript_database():
    with patch('adapters.MORF_transcript_gene_adapter.ArangoDB') as db:
        db.return_value.get_igvf_connection.return_value.aql.execute.return_value = []
        yield db


def test_refseq_fallback_ignores_versions_and_filters_catalog(tmp_path, mock_transcript_database):
    path = tmp_path / 'mapping.tsv'
    path.write_text('ENST00000000001.2\tNM_123.2\tNP_123.1\n'
                    'ENST00000000002.1\tNM_123.3\n'
                    'ENST00000000003.1\tNM_123.3\n'
                    'ENST00000000001.2_PAR_Y\tNM_123.4\n')
    adapter = MORFTranscriptGene.__new__(MORFTranscriptGene)
    adapter.REFSEQ_MAPPING_PATH = path

    def orf(name, transcripts, refs):
        return {'morf_id': name, 'ensembl_transcript_ids': transcripts,
                'refseq_transcript_ids': refs}
    orfs = {'missing': orf('TEST_1', [], ['NM_123.1']),
            'supplied': orf('TEST_2', ['ENST00000000004'], ['NM_123.1']),
            'unmatched': orf('TEST_3', [], ['NM_999.1']),
            'control': orf('GFP_1', [], ['NM_123.1'])}
    mock_transcript_database.return_value.get_igvf_connection.return_value.aql.execute.return_value = [
        'ENST00000000001', 'ENST00000000001_PAR_Y', 'ENST00000000002']
    adapter._resolve_missing_transcripts(orfs)
    assert orfs['missing']['ensembl_transcript_ids'] == [
        'ENST00000000001', 'ENST00000000001_PAR_Y', 'ENST00000000002']
    assert orfs['missing']['refseq_transcript_ids'] == ['NM_123.1']
    assert orfs['missing']['transcript_mapping_method'] == 'GENCODE v43 RefSeq accession without version'
    assert orfs['supplied']['ensembl_transcript_ids'] == ['ENST00000000004']
    assert orfs['unmatched']['ensembl_transcript_ids'] == []
    assert orfs['control']['ensembl_transcript_ids'] == []


@pytest.fixture(autouse=True)
def empty_exclusion_file(tmp_path, monkeypatch):
    path = tmp_path / 'exclusions.tsv'
    path.write_text('screen_accession\tMORF_id\treason\n')
    monkeypatch.setattr(MORFTranscriptGene, 'EXCLUSION_PATH', path)
    return path


def test_exclusions_are_screen_specific_and_normalized(empty_exclusion_file, mock_file_fileset, mock_gene_validator, caplog):
    empty_exclusion_file.write_text(
        'screen_accession\tMORF_id\treason\n'
        'IGVFFI6734IWRB\tNKX2-1_1\tmanual_exclusion\n'
        'IGVFFI6032GREJ\tAATF_1\tother_screen\n')
    caplog.set_level('INFO')
    writer = SpyWriter()
    adapter = _build_adapter(writer)
    adapter.process_file()
    docs = _parsed_docs(writer)
    assert not any(d['morf_id'] == 'NKX2_1_1' for d in docs)
    assert any(d['morf_id'] == 'AATF_1' for d in docs)
    assert 'manual_exclusion' in caplog.text


def test_excluded_constructs_do_not_reach_mapping(empty_exclusion_file, mock_file_fileset, mock_gene_validator):
    empty_exclusion_file.write_text(
        'screen_accession\tMORF_id\treason\nIGVFFI6734IWRB\tACTL6A_2\tno_transcript\n')
    adapter = _build_adapter(SpyWriter())
    with patch.object(adapter, '_resolve_missing_transcripts') as resolve:
        adapter.process_file()
    assert 'ACTL6A_2' not in resolve.call_args.args[0]
