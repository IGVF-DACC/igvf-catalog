import io
import json
from unittest.mock import patch

from adapters.ontology_term_validator import OntologyTermValidator


def test_ensure_true_and_false():
    with patch.object(OntologyTermValidator, 'preload', return_value=None):
        v = OntologyTermValidator()
        v._valid_term_keys = {'GO_1'}
        assert v.ensure('GO_1') is True
        assert v.ensure('GO_missing') is False


def test_normalize_term_key():
    assert OntologyTermValidator.normalize_term_key(
        'GO:0006914') == 'GO_0006914'
    assert OntologyTermValidator.normalize_term_key(
        'ontology_terms/GO_0006914') == 'GO_0006914'
    assert OntologyTermValidator.normalize_term_key(
        'GO_0006914') == 'GO_0006914'
    assert OntologyTermValidator.normalize_term_key('') is None
    assert OntologyTermValidator.normalize_term_key(None) is None


def _iri_for_key(term_key):
    ontology_id, iri = OntologyTermValidator._ols_ontology_and_iri(term_key)
    assert ontology_id and iri
    return iri


def _ols_response(term_key, *, is_obsolete=False, replaced_by=None, consider=None,
                  use_term_replaced_by=True):
    annotation = {}
    term = {
        'label': term_key,
        'is_obsolete': is_obsolete,
        'annotation': annotation,
    }
    if replaced_by is not None:
        annotation['term replaced by'] = [_iri_for_key(r) for r in replaced_by]
        if use_term_replaced_by and len(replaced_by) == 1:
            term['term_replaced_by'] = replaced_by[0]
    if consider is not None:
        annotation['consider'] = [_iri_for_key(c) for c in consider]
    payload = {'_embedded': {'terms': [term]}}
    return io.BytesIO(json.dumps(payload).encode('utf-8'))


def test_single_replaced_by_prefers_top_level():
    v = OntologyTermValidator()
    assert v._single_replaced_by({
        'term_replaced_by': 'MONDO_0018894',
        'annotation': {
            'term replaced by': [
                'http://purl.obolibrary.org/obo/MONDO_9999999',
            ],
        },
    }) == 'MONDO_0018894'


def test_single_replaced_by_falls_back_to_annotation():
    v = OntologyTermValidator()
    assert v._single_replaced_by({
        'annotation': {
            'term replaced by': [
                'http://purl.obolibrary.org/obo/MONDO_0018894',
            ],
        },
    }) == 'MONDO_0018894'


def test_single_replaced_by_normalizes_curie():
    v = OntologyTermValidator()
    assert v._single_replaced_by({
        'term_replaced_by': 'MONDO:0018894',
    }) == 'MONDO_0018894'


def test_ols_ontology_and_iri_obo_efo_orphanet():
    assert OntologyTermValidator._ols_ontology_and_iri('MONDO_0005148') == (
        'mondo',
        'http://purl.obolibrary.org/obo/MONDO_0005148',
    )
    assert OntologyTermValidator._ols_ontology_and_iri('EFO_0002869') == (
        'efo',
        'http://www.ebi.ac.uk/efo/EFO_0002869',
    )
    assert OntologyTermValidator._ols_ontology_and_iri('Orphanet_15') == (
        'ordo',
        'http://www.orpha.net/ORDO/Orphanet_15',
    )
    assert OntologyTermValidator._ols_ontology_and_iri('ORPHANET_15') == (
        'ordo',
        'http://www.orpha.net/ORDO/ORPHANET_15',
    )


def _validator_with_db(valid_keys):
    """Return a validator whose DB query marks only valid_keys as present."""
    v = OntologyTermValidator()
    valid = set(valid_keys)

    def fake_query(term_keys):
        return set(term_keys) & valid

    v._query_existing_keys = fake_query
    return v


@patch('adapters.ontology_term_validator.urllib.request.urlopen')
def test_preload_resolve_via_ols_single_replaced_by(mock_urlopen):
    mock_urlopen.return_value.__enter__.side_effect = [
        _ols_response(
            'MONDO_0000075', is_obsolete=True, replaced_by=['MONDO_0018894']),
        _ols_response('MONDO_0018894', is_obsolete=False),
    ]

    v = _validator_with_db({'MONDO_0018894'})
    v.preload(['MONDO_0000075', 'MONDO_0018894'], resolve_via_ols=True)

    assert v._remaps == {'MONDO_0000075': 'MONDO_0018894'}
    assert 'MONDO_0018894' in v._valid_term_keys
    assert v.resolve('MONDO_0000075') == 'MONDO_0018894'
    assert v.resolve('MONDO_0018894') == 'MONDO_0018894'


@patch('adapters.ontology_term_validator.urllib.request.urlopen')
def test_preload_resolve_via_ols_follows_obsolete_chain(mock_urlopen):
    mock_urlopen.return_value.__enter__.side_effect = [
        _ols_response(
            'MONDO_0010107', is_obsolete=True, replaced_by=['MONDO_8000017']),
        _ols_response(
            'MONDO_8000017', is_obsolete=True, replaced_by=['MONDO_8000015']),
        _ols_response('MONDO_8000015', is_obsolete=False),
    ]

    v = _validator_with_db({'MONDO_8000015'})
    v.preload(['MONDO_0010107'], resolve_via_ols=True)

    assert v._remaps == {'MONDO_0010107': 'MONDO_8000015'}
    assert v.resolve('MONDO_0010107') == 'MONDO_8000015'


