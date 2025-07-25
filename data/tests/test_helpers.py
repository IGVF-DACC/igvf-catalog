import pytest
import hashlib
from adapters.helpers import build_variant_id, build_regulatory_region_id, to_float, check_illegal_base_in_spdi, load_variant
from unittest.mock import patch, MagicMock
from adapters.helpers import bulk_check_variants_in_arangodb


def test_build_variant_id_fails_for_unsupported_assembly():
    with pytest.raises(ValueError, match='Assembly not supported'):
        build_variant_id(None, None, None, None, 'hg19')


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


def test_bulk_check_variants_in_arangodb_returns_correct_set():
    spdis = ['NC_000001.11:100:A:T', 'NC_000002.12:200:G:C']
    expected_result = {'NC_000001.11:100:A:T'}

    mock_cursor = MagicMock()
    mock_cursor.__iter__.return_value = iter(expected_result)

    with patch('adapters.helpers.ArangoDB') as MockArangoDB:
        mock_db_instance = MockArangoDB.return_value.get_igvf_connection.return_value
        mock_db_instance.aql.execute.return_value = mock_cursor

        result = bulk_check_variants_in_arangodb(spdis)

        assert result == expected_result
        mock_db_instance.aql.execute.assert_called_once_with(
            'FOR v IN variants FILTER v._key IN @spdis RETURN v._key',
            bind_vars={'spdis': spdis}
        )


def test_bulk_check_variants_in_arangodb_handles_empty_input():
    spdis = []
    expected_result = set()

    mock_cursor = MagicMock()
    mock_cursor.__iter__.return_value = iter(expected_result)

    with patch('adapters.helpers.ArangoDB') as MockArangoDB:
        mock_db_instance = MockArangoDB.return_value.get_igvf_connection.return_value
        mock_db_instance.aql.execute.return_value = mock_cursor

        result = bulk_check_variants_in_arangodb(spdis)

        assert result == expected_result
        mock_db_instance.aql.execute.assert_called_once_with(
            'FOR v IN variants FILTER v._key IN @spdis RETURN v._key',
            bind_vars={'spdis': spdis}
        )


def test_bulk_check_variants_in_arangodb_handles_no_matches():
    spdis = ['NC_000003.12:300:T:A']
    expected_result = set()

    mock_cursor = MagicMock()
    mock_cursor.__iter__.return_value = iter(expected_result)

    with patch('adapters.helpers.ArangoDB') as MockArangoDB:
        mock_db_instance = MockArangoDB.return_value.get_igvf_connection.return_value
        mock_db_instance.aql.execute.return_value = mock_cursor

        result = bulk_check_variants_in_arangodb(spdis)

        assert result == expected_result
        mock_db_instance.aql.execute.assert_called_once_with(
            'FOR v IN variants FILTER v._key IN @spdis RETURN v._key',
            bind_vars={'spdis': spdis}
        )


def test_bulk_check_variants_in_arangodb():
    spdis = ['NC_000003.12:300:T:A', 'NC_000003.12:300:G:C']
    expected_result = set(['NC_000003.12:300:G:C'])

    mock_cursor = MagicMock()
    mock_cursor.__iter__.return_value = iter(expected_result)

    with patch('adapters.helpers.ArangoDB') as MockArangoDB:
        mock_db_instance = MockArangoDB.return_value.get_igvf_connection.return_value
        mock_db_instance.aql.execute.return_value = mock_cursor

        result = bulk_check_variants_in_arangodb(spdis)

        assert result == expected_result
        mock_db_instance.aql.execute.assert_called_once_with(
            'FOR v IN variants FILTER v._key IN @spdis RETURN v._key',
            bind_vars={'spdis': spdis}
        )


def test_check_illegal_base_valid_bases():
    spdi = 'NC_000001.11:12345:A:T'
    assert check_illegal_base_in_spdi(spdi) is None


def test_check_illegal_base_invalid_ref():
    spdi = 'NC_000001.11:12345:N:T'
    result = check_illegal_base_in_spdi(spdi)
    assert result == {'variant_id': spdi, 'reason': 'Ambigious ref allele'}


def test_check_illegal_base_invalid_alt():
    spdi = 'NC_000001.11:12345:A:N'
    result = check_illegal_base_in_spdi(spdi)
    assert result == {'variant_id': spdi, 'reason': 'Ambigious alt allele'}


@patch('adapters.helpers.get_ref_seq_by_spdi', return_value='A')
@patch('adapters.helpers.get_seqrepo')
@patch('adapters.helpers.SeqRepoDataProxy')
@patch('adapters.helpers.AlleleTranslator')
@patch('adapters.helpers.build_spdi', return_value='NC_000001.11:12345:A:T')
@patch('adapters.helpers.build_hgvs_from_spdi', return_value='NC_000001.11:g.12346A>T')
def test_valid_spdi_input(mock_hgvs, mock_build, mock_translator, mock_proxy, mock_seqrepo, mock_ref_seq):
    variant_id = 'NC_000001.11:12345:A:T'
    result, skipped = load_variant(variant_id)
    assert skipped is None
    assert result['ref'] == 'A'
    assert result['alt'] == 'T'
    assert result['variation_type'] == 'SNP'
    assert result['hgvs'] == 'NC_000001.11:g.12346A>T'


