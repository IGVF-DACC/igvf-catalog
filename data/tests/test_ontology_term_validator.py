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
