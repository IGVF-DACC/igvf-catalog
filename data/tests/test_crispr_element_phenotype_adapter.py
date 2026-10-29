import csv
import gzip
import json
from math import log10
from pathlib import Path
import pytest
from unittest.mock import patch
from adapters.CRISPR_element_phenotype_adapter import CRISPRElementPhenotype
from adapters.ontology_term_validator import OntologyTermValidator
from adapters.writer import SpyWriter

MIGRATION_PATH = './tests/fixtures/IGVFFI5135QZCS_crispr_element_phenotype_migration.example.tsv'
GROWTH_PATH = './tests/fixtures/IGVFFI9584UDAS_crispr_element_phenotype_growth.example.tsv'
FRACTEL_PATH = './tests/fixtures/IGVFFI4336LSYJ_crispr_element_phenotype_fractel.example.csv'


@pytest.fixture
def mock_file_fileset():
    with patch('adapters.CRISPR_element_phenotype_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'method': 'CRISPR screen',
            'class': 'observed data',
            'perturbation': 'CRISPR interference',
            'simple_sample_summaries': ['human HFF-1 cell line from donor(s) IGVFDO0058YJWC'],
            'samples': ['ontology_terms/CLO_0003730'],
            'treatments_term_ids': None,
        }
        yield mock_get_file_fileset


@pytest.fixture
def mock_ontology_term_validator():
    with patch('adapters.CRISPR_element_phenotype_adapter.OntologyTermValidator') as MockValidator:
        MockValidator.normalize_term_key = staticmethod(
            OntologyTermValidator.normalize_term_key)
        mock_validator = MockValidator.return_value
        mock_validator.validate.return_value = True
        mock_validator.ensure.return_value = True
        yield mock_validator


