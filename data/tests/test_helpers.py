import pytest
from adapters.helpers import build_variant_id, build_accessible_dna_region_id


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

    assert variant_id == '{}_{}_{}_{}_{}'.format(
        chr, pos, ref_seq, alt_seq, 'GRCh38')


def test_build_open_chromatic_region_id_fails_for_unsupported_assembly():
    with pytest.raises(ValueError, match='Assembly not supported'):
        build_accessible_dna_region_id(None, None, None, 'hg19')

    try:
        build_accessible_dna_region_id(None, None, None, 'GRCh38')
        build_accessible_dna_region_id(None, None, None)
    except:
        assert False, 'build_chromatic_region_id raised exception for GRCh38'


def test_build_variant_id_creates_id_string():
    chr = 'chr'
    pos_start = 'start'
    pos_end = 'end'
    assembly = 'GRCh38'

    id = build_accessible_dna_region_id(chr, pos_start, pos_end, assembly)

    assert id == '{}_{}_{}_{}'.format(chr, pos_start, pos_end, assembly)
