import json
import tarfile
from unittest.mock import patch

import pytest

from adapters.adastra_asb_adapter import ASB
from adapters.writer import SpyWriter


FILE_ACCESSION = 'IGVFFI5943XCOS'
SAMPLE_DIR = './samples/allele_specific_binding'
SAMPLE_PROTEIN_MAP = {
    'P18846': ['ENSP00000262053'],  # ATF1_HUMAN
    'P17098': ['ENSP00000262317'],  # ZNF8_HUMAN
}


@pytest.fixture
def sample_archive(tmp_path):
    archive_filepath = tmp_path / f'{FILE_ACCESSION}.tar.gz'
    with tarfile.open(archive_filepath, 'w:gz') as archive:
        archive.add(SAMPLE_DIR, arcname='.')
    return str(archive_filepath)


@pytest.fixture
def mock_file_fileset():
    """Mock get_file_fileset_by_accession_in_arangodb so ArangoDB is not required."""
    with patch('adapters.adastra_asb_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'class': 'observed data',
            'method': 'ADASTRA'
        }
        yield mock_get_file_fileset


@pytest.fixture
def mock_protein_map():
    with patch('adapters.protein_map.get_protein_map_from_arangodb') as mock_get:
        mock_get.return_value = SAMPLE_PROTEIN_MAP
        yield mock_get


@pytest.fixture
def mock_bulk_check_variants():
    """Mock bulk_check_variants_in_arangodb. Defaults to treating every
    computed variant id as already loaded, so tests that aren't specifically
    exercising the existence check still see edges emitted; override
    .side_effect/.return_value in a test to exercise the skip path."""
    with patch('adapters.adastra_asb_adapter.bulk_check_variants_in_arangodb') as mock_check:
        mock_check.side_effect = lambda variant_ids, **kwargs: set(
            variant_ids)
        yield mock_check


def test_adastra_asb_adapter_invalid_label(sample_archive):
    """Test invalid label handling"""
    with pytest.raises(ValueError, match='Invalid label'):
        ASB(filepath=sample_archive, label='invalid_label')


@patch('adapters.adastra_asb_adapter.build_variant_id')
def test_adastra_asb_adapter_process_file_asb(mock_build_variant_id, mock_file_fileset, mock_protein_map, mock_bulk_check_variants, sample_archive):
    """Test processing file with asb label"""
    # Set up mock data
    mock_build_variant_id.return_value = 'NC_000019.10:9435653:C:A'

    adapter = ASB(filepath=sample_archive,
                  label='asb', writer=SpyWriter(), validate=True)

    # Actually call process_file to test the full functionality
    adapter.process_file()

    mock_protein_map.assert_called_once_with(
        field='uniprot_ids',
        organism='Homo sapiens',
        dbxref_name=None,
    )
    # Verify that some output was generated
    assert len(adapter.writer.contents) > 0
    assert adapter.file_accession == FILE_ACCESSION

    # Parse the first output item
    first_item = json.loads(adapter.writer.contents[0])

    # Verify the structure of the output
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert first_item['_from'].startswith('variants/')
    assert first_item['_to'].startswith('proteins/')
    assert 'chr' in first_item
    assert 'rsid' in first_item
    assert 'motif_fc' in first_item
    assert first_item['motif_fc'] is None or isinstance(
        first_item['motif_fc'], (int, float))
    assert 'motif_pos' in first_item
    assert first_item['motif_pos'] is None or isinstance(
        first_item['motif_pos'], int)
    assert 'motif_orient' in first_item
    assert 'motif_conc' in first_item
    assert first_item['source'] == ASB.SOURCE
    assert first_item['label'] == 'allele-specific binding'
    assert first_item['method'] == 'ADASTRA'
    assert first_item['class'] == 'observed data'
    assert first_item['files_filesets'] == f'files_filesets/{FILE_ACCESSION}'
    assert first_item['name'] == 'modulates binding of'
    assert first_item['inverse_name'] == 'binding modulated by'
    assert first_item['biological_process'] == 'ontology_terms/GO_0051101'
    assert isinstance(first_item['es_mean_ref'], float)
    assert isinstance(first_item['es_mean_alt'], float)
    assert 'neg_log10_pvalue_adj_ref' in first_item
    assert 'neg_log10_pvalue_adj_alt' in first_item
    assert 'biological_context' in first_item
    assert 'biosample_term' in first_item
    assert first_item['biosample_term'].startswith('ontology_terms/')
    assert 'source_url' in first_item

    invalid_doc = {
        '_key': 'NC_000019.10:9435653:C:A',
        '_from': 'variants/NC_000019.10:9435653:C:A',
        '_to': 'proteins/ENSP00000383070',
        'chr': 'chr10',
        'rsid': 'rs1234567890',
    }
    with pytest.raises(ValueError, match='Document validation failed'):
        adapter.validate_doc(invalid_doc)


