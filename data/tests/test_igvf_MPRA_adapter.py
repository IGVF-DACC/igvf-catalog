import json
import pytest
from adapters.mpra_adapter import MPRAAdapter
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
        filepath='./samples/igvf_mpra_variant_effects.example.tsv',
        label='variant',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI1323RCIE/',
        reference_filepath='./samples/igvf_mpra_sequence_designs.example.tsv',
        reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI4914OUJH/',
        writer=writer,
        validate=True
    )
    adapter.process_file()
    assert any(
        '"spdi": "NC_000009.12:135961939:C:T"' in entry for entry in writer.contents)


def test_genomic_element(mock_file_fileset):

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath='./samples/igvf_mpra_element_effects.example.tsv',
        label='genomic_element',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI1323RCIE/',
        reference_filepath='./samples/igvf_mpra_sequence_designs.example.tsv',
        reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI4914OUJH/',
        writer=writer,
        validate=True
    )
    adapter.process_file()
    parsed = [json.loads(x) for x in writer.contents]
    assert any(p['chr'] == 'chr9' and p['type'] ==
               'tested elements' and p['method'] == 'MPRA' for p in parsed)


def test_genomic_element_missing_design_entry_warns_and_skips(tmp_path, mock_file_fileset, caplog):
    design_file = tmp_path / 'design.tsv'
    design_file.write_text(
        'chr\tstart\tend\tname\tSPDI\tallele\tstrand\n'
        'chr8\t100722043\t100722293\tElem_design_plus\tNA\tNA\t+\n'
    )
    effects_file = tmp_path / 'effects.tsv'
    effects_file.write_text(
        'chr8\t100722043\t100722293\tElem_effect_minus\t995\t-\t4.06\t33.13\t572.85\t22.92\t20.60\n'
    )

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath=str(effects_file),
        label='genomic_element',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI0000TEST/',
        reference_filepath=str(design_file),
        reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI0000REF/',
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
        filepath='./samples/igvf_mpra_variant_effects.example.tsv',
        label='genomic_element_from_variant',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI1323RCIE/',
        reference_filepath='./samples/igvf_mpra_sequence_designs.example.tsv',
        reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI4914OUJH/',
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
        filepath='./samples/igvf_mpra_variant_effects.example.tsv',
        label='genomic_element_from_variant',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI1323RCIE/',
        reference_filepath='./samples/igvf_mpra_sequence_designs.example.tsv',
        reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI4914OUJH/',
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
def test_variant_biosample(mock_load_variant, mock_check, mock_file_fileset):

    mock_load_variant.return_value = ({
        '_key': 'NC_000009.12:136248440:T:C',
    }, None)

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath='./samples/igvf_mpra_variant_effects.example.tsv',
        label='variant_biosample',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI1323RCIE/',
        reference_filepath='./samples/igvf_mpra_sequence_designs.example.tsv',
        reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI4914OUJH/',
        writer=writer,
        validate=True
    )

    adapter.process_file()

    # Parse all items and find the expected one by _key (order may vary due to set iteration)
    parsed_items = [json.loads(item) for item in writer.contents]
    biosample_term_key = 'CL_0000679'
    expected_key = f'NC_000009.12:136248440:T:C_MPRA_chr9_136886228_136886428_GRCh38_IGVFFI4914OUJH_plus_{biosample_term_key}_IGVFFI1323RCIE'
    found_item = next(
        (item for item in parsed_items if item['_key'] == expected_key), None)

    assert found_item is not None, f"Expected item with _key '{expected_key}' not found in writer contents"
    assert found_item == {
        '_key': expected_key,
        '_from': 'variants/NC_000009.12:136248440:T:C',
        '_to': 'ontology_terms/CL_0000679',
        'genomic_element': 'genomic_elements/MPRA_chr9_136886228_136886428_GRCh38_IGVFFI4914OUJH',
        'bed_score': 66,
        'log2FC': -0.0768,
        'DNA_count_ref': 0.5948,
        'RNA_count_ref': 0.3434,
        'DNA_count_alt': 0.6516,
        'RNA_count_alt': 0.3039,
        'minusLog10PValue': 5.9634,
        'minusLog10QValue': 4.7221,
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
        'source_url': 'https://api.data.igvf.org/tabular-files/IGVFFI1323RCIE/',
        'files_filesets': 'files_filesets/IGVFFI1323RCIE',
    }


