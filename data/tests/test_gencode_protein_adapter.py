import pytest
import pickle
from unittest.mock import MagicMock, patch, mock_open
from adapters.gencode_protein_adapter import GencodeProtein
from adapters.writer import SpyWriter
import json
from jsonschema import ValidationError

SAMPLE_DATA = "# header\nchr1\tHAVANA\ttranscript\t65419\t71585\t.\t+\t.\tgene_id \"ENSG00000186092.7\"; transcript_id \"ENST00000641515.2\"; gene_type \"protein_coding\"; gene_name \"OR4F5\"; transcript_type \"protein_coding\"; transcript_name \"OR4F5-201\"; level 2; protein_id \"ENSP00000493376.2\"; hgnc_id \"HGNC:14825\"; tag \"MANE_Select\";\n"


@pytest.fixture
def mock_writer():
    return SpyWriter()


@pytest.fixture
def gencode_protein_human(mock_writer):
    with patch('adapters.gencode_protein_adapter.open', mock_open(read_data=SAMPLE_DATA)):
        yield GencodeProtein(
            filepath='dummy.gtf',
            label='gencode_protein',
            organism='HUMAN',
            writer=mock_writer,
            uniprot_sprot_file_path='dummy_sprot.gz',
            uniprot_trembl_file_path='dummy_trembl.gz',
            validate=True
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
    assert parsed['gene_name'] == 'OR4F5'


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


@patch.object(GencodeProtein, 'get_uniprot_xrefs', return_value={'P12345': {'name': 'PROT_ABC', 'dbxrefs': [{'name': 'RefSeq', 'id': 'RS1'}], 'full_name': 'Protein ABC'}})
def test_process_file_writes_json(mock_get_uniprot, mock_writer):
    # Patch pickle.load and mapping files
    with patch('pickle.load', return_value={'ENSP00000493376': ['P12345']}):
        gencode = GencodeProtein(
            filepath='dummy.gtf',
            label='gencode_protein',
            organism='HUMAN',
            writer=mock_writer,
            uniprot_sprot_file_path='dummy_sprot.gz',
            uniprot_trembl_file_path='dummy_trembl.gz',
            validate=True
        )
        # Patch the file opening only for process_file
        with patch('adapters.gencode_protein_adapter.open', mock_open(read_data=SAMPLE_DATA)):
            gencode.process_file()
        first_item = json.loads(mock_writer.contents[0])
        assert '_key' in first_item
        assert 'name' in first_item
        assert 'protein_id' in first_item
        assert 'source' in first_item
        assert 'version' in first_item
        assert 'source_url' in first_item
        assert 'organism' in first_item
        assert 'uniprot_collection' in first_item
        assert 'uniprot_ids' in first_item
        assert 'uniprot_names' in first_item
        assert 'dbxrefs' in first_item
        assert 'uniprot_full_names' in first_item
        assert first_item['name'] == 'OR4F5'
        assert first_item['protein_id'] == 'ENSP00000493376.2'
        assert first_item['source'] == 'GENCODE'
        assert first_item['version'] == 'v43'
        assert first_item['source_url'] == 'https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_43/gencode.v43.chr_patch_hapl_scaff.annotation.gtf.gz'
        assert first_item['organism'] == 'Homo sapiens'
        assert first_item['uniprot_collection'] == 'Swiss-Prot'
        assert first_item['uniprot_ids'] == ['P12345']
        assert first_item['uniprot_names'] == ['PROT_ABC']
        assert first_item['dbxrefs'] == [{'name': 'RefSeq', 'id': 'RS1'}]
        assert first_item['uniprot_full_names'] == ['Protein ABC']
        invalid_doc = {
            '_key': 'ENSP00000493376',
            'protein_id': 'ENSP00000493376.2',
            'source': 'GENCODE',
            'version': 'v43',
            'source_url': 'https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_43/gencode.v43.chr_patch_hapl_scaff.annotation.gtf.gz',
            'organism': 'Homo sapiens',
        }
        with pytest.raises(ValueError):
            gencode.validate_doc(invalid_doc)


def test_init_mouse_organism(mock_writer):
    """Test initialization with MOUSE organism"""
    with patch('pickle.load', return_value={}):
        gencode = GencodeProtein(
            filepath='dummy.gtf',
            label='gencode_protein',
            organism='MOUSE',
            writer=mock_writer,
            uniprot_sprot_file_path='dummy_sprot.gz',
            uniprot_trembl_file_path='dummy_trembl.gz'
        )
        assert gencode.organism == 'Mus musculus'
        assert gencode.version == 'vM36'
        assert gencode.transcript_endpoint == 'mm_transcripts/'
        assert gencode.taxonomy_id == '10090'
        assert 'mouse' in gencode.source_url.lower()


def test_process_file_edge_translates_to(mock_writer):
    """Test process_file with gencode_translates_to label"""
    with patch('pickle.load', return_value={}):
        gencode = GencodeProtein(
            filepath='dummy.gtf',
            label='gencode_translates_to',
            organism='HUMAN',
            writer=mock_writer,
            uniprot_sprot_file_path='dummy_sprot.gz',
            uniprot_trembl_file_path='dummy_trembl.gz',
            validate=True
        )
        # Patch the file opening for process_file
        with patch('adapters.gencode_protein_adapter.open', mock_open(read_data=SAMPLE_DATA)):
            gencode.process_file()

        # Parse the output
        first_item = json.loads(mock_writer.contents[0])
        assert '_from' in first_item
        assert '_to' in first_item
        assert first_item['_from'].startswith('transcripts/')
        assert first_item['_to'].startswith('proteins/')
        assert first_item['source'] == 'GENCODE'
        assert first_item['name'] == 'translates to'
        assert first_item['inverse_name'] == 'translated from'
        assert first_item['biological_process'] == 'ontology_terms/GO_0006412'
