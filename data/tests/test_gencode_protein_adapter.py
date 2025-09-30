import pytest
import pickle
from unittest.mock import MagicMock, patch, mock_open
from adapters.gencode_protein_adapter import GencodeProtein

SAMPLE_DATA = "# header\nchr1\tHAVANA\ttranscript\t65419\t71585\t.\t+\t.\tgene_id \"ENSG00000186092.7\"; transcript_id \"ENST00000641515.2\"; gene_type \"protein_coding\"; gene_name \"OR4F5\"; transcript_type \"protein_coding\"; transcript_name \"OR4F5-201\"; level 2; protein_id \"ENSP00000493376.2\"; hgnc_id \"HGNC:14825\"; tag \"basic\";\n"


@pytest.fixture
def mock_writer():
    return MagicMock()


@pytest.fixture
def gencode_protein_human(mock_writer):
    with patch('adapters.gencode_protein_adapter.open', mock_open(read_data=SAMPLE_DATA)):
        yield GencodeProtein(
            filepath='dummy.gtf',
            label='gencode_protein',
            organism='HUMAN',
            writer=mock_writer,
            uniprot_sprot_file_path='dummy_sprot.gz',
            uniprot_trembl_file_path='dummy_trembl.gz'
        )


def test_init_invalid_organism(mock_writer):
    with pytest.raises(ValueError):
        GencodeProtein(filepath='dummy.gtf', label='gencode_protein',
                       organism='INVALID', writer=mock_writer)


def test_init_invalid_label(mock_writer):
    with pytest.raises(ValueError):
        GencodeProtein(filepath='dummy.gtf', label='invalid_label',
                       organism='HUMAN', writer=mock_writer)


def test_parse_info_metadata_extracts_keys(gencode_protein_human):
    info = [
        'gene_id', '"ENSG00000186092.7";',
        'transcript_id', '"ENST00000641515.2";',
        'gene_type', '"protein_coding";',
        'gene_name', '"OR4F5";',
        'transcript_type', '"protein_coding";',
        'transcript_name', '"OR4F5-201";',
        'protein_id', '"ENSP00000493376.2";'
    ]
    parsed = gencode_protein_human.parse_info_metadata(info)
    assert parsed['gene_id'] == 'ENSG00000186092.7'
    assert parsed['protein_id'] == 'ENSP00000493376.2'


def test_get_full_name_extracts_full_name(gencode_protein_human):
    desc = 'RecName: Full=Protein ABC; AltName: Full=Other name;'
    assert gencode_protein_human.get_full_name(desc) == 'Protein ABC'


def test_get_dbxrefs_handles_embl_and_refseq(gencode_protein_human):
    cross_refs = [
        ['EMBL', 'ID1', 'ID2'],
        ['RefSeq', 'RS1', 'RS2'],
        ['OtherDB', 'OID']
    ]
    dbxrefs = gencode_protein_human.get_dbxrefs(cross_refs)
    assert {'name': 'EMBL', 'id': 'ID1'} in dbxrefs
    assert {'name': 'EMBL', 'id': 'ID2'} in dbxrefs
    assert {'name': 'RefSeq', 'id': 'RS1'} in dbxrefs
    assert {'name': 'RefSeq', 'id': 'RS2'} in dbxrefs
    assert {'name': 'OtherDB', 'id': 'OID'} in dbxrefs


@patch('adapters.gencode_protein_adapter.gzip.open')
@patch('adapters.gencode_protein_adapter.SwissProt.parse')
def test_get_uniprot_xrefs_parses_records(mock_parse, mock_gzip, gencode_protein_human):
    record = MagicMock()
    record.taxonomy_id = [gencode_protein_human.taxonomy_id]
    record.accessions = ['P12345']
    record.cross_references = [['RefSeq', 'RS1']]
    record.description = 'RecName: Full=Protein ABC;'
    record.entry_name = 'PROT_ABC'
    mock_parse.return_value = [record]
    mock_gzip.return_value.__enter__.return_value = MagicMock()
    result = gencode_protein_human.get_uniprot_xrefs('dummy.gz')
    assert 'P12345' in result
    assert result['P12345']['name'] == 'PROT_ABC'
    assert result['P12345']['full_name'] == 'Protein ABC'
    assert {'name': 'RefSeq', 'id': 'RS1'} in result['P12345']['dbxrefs']


@patch('adapters.gencode_protein_adapter.open', new_callable=mock_open, read_data=SAMPLE_DATA)
@patch.object(GencodeProtein, 'get_uniprot_xrefs', return_value={'P12345': {'name': 'PROT_ABC', 'dbxrefs': [], 'full_name': 'Protein ABC'}})
def test_process_file_writes_json(mock_get_uniprot, mock_open_file, mock_writer):
    # Patch pickle.load and mapping files
    with patch('builtins.open', mock_open(read_data=pickle.dumps({'ENSP00000493376': ['P12345']}))) as mock_pickle_open, \
            patch('pickle.load', return_value={'ENSP00000493376': ['P12345']}):
        gencode = GencodeProtein(
            filepath='dummy.gtf',
            label='gencode_protein',
            organism='HUMAN',
            writer=mock_writer,
            uniprot_sprot_file_path='dummy_sprot.gz',
            uniprot_trembl_file_path='dummy_trembl.gz'
        )
        gencode.process_file()
        assert mock_writer.open.called
        assert mock_writer.write.call_count > 0
        assert mock_writer.close.called
