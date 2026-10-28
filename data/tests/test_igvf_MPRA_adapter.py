from contextlib import nullcontext
import gzip
import json
import pytest
from adapters.mpra_adapter import MPRAAdapter
from adapters.ontology_term_validator import OntologyTermValidator
from adapters.writer import SpyWriter
from unittest.mock import patch


# mock get_file_fileset_by_accession_in_arangodb so files_fileset data change will not affect the test
@pytest.fixture
def mock_file_fileset():
    """Fixture to mock get_file_fileset_by_accession_in_arangodb function."""
    with patch('adapters.mpra_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'method': 'MPRA',
            'class': 'observed data',
            'samples': ['ontology_terms/CL_0000679'],
            'simple_sample_summaries': [
                'glutamatergic neuron differentiated cell specimen, pooled cell'
            ],
            'treatments_term_ids': None
        }
        yield mock_get_file_fileset


@pytest.fixture
def mock_ontology_term_validator():
    with patch('adapters.mpra_adapter.OntologyTermValidator') as MockValidator:
        MockValidator.normalize_term_key = staticmethod(
            OntologyTermValidator.normalize_term_key)
        mock_validator = MockValidator.return_value
        mock_validator.validate.return_value = True
        mock_validator.ensure.return_value = True
        yield mock_validator


@patch('adapters.mpra_adapter.bulk_check_variants_in_arangodb', return_value=set())
@patch('adapters.mpra_adapter.load_variant')
def test_variant(mock_load_variant, mock_check, mock_file_fileset):
    mock_load_variant.return_value = ({
        '_key': 'NC_000009.12:135961939:C:T',
        'spdi': 'NC_000009.12:135961939:C:T',
        'hgvs': 'NC_000009.12:g.135961940C>T',
        'variation_type': 'SNP',
    }, None)

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath='./tests/fixtures/IGVFFI1323RCIE_igvf_mpra_variant_effects.example.tsv',
        label='variant',
        reference_filepath='./tests/fixtures/IGVFFI4914OUJH_igvf_mpra_sequence_designs.example.tsv',
        writer=writer,
        validate=True
    )
    adapter.process_file()
    assert any(
        '"spdi": "NC_000009.12:135961939:C:T"' in entry for entry in writer.contents)


def test_genomic_element_uses_ref_name_when_ref_and_alt_share_coords(
        tmp_path, mock_file_fileset):
    """Alt-only rows must not overwrite the element name; non-variant (no allele) still loads."""
    design_file = tmp_path / 'IGVFFI0000REF_design.tsv'
    design_file.write_text(
        'name\tsequence\tcategory\tclass\tsource\tref\tchr\tstart\tend\t'
        'strand\tvariant_class\tvariant_pos\tSPDI\tallele\tinfo\n'
        'ALT_only_name\tN\tvariant\ttest\tunc\tGRCh38\tchr1\t10\t20\t+'
        '\t["SNV"]\t[12]\t["NC_000001.11:11:A:C"]\t["alt"]\tNA\n'
        'REF_name\tN\tvariant\ttest\tunc\tGRCh38\tchr1\t10\t20\t+'
        '\t["SNV"]\t[12]\t["NC_000001.11:11:A:C"]\t["ref"]\tNA\n'
    )
    effects_file = tmp_path / 'IGVFFI0000TEST_effects.tsv'
    effects_file.write_text(
        'chr1\t10\t20\tignored_in_igvf\t100\t+\t0.25\t1.0\t2.0\t3.0\t1.5\n'
    )
    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath=str(effects_file),
        label='genomic_element',
        reference_filepath=str(design_file),
        writer=writer,
        validate=True
    )
    adapter.process_file()
    parsed = [json.loads(x) for x in writer.contents]
    assert len(parsed) == 1
    assert parsed[0]['name'] == 'REF_name'


def test_genomic_element_mixed_ref_alt_on_one_row_is_single_ref_element(
        tmp_path, mock_file_fileset):
    """['ref', 'alt'] on one line: one ref tile; alt in the list pairs with that ref at same locus."""
    design_file = tmp_path / 'IGVFFI0000REF_design.tsv'
    design_file.write_text(
        'name\tsequence\tcategory\tclass\tsource\tref\tchr\tstart\tend\t'
        'strand\tvariant_class\tvariant_pos\tSPDI\tallele\tinfo\n'
        'one_tile_mixed\tN\tvariant\ttest\tunc\tGRCh38\tchr1\t10\t20\t+'
        '\t["SNV"]\t[12]\t["NC_000001.11:11:A:C"]\t["ref", "alt"]\tNA\n'
    )
    effects_file = tmp_path / 'IGVFFI0000TEST_effects.tsv'
    effects_file.write_text(
        'chr1\t10\t20\ty\t100\t+\t0.25\t1.0\t2.0\t3.0\t1.5\n'
    )
    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath=str(effects_file),
        label='genomic_element',
        reference_filepath=str(design_file),
        writer=writer,
        validate=True
    )
    adapter.process_file()
    parsed = [json.loads(x) for x in writer.contents]
    assert len(parsed) == 1
    assert parsed[0]['name'] == 'one_tile_mixed'
    assert parsed[0]['chr'] == 'chr1'
    assert parsed[0]['start'] == 10
    assert parsed[0]['end'] == 20