@patch('adapters.mpra_adapter.bulk_check_variants_in_arangodb', return_value={'NC_000001.11:25:A:C'})
@patch('adapters.mpra_adapter.load_variant')
def test_variant_biosample_uses_variant_pos_for_overlapping_elements(mock_load_variant, mock_check, mock_file_fileset, tmp_path):
    mock_load_variant.return_value = ({
        '_key': 'NC_000001.11:25:A:C',
    }, None)

    design_file = tmp_path / 'design.tsv'
    design_file.write_text(
        'name\tsequence\tcategory\tclass\tsource\tref\tchr\tstart\tend\tstrand\tvariant_class\tvariant_pos\tSPDI\tallele\tinfo\n'
        'tile_1_ref\tACGT\tvariant\ttest\tunc\tGRCh38\tchr1\t0\t250\t+\t["SNV"]\t[224]\t["NC_000001.11:25:A:C"]\t["ref"]\tNA\n'
        'tile_1_alt\tACGT\tvariant\ttest\tunc\tGRCh38\tchr1\t0\t250\t+\t["SNV"]\t[224]\t["NC_000001.11:25:A:C"]\t["alt"]\tNA\n'
        'tile_2_ref\tACGT\tvariant\ttest\tunc\tGRCh38\tchr1\t100\t350\t+\t["SNV"]\t[125]\t["NC_000001.11:25:A:C"]\t["ref"]\tNA\n'
        'tile_2_alt\tACGT\tvariant\ttest\tunc\tGRCh38\tchr1\t100\t350\t+\t["SNV"]\t[125]\t["NC_000001.11:25:A:C"]\t["alt"]\tNA\n'
    )
    effects_file = tmp_path / 'effects.tsv'
    effects_file.write_text(
        'chr1\t25\t26\tNC_000001.11:25:A:C\t3\t+\t0.1\t1\t2\t3\t4\t1.2\t0.2\t0.5\t-0.1\t0.1\t224\tA\tC\n'
        'chr1\t25\t26\tNC_000001.11:25:A:C\t918\t+\t0.6\t1\t2\t3\t4\t3.4\t2.3\t0.8\t0.2\t1.0\t125\tA\tC\n'
    )

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath=str(effects_file),
        label='variant_biosample',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI0000TEST/',
        reference_filepath=str(design_file),
        reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI0000REF/',
        writer=writer,
        validate=True
    )
    adapter.process_file()

    parsed = [json.loads(x) for x in writer.contents]
    assert len(parsed) == 2

    by_score = {p['bed_score']: p for p in parsed}
    assert by_score[3]['genomic_element'] == 'genomic_elements/MPRA_chr1_0_250_GRCh38_IGVFFI0000REF'
    assert by_score[918]['genomic_element'] == 'genomic_elements/MPRA_chr1_100_350_GRCh38_IGVFFI0000REF'


@patch('adapters.mpra_adapter.bulk_check_variants_in_arangodb', return_value={'NC_000006.12:52763752:A:G'})
@patch('adapters.mpra_adapter.load_variant')
def test_variant_biosample_uses_strand_for_reverse_complement_designs(mock_load_variant, mock_check, mock_file_fileset, tmp_path):
    mock_load_variant.return_value = ({
        '_key': 'NC_000006.12:52763752:A:G',
    }, None)

    design_file = tmp_path / 'design.tsv'
    design_file.write_text(
        'name\tsequence\tcategory\tclass\tsource\tref\tchr\tstart\tend\tstrand\tvariant_class\tvariant_pos\tSPDI\tallele\tinfo\n'
        'tile_plus_ref\tACGT\tvariant\ttest\tunc\tGRCh38\tchr6\t52763627\t52763877\t+\t["SNV"]\t[125]\t["NC_000006.12:52763752:A:G"]\t["ref"]\tNA\n'
        'tile_plus_alt\tACGT\tvariant\ttest\tunc\tGRCh38\tchr6\t52763627\t52763877\t+\t["SNV"]\t[125]\t["NC_000006.12:52763752:A:G"]\t["alt"]\tNA\n'
        'tile_minus_ref\tACGT\tvariant\ttest\tunc\tGRCh38\tchr6\t52763627\t52763877\t-\t["SNV"]\t[125]\t["NC_000006.12:52763752:A:G"]\t["ref"]\tNA\n'
        'tile_minus_alt\tACGT\tvariant\ttest\tunc\tGRCh38\tchr6\t52763627\t52763877\t-\t["SNV"]\t[125]\t["NC_000006.12:52763752:A:G"]\t["alt"]\tNA\n'
    )
    effects_file = tmp_path / 'effects.tsv'
    effects_file.write_text(
        'chr6\t52763752\t52763753\tNC_000006.12:52763752:A:G\t352\t+\t0.13\t31\t16\t43\t25\t0.48\t0.30\t0.5\t-0.1\t0.1\t125\tA\tG\n'
        'chr6\t52763752\t52763753\tNC_000006.12:52763752:A:G\t368\t-\t0.14\t29\t23\t67\t59\t0.51\t0.31\t0.6\t-0.1\t0.1\t125\tA\tG\n'
    )

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath=str(effects_file),
        label='variant_biosample',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI0000TEST/',
        reference_filepath=str(design_file),
        reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI5172VOJF/',
        writer=writer,
        validate=True
    )
    adapter.process_file()

    parsed = [json.loads(x) for x in writer.contents]
    assert len(parsed) == 2

    by_score = {p['bed_score']: p for p in parsed}
    assert '_plus_' in by_score[352]['_key']
    assert '_minus_' in by_score[368]['_key']