@patch('adapters.adastra_asb_adapter.build_variant_id')
def test_adastra_asb_adapter_skips_edge_when_variant_not_loaded(mock_build_variant_id, mock_file_fileset, mock_protein_map, mock_bulk_check_variants, sample_archive, caplog):
    """ADASTRA never creates variant nodes itself, so a variant that isn't
    already in the variants collection must be skipped, not turned into a
    dangling edge."""
    mock_build_variant_id.return_value = 'NC_000019.10:9435653:C:A'
    mock_bulk_check_variants.side_effect = None
    mock_bulk_check_variants.return_value = set()

    adapter = ASB(filepath=sample_archive,
                  label='asb', writer=SpyWriter(), validate=True)
    adapter.process_file()

    non_empty_contents = [
        content for content in adapter.writer.contents if content.strip()]
    assert len(non_empty_contents) == 0
    assert 'variant not found in variants collection' in caplog.text


ASB_HEADER = (
    '#chr\tpos\tID\tref\talt\trepeat_type\tmean_BAD\tmean_SNP_per_segment\t'
    'total_cover\tn_aggregated\tes_mean_ref\tes_mean_alt\tlogitp_ref\t'
    'fdrp_bh_ref\tlogitp_alt\tfdrp_bh_alt\tmotif_log_pref\tmotif_log_palt\t'
    'motif_fc\tmotif_pos\tmotif_orient\tmotif_conc\tnovel'
)


@pytest.fixture
def zero_fdrp_archive(tmp_path):
    """Archive with a single row whose fdrp_bh_ref/alt are 0 (the -log10 edge case)."""
    # fdrp_bh_ref (col 13) and fdrp_bh_alt (col 15) are both 0.
    row = (
        'chr19\t9435653.0\trs1433060\tC\tA\t\t1.25\t263.5\t73.0\t2.0\t'
        '1.4349511461894011\t-1.104751195642913\t4.221586590047205e-05\t0\t'
        '0.9967883068007664\t0\t2.003495359068703\t1.968913183373999\t'
        '-0.1148795010225674\t10\t-\tNo Hit\tFalse'
    )
    tsv_path = tmp_path / 'ATF1_HUMAN@HepG2__hepatoblastoma_.tsv'
    tsv_path.write_text(f'{ASB_HEADER}\n{row}\n')

    archive_filepath = tmp_path / f'{FILE_ACCESSION}.tar.gz'
    with tarfile.open(archive_filepath, 'w:gz') as archive:
        archive.add(str(tsv_path),
                    arcname='ATF1_HUMAN@HepG2__hepatoblastoma_.tsv')
    return str(archive_filepath)


@patch('adapters.adastra_asb_adapter.build_variant_id')
def test_adastra_asb_adapter_caps_zero_fdrp_instead_of_infinity(mock_build_variant_id, mock_file_fileset, mock_protein_map, mock_bulk_check_variants, zero_fdrp_archive):
    """When fdrp_bh is 0, neg_log10_pvalue_adj must be capped, not float('inf')."""
    mock_build_variant_id.return_value = 'NC_000019.10:9435653:C:A'

    adapter = ASB(filepath=zero_fdrp_archive,
                  label='asb', writer=SpyWriter())
    adapter.process_file()

    non_empty_contents = [
        content for content in adapter.writer.contents if content.strip()]
    assert len(non_empty_contents) > 0

    for content in non_empty_contents:
        item = json.loads(content)
        assert item['neg_log10_pvalue_adj_ref'] == ASB.MAX_LOG10_PVALUE
        assert item['neg_log10_pvalue_adj_alt'] == ASB.MAX_LOG10_PVALUE
        # allow_nan=False raises on Infinity/NaN, guaranteeing valid JSON output.
        json.dumps(item, allow_nan=False)