def test_genomic_element(mock_file_fileset):

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath='./tests/fixtures/IGVFFI1323RCIE_igvf_mpra_element_effects.example.tsv',
        label='genomic_element',
        reference_filepath='./tests/fixtures/IGVFFI4914OUJH_igvf_mpra_sequence_designs.example.tsv',
        writer=writer,
        validate=True
    )
    adapter.process_file()
    parsed = [json.loads(x) for x in writer.contents]
    assert any(p['chr'] == 'chr9' and p['type'] ==
               'tested elements' and p['method'] == 'MPRA' for p in parsed)


def test_genomic_element_missing_design_entry_warns_and_skips(tmp_path, mock_file_fileset, caplog):
    design_file = tmp_path / 'IGVFFI0000REF_design.tsv'
    design_file.write_text(
        'chr\tstart\tend\tname\tSPDI\tallele\tstrand\n'
        'chr8\t100722043\t100722293\tElem_design_plus\tNA\tNA\t+\n'
    )
    effects_file = tmp_path / 'IGVFFI0000TEST_effects.tsv'
    effects_file.write_text(
        'chr8\t100722043\t100722293\tElem_effect_minus\t995\t-\t4.06\t33.13\t572.85\t22.92\t20.60\n'
    )

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath=str(effects_file),
        label='genomic_element',
        reference_filepath=str(design_file),
        writer=writer,
        validate=True
    )

    with caplog.at_level('WARNING'):
        adapter.process_file()

    assert len(writer.contents) == 0
    assert any(
        'Skipping genomic element' in rec.message and
        'not present in MPRA sequence designs file' in rec.message
        for rec in caplog.records
    )


def test_elements_from_variant_file(mock_file_fileset):

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath='./tests/fixtures/IGVFFI1323RCIE_igvf_mpra_variant_effects.example.tsv',
        label='genomic_element_from_variant',
        reference_filepath='./tests/fixtures/IGVFFI4914OUJH_igvf_mpra_sequence_designs.example.tsv',
        writer=writer,
        validate=True
    )
    adapter.process_file()
    parsed = [json.loads(x) for x in writer.contents]
    assert any(p['chr'] == 'chr9' and p['type'] ==
               'tested elements' for p in parsed)


def test_elements_from_variant_file_no_duplicates_across_chunks(mock_file_fileset):
    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath='./tests/fixtures/IGVFFI1323RCIE_igvf_mpra_variant_effects.example.tsv',
        label='genomic_element_from_variant',
        reference_filepath='./tests/fixtures/IGVFFI4914OUJH_igvf_mpra_sequence_designs.example.tsv',
        writer=writer,
        validate=True
    )
    # Force multiple chunk passes to ensure dedupe persists across chunks.
    adapter.CHUNK_SIZE = 1
    adapter.process_file()
    parsed = [json.loads(x) for x in writer.contents]
    keys = [p['_key'] for p in parsed]
    assert len(keys) == len(set(keys))