def test_genomic_element_biosample(mock_file_fileset):

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath='./samples/igvf_mpra_element_effects.example.tsv',
        label='genomic_element_biosample',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI1323RCIE/',
        reference_filepath='./samples/igvf_mpra_sequence_designs.example.tsv',
        reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI4914OUJH/',
        writer=writer,
        validate=True
    )
    adapter.process_file()
    parsed = [json.loads(x) for x in writer.contents]
    assert all(p['_from'].startswith('genomic_elements/')
               and p['_to'].startswith('ontology_terms/') for p in parsed)


def test_genomic_element_biosample_ref_allele_only_writes(tmp_path, mock_file_fileset):
    design_file = tmp_path / 'design.tsv'
    design_file.write_text(
        'chr\tstart\tend\tname\tSPDI\tallele\n'
        'chr1\t10\t20\tElem1\tNA\t["ref"]\n'
    )
    effects_file = tmp_path / 'effects.tsv'
    effects_file.write_text(
        'chr1\t10\t20\tElem1\t100\t+\t0.25\t1.0\t2.0\t3.0\t1.5\n'
    )

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath=str(effects_file),
        label='genomic_element_biosample',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI0000TEST/',
        reference_filepath=str(design_file),
        reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI0000REF/',
        writer=writer,
        validate=True
    )
    adapter.process_file()
    assert len(writer.contents) == 1


def test_genomic_element_biosample_mixed_ref_alt_writes_ref_element_effect(tmp_path, mock_file_fileset):
    """Design row with both ref and alt is valid; biosample edge loads (ref is present)."""
    design_file = tmp_path / 'design.tsv'
    design_file.write_text(
        'chr\tstart\tend\tname\tSPDI\tallele\n'
        'chr1\t10\t20\tElem1\tNA\t["ref", "alt"]\n'
    )
    effects_file = tmp_path / 'effects.tsv'
    effects_file.write_text(
        'chr1\t10\t20\tElem1\t100\t+\t0.25\t1.0\t2.0\t3.0\t1.5\n'
    )

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath=str(effects_file),
        label='genomic_element_biosample',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI0000TEST/',
        reference_filepath=str(design_file),
        reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI0000REF/',
        writer=writer,
        validate=True
    )
    adapter.process_file()
    assert len(writer.contents) == 1


def test_genomic_element_biosample_missing_allele_writes(tmp_path, mock_file_fileset):
    design_file = tmp_path / 'design.tsv'
    design_file.write_text(
        'chr\tstart\tend\tname\tSPDI\tallele\n'
        'chr1\t10\t20\tElem1\tNA\tNA\n'
    )
    effects_file = tmp_path / 'effects.tsv'
    effects_file.write_text(
        'chr1\t10\t20\tElem1\t100\t+\t0.25\t1.0\t2.0\t3.0\t1.5\n'
    )

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath=str(effects_file),
        label='genomic_element_biosample',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI0000TEST/',
        reference_filepath=str(design_file),
        reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI0000REF/',
        writer=writer,
        validate=True
    )
    adapter.process_file()
    assert len(writer.contents) == 1


def test_genomic_element_biosample_missing_allele_multi_effect_is_flagged(tmp_path, mock_file_fileset):
    design_file = tmp_path / 'design.tsv'
    design_file.write_text(
        'chr\tstart\tend\tname\tSPDI\tallele\n'
        'chr1\t10\t20\tElem1\tNA\tNA\n'
        'chr1\t10\t20\tElem2\tNA\t["ref"]\n'
    )
    effects_file = tmp_path / 'effects.tsv'
    effects_file.write_text(
        'chr1\t10\t20\tElem1\t100\t+\t0.25\t1.0\t2.0\t3.0\t1.5\n'
        'chr1\t10\t20\tElem2\t100\t+\t0.25\t1.0\t2.0\t3.0\t1.5\n'
    )

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath=str(effects_file),
        label='genomic_element_biosample',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI0000TEST/',
        reference_filepath=str(design_file),
        reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI0000REF/',
        writer=writer,
        validate=True
    )
    with pytest.raises(ValueError, match='Missing allele annotations for regions with multiple element effects'):
        adapter.process_file()


