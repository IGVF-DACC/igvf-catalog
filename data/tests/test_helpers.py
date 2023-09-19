import pytest
import hashlib
from adapters.helpers import build_variant_id, build_regulatory_region_id, to_float


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
        class_name, chr, pos_start, pos_end, assembly)

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
    assert to_float(number) == (number * 100)  # 3.14e-308

    number = float('3.14e-400')
    assert to_float(number) == 0
