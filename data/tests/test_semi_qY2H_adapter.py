import json
from unittest.mock import patch, mock_open
from adapters.writer import SpyWriter
from adapters.semi_qY2H_adapter import SemiQY2H
import pytest


# allele_type=reference row is filtered out; the four variant rows below each
# exercise a different code path:
#   CCSBVarC003578 -> interactor + coding variant + PPI edge all resolve (success)
#   CCSBVarC003579 -> interactor ORF has no protein_id in the portal API response
#   CCSBVarC003580 -> interactor resolves, but no coding variant found for the spdi/hgvsp
#   CCSBVarC003581 -> interactor + coding variant resolve, but no proteins_proteins edge found
PPI_TSV = (
    'spdi\tsymbol\tensembl_gene_id\tccsb_mutation_id\tCCSB_referenece_orf_id\thgvs_orf\thgvs_protein\tallele_type\t'
    'interactor_id\tinteractor_symbol\tinteractor_ensembl_gene_id\tconsensus_score\twt_consensus_score\tlog2fc\n'
    '\tACSF3\tENSG00000176715\t\tCCSBORF71337\t\t\treference\tCCSBORF54668\tKRT40\tENSG00000204889\t311.16\t311.16\t0\n'
    'NC_000016.10:89102664:C:T\tACSF3\tENSG00000176715\tCCSBVarC003578\tCCSBORF71337\t728C>T\t'
    'ENSP00000320646.4:p.Pro243Leu\tvariant\tCCSBORF54668\tKRT40\tENSG00000204889\t26.99\t311.16\t-3.48\n'
    'NC_000016.10:89102700:A:G\tACSF3\tENSG00000176715\tCCSBVarC003579\tCCSBORF71337\t764A>G\t'
    'ENSP00000320646.4:p.Ala1Val\tvariant\tCCSBORF00000\tUNKNOWN\tENSG00000999999\t10.0\t311.16\t-5.0\n'
    'NC_000016.10:89102800:G:A\tACSF3\tENSG00000176715\tCCSBVarC003580\tCCSBORF71337\t864G>A\t'
    'ENSP00000320646.4:p.Gly10Asp\tvariant\tCCSBORF54668\tKRT40\tENSG00000204889\t15.0\t311.16\t-4.4\n'
    'NC_000016.10:89103000:T:C\tACSF3\tENSG00000176715\tCCSBVarC003581\tCCSBORF71337\t964T>C\t'
    'ENSP00000320646.4:p.Leu50Phe\tvariant\tCCSBORF54670\tOTHER\tENSG00000888888\t5.0\t300.0\t-6.0\n'
)

PHENOTYPES_TSV = (
    'spdi\tsymbol\tensembl_gene_id\tccsb_mutation_id\tCCSB_referenece_orf_id\thgvs_orf\thgvs_protein\tnorm_dist_rms\n'
    'NC_000016.10:89102664:C:T\tACSF3\tENSG00000176715\tCCSBVarC003578\tCCSBORF71337\t728C>T\t'
    'ENSP00000320646.4:p.Pro243Leu\t0.3868541857467328\n'
)

MOCKED_ORF_PROTEIN_MAP = {
    '@graph': [
        {'orf_id': 'CCSBORF54668', 'protein_id': 'ENSP00000366984.5'},
        {'orf_id': 'CCSBORF54670', 'protein_id': 'ENSP00000111111.3'},
    ]
}

MOCKED_CODING_VARIANTS = {
    ('NC_000016.10:89102664:C:T', 'ENSP00000320646', 'p.Pro243Leu'): ['ACSF3_ENST00000317447_p.Pro243Leu_c.728C-T'],
    ('NC_000016.10:89103000:T:C', 'ENSP00000320646', 'p.Leu50Phe'): ['ACSF3_ENST00000317447_p.Leu50Phe_c.964T-C'],
}

MOCKED_PPI_EDGES = {
    ('ENSP00000320646', 'ENSP00000366984'): [
        '000002a5a51a3c5a92fc1245bb32701679a33f20b67baff8dfa1a359998dafa4',
        '111112a5a51a3c5a92fc1245bb32701679a33f20b67baff8dfa1a359998dafa4',
    ],
}

