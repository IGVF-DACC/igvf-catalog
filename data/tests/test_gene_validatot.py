import pytest
from unittest.mock import MagicMock
from adapters.gene_validator import GeneValidator


@pytest.fixture
def mock_arango_db():
    # Mock the ArangoDB connection and its methods
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.__iter__.return_value = ['gene1', 'gene2', 'gene3']
    mock_db.aql.execute.return_value = mock_cursor
    return mock_db


@pytest.fixture
def gene_validator(mock_arango_db, monkeypatch):
    # Patch the ArangoDB connection in GeneValidator
    monkeypatch.setattr(
        'db.arango_db.ArangoDB.get_igvf_connection', lambda _: mock_arango_db)
    return GeneValidator()


def test_validate_valid_gene(gene_validator):
    assert gene_validator.validate('gene1') is True
    assert gene_validator.validate('gene2') is True


def test_validate_invalid_gene(gene_validator):
    assert gene_validator.validate('invalid_gene') is False
    assert 'invalid_gene' in gene_validator.invalid_gene_ids


def test_log_invalid_gene_ids(gene_validator, capsys):
    gene_validator.validate('invalid_gene')
    gene_validator.log()
    captured = capsys.readouterr()
    assert 'Invalid gene IDs encountered: 1' in captured.out
    assert 'Invalid gene IDs: [\'invalid_gene\']' in captured.out


def test_log_all_valid_gene_ids(gene_validator, capsys):
    gene_validator.validate('gene1')
    gene_validator.validate('gene2')
    gene_validator.log()
    captured = capsys.readouterr()
    assert 'All gene IDs are valid.' in captured.out