@patch('adapters.mpra_adapter.bulk_check_variants_in_arangodb', return_value={'NC_000009.12:136248440:T:C'})
@patch('adapters.mpra_adapter.load_variant')
def test_variant_biosample(
        mock_load_variant, mock_check, mock_file_fileset,
        mock_ontology_term_validator):

    mock_load_variant.return_value = ({
        '_key': 'NC_000009.12:136248440:T:C',
    }, None)

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath='./tests/fixtures/IGVFFI1323RCIE_igvf_mpra_variant_effects.example.tsv',
        label='variant_biosample',
        reference_filepath='./tests/fixtures/IGVFFI4914OUJH_igvf_mpra_sequence_designs.example.tsv',
        writer=writer,
        validate=True
    )

    adapter.process_file()

    # Parse all items and find the expected one by _key (order may vary due to set iteration)
    parsed_items = [json.loads(item) for item in writer.contents]
    biosample_term_key = 'CL_0000679'
    expected_key = f'NC_000009.12:136248440:T:C_MPRA_chr9_136886228_136886428_GRCh38_plus_IGVFFI4914OUJH_{biosample_term_key}_IGVFFI1323RCIE'
    found_item = next(
        (item for item in parsed_items if item['_key'] == expected_key), None)

    assert found_item is not None, f"Expected item with _key '{expected_key}' not found in writer contents"
    assert found_item == {
        '_key': expected_key,
        '_from': 'variants/NC_000009.12:136248440:T:C',
        '_to': 'ontology_terms/CL_0000679',
        'genomic_element': 'genomic_elements/MPRA_chr9_136886228_136886428_GRCh38_plus_IGVFFI4914OUJH',
        'strand': '+',
        'bed_score': 66,
        'log2FC': -0.0768,
        'inputCountRef': 0.5948,
        'outputCountRef': 0.3434,
        'inputCountAlt': 0.6516,
        'outputCountAlt': 0.3039,
        'neg_log10_pvalue': 5.9634,
        'neg_log10_pvalue_adj': 4.7221,
        'significant': True,
        'postProbEffect': 0.992,
        'CI_lower_95': -0.1076,
        'CI_upper_95': -0.0461,
        'class': 'observed data',
        'label': 'variant effect on regulatory element activity',
        'biological_context': 'glutamatergic neuron differentiated cell specimen, pooled cell',
        'biosample_term': 'ontology_terms/CL_0000679',
        'treatments_term_ids': None,
        'name': 'modulates regulatory activity of',
        'inverse_name': 'regulatory activity modulated by',
        'method': 'MPRA',
        'source': 'IGVF',
        'source_url': 'https://data.igvf.org/tabular-files/IGVFFI1323RCIE',
        'files_filesets': 'files_filesets/IGVFFI1323RCIE',
    }


@patch('adapters.mpra_adapter.bulk_check_variants_in_arangodb', return_value={'NC_000001.11:25:A:C'})
@patch('adapters.mpra_adapter.load_variant')
def test_variant_biosample_uses_variant_pos_for_overlapping_elements(
        mock_load_variant, mock_check, mock_file_fileset, tmp_path,
        mock_ontology_term_validator):
    mock_load_variant.return_value = ({
        '_key': 'NC_000001.11:25:A:C',
    }, None)

    design_file = tmp_path / 'IGVFFI0000REF_design.tsv'
    design_file.write_text(
        'name\tsequence\tcategory\tclass\tsource\tref\tchr\tstart\tend\tstrand\tvariant_class\tvariant_pos\tSPDI\tallele\tinfo\n'
        'tile_1_ref\tACGT\tvariant\ttest\tunc\tGRCh38\tchr1\t0\t250\t+\t["SNV"]\t[224]\t["NC_000001.11:25:A:C"]\t["ref"]\tNA\n'
        'tile_1_alt\tACGT\tvariant\ttest\tunc\tGRCh38\tchr1\t0\t250\t+\t["SNV"]\t[224]\t["NC_000001.11:25:A:C"]\t["alt"]\tNA\n'
        'tile_2_ref\tACGT\tvariant\ttest\tunc\tGRCh38\tchr1\t100\t350\t+\t["SNV"]\t[125]\t["NC_000001.11:25:A:C"]\t["ref"]\tNA\n'
        'tile_2_alt\tACGT\tvariant\ttest\tunc\tGRCh38\tchr1\t100\t350\t+\t["SNV"]\t[125]\t["NC_000001.11:25:A:C"]\t["alt"]\tNA\n'
    )
    effects_file = tmp_path / 'IGVFFI0000TEST_effects.tsv'
    effects_file.write_text(
        'chr1\t25\t26\tNC_000001.11:25:A:C\t3\t+\t0.1\t1\t2\t3\t4\t1.2\t0.2\t0.5\t-0.1\t0.1\t224\tA\tC\n'
        'chr1\t25\t26\tNC_000001.11:25:A:C\t918\t+\t0.6\t1\t2\t3\t4\t3.4\t2.3\t0.8\t0.2\t1.0\t125\tA\tC\n'
    )

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath=str(effects_file),
        label='variant_biosample',
        reference_filepath=str(design_file),
        writer=writer,
        validate=True
    )
    adapter.process_file()

    parsed = [json.loads(x) for x in writer.contents]
    assert len(parsed) == 2

    by_score = {p['bed_score']: p for p in parsed}
    assert by_score[3]['genomic_element'] == 'genomic_elements/MPRA_chr1_0_250_GRCh38_plus_IGVFFI0000REF'
    assert by_score[3]['strand'] == '+'
    assert by_score[918]['genomic_element'] == 'genomic_elements/MPRA_chr1_100_350_GRCh38_plus_IGVFFI0000REF'
    assert by_score[918]['strand'] == '+'


