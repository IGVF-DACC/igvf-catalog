import pytest
import hashlib
from adapters.helpers import build_variant_id, build_regulatory_region_id, to_float
from unittest.mock import patch, MagicMock
from adapters.helpers import bulk_check_spdis_in_arangodb


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


def test_bulk_check_spdis_in_arangodb_returns_correct_set():
    spdis = ['NC_000001.11:100:A:T', 'NC_000002.12:200:G:C']
    expected_result = {'NC_000001.11:100:A:T'}

    mock_cursor = MagicMock()
    mock_cursor.__iter__.return_value = iter(expected_result)

    with patch('adapters.helpers.ArangoDB') as MockArangoDB:
        mock_db_instance = MockArangoDB.return_value.get_igvf_connection.return_value
        mock_db_instance.aql.execute.return_value = mock_cursor

        result = bulk_check_spdis_in_arangodb(spdis)

        assert result == expected_result
        mock_db_instance.aql.execute.assert_called_once_with(
            'FOR v IN variants FILTER v.spdi IN @spids RETURN v.spdi',
            bind_vars={'spids': spdis}
        )


def test_bulk_check_spdis_in_arangodb_handles_empty_input():
    spdis = []
    expected_result = set()

    mock_cursor = MagicMock()
    mock_cursor.__iter__.return_value = iter(expected_result)

    with patch('adapters.helpers.ArangoDB') as MockArangoDB:
        mock_db_instance = MockArangoDB.return_value.get_igvf_connection.return_value
        mock_db_instance.aql.execute.return_value = mock_cursor

        result = bulk_check_spdis_in_arangodb(spdis)

        assert result == expected_result
        mock_db_instance.aql.execute.assert_called_once_with(
            'FOR v IN variants FILTER v.spdi IN @spids RETURN v.spdi',
            bind_vars={'spids': spdis}
        )


def test_bulk_check_spdis_in_arangodb_handles_no_matches():
    spdis = ['NC_000003.12:300:T:A']
    expected_result = set()

    mock_cursor = MagicMock()
    mock_cursor.__iter__.return_value = iter(expected_result)

    with patch('adapters.helpers.ArangoDB') as MockArangoDB:
        mock_db_instance = MockArangoDB.return_value.get_igvf_connection.return_value
        mock_db_instance.aql.execute.return_value = mock_cursor

        result = bulk_check_spdis_in_arangodb(spdis)

        assert result == expected_result
        mock_db_instance.aql.execute.assert_called_once_with(
            'FOR v IN variants FILTER v.spdi IN @spids RETURN v.spdi',
            bind_vars={'spids': spdis}
        )


def test_bulk_check_spdis_in_arangodb():
    spdis = ['NC_000003.12:300:T:A', 'NC_000003.12:300:G:C']
    expected_result = set(['NC_000003.12:300:G:C'])

    mock_cursor = MagicMock()
    mock_cursor.__iter__.return_value = iter(expected_result)

    with patch('adapters.helpers.ArangoDB') as MockArangoDB:
        mock_db_instance = MockArangoDB.return_value.get_igvf_connection.return_value
        mock_db_instance.aql.execute.return_value = mock_cursor

        result = bulk_check_spdis_in_arangodb(spdis)

        assert result == expected_result
        mock_db_instance.aql.execute.assert_called_once_with(
            'FOR v IN variants FILTER v.spdi IN @spids RETURN v.spdi',
            bind_vars={'spids': spdis}
        )