def test_genomic_element_biosample_control_ignored_and_ref_loaded(tmp_path, mock_file_fileset):
    design_file = tmp_path / 'design.tsv'
    design_file.write_text(
        'chr\tstart\tend\tname\tSPDI\tallele\tclass\n'
        'chr1\t10\t20\tNegative 1 (chr1:11-21)\tNA\tNA\telement inactive control\n'
        'chr1\t10\t20\tVariant 1 (chr1:11-21)\t["NC_000001.11:11:A:C"]\t["ref"]\ttest\n'
        'chr1\t10\t20\tVariant 2 (chr1:11-21)\t["NC_000001.11:11:A:C"]\t["alt"]\ttest\n'
    )
    effects_file = tmp_path / 'effects.tsv'
    effects_file.write_text(
        'chr1\t10\t20\tNegative_1_(chr1:11-21)\t100\t+\t0.25\t1.0\t2.0\t3.0\t1.5\n'
        'chr1\t10\t20\tVariant_1_(chr1:11-21)\t100\t+\t0.25\t1.0\t2.0\t3.0\t1.5\n'
        'chr1\t10\t20\tVariant_2_(chr1:11-21)\t100\t+\t0.25\t1.0\t2.0\t3.0\t1.5\n'
    )

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath=str(effects_file),
        label='genomic_element_biosample',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI0000TEST/',
        reference_filepath=str(design_file),
        reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI0000REF/',
        writer=writer,
        validate=True
    )
    adapter.process_file()
    assert len(writer.contents) == 1


def test_genomic_element_biosample_same_coords_different_strands_have_unique_ids(tmp_path, mock_file_fileset):
    design_file = tmp_path / 'design.tsv'
    design_file.write_text(
        'chr\tstart\tend\tname\tSPDI\tallele\tclass\tstrand\n'
        'chr1\t10\t20\tElem_fwd\t["NC_000001.11:11:A:C"]\t["ref"]\ttest\t+\n'
        'chr1\t10\t20\tElem_rev\t["NC_000001.11:11:A:C"]\t["ref"]\ttest\t-\n'
    )
    effects_file = tmp_path / 'effects.tsv'
    effects_file.write_text(
        'chr1\t10\t20\tElem_fwd\t100\t+\t0.25\t1.0\t2.0\t3.0\t1.5\n'
        'chr1\t10\t20\tElem_rev\t90\t-\t0.2\t1.0\t2.0\t3.0\t1.5\n'
    )

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath=str(effects_file),
        label='genomic_element_biosample',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI0000TEST/',
        reference_filepath=str(design_file),
        reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI0000REF/',
        writer=writer,
        validate=True
    )
    adapter.process_file()
    parsed = [json.loads(x) for x in writer.contents]
    assert len(parsed) == 2
    assert len({p['_key'] for p in parsed}) == 2
    assert len({p['_from'] for p in parsed}) == 1


@pytest.mark.parametrize('label', ['genomic_element', 'genomic_element_biosample'])
def test_igvffi1436trih_exclusion_list_is_applied(tmp_path, mock_file_fileset, label):
    excluded_name = (
        'cardiac_neuro_cava_random:ALT_KANSL1|ENSG00000120071.15|'
        'EH38E3227108_rev_tile1-1_KANSL1|ENSG00000120071.15|'
        'EH38E3227108|17-46152590-G-C'
    )
    design_file = tmp_path / 'design.tsv'
    design_file.write_text(
        'chr\tstart\tend\tname\tSPDI\tallele\tclass\tstrand\n'
        f'chr17\t46152515\t46152785\t{excluded_name}\tNA\tNA\ttest\t-\n'
    )
    effects_file = tmp_path / 'effects.tsv'
    effects_file.write_text(
        f'chr17\t46152515\t46152785\t{excluded_name}\t100\t-\t0.25\t1.0\t2.0\t3.0\t1.5\n'
    )

    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath=str(effects_file),
        label=label,
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI0000TEST/',
        reference_filepath=str(design_file),
        reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI1436TRIH/',
        writer=writer,
        validate=True
    )
    adapter.process_file()
    assert len(writer.contents) == 0


def test_invalid_label(mock_file_fileset):
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_label'):
        MPRAAdapter(
            filepath='./samples/igvf_mpra_element_effects.example.tsv',
            label='invalid_label',
            source_url='https://api.data.igvf.org/tabular-files/IGVFFI1323RCIE/',
            reference_filepath='./samples/igvf_mpra_sequence_designs.example.tsv',
            reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI4914OUJH/',
            writer=writer,
            validate=True)


def test_validate_doc_invalid(mock_file_fileset):
    writer = SpyWriter()
    adapter = MPRAAdapter(
        filepath='./samples/igvf_mpra_element_effects.example.tsv',
        label='genomic_element',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI1323RCIE/',
        reference_filepath='./samples/igvf_mpra_sequence_designs.example.tsv',
        reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI4914OUJH/',
        writer=writer,
        validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