def test_unable_to_parse_variant():
    variant_id = 'BAD_FORMAT'
    result, skipped = load_variant(variant_id)
    assert result == {}
    assert skipped == {'variant_id': variant_id,
                       'reason': 'Unable to parse this variant id'}


@patch('adapters.helpers.get_ref_seq_by_spdi', return_value='A')
def test_empty_alt(mock_ref_seq):
    variant_id = 'NC_000001.11:12345:A:'
    result, skipped = load_variant(variant_id)
    assert result['ref'] == 'A'
    assert result['alt'] == ''
    assert result['variation_type'] == 'deletion'
    assert skipped is None or 'Ref allele mismatch' not in skipped.get(
        'reason', '')


@patch('adapters.helpers.get_ref_seq_by_spdi', return_value='')
def test_spdi_empty_ref(mock_ref_seq):
    variant_id = 'NC_000010.11:79347444::CCTCCTCAGG'
    result, skipped = load_variant(variant_id)
    assert result['ref'] == ''
    assert result['alt'] == 'CCTCCTCAGG'
    assert result['variation_type'] == 'insertion'
    assert skipped is None or 'Ref allele mismatch' not in skipped.get(
        'reason', '')


@patch('adapters.helpers.get_ref_seq_by_spdi', return_value='T')
def test_ref_mismatch_on_partial_spdi(mock_ref_seq):
    variant_id = 'NC_000001.11:12345:A:'  # ref != genome
    result, skipped = load_variant(variant_id)
    assert result == {}
    assert skipped['reason'] == 'Ref allele mismatch'


@patch('adapters.helpers.get_seqrepo')
@patch('adapters.helpers.SeqRepoDataProxy')
@patch('adapters.helpers.AlleleTranslator')
@patch('adapters.helpers.build_spdi', side_effect=ValueError('Ref allele mismatch'))
def test_build_spdi_raises_error(mock_build, mock_translator, mock_proxy, mock_seqrepo):
    variant_id = 'NC_000001.11:12345:A:T'
    result, skipped = load_variant(variant_id)
    assert result == {}
    assert skipped['reason'] == 'Ref allele mismatch'


@patch('adapters.helpers.get_seqrepo')
@patch('adapters.helpers.SeqRepoDataProxy')
@patch('adapters.helpers.AlleleTranslator')
@patch('adapters.helpers.build_spdi', return_value='NC_000001.11:12345:A:N')
def test_illegal_base_in_alt(mock_build, mock_translator, mock_proxy, mock_seqrepo):
    variant_id = 'NC_000001.11:12345:A:N'
    result, skipped = load_variant(variant_id)
    assert result == {}
    assert skipped == {'variant_id': variant_id,
                       'reason': 'Ambigious alt allele'}


@patch('adapters.helpers.get_seqrepo')
@patch('adapters.helpers.SeqRepoDataProxy')
@patch('adapters.helpers.AlleleTranslator')
@patch('adapters.helpers.build_spdi', return_value='NC_000010.11:79347444:T:CCTCCTCAGG')
@patch('adapters.helpers.build_hgvs_from_spdi', return_value='NC_000010.11:g.79347445T>CCTCCTCAGG')
def test_valid_vcf_input(mock_hgvs, mock_build, mock_translator, mock_proxy, mock_seqrepo):
    variant_id = '10-79347445-T-CCTCCTCAGG'
    result, skipped = load_variant(variant_id)
    assert skipped is None
    assert result['chr'] == 'chr10'
    assert result['ref'] == 'T'
    assert result['alt'] == 'CCTCCTCAGG'
    assert result['spdi'] == 'NC_000010.11:79347444:T:CCTCCTCAGG'
    assert result['variation_type'] == 'insertion'
    assert result['hgvs'] == 'NC_000010.11:g.79347445T>CCTCCTCAGG'


@patch('adapters.helpers.build_allele')
def test_long_spdi_triggers_digest(mock_build_allele):
    long_alt = 'T' * 245
    variant_id = f'1-12345-A-{long_alt}'
    long_spdi = f'NC_000001.11:12344:A:{long_alt}'

    # Mock build_spdi to return long SPDI
    with patch('adapters.helpers.build_spdi', return_value=long_spdi), \
            patch('adapters.helpers.build_hgvs_from_spdi', return_value='NC_000001.11:g.12345delins' + long_alt), \
            patch('adapters.helpers.get_seqrepo'), \
            patch('adapters.helpers.SeqRepoDataProxy'), \
            patch('adapters.helpers.AlleleTranslator'):

        mock_build_allele.return_value.digest = 'digest123'

        result, skipped = load_variant(variant_id)

        assert skipped is None
        assert result['_key'] == 'digest123'
        assert result['spdi'] == long_spdi