@pytest.fixture
def directional_score_archive(tmp_path):
    """Archive with rows covering every branch of ASB._compute_score:
    ref-only significant, alt-only significant, both significant, neither."""
    rows = [
        # fdrp_bh_ref=0.01 (col 13), fdrp_bh_alt=0.5 (col 15) -> ref-only significant
        'chr19\t9435653.0\trs1\tC\tA\t\t1.25\t263.5\t73.0\t2.0\t'
        '1.0\t-1.0\t4.221586590047205e-05\t0.01\t'
        '0.9967883068007664\t0.5\t2.003495359068703\t1.968913183373999\t'
        '-0.1148795010225674\t10\t-\tNo Hit\tFalse',
        # fdrp_bh_ref=0.5, fdrp_bh_alt=0.02 -> alt-only significant
        'chr19\t9435654.0\trs2\tC\tA\t\t1.25\t263.5\t73.0\t2.0\t'
        '1.0\t-1.0\t4.221586590047205e-05\t0.5\t'
        '0.9967883068007664\t0.02\t2.003495359068703\t1.968913183373999\t'
        '-0.1148795010225674\t10\t-\tNo Hit\tFalse',
        # fdrp_bh_ref=0.01, fdrp_bh_alt=0.01 -> both significant
        'chr19\t9435655.0\trs3\tC\tA\t\t1.25\t263.5\t73.0\t2.0\t'
        '1.0\t-1.0\t4.221586590047205e-05\t0.01\t'
        '0.9967883068007664\t0.01\t2.003495359068703\t1.968913183373999\t'
        '-0.1148795010225674\t10\t-\tNo Hit\tFalse',
        # fdrp_bh_ref=0.5, fdrp_bh_alt=0.5 -> neither significant
        'chr19\t9435656.0\trs4\tC\tA\t\t1.25\t263.5\t73.0\t2.0\t'
        '1.0\t-1.0\t4.221586590047205e-05\t0.5\t'
        '0.9967883068007664\t0.5\t2.003495359068703\t1.968913183373999\t'
        '-0.1148795010225674\t10\t-\tNo Hit\tFalse',
    ]
    tsv_path = tmp_path / 'ATF1_HUMAN@HepG2__hepatoblastoma_.tsv'
    tsv_path.write_text(f'{ASB_HEADER}\n' + '\n'.join(rows) + '\n')

    archive_filepath = tmp_path / f'{FILE_ACCESSION}.tar.gz'
    with tarfile.open(archive_filepath, 'w:gz') as archive:
        archive.add(str(tsv_path),
                    arcname='ATF1_HUMAN@HepG2__hepatoblastoma_.tsv')
    return str(archive_filepath)


@patch('adapters.adastra_asb_adapter.build_variant_id')
def test_adastra_asb_adapter_computes_directional_score(mock_build_variant_id, mock_file_fileset, mock_protein_map, mock_bulk_check_variants, directional_score_archive):
    """score should be the negative ref p-value, the positive alt p-value, or
    None when both or neither allele is significant - computed at load time
    rather than by the API router."""
    mock_build_variant_id.side_effect = [
        'NC_000019.10:9435653:C:A',
        'NC_000019.10:9435654:C:A',
        'NC_000019.10:9435655:C:A',
        'NC_000019.10:9435656:C:A',
    ]

    adapter = ASB(filepath=directional_score_archive,
                  label='asb', writer=SpyWriter())
    adapter.process_file()

    non_empty_contents = [
        content for content in adapter.writer.contents if content.strip()]
    items_by_from = {
        json.loads(content)['_from']: json.loads(content)
        for content in non_empty_contents
    }

    assert items_by_from['variants/NC_000019.10:9435653:C:A']['score'] == -0.01
    assert items_by_from['variants/NC_000019.10:9435654:C:A']['score'] == 0.02
    assert items_by_from['variants/NC_000019.10:9435655:C:A']['score'] is None
    assert items_by_from['variants/NC_000019.10:9435656:C:A']['score'] is None


