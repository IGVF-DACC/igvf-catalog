import json
import pytest
from unittest.mock import patch
from adapters.CRISPR_E2P_adapter import CRISPR_E2P
from adapters.writer import SpyWriter


@pytest.fixture
def mock_file_fileset():
    with patch('adapters.CRISPR_E2P_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'method': 'CRISPR screen',
            'class': 'observed data',
            'crispr_modality': 'interference',
            'simple_sample_summaries': ['human HFF-1 cell line from donor(s) IGVFDO0058YJWC'],
            'samples': ['ontology_terms/CLO_0003730'],
            'treatments_term_ids': None,
        }
        yield mock_get_file_fileset


def test_crispr_e2p_genomic_element_migration(mock_file_fileset):
    writer = SpyWriter()
    adapter = CRISPR_E2P(
        filepath='./samples/crispr_e2p_migration.example.tsv',
        label='genomic_element',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI5135QZCS/',
        writer=writer,
        validate=True,
    )
    adapter.process_file()

    assert len(writer.contents) == 5
    first_item = json.loads(writer.contents[0])
    assert first_item['_key'] == 'CRISPR_chr1_101174581_101175330_GRCh38_IGVFFI5135QZCS'
    assert first_item['chr'] == 'chr1'
    assert first_item['start'] == 101174581
    assert first_item['end'] == 101175330
    assert first_item['type'] == 'tested elements'
    assert first_item['source_annotation'] == 'enhancer'
    assert first_item['method'] == 'CRISPR screen'
    assert first_item['source'] == 'IGVF'
    assert first_item['files_filesets'] == 'files_filesets/IGVFFI5135QZCS'


def test_crispr_e2p_genomic_element_phenotype_migration(mock_file_fileset):
    writer = SpyWriter()
    adapter = CRISPR_E2P(
        filepath='./samples/crispr_e2p_migration.example.tsv',
        label='genomic_element_phenotype',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI5135QZCS/',
        writer=writer,
        validate=True,
    )
    adapter.process_file()

    assert len(writer.contents) == 5
    first_item = json.loads(writer.contents[0])
    assert first_item['_from'] == 'genomic_elements/CRISPR_chr1_101174581_101175330_GRCh38_IGVFFI5135QZCS'
    assert first_item['_to'] == 'ontology_terms/GO_0016477'
    assert first_item['_key'] == 'CRISPR_chr1_101174581_101175330_GRCh38_IGVFFI5135QZCS_GO_0016477'
    assert first_item['z_score'] == pytest.approx(0.011457821)
    assert first_item['p_value'] == pytest.approx(0.623284698)
    assert first_item['significant'] is False
    assert first_item['num_guides'] == 32
    assert first_item['hit_guide_count'] == 0
    assert first_item['nonhit_guide_count'] == 32
    assert first_item['fraction_hit'] == 0.0
    assert first_item['crispr_modality'] == 'interference'
    assert first_item['label'] == 'regulatory genomic element effect on phenotype'
    assert first_item['name'] == 'associated with'
    assert first_item[
        'biological_context'] == 'human HFF-1 cell line from donor(s) IGVFDO0058YJWC'
    assert first_item['biosample_term'] == 'ontology_terms/CLO_0003730'


def test_crispr_e2p_genomic_element_phenotype_growth(mock_file_fileset):
    writer = SpyWriter()
    adapter = CRISPR_E2P(
        filepath='./samples/crispr_e2p_growth.example.tsv',
        label='genomic_element_phenotype',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI9584UDAS/',
        writer=writer,
        validate=True,
    )
    adapter.process_file()

    assert len(writer.contents) == 5
    first_item = json.loads(writer.contents[0])
    assert first_item['_to'] == 'ontology_terms/GO_0016049'
    assert first_item['z_score'] == pytest.approx(-0.122645943)
    assert first_item['p_value'] == pytest.approx(0.718493129)
    assert first_item['hit_guide_count'] == 1
    assert first_item['nonhit_guide_count'] == 31
    assert first_item['fraction_hit'] == pytest.approx(0.03125)
    assert first_item['files_filesets'] == 'files_filesets/IGVFFI9584UDAS'


def test_crispr_e2p_invalid_label(mock_file_fileset):
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_label'):
        CRISPR_E2P(
            filepath='./samples/crispr_e2p_migration.example.tsv',
            label='invalid_label',
            source_url='https://api.data.igvf.org/tabular-files/IGVFFI5135QZCS/',
            writer=writer,
        )


def test_crispr_e2p_unsupported_accession(mock_file_fileset):
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Unsupported file accession'):
        CRISPR_E2P(
            filepath='./samples/crispr_e2p_migration.example.tsv',
            label='genomic_element',
            source_url='https://api.data.igvf.org/tabular-files/IGVFFI0000AAAA/',
            writer=writer,
        )


def test_parse_element_coords():
    chrom, start, end = CRISPR_E2P._parse_element_coords(
        'chr1:101174581-101175330_93')
    assert chrom == 'chr1'
    assert start == 101174581
    assert end == 101175330


def test_parse_element_coords_skips_na_gene_controls():
    assert CRISPR_E2P._parse_element_coords('NA:NA-NA_ABI2') is None
    assert CRISPR_E2P._parse_element_coords('NA:NA-NA_ABL1') is None


def test_parse_element_coords_raises_on_unrecognized():
    with pytest.raises(ValueError, match='Unrecognized element coordinates'):
        CRISPR_E2P._parse_element_coords('not_a_coordinate')
    with pytest.raises(ValueError, match='Unrecognized element coordinates'):
        CRISPR_E2P._parse_element_coords('NA:something_else')


def test_crispr_e2p_skips_na_coordinate_rows(mock_file_fileset, tmp_path):
    sample = tmp_path / 'mixed.tsv'
    sample.write_text(
        'dhs\tdhs_coords\tdhs_count\tavg_migration_pZ\thit_gRNA_count_mig\t'
        'nonhit_gRNA_count_mig\tfraction_hit_mig\tmigration_pval\tmig_significant\n'
        '93\tchr1:101174581-101175330_93\t32\t0.011457821\t0\t32\t0\t0.623284698\tFALSE\n'
        'ABI2\tNA:NA-NA_ABI2\t6\t-0.2183156\t0\t6\t0\t1\tFALSE\n'
        'ABL1\tNA:NA-NA_ABL1\t6\t0.72319595\t0\t6\t0\t1\tFALSE\n'
    )
    writer = SpyWriter()
    adapter = CRISPR_E2P(
        filepath=str(sample),
        label='genomic_element_phenotype',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI5135QZCS/',
        writer=writer,
        validate=True,
    )
    adapter.process_file()

    assert len(writer.contents) == 1
    item = json.loads(writer.contents[0])
    assert item['_from'] == 'genomic_elements/CRISPR_chr1_101174581_101175330_GRCh38_IGVFFI5135QZCS'
