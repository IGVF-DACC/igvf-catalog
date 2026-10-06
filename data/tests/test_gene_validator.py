from unittest.mock import patch

import pytest

from adapters.gene_validator import GeneValidator


@pytest.mark.parametrize('collection,gene', [
    ('genes', 'ENSG00000123685'),
    ('mm_genes', 'ENSMUSG00000032440'),
])
def test_gene_validator_uses_species_collection(collection, gene):
    with patch('adapters.gene_validator.ArangoDB') as arango:
        query = arango.return_value.get_igvf_connection.return_value.aql.execute
        query.return_value = [gene]
        validator = GeneValidator(collection)
        assert validator.validate(gene)
        assert not validator.validate('missing')
        query.assert_called_once_with(
            f'FOR gene IN {collection} RETURN gene._key')
