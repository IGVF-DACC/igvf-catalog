import pytest
import hashlib
from adapters.helpers import build_variant_id, build_regulatory_region_id, to_float, query_fileset_files_props_igvf


def test_build_variant_id_fails_for_unsupported_assembly():
    with pytest.raises(ValueError, match='Assembly not supported'):
        build_variant_id(None, None, None, None, 'hg19')

    try:
        build_variant_id(None, None, None, None, 'GRCh38')
        build_variant_id(None, None, None, None)
    except:
        assert False, 'build_variant_id raised exception for GRCh38'


def test_build_variant_id_creates_id_string():
    chr = 'chr'
    pos = 'pos'
    ref_seq = 'ref_seq'
    alt_seq = 'alt_seq'
    assembly = 'GRCh38'

    variant_id = build_variant_id(chr, pos, ref_seq, alt_seq, assembly)
    assert variant_id == hashlib.sha256('{}_{}_{}_{}_{}'.format(
        chr.replace('chr', '').lower(), pos, ref_seq, alt_seq, 'GRCh38').encode()).hexdigest()


def test_build_regulatory_region_id_creates_id_string():
    class_name = 'class_name'
    chr = 'chr'
    pos_start = 'start'
    pos_end = 'end'
    assembly = 'GRCh38'

    id = build_regulatory_region_id(
        chr, pos_start, pos_end, class_name, assembly)

    assert id == '{}_{}_{}_{}_{}'.format(
        class_name, chr, pos_start, pos_end, assembly)


def test_build_regulatory_region_id_fails_for_unsupported_assembly():
    with pytest.raises(ValueError, match='Assembly not supported'):
        build_regulatory_region_id(None, None, None, None, 'hg19')

    try:
        build_regulatory_region_id(None, None, None, None, 'GRCh38')
        build_regulatory_region_id(None, None, None, None)
    except:
        assert False, 'build_regulatory_region_id raised exception for GRCh38'


def test_to_float_adapts_exponent_correctly():
    number = '3.14'
    assert to_float('3.14') == 3.14

    number = '3.14e10'
    assert to_float(number) == float(number)

    number = '3.14e400'
    assert to_float(number) == float('1e307')

    number = '3.14e-10'
    assert to_float(number) == float(number)

    number = float('3.14e-310')
    assert to_float(number) == (number * 1000)  # 3.14e-307

    number = float('3.14e-400')
    assert to_float(number) == 0


def test_query_fileset_files_props_igvf():
    blue_starr_prediction_props = query_fileset_files_props_igvf(
        'IGVFFI1236SEPK')
    assert blue_starr_prediction_props == {
        '_key': 'IGVFFI1236SEPK',
        'file_set_id': 'IGVFDS0257SDNV',
        'lab': '/labs/bill-majoros/',
        'preferred_assay_title': None,
        'assay_term': None,
        'prediction': True,
        'prediction_method': 'functional effect',
        'software': 'bluestarr',
        'sample': 'K562',
        'sample_id': ['IGVFSM7883WOIS'],
        'simple_sample_summary': 'K562',
        'donor_id': 'IGVFDO9208RPQQ',
        'treatments_term_ids': None,
        'publications': None,
    }
    scCRISPRscreen_DE_props = query_fileset_files_props_igvf('IGVFFI4846IRZK')
    assert scCRISPRscreen_DE_props == {
        '_key': 'IGVFFI4846IRZK',
        'file_set_id': 'IGVFDS4021XJLW',
        'lab': '/labs/jay-shendure/',
        'preferred_assay_title': 'scCRISPR screen',
        'assay_term': '/assay-terms/OBI_0003660/',
        'prediction': False,
        'prediction_method': None,
        'software': ['sceptre'],
        'sample': 'GM25256 (WTC-11)',
        'sample_id': ['IGVFSM7750SNNY', 'IGVFSM8317ZTFV', 'IGVFSM8382KOXO', 'IGVFSM9913PXTT'],
        'simple_sample_summary': 'GM25256 (WTC-11)',
        'donor_id': 'IGVFDO1756PPKO',
        'treatments_term_ids': None,
        'publications': 'doi:10.1038/s41467-024-52490-4',
    }