@patch('adapters.mpra_adapter.bulk_check_variants_in_arangodb', return_value={'NC_000010.11:79347485:CGCGC:TTGGG'})
@patch('adapters.mpra_adapter.load_variant')
def test_variant_biosample_maps_alt_spdi_when_ref_row_has_no_spdi(
        mock_load_variant, mock_check, mock_file_fileset, tmp_path,
        mock_ontology_term_validator):
    mock_load_variant.return_value = ({
        '_key': 'NC_000010.11:79347485:CGCGC:TTGGG',
    }, None)

    design_file = tmp_path / 'IGVFFI9852HQHD_design.tsv'
    design_file.write_text(
        'name\tsequence\tcategory\tclass\tsource\tref\tchr\tstart\tend\tstrand\tvariant_class\tvariant_pos\tSPDI\tallele\tinfo\n'
        'PPIF_promoter_WT\tN\telement\tvariant negative control\tunc\tGRCh38\tchr10\t79347211\t79347779\t.\tNA\tNA\tNA\t["ref"]\tNA\n'
        'PPIF_promoter_MUT\tN\tvariant\ttest\tunc\tGRCh38\tchr10\t79347211\t79347779\t.\t["indel"]\t[274]\t["NC_000010.11:79347485:CGCGC:TTGGG"]\t["alt"]\tNA\n'
    )
    effects_file = tmp_path / 'IGVFFI0000TEST_effects.tsv'
    effects_file.write_text(
        'chr10\t79347485\t79347490\tNC_000010.11:79347485:CGCGC:TTGGG\t11\t.\t0.42\t1\t2\t3\t4\t5.89\t3.49\t0.9\t0.1\t1.2\t274\tCGCGC\tTTGGG\n'
    )

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath=str(effects_file),
        label='variant_biosample',
        reference_filepath=str(design_file),
        writer=writer,
        validate=True
    )
    adapter.process_file()

    parsed = [json.loads(x) for x in writer.contents]
    assert len(parsed) == 1
    assert parsed[0]['genomic_element'] == 'genomic_elements/MPRA_chr10_79347211_79347779_GRCh38_na_IGVFFI9852HQHD'
    assert parsed[0]['strand'] == '.'


@patch('adapters.mpra_adapter.bulk_check_variants_in_arangodb', return_value={'NC_000006.12:52763752:A:G'})
@patch('adapters.mpra_adapter.load_variant')
def test_variant_biosample_uses_strand_for_reverse_complement_designs(
        mock_load_variant, mock_check, mock_file_fileset, tmp_path,
        mock_ontology_term_validator):
    mock_load_variant.return_value = ({
        '_key': 'NC_000006.12:52763752:A:G',
    }, None)

    design_file = tmp_path / 'IGVFFI5172VOJF_design.tsv'
    design_file.write_text(
        'name\tsequence\tcategory\tclass\tsource\tref\tchr\tstart\tend\tstrand\tvariant_class\tvariant_pos\tSPDI\tallele\tinfo\n'
        'tile_plus_ref\tACGT\tvariant\ttest\tunc\tGRCh38\tchr6\t52763627\t52763877\t+\t["SNV"]\t[125]\t["NC_000006.12:52763752:A:G"]\t["ref"]\tNA\n'
        'tile_plus_alt\tACGT\tvariant\ttest\tunc\tGRCh38\tchr6\t52763627\t52763877\t+\t["SNV"]\t[125]\t["NC_000006.12:52763752:A:G"]\t["alt"]\tNA\n'
        'tile_minus_ref\tACGT\tvariant\ttest\tunc\tGRCh38\tchr6\t52763627\t52763877\t-\t["SNV"]\t[125]\t["NC_000006.12:52763752:A:G"]\t["ref"]\tNA\n'
        'tile_minus_alt\tACGT\tvariant\ttest\tunc\tGRCh38\tchr6\t52763627\t52763877\t-\t["SNV"]\t[125]\t["NC_000006.12:52763752:A:G"]\t["alt"]\tNA\n'
    )
    effects_file = tmp_path / 'IGVFFI0000TEST_effects.tsv'
    effects_file.write_text(
        'chr6\t52763752\t52763753\tNC_000006.12:52763752:A:G\t352\t+\t0.13\t31\t16\t43\t25\t0.48\t0.30\t0.5\t-0.1\t0.1\t125\tA\tG\n'
        'chr6\t52763752\t52763753\tNC_000006.12:52763752:A:G\t368\t-\t0.14\t29\t23\t67\t59\t0.51\t0.31\t0.6\t-0.1\t0.1\t125\tA\tG\n'
    )

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath=str(effects_file),
        label='variant_biosample',
        reference_filepath=str(design_file),
        writer=writer,
        validate=True
    )
    adapter.process_file()

    parsed = [json.loads(x) for x in writer.contents]
    assert len(parsed) == 2

    by_score = {p['bed_score']: p for p in parsed}
    assert '_plus_' in by_score[352]['_key']
    assert '_minus_' in by_score[368]['_key']
    assert by_score[352]['strand'] == '+'
    assert by_score[368]['strand'] == '-'