def test_crispr_element_phenotype_genomic_element_migration(mock_file_fileset):
    writer = SpyWriter()
    adapter = CRISPRElementPhenotype(
        filepath=MIGRATION_PATH,
        label='genomic_element',
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
    assert first_item['source_annotation'] == 'candidate enhancer'
    assert first_item['method'] == 'CRISPR screen'
    assert first_item['source'] == 'IGVF'
    assert first_item['source_url'] == 'https://data.igvf.org/tabular-files/IGVFFI5135QZCS/'
    assert first_item['files_filesets'] == 'files_filesets/IGVFFI5135QZCS'


def test_crispr_element_phenotype_genomic_element_phenotype_migration(
        mock_file_fileset, mock_ontology_term_validator):
    writer = SpyWriter()
    adapter = CRISPRElementPhenotype(
        filepath=MIGRATION_PATH,
        label='genomic_element_phenotype',
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
    assert first_item['num_guides_hit'] == 0
    assert first_item['num_guides_nonhit'] == 32
    assert first_item['fraction_guides_hit'] == 0.0
    assert first_item['perturbation'] == 'CRISPR interference'
    assert first_item['label'] == 'regulatory element effect on phenotype'
    assert first_item['name'] == 'associated with'
    assert first_item[
        'biological_context'] == 'human HFF-1 cell line from donor(s) IGVFDO0058YJWC'
    assert first_item['biosample_term'] == 'ontology_terms/CLO_0003730'


def test_crispr_element_phenotype_genomic_element_phenotype_growth(
        mock_file_fileset, mock_ontology_term_validator):
    writer = SpyWriter()
    adapter = CRISPRElementPhenotype(
        filepath=GROWTH_PATH,
        label='genomic_element_phenotype',
        writer=writer,
        validate=True,
    )
    adapter.process_file()

    assert len(writer.contents) == 5
    first_item = json.loads(writer.contents[0])
    assert first_item['_to'] == 'ontology_terms/GO_0008283'
    assert first_item['z_score'] == pytest.approx(-0.122645943)
    assert first_item['p_value'] == pytest.approx(0.718493129)
    assert first_item['num_guides_hit'] == 1
    assert first_item['num_guides_nonhit'] == 31
    assert first_item['fraction_guides_hit'] == pytest.approx(0.03125)
    assert first_item['files_filesets'] == 'files_filesets/IGVFFI9584UDAS'


@pytest.mark.parametrize('compressed', [False, True])
def test_crispr_element_phenotype_fractel(
        mock_file_fileset, mock_ontology_term_validator, tmp_path, compressed):
    mock_file_fileset.return_value.update({
        'file_set_id': 'IGVFDS7817TGWI',
        'simple_sample_summaries': ['human K562 cell line from donor(s) IGVFDO9208RPQQ'],
        'samples': ['ontology_terms/EFO_0002067'],
    })
    filepath = FRACTEL_PATH
    if compressed:
        filepath = str(tmp_path / 'IGVFFI4336LSYJ.csv.gz')
        with gzip.open(filepath, 'wt') as f:
            f.write(Path(FRACTEL_PATH).read_text())

    writers = {}
    for label in CRISPRElementPhenotype.ALLOWED_LABELS:
        writer = SpyWriter()
        CRISPRElementPhenotype(
            filepath=filepath, label=label, writer=writer, validate=True,
        ).process_file()
        writers[label] = [json.loads(line) for line in writer.contents]

    nodes = writers['genomic_element']
    edges = writers['genomic_element_phenotype']
    assert len(nodes) == len(edges) == 3
    assert nodes[0]['_key'] == 'CRISPR_chr7_74019708_74019787_GRCh38_IGVFFI4336LSYJ'
    assert (nodes[0]['chr'], nodes[0]['start'], nodes[0]['end']) == (
        'chr7', 74019708, 74019787)
    for node, edge in zip(nodes, edges):
        assert edge['_from'] == f'genomic_elements/{node["_key"]}'
        assert edge['_key'] == f'{node["_key"]}_GO_0008283'
        assert edge['_to'] == 'ontology_terms/GO_0008283'
        assert edge['files_filesets'] == 'files_filesets/IGVFFI4336LSYJ'
        assert edge['source_url'] == 'https://data.igvf.org/tabular-files/IGVFFI4336LSYJ/'
        assert edge['biosample_term'] == 'ontology_terms/EFO_0002067'
        assert edge['biological_context'] == mock_file_fileset.return_value['simple_sample_summaries'][0]
        assert not {'z_score', 'num_guides', 'num_guides_hit',
                    'num_guides_nonhit', 'fraction_guides_hit'} & edge.keys()
    assert edges[0]['log2FC'] == pytest.approx(-0.2722013279866264)
    assert edges[0]['p_value'] == edges[0]['p_value_adj'] == 0
    assert edges[0]['neg_log10_pvalue'] == edges[0]['neg_log10_pvalue_adj'] == 240
    assert edges[0]['significant'] is True
    assert edges[1]['p_value'] == pytest.approx(1e-7)
    assert edges[1]['p_value_adj'] == pytest.approx(1.0785498489425983e-7)
    assert edges[1]['neg_log10_pvalue'] == pytest.approx(7)
    assert edges[1]['neg_log10_pvalue_adj'] == pytest.approx(
        -log10(1.0785498489425983e-7))
    assert edges[2]['log2FC'] == pytest.approx(0.0202159843218936)
    assert edges[2]['significant'] is False


@pytest.mark.parametrize('adjusted_p_value,expected', [
    (0.049, True), (0.05, False), (0.051, False),
])
def test_fractel_significance_uses_adjusted_p_value(
        mock_file_fileset, mock_ontology_term_validator, tmp_path,
        adjusted_p_value, expected):
    with open(FRACTEL_PATH) as f:
        reader = csv.DictReader(f, delimiter='\t')
        row = next(reader)
    row['FRACTEL_pval'] = '0.001'
    row['FRACTEL_pval_fdr_corr'] = str(adjusted_p_value)
    filepath = tmp_path / 'IGVFFI4336LSYJ.csv'
    with filepath.open('w') as f:
        writer = csv.DictWriter(f, fieldnames=row, delimiter='\t')
        writer.writeheader()
        writer.writerow(row)
    writer = SpyWriter()
    CRISPRElementPhenotype(
        filepath=str(filepath), label='genomic_element_phenotype',
        writer=writer, validate=True,
    ).process_file()
    assert json.loads(writer.contents[0])['significant'] is expected


def test_crispr_element_phenotype_invalid_label(mock_file_fileset):
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_label'):
        CRISPRElementPhenotype(
            filepath=MIGRATION_PATH,
            label='invalid_label',
            writer=writer,
        )


def test_crispr_element_phenotype_unsupported_accession(mock_file_fileset, tmp_path):
    sample = tmp_path / 'IGVFFI0000AAAA_unsupported.tsv'
    sample.write_text('dhs\tdhs_coords\n')
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Unsupported file accession'):
        CRISPRElementPhenotype(
            filepath=str(sample),
            label='genomic_element',
            writer=writer,
        )


def test_parse_element_coords():
    chrom, start, end = CRISPRElementPhenotype._parse_element_coords(
        'chr1:101174581-101175330_93')
    assert chrom == 'chr1'
    assert start == 101174581
    assert end == 101175330


def test_parse_element_coords_skips_na_gene_controls():
    assert CRISPRElementPhenotype._parse_element_coords(
        'NA:NA-NA_ABI2') is None
    assert CRISPRElementPhenotype._parse_element_coords(
        'NA:NA-NA_ABL1') is None


def test_parse_element_coords_raises_on_unrecognized():
    with pytest.raises(ValueError, match='Unrecognized element coordinates'):
        CRISPRElementPhenotype._parse_element_coords('not_a_coordinate')
    with pytest.raises(ValueError, match='Unrecognized element coordinates'):
        CRISPRElementPhenotype._parse_element_coords('NA:something_else')


def test_crispr_element_phenotype_skips_na_coordinate_rows(
        mock_file_fileset, mock_ontology_term_validator, tmp_path):
    sample = tmp_path / 'IGVFFI5135QZCS_mixed.tsv'
    sample.write_text(
        'dhs\tdhs_coords\tdhs_count\tavg_migration_pZ\thit_gRNA_count_mig\t'
        'nonhit_gRNA_count_mig\tfraction_hit_mig\tmigration_pval\tmig_significant\n'
        '93\tchr1:101174581-101175330_93\t32\t0.011457821\t0\t32\t0\t0.623284698\tFALSE\n'
        'ABI2\tNA:NA-NA_ABI2\t6\t-0.2183156\t0\t6\t0\t1\tFALSE\n'
        'ABL1\tNA:NA-NA_ABL1\t6\t0.72319595\t0\t6\t0\t1\tFALSE\n'
    )
    writer = SpyWriter()
    adapter = CRISPRElementPhenotype(
        filepath=str(sample),
        label='genomic_element_phenotype',
        writer=writer,
        validate=True,
    )
    adapter.process_file()

    assert len(writer.contents) == 1
    item = json.loads(writer.contents[0])
    assert item['_from'] == 'genomic_elements/CRISPR_chr1_101174581_101175330_GRCh38_IGVFFI5135QZCS'


@pytest.mark.parametrize('accession', ['IGVFFI5135QZCS', 'IGVFFI9584UDAS'])
@pytest.mark.parametrize('p_value,source_flag,expected', [
    (0.049, 'FALSE', True),
    (0.05, 'TRUE', False),
    (0.051, 'TRUE', False),
])
def test_significance_uses_adapter_threshold(
        mock_file_fileset, mock_ontology_term_validator, tmp_path, accession, p_value, source_flag, expected):
    config = CRISPRElementPhenotype.FILE_CONFIG[accession]
    row = {
        'dhs_coords': 'chr1:100-200_1', 'dhs_count': 2,
        config['z_score_col']: 0,
        config['p_value_col']: p_value,
        config['num_guides_hit_col']: 0,
        config['num_guides_nonhit_col']: 2,
        config['fraction_guides_hit_col']: 0,
        'mig_significant': source_flag, 'growth_significant': source_flag,
    }
    sample = tmp_path / f'{accession}_threshold.tsv'
    sample.write_text('\t'.join(row) + '\n' +
                      '\t'.join(map(str, row.values())) + '\n')
    writer = SpyWriter()
    CRISPRElementPhenotype(
        filepath=str(sample), label='genomic_element_phenotype',
        writer=writer, validate=True,
    ).process_file()
    assert json.loads(writer.contents[0])['significant'] is expected
