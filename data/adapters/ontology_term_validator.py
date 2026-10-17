import json
import urllib.error
import urllib.request
from urllib.parse import quote

from db.arango_db import ArangoDB


class OntologyTermValidator:
    """Validate ontology term IDs against the ontology_terms collection.

    Prefer bulk checking the unique terms from a datafile via ``preload()``,
    then calling ``validate()`` or ``resolve()`` per row. This avoids loading
    the full ontology_terms collection into memory.

    Pass ``resolve_via_ols=True`` to ``preload()`` to remap obsolete terms
    (absent from the DB) to their current successors via OLS.

    OLS current-term lookup (``resolve_via_ols``) supports:

    - OBO Foundry-style IRIs (``http://purl.obolibrary.org/obo/{TERM_KEY}``),
      including MONDO, GO, HP, UBERON, DOID, CL, CLO, CHEBI, NCIT, OBA, OBI,
      PCL, VARIO, BAO, and other OLS ontologies that use that IRI pattern
    - EFO (``http://www.ebi.ac.uk/efo/{TERM_KEY}``, OLS id ``efo``)
    - ORPHANET / Orphanet (``http://www.orpha.net/ORDO/{TERM_KEY}``,
      OLS id ``ordo``)

    Not supported for OLS remap: Oncotree, ENCODE custom terms, and any
    ontology without a matching OLS id / IRI pattern above.
    """

    OLS_API_BASE = 'https://www.ebi.ac.uk/ols4/api/ontologies/{ontology}/terms'
    OLS_OBO_IRI = 'http://purl.obolibrary.org/obo/{term_key}'
    # Prefix (case-insensitive) -> (OLS ontology id, IRI template).
    # Default for unlisted prefixes: OLS id = lowercase prefix, OBO IRI.
    OLS_PREFIX_CONFIG = {
        'EFO': ('efo', 'http://www.ebi.ac.uk/efo/{term_key}'),
        'ORPHANET': ('ordo', 'http://www.orpha.net/ORDO/{term_key}'),
    }
    OLS_TIMEOUT_SECONDS = 30

    def __init__(self, collection='ontology_terms', chunk_size=500):
        if collection != 'ontology_terms':
            raise ValueError(
                f'Unsupported ontology term collection: {collection}')
        self.collection = collection
        self.chunk_size = chunk_size
        self._valid_term_keys = None
        self._remaps = {}
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

    @classmethod
    def _ols_ontology_and_iri(cls, term_key):
        """Return (OLS ontology id, term IRI) for ``term_key``, or (None, None)."""
        if '_' not in term_key:
            return None, None
        prefix = term_key.split('_', 1)[0]
        config = cls.OLS_PREFIX_CONFIG.get(prefix.upper())
        if config is not None:
            ontology_id, iri_template = config
            return ontology_id, iri_template.format(term_key=term_key)
        return prefix.lower(), cls.OLS_OBO_IRI.format(term_key=term_key)

    @staticmethod
    def _iri_to_term_key(iri):
        if not iri:
            return None
        return str(iri).rstrip('/').split('/')[-1].replace(':', '_')

    def _query_existing_keys(self, term_keys):
        """Return the subset of ``term_keys`` present in the database."""
        found = set()
        if not term_keys:
            return found
        db = ArangoDB().get_igvf_connection()
        query = f'''
        FOR term IN {self.collection}
          FILTER term._key IN @ids
          RETURN term._key
        '''
        ids = list(term_keys)
        for i in range(0, len(ids), self.chunk_size):
            chunk = ids[i:i + self.chunk_size]
            cursor = db.aql.execute(query, bind_vars={'ids': chunk})
            found.update(cursor)
        return found

    def preload(self, term_keys, resolve_via_ols=False):
        """Bulk-query which of ``term_keys`` exist in the database.

        Safe to call multiple times; newly found keys are merged into the
        cached valid set. Must be called before ``validate()`` or ``resolve()``.

        If ``resolve_via_ols`` is True, terms missing from the DB are looked up
        in OLS and remapped when there is a single ``replaced_by`` successor
        that exists in the DB. Updates both ``_valid_term_keys`` and ``_remaps``.
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
        if to_query:
            self._valid_term_keys.update(self._query_existing_keys(to_query))

        if resolve_via_ols:
            self._resolve_missing_via_ols(normalized)

        return self._valid_term_keys

    def _resolve_missing_via_ols(self, normalized_keys):
        """Remap DB-missing keys via OLS replaced_by into ``_remaps``."""
        missing = sorted(
            key for key in normalized_keys
            if key not in self._valid_term_keys and key not in self._remaps
        )
        if not missing:
            return

        candidates = {}
        for key in missing:
            resolved = self._follow_replaced_by_chain(key)
            if resolved and resolved != key:
                candidates[key] = resolved

        if not candidates:
            return

        # Load successors from DB only; do not recurse into OLS.
        self.preload(set(candidates.values()), resolve_via_ols=False)
        for old_key, new_key in candidates.items():
            if new_key in self._valid_term_keys:
                self._remaps[old_key] = new_key

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

    def _fetch_ols_term(self, term_key):
        ontology_id, iri = self._ols_ontology_and_iri(term_key)
        if not ontology_id or not iri:
            return None
        url = (
            f'{self.OLS_API_BASE.format(ontology=ontology_id)}'
            f'?iri={quote(iri, safe="")}'
        )
        try:
            with urllib.request.urlopen(url, timeout=self.OLS_TIMEOUT_SECONDS) as resp:
                data = json.load(resp)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, ValueError):
            return None
        terms = data.get('_embedded', {}).get('terms', [])
        if not terms:
            return None
        return terms[0]

    def _single_replaced_by(self, ols_term):
        """Return the replacement term key, or None if absent/ambiguous.

        Prefers OLS top-level ``term_replaced_by`` (string: bare key or IRI),
        then falls back to ``annotation['term replaced by']`` when it has
        exactly one IRI.
        """
        top_level = ols_term.get('term_replaced_by')
        if top_level:
            # V1Term.term_replaced_by is a string (bare key or IRI).
            # Schema: https://www.ebi.ac.uk/ols4/v3/api-docs
            return self._iri_to_term_key(top_level)

        annotation = ols_term.get('annotation') or {}
        replaced = annotation.get('term replaced by') or []
        if len(replaced) != 1:
            return None
        return self._iri_to_term_key(replaced[0])

    def _follow_replaced_by_chain(self, term_key, seen=None):
        """Recursively follow OLS replaced_by until a non-obsolete term.

        Returns the final candidate key, or None if no unambiguous remap
        (including cycles).
        """
        if seen is None:
            seen = set()
        if term_key in seen:
            return None
        seen.add(term_key)

        ols_term = self._fetch_ols_term(term_key)
        if ols_term is None:
            return None
        if not ols_term.get('is_obsolete'):
            return term_key

        replacement = self._single_replaced_by(ols_term)
        if replacement is None:
            return None
        return self._follow_replaced_by_chain(replacement, seen)

    def resolve(self, term_key):
        """Return the current DB term key (identity or remapped), or None."""
        if self._valid_term_keys is None:
            raise RuntimeError(
                'Call preload() before resolve()'
            )
        key = self.normalize_term_key(term_key)
        if key is None:
            self.invalid_term_keys.add(term_key)
            return None
        if key in self._valid_term_keys:
            return key
        remapped = self._remaps.get(key)
        if remapped is not None and remapped in self._valid_term_keys:
            return remapped
        self.invalid_term_keys.add(key)
        return None

    def log(self):
        if self.invalid_term_keys:
            print(
                f'Invalid ontology term IDs encountered: {len(self.invalid_term_keys)}')
            print(
                f'Invalid ontology term IDs: {sorted(self.invalid_term_keys)}')
        elif not self._remaps:
            print('All ontology term IDs are valid.')
        if self._remaps:
            print(
                f'Ontology term IDs remapped via OLS: {len(self._remaps)}')
            for old_key, new_key in sorted(self._remaps.items()):
                print(f'  {old_key} -> {new_key}')