def test_genomic_element_biosample(mock_file_fileset, mock_ontology_term_validator):

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath='./tests/fixtures/IGVFFI1323RCIE_igvf_mpra_element_effects.example.tsv',
        label='genomic_element_biosample',
        reference_filepath='./tests/fixtures/IGVFFI4914OUJH_igvf_mpra_sequence_designs.example.tsv',
        writer=writer,
        validate=True
    )
    adapter.process_file()
    parsed = [json.loads(x) for x in writer.contents]
    assert all(p['_from'].startswith('genomic_elements/')
               and p['_to'].startswith('ontology_terms/') for p in parsed)


def test_genomic_element_biosample_ref_allele_only_writes(
        tmp_path, mock_file_fileset, mock_ontology_term_validator):
    design_file = tmp_path / 'IGVFFI0000REF_design.tsv'
    design_file.write_text(
        'chr\tstart\tend\tname\tSPDI\tallele\n'
        'chr1\t10\t20\tElem1\tNA\t["ref"]\n'
    )
    effects_file = tmp_path / 'IGVFFI0000TEST_effects.tsv'
    effects_file.write_text(
        'chr1\t10\t20\tElem1\t100\t+\t0.25\t1.0\t2.0\t3.0\t1.5\n'
    )

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath=str(effects_file),
        label='genomic_element_biosample',
        reference_filepath=str(design_file),
        writer=writer,
        validate=True
    )
    adapter.process_file()
    assert len(writer.contents) == 1


def test_genomic_element_biosample_mixed_ref_alt_writes_ref_element_effect(
        tmp_path, mock_file_fileset, mock_ontology_term_validator):
    """Design row with both ref and alt is valid; biosample edge loads (ref is present)."""
    design_file = tmp_path / 'IGVFFI0000REF_design.tsv'
    design_file.write_text(
        'chr\tstart\tend\tname\tSPDI\tallele\n'
        'chr1\t10\t20\tElem1\tNA\t["ref", "alt"]\n'
    )
    effects_file = tmp_path / 'IGVFFI0000TEST_effects.tsv'
    effects_file.write_text(
        'chr1\t10\t20\tElem1\t100\t+\t0.25\t1.0\t2.0\t3.0\t1.5\n'
    )

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath=str(effects_file),
        label='genomic_element_biosample',
        reference_filepath=str(design_file),
        writer=writer,
        validate=True
    )
    adapter.process_file()
    assert len(writer.contents) == 1


def test_genomic_element_biosample_missing_allele_writes(
        tmp_path, mock_file_fileset, mock_ontology_term_validator):
    design_file = tmp_path / 'IGVFFI0000REF_design.tsv'
    design_file.write_text(
        'chr\tstart\tend\tname\tSPDI\tallele\n'
        'chr1\t10\t20\tElem1\tNA\tNA\n'
    )
    effects_file = tmp_path / 'IGVFFI0000TEST_effects.tsv'
    effects_file.write_text(
        'chr1\t10\t20\tElem1\t100\t+\t0.25\t1.0\t2.0\t3.0\t1.5\n'
    )

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath=str(effects_file),
        label='genomic_element_biosample',
        reference_filepath=str(design_file),
        writer=writer,
        validate=True
    )
    adapter.process_file()
    assert len(writer.contents) == 1


def test_genomic_element_biosample_missing_allele_multi_effect_is_flagged(
        tmp_path, mock_file_fileset, mock_ontology_term_validator):
    design_file = tmp_path / 'IGVFFI0000REF_design.tsv'
    design_file.write_text(
        'chr\tstart\tend\tname\tSPDI\tallele\n'
        'chr1\t10\t20\tElem1\tNA\tNA\n'
        'chr1\t10\t20\tElem2\tNA\t["ref"]\n'
    )
    effects_file = tmp_path / 'IGVFFI0000TEST_effects.tsv'
    effects_file.write_text(
        'chr1\t10\t20\tElem1\t100\t+\t0.25\t1.0\t2.0\t3.0\t1.5\n'
        'chr1\t10\t20\tElem2\t100\t+\t0.25\t1.0\t2.0\t3.0\t1.5\n'
    )

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath=str(effects_file),
        label='genomic_element_biosample',
        reference_filepath=str(design_file),
        writer=writer,
        validate=True
    )
    with pytest.raises(ValueError, match='Missing allele annotations for regions with multiple element effects'):
        adapter.process_file()


