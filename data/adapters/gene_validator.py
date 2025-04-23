from db.arango_db import ArangoDB


class GeneValidator:
    def __init__(self):
        self.db = ArangoDB().get_igvf_connection()
        self.valid_gene_ids = self._load_valid_gene_ids()
        self.invalid_gene_ids = set()

    def _load_valid_gene_ids(self):
        cursor = self.db.aql.execute(
            'FOR gene IN genes RETURN gene._key'
        )
        return set(cursor)

    def validate(self, gene_id: str) -> bool:
        if gene_id not in self.valid_gene_ids:
            self.invalid_gene_ids.add(gene_id)
            return False
        return True

    def log(self):
        if self.invalid_gene_ids:
            print(
                f'Invalid gene IDs encountered: {len(self.invalid_gene_ids)}')
            print(f'Invalid gene IDs: {sorted(self.invalid_gene_ids)}')
        else:
            print('All gene IDs are valid.')