MOCKED_FILE_FILESET = {
    'method': 'yeast two-hybrid',
    'class': 'observed data',
}


@patch('adapters.semi_qY2H_adapter.get_file_fileset_by_accession_in_arangodb', return_value=MOCKED_FILE_FILESET)
@patch('adapters.semi_qY2H_adapter.bulk_query_proteins_proteins_edge_keys_in_arangodb', return_value=MOCKED_PPI_EDGES)
@patch('adapters.semi_qY2H_adapter.bulk_query_coding_variants_from_spdi_in_arangodb', return_value=MOCKED_CODING_VARIANTS)
@patch('adapters.semi_qY2H_adapter.requests.get')
@patch('gzip.open', new_callable=mock_open, read_data=PPI_TSV)
def test_process_file_coding_variants_PPI(
    mock_gzip_open, mock_requests_get, mock_coding_variants, mock_ppi_edges, mock_file_fileset, caplog
):
    mock_requests_get.return_value.json.return_value = MOCKED_ORF_PROTEIN_MAP

    writer = SpyWriter()
    adapter = SemiQY2H(
        'IGVFFI2460BBXY.tsv.gz',
        label='coding_variants_PPI',
        writer=writer,
        validate=True
    )
    with caplog.at_level('WARNING'):
        adapter.process_file()

    records = [json.loads(c) for c in writer.contents if c != '\n']
    # row A matches two proteins_proteins edges -> one coding_variants_PPI edge per match
    assert len(records) == 2

    expected_ppi_keys = {
        '000002a5a51a3c5a92fc1245bb32701679a33f20b67baff8dfa1a359998dafa4',
        '111112a5a51a3c5a92fc1245bb32701679a33f20b67baff8dfa1a359998dafa4',
    }
    assert {r['_to'].split('/')[1] for r in records} == expected_ppi_keys
    assert {r['_key'] for r in records} == {
        'ACSF3_ENST00000317447_p.Pro243Leu_c.728C-T_' + key + '_IGVFFI2460BBXY'
        for key in expected_ppi_keys
    }

    record = records[0]
    assert record['_from'] == 'coding_variants/ACSF3_ENST00000317447_p.Pro243Leu_c.728C-T'
    assert record['name'] == 'modulates interaction of'
    assert record['inverse_name'] == 'interaction modulated by'
    assert record['consensus_score'] == 26.99
    assert record['wt_consensus_score'] == 311.16
    assert record['log2FC'] == -3.48
    assert record['molecular_function'] == 'ontology_terms/GO_0005515'
    assert record['method'] == 'yeast two-hybrid'
    assert record['label'] == 'protein variant effect'
    assert record['class'] == 'observed data'
    assert record['source'] == 'IGVF'
    assert record['source_url'] == 'https://data.igvf.org/tabular-files/IGVFFI2460BBXY'
    assert record['files_filesets'] == 'files_filesets/IGVFFI2460BBXY'

    assert 'Skipping CCSBVarC003579: no protein_id for interactor CCSBORF00000' in caplog.text
    assert 'Skipping CCSBVarC003580: no coding variant found' in caplog.text
    assert 'Skipping CCSBVarC003581: no proteins_proteins edge found for ENSP00000320646, ENSP00000111111' in caplog.text