def test_genomic_element_biosample_control_ignored_and_ref_loaded(
        tmp_path, mock_file_fileset, mock_ontology_term_validator):
    design_file = tmp_path / 'IGVFFI0000REF_design.tsv'
    design_file.write_text(
        'chr\tstart\tend\tname\tSPDI\tallele\tclass\n'
        'chr1\t10\t20\tNegative 1 (chr1:11-21)\tNA\tNA\telement inactive control\n'
        'chr1\t10\t20\tVariant 1 (chr1:11-21)\t["NC_000001.11:11:A:C"]\t["ref"]\ttest\n'
        'chr1\t10\t20\tVariant 2 (chr1:11-21)\t["NC_000001.11:11:A:C"]\t["alt"]\ttest\n'
    )
    effects_file = tmp_path / 'IGVFFI0000TEST_effects.tsv'
    effects_file.write_text(
        'chr1\t10\t20\tNegative_1_(chr1:11-21)\t100\t+\t0.25\t1.0\t2.0\t3.0\t1.5\n'
        'chr1\t10\t20\tVariant_1_(chr1:11-21)\t100\t+\t0.25\t1.0\t2.0\t3.0\t1.5\n'
        'chr1\t10\t20\tVariant_2_(chr1:11-21)\t100\t+\t0.25\t1.0\t2.0\t3.0\t1.5\n'
    )

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath=str(effects_file),
        label='genomic_element_biosample',
        reference_filepath=str(design_file),
        writer=writer,
        validate=True
    )
    adapter.process_file()
    assert len(writer.contents) == 1


def test_genomic_element_biosample_same_coords_different_strands_have_unique_ids(
        tmp_path, mock_file_fileset, mock_ontology_term_validator):
    design_file = tmp_path / 'IGVFFI0000REF_design.tsv'
    design_file.write_text(
        'chr\tstart\tend\tname\tSPDI\tallele\tclass\tstrand\n'
        'chr1\t10\t20\tElem_fwd\t["NC_000001.11:11:A:C"]\t["ref"]\ttest\t+\n'
        'chr1\t10\t20\tElem_rev\t["NC_000001.11:11:A:C"]\t["ref"]\ttest\t-\n'
    )
    effects_file = tmp_path / 'IGVFFI0000TEST_effects.tsv'
    effects_file.write_text(
        'chr1\t10\t20\tElem_fwd\t100\t+\t0.25\t1.0\t2.0\t3.0\t1.5\n'
        'chr1\t10\t20\tElem_rev\t90\t-\t0.2\t1.0\t2.0\t3.0\t1.5\n'
    )

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath=str(effects_file),
        label='genomic_element_biosample',
        reference_filepath=str(design_file),
        writer=writer,
        validate=True
    )
    adapter.process_file()
    parsed = [json.loads(x) for x in writer.contents]
    assert len(parsed) == 2
    assert len({p['_key'] for p in parsed}) == 2
    assert len({p['_from'] for p in parsed}) == 2


@pytest.mark.parametrize('label', ['genomic_element', 'genomic_element_biosample'])
def test_igvffi1436trih_exclusion_list_is_applied(
        tmp_path, mock_file_fileset, mock_ontology_term_validator, label):
    excluded_name = (
        'cardiac_neuro_cava_random:ALT_KANSL1|ENSG00000120071.15|'
        'EH38E3227108_rev_tile1-1_KANSL1|ENSG00000120071.15|'
        'EH38E3227108|17-46152590-G-C'
    )
    design_file = tmp_path / 'IGVFFI1436TRIH_design.tsv'
    design_file.write_text(
        'chr\tstart\tend\tname\tSPDI\tallele\tclass\tstrand\n'
        f'chr17\t46152515\t46152785\t{excluded_name}\tNA\tNA\ttest\t-\n'
    )
    effects_file = tmp_path / 'IGVFFI0000TEST_effects.tsv'
    effects_file.write_text(
        f'chr17\t46152515\t46152785\t{excluded_name}\t100\t-\t0.25\t1.0\t2.0\t3.0\t1.5\n'
    )

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath=str(effects_file),
        label=label,
        reference_filepath=str(design_file),
        writer=writer,
        validate=True
    )
    adapter.process_file()
    assert len(writer.contents) == 0


def test_invalid_label(mock_file_fileset):
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_label'):
        MPRAAdapter(
            filepath='./tests/fixtures/IGVFFI1323RCIE_igvf_mpra_element_effects.example.tsv',
            label='invalid_label',
            reference_filepath='./tests/fixtures/IGVFFI4914OUJH_igvf_mpra_sequence_designs.example.tsv',
            writer=writer,
            validate=True)


