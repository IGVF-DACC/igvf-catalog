from db.arango_db import ArangoDB


class OntologyTermValidator:
    """Validate ontology term IDs against the ontology_terms collection.

    Prefer bulk checking the unique terms from a datafile via ``preload()``,
    then calling ``validate()`` per row. This avoids loading the full
    ontology_terms collection into memory.
    """

    def __init__(self, collection='ontology_terms', chunk_size=500):
        if collection != 'ontology_terms':
            raise ValueError(
                f'Unsupported ontology term collection: {collection}')
        self.collection = collection
        self.chunk_size = chunk_size
        self._valid_term_keys = None
        self.invalid_term_keys = set()

    @staticmethod
    def normalize_term_key(term_key):
        """Return a bare ontology_terms _key, or None if term_key is empty.

        Accepts bare keys (``GO_0006914``), CURIE forms (``GO:0006914``), or
        full handles (``ontology_terms/GO_0006914``).
        """
        if not term_key:
            return None
        key = str(term_key).strip()
        if key.startswith('ontology_terms/'):
            key = key.split('/', 1)[1]
        if not key:
            return None
        return key.replace(':', '_')

    def preload(self, term_keys):
        """Bulk-query which of ``term_keys`` exist in the database.

        Safe to call multiple times; newly found keys are merged into the
        cached valid set. Must be called before ``validate()``.
        """
        normalized = {
            key for key in (
                self.normalize_term_key(term_key) for term_key in term_keys
            )
            if key
        }
        if self._valid_term_keys is None:
            self._valid_term_keys = set()

        to_query = normalized - self._valid_term_keys
        if not to_query:
            return self._valid_term_keys

        db = ArangoDB().get_igvf_connection()
        query = f'''
        FOR term IN {self.collection}
          FILTER term._key IN @ids
          RETURN term._key
        '''
        ids = list(to_query)
        for i in range(0, len(ids), self.chunk_size):
            chunk = ids[i:i + self.chunk_size]
            cursor = db.aql.execute(query, bind_vars={'ids': chunk})
            self._valid_term_keys.update(cursor)
        return self._valid_term_keys

    def validate(self, term_key) -> bool:
        """Return True if the term exists in the preloaded valid set."""
        if self._valid_term_keys is None:
            raise RuntimeError(
                'Call preload() with the file\'s ontology term IDs before validate()'
            )
        key = self.normalize_term_key(term_key)
        if key is None or key not in self._valid_term_keys:
            self.invalid_term_keys.add(key if key is not None else term_key)
            return False
        return True

    def ensure(self, *term_keys) -> bool:
        """Preload and validate one or more terms. Return True if all are valid."""
        keys = [key for key in term_keys if key]
        self.preload(keys)
        return all(self.validate(key) for key in keys)

    def log(self):
        if self.invalid_term_keys:
            print(
                f'Invalid ontology term IDs encountered: {len(self.invalid_term_keys)}')
            print(
                f'Invalid ontology term IDs: {sorted(self.invalid_term_keys)}')
        else:
            print('All ontology term IDs are valid.')