@patch('adapters.semi_qY2H_adapter.get_file_fileset_by_accession_in_arangodb', return_value=MOCKED_FILE_FILESET)
@patch('adapters.semi_qY2H_adapter.bulk_query_proteins_proteins_edge_keys_in_arangodb', return_value=MOCKED_PPI_EDGES)
@patch('adapters.semi_qY2H_adapter.bulk_query_coding_variants_from_spdi_in_arangodb')
@patch('adapters.semi_qY2H_adapter.requests.get')
@patch('gzip.open', new_callable=mock_open, read_data=PPI_TSV)
def test_multiple_coding_variants_logs_warning_and_uses_first_PPI(
    mock_gzip_open, mock_requests_get, mock_coding_variants, mock_ppi_edges, mock_file_fileset, caplog
):
    mock_requests_get.return_value.json.return_value = MOCKED_ORF_PROTEIN_MAP
    mock_coding_variants.return_value = {
        ('NC_000016.10:89102664:C:T', 'ENSP00000320646', 'p.Pro243Leu'): [
            'ACSF3_ENST00000317447_p.Pro243Leu_c.728C-T',
            'ACSF3_ENST99999999_p.Pro243Leu_c.728C-T',
        ],
    }

    writer = SpyWriter()
    adapter = SemiQY2H(
        'IGVFFI2460BBXY.tsv.gz',
        label='coding_variants_PPI',
        writer=writer,
        validate=True
    )
    with caplog.at_level('WARNING'):
        adapter.process_file()

    records = [json.loads(c) for c in writer.contents if c != '\n']
    assert len(records) == 2
    assert all(
        r['_from'] == 'coding_variants/ACSF3_ENST00000317447_p.Pro243Leu_c.728C-T' for r in records)
    assert (
        'Multiple coding variants found for NC_000016.10:89102664:C:T, ENSP00000320646, p.Pro243Leu: '
        "['ACSF3_ENST00000317447_p.Pro243Leu_c.728C-T', 'ACSF3_ENST99999999_p.Pro243Leu_c.728C-T'], "
        'using ACSF3_ENST00000317447_p.Pro243Leu_c.728C-T'
    ) in caplog.text


@patch('adapters.semi_qY2H_adapter.get_file_fileset_by_accession_in_arangodb', return_value=MOCKED_FILE_FILESET)
@patch('adapters.semi_qY2H_adapter.bulk_query_coding_variants_from_spdi_in_arangodb')
@patch('gzip.open', new_callable=mock_open, read_data=PHENOTYPES_TSV)
def test_process_file_coding_variants_phenotypes(mock_gzip_open, mock_bulk_query, mock_file_fileset):
    mock_bulk_query.return_value = {
        ('NC_000016.10:89102664:C:T', 'ENSP00000320646', 'p.Pro243Leu'): ['ACSF3_ENST00000317447_p.Pro243Leu_c.728C-T'],
    }

    writer = SpyWriter()
    adapter = SemiQY2H(
        'IGVFFI7393MGJK.tsv.gz',
        label='coding_variants_phenotypes',
        writer=writer,
        validate=True
    )
    adapter.process_file()

    records = [json.loads(c) for c in writer.contents if c != '\n']
    assert len(records) == 1

    record = records[0]
    assert record['_key'] == 'ACSF3_ENST00000317447_p.Pro243Leu_c.728C-T_IGVFFI7393MGJK'
    assert record['_from'] == 'coding_variants/ACSF3_ENST00000317447_p.Pro243Leu_c.728C-T'
    assert record['_to'] == 'ontology_terms/GO_0005515'
    assert record['name'] == 'mutational effect'
    assert record['inverse_name'] == 'altered due to mutation'
    assert record['norm_dist_rms'] == 0.3868541857467328
    assert record['method'] == 'yeast two-hybrid'
    assert record['label'] == 'protein variant effect'
    assert record['class'] == 'observed data'
    assert record['source'] == 'IGVF'
    assert record['source_url'] == 'https://data.igvf.org/tabular-files/IGVFFI7393MGJK'
    assert record['files_filesets'] == 'files_filesets/IGVFFI7393MGJK'


def test_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_label. Allowed values: coding_variants_PPI, coding_variants_phenotypes'):
        SemiQY2H(
            'IGVFFI2460BBXY.tsv.gz',
            label='invalid_label',
            writer=writer,
        )


@patch('adapters.semi_qY2H_adapter.get_file_fileset_by_accession_in_arangodb', return_value=MOCKED_FILE_FILESET)
@patch('adapters.semi_qY2H_adapter.bulk_query_coding_variants_from_spdi_in_arangodb', return_value={})
@patch('gzip.open', new_callable=mock_open, read_data=PHENOTYPES_TSV)
def test_validate_doc_invalid(mock_gzip_open, mock_bulk_query, mock_file_fileset):
    writer = SpyWriter()
    adapter = SemiQY2H(
        'IGVFFI7393MGJK.tsv.gz',
        label='coding_variants_phenotypes',
        writer=writer,
        validate=True
    )
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc({'invalid_field': 'bad'})