@patch('adapters.ontology_term_validator.urllib.request.urlopen')
def test_preload_resolve_via_ols_no_replaced_by(mock_urlopen):
    mock_urlopen.return_value.__enter__.return_value = _ols_response(
        'MONDO_9999999',
        is_obsolete=True,
        replaced_by=[],
    )

    v = _validator_with_db(set())
    v.preload(['MONDO_9999999'], resolve_via_ols=True)

    assert v._remaps == {}
    assert v.resolve('MONDO_9999999') is None
    assert 'MONDO_9999999' in v.invalid_term_keys


@patch('adapters.ontology_term_validator.urllib.request.urlopen')
def test_preload_resolve_via_ols_skips_multi_consider(mock_urlopen):
    # Obsolete with only consider (no single replaced_by) must not remap.
    mock_urlopen.return_value.__enter__.return_value = _ols_response(
        'MONDO_0014824',
        is_obsolete=True,
        consider=['MONDO_0031632', 'MONDO_0800438'],
    )

    v = _validator_with_db({'MONDO_0031632', 'MONDO_0800438'})
    v.preload(['MONDO_0014824'], resolve_via_ols=True)

    assert v._remaps == {}
    assert v.resolve('MONDO_0014824') is None


@patch('adapters.ontology_term_validator.urllib.request.urlopen')
def test_preload_resolve_via_ols_rejects_replacement_not_in_db(mock_urlopen):
    mock_urlopen.return_value.__enter__.side_effect = [
        _ols_response(
            'MONDO_0000075', is_obsolete=True, replaced_by=['MONDO_0018894']),
        _ols_response('MONDO_0018894', is_obsolete=False),
    ]

    v = _validator_with_db(set())  # replacement not in DB
    v.preload(['MONDO_0000075'], resolve_via_ols=True)

    assert v._remaps == {}
    assert v.resolve('MONDO_0000075') is None


def test_preload_without_ols_skips_network():
    v = _validator_with_db({'MONDO_0008426'})
    with patch.object(v, '_fetch_ols_term') as mock_fetch:
        v.preload(['MONDO_0008426'])
        mock_fetch.assert_not_called()
    assert v._remaps == {}
    assert v.resolve('MONDO_0008426') == 'MONDO_0008426'


def test_preload_resolve_via_ols_noop_when_already_in_db():
    v = _validator_with_db({'MONDO_0008426'})
    with patch.object(v, '_fetch_ols_term') as mock_fetch:
        v.preload(['MONDO_0008426'], resolve_via_ols=True)
        mock_fetch.assert_not_called()
    assert v._remaps == {}
    assert v.resolve('MONDO_0008426') == 'MONDO_0008426'


@patch('adapters.ontology_term_validator.urllib.request.urlopen')
def test_preload_resolve_via_ols_breaks_cycles(mock_urlopen):
    mock_urlopen.return_value.__enter__.side_effect = [
        _ols_response(
            'MONDO_AAAA', is_obsolete=True, replaced_by=['MONDO_BBBB']),
        _ols_response(
            'MONDO_BBBB', is_obsolete=True, replaced_by=['MONDO_AAAA']),
    ]

    v = _validator_with_db(set())
    v.preload(['MONDO_AAAA'], resolve_via_ols=True)

    assert v._remaps == {}
    assert v.resolve('MONDO_AAAA') is None


@patch('adapters.ontology_term_validator.urllib.request.urlopen')
def test_preload_resolve_via_ols_efo(mock_urlopen):
    mock_urlopen.return_value.__enter__.side_effect = [
        _ols_response(
            'EFO_0000400', is_obsolete=True, replaced_by=['EFO_0000408']),
        _ols_response('EFO_0000408', is_obsolete=False),
    ]

    v = _validator_with_db({'EFO_0000408'})
    v.preload(['EFO_0000400'], resolve_via_ols=True)

    assert v._remaps == {'EFO_0000400': 'EFO_0000408'}
    assert v.resolve('EFO_0000400') == 'EFO_0000408'
    requested = mock_urlopen.call_args_list[0].args[0]
    assert '/ontologies/efo/terms?' in requested
    assert 'www.ebi.ac.uk%2Fefo%2FEFO_0000400' in requested


@patch('adapters.ontology_term_validator.urllib.request.urlopen')
def test_preload_resolve_via_ols_orphanet(mock_urlopen):
    mock_urlopen.return_value.__enter__.side_effect = [
        _ols_response(
            'Orphanet_111', is_obsolete=True, replaced_by=['Orphanet_222']),
        _ols_response('Orphanet_222', is_obsolete=False),
    ]

    v = _validator_with_db({'Orphanet_222'})
    v.preload(['Orphanet_111'], resolve_via_ols=True)

    assert v._remaps == {'Orphanet_111': 'Orphanet_222'}
    assert v.resolve('Orphanet_111') == 'Orphanet_222'
    requested = mock_urlopen.call_args_list[0].args[0]
    assert '/ontologies/ordo/terms?' in requested
    assert 'www.orpha.net%2FORDO%2FOrphanet_111' in requested


def test_log_prints_remaps(capsys):
    v = OntologyTermValidator()
    v._valid_term_keys = {'MONDO_0018894'}
    v._remaps = {'MONDO_0000075': 'MONDO_0018894'}
    v.log()
    captured = capsys.readouterr().out
    assert 'Ontology term IDs remapped via OLS: 1' in captured
    assert 'MONDO_0000075 -> MONDO_0018894' in captured
    assert 'All ontology term IDs are valid.' not in captured


def test_log_all_valid_only_without_remaps(capsys):
    v = OntologyTermValidator()
    v._valid_term_keys = {'MONDO_0008426'}
    v.log()
    captured = capsys.readouterr().out
    assert captured.strip() == 'All ontology term IDs are valid.'