def test_validate_doc_invalid(mock_file_fileset):
    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath='./tests/fixtures/IGVFFI1323RCIE_igvf_mpra_element_effects.example.tsv',
        label='genomic_element',
        reference_filepath='./tests/fixtures/IGVFFI4914OUJH_igvf_mpra_sequence_designs.example.tsv',
        writer=writer,
        validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)


@pytest.mark.parametrize('compressed', [False, True])
@pytest.mark.parametrize('prefix,assembly,organism', [
    ('', 'GRCh38', 'Homo sapiens'),
    ('mm_', 'GRCm39', 'Mus musculus'),
])
@pytest.mark.parametrize('label,collection', [
    ('genomic_element', 'genomic_elements'),
    ('genomic_element_biosample', 'genomic_elements_biosamples'),
    ('genomic_element_from_variant', 'genomic_elements'),
    ('variant', 'variants'),
    ('variant_biosample', 'variants_biosamples'),
])
def test_mpra_collections_and_references(tmp_path, mock_file_fileset, mock_ontology_term_validator,
                                         label, collection, prefix, assembly, organism, compressed):
    accession = 'NC_000067.7' if prefix else 'NC_000001.11'
    spdi = f'{accession}:11:A:C'
    design = tmp_path / 'IGVFFI4261NSQZ.tsv'
    design.write_text(
        'name\tref\tchr\tstart\tend\tstrand\tSPDI\tallele\tvariant_pos\n'
        f'ref_tile\t{assembly}\tchr1\t10\t20\t+\t["{spdi}"]\t["ref"]\t[1]\n'
    )
    effects = tmp_path / 'IGVFFI2111LQGF.bed'
    if label in ('genomic_element', 'genomic_element_biosample'):
        effects.write_text(
            'chr1\t10\t20\tref_tile\t100\t+\t0.25\t1\t2\t3\t1.5\n')
    else:
        effects.write_text(
            f'chr1\t11\t12\t{spdi}\t100\t+\t0.25\t1\t2\t3\t4\t5\t6\t0.9\t0.1\t0.4\t1\tA\tC\n')
    if compressed:
        compressed_design = design.with_suffix(design.suffix + '.gz')
        compressed_effects = effects.with_suffix(effects.suffix + '.gz')
        compressed_design.write_bytes(gzip.compress(design.read_bytes()))
        compressed_effects.write_bytes(gzip.compress(effects.read_bytes()))
        design.unlink()
        effects.unlink()
        design, effects = compressed_design, compressed_effects
    input_files = set(tmp_path.iterdir())
    variant = {
        '_key': spdi, 'name': spdi, 'spdi': spdi, 'chr': 'chr1', 'pos': 11,
        'ref': 'A', 'alt': 'C', 'variation_type': 'SNP',
        'hgvs': f'{accession}:g.12A>C', 'organism': organism,
    }
    writer = SpyWriter()
    with patch('adapters.mpra_adapter.bulk_check_variants_in_arangodb',
               return_value={spdi} if label == 'variant_biosample' else set()) as check, \
            patch('adapters.mpra_adapter.load_variant', return_value=(variant, None)) as load:
        adapter = MPRAAdapter(
            filepath=effects, label=f'{prefix}{label}', writer=writer, validate=True,
            reference_filepath=design,
        )
        assert adapter._get_collection_name() == prefix + collection
        assert adapter.schema['db_collection_name'] == prefix + collection
        adapter.process_file()
        records = [json.loads(row) for row in writer.contents]
        assert len(records) == 1
        record = records[0]
        element_key = f'MPRA_chr1_10_20_{assembly}_plus_IGVFFI4261NSQZ'
        if label in ('genomic_element', 'genomic_element_from_variant'):
            assert record['_key'] == element_key
        elif label == 'genomic_element_biosample':
            assert record['_from'] == f'{prefix}genomic_elements/{element_key}'
        elif label == 'variant_biosample':
            assert record['_from'] == f'{prefix}variants/{spdi}'
            assert record['genomic_element'] == f'{prefix}genomic_elements/{element_key}'
            assert record['_key'] == f'{spdi}_{element_key}_CL_0000679_IGVFFI2111LQGF'
        if label in ('variant', 'variant_biosample'):
            assert check.call_args.kwargs['collection'] == f'{prefix}variants'
            load.assert_called_once_with(spdi, assembly=assembly)
        assert set(tmp_path.iterdir()) == input_files


