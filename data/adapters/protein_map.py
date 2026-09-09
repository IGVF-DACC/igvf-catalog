from db.arango_db import ArangoDB


def get_protein_map_from_arangodb(field='uniprot_ids', organism=None, dbxref_name=None):
    """Return {id: [protein._key, ...]} from the proteins collection.

    ``uniprot_ids`` is an array on each protein. Isoform accessions (e.g.
    ``P62258-1``) are also indexed under the canonical accession (``P62258``)
    so callers can look up either form.

    Use ``dbxref_name`` (e.g. ``'MGI'``) to invert ``protein.dbxrefs`` entries
    with that name instead of a top-level field.
    """
    db = ArangoDB().get_igvf_connection()
    bind_vars = {}
    filter_clause = ''
    if organism:
        filter_clause = 'FILTER protein.organism == @organism'
        bind_vars['organism'] = organism

    if dbxref_name:
        bind_vars['dbxref_name'] = dbxref_name
        value_expr = '''UNIQUE(
            FOR xref IN protein.dbxrefs || []
              FILTER xref.name == @dbxref_name AND xref.id != null
              RETURN xref.id
        )'''
    else:
        value_expr = f'protein.{field}'

    cursor = db.aql.execute(
        f'''
        FOR protein IN proteins
          {filter_clause}
          RETURN {{ key: protein._key, value: {value_expr} }}
        ''',
        bind_vars=bind_vars
    )
    protein_map = {}
    for record in cursor:
        protein_key = record['key']
        field_value = record['value']
        if not field_value:
            continue
        values = field_value if isinstance(
            field_value, list) else [field_value]
        for value in values:
            if not value:
                continue
            _add_protein_map_entry(protein_map, value, protein_key)
            if not dbxref_name and field == 'uniprot_ids' and '-' in value:
                canonical = value.split('-')[0]
                if canonical:
                    _add_protein_map_entry(protein_map, canonical, protein_key)
    return protein_map


def _add_protein_map_entry(protein_map, value, protein_key):
    if value not in protein_map:
        protein_map[value] = [protein_key]
    elif protein_key not in protein_map[value]:
        protein_map[value].append(protein_key)


class ProteinMap:
    """Look up UniProt (or other) IDs against catalog proteins.

    The protein map is loaded from ArangoDB on first ``get()``. Unmatched IDs
    are collected and logged once via ``log()``.
    """

    def __init__(self, field='uniprot_ids', organism=None, dbxref_name=None, overrides=None):
        self.field = field
        self.organism = organism
        self.dbxref_name = dbxref_name
        self.overrides = overrides or {}
        self._protein_map = None
        self.unmatched_ids = set()
        self.unmatched_count = 0

    def _load_protein_map(self):
        if self._protein_map is None:
            self._protein_map = get_protein_map_from_arangodb(
                field=self.field,
                organism=self.organism,
                dbxref_name=self.dbxref_name,
            )
            for uniprot_id, ensps in self.overrides.items():
                if uniprot_id not in self._protein_map:
                    self._protein_map[uniprot_id] = list(ensps)
        return self._protein_map

    def get(self, protein_id):
        """Return mapped protein keys, or None if the ID is missing."""
        if not protein_id:
            return None
        protein_map = self._load_protein_map()
        ensembl_ids = protein_map.get(protein_id)
        if not ensembl_ids and '-' in protein_id:
            ensembl_ids = protein_map.get(protein_id.split('-')[0])
        if not ensembl_ids:
            self.unmatched_ids.add(protein_id)
            self.unmatched_count += 1
            return None
        return ensembl_ids

    def log(self, logger=None):
        if not self.unmatched_ids:
            return
        ids = sorted(self.unmatched_ids)
        message = (
            f'{self.unmatched_count} unmatched protein lookups '
            f'({len(ids)} unique ids): {ids}'
        )
        if logger is not None:
            logger.warning(message)
        else:
            print(message)
