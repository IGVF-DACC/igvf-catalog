from db.arango_db import ArangoDB


class GeneValidator:
    def __init__(self):
        self._valid_gene_ids = None  # Lazy loading - will be loaded on first use
        self.invalid_gene_ids = set()

    def _load_valid_gene_ids(self):
        """Load valid gene IDs from database only when needed."""
        if self._valid_gene_ids is None:
            db = ArangoDB().get_igvf_connection()
            cursor = db.aql.execute(
                'FOR gene IN genes RETURN gene._key'
            )
            self._valid_gene_ids = set(cursor)
        return self._valid_gene_ids

    def validate(self, gene_id: str) -> bool:
        """Validate a gene ID against the database."""
        valid_ids = self._load_valid_gene_ids()
        if gene_id not in valid_ids:
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