def test_mouse_design_ignores_human_controls(tmp_path, mock_file_fileset, mock_ontology_term_validator):
    design = tmp_path / 'IGVFFI1204BCKQ.tsv'
    design.write_text(
        'name\tref\tclass\tchr\tstart\tend\tstrand\tallele\n'
        'mouse_tile\tGRCm39\ttest\tchr1\t10\t20\t+\tNA\n'
        'human_control\tGRCh38\telement active control\tchr2\t30\t40\t+\tNA\n'
    )
    effects = tmp_path / 'IGVFFI3406MEAD.bed'
    effects.write_text(
        'chr1\t10\t20\tmouse_tile\t100\t+\t1\t2\t3\t4\t5\n'
        'chr2\t30\t40\thuman_control\t100\t+\t1\t2\t3\t4\t5\n'
    )
    for label in ('genomic_element', 'genomic_element_biosample'):
        writer = SpyWriter()
        adapter = MPRAAdapter(
            filepath=str(effects), label=f'mm_{label}', writer=writer, validate=True,
            reference_filepath=str(design),
        )
        adapter.process_file()
        assert adapter.assembly == 'GRCm39'
        assert len(writer.contents) == 1
        assert 'GRCm39' in json.loads(writer.contents[0])['_key']


@pytest.mark.parametrize('design_accession', ['IGVFFI4261NSQZ', 'IGVFFI1789LDNT', 'IGVFFI0000TEST'])
@pytest.mark.parametrize('strand', ['+', '-'])
def test_mouse_design_maps_changed_bases_by_coordinates(tmp_path, mock_file_fileset, mock_ontology_term_validator, strand, design_accession):
    design = tmp_path / f'{design_accession}.tsv'
    # ALT precedes WT and covers only the changed base, not the full tile.
    design.write_text(
        'name\tref\tclass\tchr\tstart\tend\tstrand\tallele\tSPDI\tvariant_pos\n'
        f'arbitrary_variant_name\tGRCm39\ttest\tchr1\t11\t12\t{strand}\t["alt"]\t["NC_000067.7:11:A:C"]\t[1]\n'
        f'unrelated_reference_name\tGRCm39\ttest\tchr1\t10\t20\t{strand}\t["ref"]\tNA\tNA\n'
    )
    effects = tmp_path / 'IGVFFI0975AQKF.bed'
    effects.write_text(
        f'chr1\t10\t20\tunrelated_reference_name\t100\t{strand}\t1\t2\t3\t4\t5\n')
    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath=str(effects), label='mm_genomic_element_biosample', writer=writer, validate=True,
        reference_filepath=str(design),
    )
    assert adapter.variant_to_element['NC_000067.7:11:A:C'] == {
        ('chr1', '10', '20', strand)}
    assert adapter.variant_pos_to_element[('NC_000067.7:11:A:C', 1)] == {
        ('chr1', '10', '20', strand)}
    adapter.process_file()
    assert len(writer.contents) == 1
    assert json.loads(writer.contents[0])['_from'].startswith(
        'mm_genomic_elements/MPRA_chr1_10_20_GRCm39_')


@pytest.mark.parametrize('reference_rows', ['',
                                            'ref_a\tGRCm39\tchr1\t10\t20\t+\t["ref"]\tNA\n'
                                            'ref_b\tGRCm39\tchr1\t9\t21\t+\t["ref"]\tNA\n'])
def test_mouse_design_requires_unique_containing_reference(tmp_path, mock_file_fileset, reference_rows):
    design = tmp_path / 'IGVFFI0000TEST.tsv'
    design.write_text(
        'name\tref\tchr\tstart\tend\tstrand\tallele\tSPDI\n'
        'variant\tGRCm39\tchr1\t11\t12\t+\t["alt"]\t["NC_000067.7:11:A:C"]\n'
        + reference_rows)
    with pytest.raises(ValueError, match='Expected one reference tile') if reference_rows else nullcontext():
        adapter = MPRAAdapter(
            filepath='IGVFFI5939ZOZQ.bed', label='mm_variant', writer=SpyWriter(),
            reference_filepath=str(design),
        )

    if not reference_rows:
        assert not adapter.variant_to_element
        assert not adapter.variant_pos_to_element


@pytest.mark.parametrize('value', ['NaN', 'Infinity', '-Infinity'])
def test_omit_nonfinite_metrics_preserves_record(value):
    record = {
        '_key': 'test-edge',
        'log2FC': MPRAAdapter.safe_float(value),
        'outputCount': MPRAAdapter.safe_float('0'),
        'inputCount': MPRAAdapter.safe_float('12.5'),
        'optional': None,
    }
    cleaned = MPRAAdapter._drop_nonfinite_metrics(record)
    assert cleaned == {'_key': 'test-edge', 'outputCount': 0.0,
                       'inputCount': 12.5, 'optional': None}
    json.dumps(cleaned, allow_nan=False)
    assert MPRAAdapter.safe_int(value) is None
