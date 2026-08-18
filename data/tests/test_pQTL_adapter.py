import json
from unittest.mock import patch
import pytest

from adapters.pQTL_adapter import pQTL
from adapters.writer import SpyWriter

SAMPLE_PROTEIN_MAP = {
    'P04217': ['ENSP00000263100'],
    'P00519': ['ENSP00000323315'],
    'P09110': ['ENSP00000357535'],
    'P11310': ['ENSP00000447586'],
    'P12821': ['ENSP00000290866'],
    'P13686': ['ENSP00000264649'],
    'P16112': ['ENSP00000318642'],
    'P16442': ['ENSP00000364913'],
    'P22303': ['ENSP00000264374'],
    'P24666': ['ENSP00000264178'],
    'P26436': ['ENSP00000370720'],
    'P33121': ['ENSP00000357017'],
    'P35609': ['ENSP00000362576'],
    'P37023': ['ENSP00000367859'],
    'P45954': ['ENSP00000216110'],
    'P62736': ['ENSP00000224784'],
    'Q03154': ['ENSP00000301585'],
    'Q15067': ['ENSP00000324802'],
    'Q8NEB7': ['ENSP00000354612'],
    'Q96IU4': ['ENSP00000232892'],
    'Q9BTE6': ['ENSP00000261880'],
    'Q9BYF1': ['ENSP00000384860'],
    'Q9BZC7': ['ENSP00000324133'],
    'Q9H7C9': ['ENSP00000265806'],
    'Q9NPH0': ['ENSP00000302161'],
    'Q9NPJ3': ['ENSP00000222594'],
}


@patch('adapters.pQTL_adapter.get_protein_map_from_arangodb')
@patch('adapters.pQTL_adapter.get_file_fileset_by_accession_in_arangodb')
def test_pQTL_adapter(mock_get_file_fileset, mock_get_protein_map, mocker):
    mock_get_file_fileset.return_value = {
        'class': 'observed data',
        'method': 'pQTL'
    }
    mock_get_protein_map.return_value = SAMPLE_PROTEIN_MAP
    mocker.patch('adapters.pQTL_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    with patch('adapters.pQTL_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True
        adapter = pQTL(filepath='./samples/pQTL_UKB_example.csv',
                       label='variant_protein', writer=writer, validate=True)
        adapter.file_accession = 'IGVFFI0000TEST'
        adapter.process_file()
        mock_get_file_fileset.assert_called_once_with('IGVFFI0000TEST')
        mock_get_protein_map.assert_called_once_with(organism='Homo sapiens')
        docs = [json.loads(item) for item in writer.contents if item.strip()]
        assert len(docs) == 100
        first_item = docs[0]
        assert first_item['_key'] == 'fake_variant_id_ENSP00000263100_UKB'
        assert first_item['_to'] == 'proteins/ENSP00000263100'
        assert first_item['name'] == 'associated with levels of'
        assert first_item['label'] == 'pQTL'
        assert first_item['method'] == 'pQTL'
        assert first_item['class'] == 'observed data'
        assert first_item['files_filesets'] == 'files_filesets/IGVFFI0000TEST'
        assert first_item['neg_log10_pvalue'] == 79.2


def test_validate_doc_invalid(mocker):
    mocker.patch('adapters.pQTL_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    pqtl = pQTL(filepath='./samples/pQTL_UKB_example.csv',
                label='variant_protein', writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        pqtl.validate_doc(invalid_doc)
