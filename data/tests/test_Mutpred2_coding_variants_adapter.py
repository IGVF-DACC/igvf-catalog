from unittest.mock import patch, mock_open
from adapters.writer import SpyWriter
import gzip
import json
from adapters.Mutpred2_coding_variants_adapter import Mutpred2CodingVariantsScores

SAMPLE_MAPPING_TSV = (
    'ENST00000261590.13\tQ873T\tDSG2_ENST00000261590.13_p.Q873T_c.2617_2618delinsAC,DSG2_ENST00000261590.13_p.Q873T_c.2617_2619delinsACC\tc.2617_2618delinsAC,c.2617_2619delinsACC\tNC_000018.10:31546002:CA:AC,NC_000018.10:31546002:CAA:ACC\tNC_000018.10:g.31546003_31546004delinsAC,NC_000018.10:g.31546003_31546005delinsACC\tACA,ACC\t1,1\tCAA\tENSP00000261590.8\tDSG2_HUMAN'
)

SAMPLE_DATA_TSV = (
    'protein_id\ttranscript_id\tgene_id\tgene_symbol\tSubstitution\tMutPred2 score\tMechanisms\n'
    'ENSP00000261590.8\tENST00000261590.13\tENSG00000046604.15\tDSG2\tQ873T\t0.279\t"[{\"Property\": \"VSL2B_disorder\", \"Posterior Probability\": 0.3, \"P-value\": 0.04, \"Effected Position\": \"S869\", \"Type\": \"Loss\"}]"\n'
)


@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_MAPPING_TSV)
def test_load_from_mapping_file_variants(mock_gzip_open):
    writer = SpyWriter()
    adapter = Mutpred2CodingVariantsScores(
        'dummy_accession.tsv.gz', label='variants', writer=writer)
    adapter.load_from_mapping_file()

    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_key'] == 'NC_000018.10:31546002:CA:AC'
    assert first_item['chr'] == 'chr18'
    assert first_item['pos'] == 31546002
    assert first_item['ref'] == 'CA'
    assert first_item['alt'] == 'AC'