@patch('adapters.adastra_asb_adapter.build_variant_id')
def test_adastra_asb_adapter_process_file_with_mock_unmatched_ensembl(mock_build_variant_id, mock_file_fileset, mock_protein_map, mock_bulk_check_variants, sample_archive):
    """Test process_file method with mocked protein mapping"""
    # Set up mock data
    mock_build_variant_id.return_value = 'NC_000019.10:9435653:C:A'
    mock_protein_map.return_value = {
        'P18846': ['ENSP00000383070', 'ENSP00000412345']  # ATF1_HUMAN
    }

    adapter = ASB(filepath=sample_archive,
                  label='asb', writer=SpyWriter())

    # Call process_file
    adapter.process_file()

    mock_protein_map.assert_called_once_with(
        field='uniprot_ids',
        organism='Homo sapiens',
        dbxref_name=None,
    )
    # Filter out empty lines and verify output was generated
    non_empty_contents = [
        content for content in adapter.writer.contents if content.strip()]
    assert len(non_empty_contents) > 0

    # Verify the structure of outputs
    for content in non_empty_contents:
        item = json.loads(content)
        assert '_key' in item
        assert '_from' in item
        assert '_to' in item
        assert item['_from'] == 'variants/NC_000019.10:9435653:C:A'
        assert item['_to'] in (
            'proteins/ENSP00000383070', 'proteins/ENSP00000412345')
        assert item['source'] == ASB.SOURCE
        assert item['files_filesets'] == f'files_filesets/{FILE_ACCESSION}'


@patch('adapters.adastra_asb_adapter.build_variant_id')
def test_adastra_asb_adapter_process_file_skip_unmatched_tf(mock_build_variant_id, mock_file_fileset, mock_protein_map, sample_archive, caplog):
    """Test process_file skips files with unmatched TF uniprot ID"""
    # Set up mock data
    mock_build_variant_id.return_value = 'NC_000019.10:9435653:C:A'

    adapter = ASB(filepath=sample_archive,
                  label='asb', writer=SpyWriter())

    # Mock the TF mapping loading to return a mapping that doesn't include ATF1_HUMAN
    def mock_load_tf_mapping():
        adapter.tf_uniprot_id_mapping = {
            'UNKNOWN_TF': 'P12345'  # Different from ATF1_HUMAN
        }

    # Load the cell mapping normally first
    adapter.load_cell_ontology_id_mapping()

    with patch.object(adapter, 'load_tf_uniprot_id_mapping', side_effect=mock_load_tf_mapping):
        # Call process_file
        adapter.process_file()

    # Check that the skip message was logged
    assert 'TF uniprot id unavailable, skipping: ATF1_HUMAN@HepG2__hepatoblastoma_.tsv' in caplog.text

    # Verify no output was generated since the TF was skipped
    assert len(adapter.writer.contents) == 0


@patch('adapters.adastra_asb_adapter.build_variant_id')
def test_adastra_asb_adapter_process_file_skip_unmatched_cell(mock_build_variant_id, mock_file_fileset, mock_protein_map, sample_archive, caplog):
    """Test process_file skips files with unmatched cell ontology ID"""
    # Set up mock data
    mock_build_variant_id.return_value = 'NC_000019.10:9435653:C:A'

    adapter = ASB(filepath=sample_archive,
                  label='asb', writer=SpyWriter())

    # Load the TF mapping normally first
    adapter.load_tf_uniprot_id_mapping()

    # Mock the cell mapping loading to return a mapping that doesn't include HepG2__hepatoblastoma_
    def mock_load_cell_mapping():
        adapter.cell_ontology_id_mapping = {
            'unknown_cell': ('CL:0000001', 'GTRD123', 'Unknown Cell')
        }

    with patch.object(adapter, 'load_cell_ontology_id_mapping', side_effect=mock_load_cell_mapping):
        # Call process_file
        adapter.process_file()

    # Check that the skip message was logged
    assert 'Cell ontology id unavailable, skipping: ATF1_HUMAN@HepG2__hepatoblastoma_.tsv' in caplog.text

    # Verify no output was generated since the cell was skipped
    assert len(adapter.writer.contents) == 0
