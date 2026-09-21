# Shared property definitions

`mixins.json` keeps reusable property groups in one file, following the named
property groups in igvfd's mixins.json. The `file_metadata` group contains
`files_filesets`, `biological_context`, `biosample_term`, and
`treatments_term_ids`.

Each group is a schema containing `properties`. Import complete groups directly
in `allOf` when all their fields apply. Keep partial imports together in one
`properties` block, and put local overrides after the imports:

```json
"allOf": [
  { "$ref": "../mixins.json#/provenance" },
  { "$ref": "../mixins.json#/classification" },
  {
    "properties": {
      "files_filesets": {
        "$ref": "../mixins.json#/file_metadata/properties/files_filesets"
      }
    }
  },
  {
    "properties": {
      "source": { "enum": ["GenCC"] }
    }
  }
]
```

Import only the fields a schema uses; a whole-group import adds every property
in that group. Base-schema references precede mixin imports.

The Python and TypeScript loaders resolve JSON Pointer references and merge
property attributes across `allOf` entries in order. The group supplies shared
descriptions and default types: strings for file references and sample context,
and nullable arrays for treatment identifiers. Local definitions retain only
differences, such as nullable string types, enums, patterns, examples, and item
constraints. Required fields remain in the consuming schema. A field that needs
no overrides needs only its mixin import. Both loaders also merge nested
`allOf` entries so base schemas can compose mixins.

The group describes related provenance and sample metadata, not a guarantee of
how every adapter obtains it. CRISPR and MPRA adapters copy sample metadata from
files_filesets; ADASTRA and caQTL adapters also use source data or ontology
mappings. Some schemas have only a file reference, and the `files_filesets` schema
imports only `treatments_term_ids` from this group.

Common fields such as `score`, `log2FC`, and `significant` retain adapter-specific
meanings and descriptions.

Additional shared description groups are:

- `provenance`: `source`, `source_url`.
- `classification`: `method`, `label`, `class`.
- `assay_metadata`: `crispr_modality`.

These groups share descriptions and default string types. Nullable type
overrides, dataset-specific enums, examples, and required fields stay local.
Shared handle patterns (`^files_filesets/` and `^ontology_terms/`) belong in
`file_metadata`; source-specific URL patterns remain in consuming schemas. Import individual properties with the
same JSON Pointer syntax as `file_metadata`.

All schemas use the general data-class description and describe CRISPR modality
as the purpose or intended effect of the modification applied to the samples.

The `organism` group shares the string type and description for `organism`.
Schemas import `../mixins.json#/organism` and retain their species
enums and required-field declarations locally.

## Ontology-term base

`nodes/ontology_terms.base.json` extends `node.base.json` with the shared string
properties `uri` and `term_id`, both required. All five ontology-term schemas
inherit this base and keep examples and adapter-specific properties locally.
The base does not add synonyms, classification, or file metadata because those
are not shared by every ontology-term schema.

Shared attributes belong in mixins, including collection references and array
item types. `files_filesets` declares `collections: ["files_filesets"]`, and
`treatments_term_ids` declares string items. File references use a shared example, with local overrides only for fixed
accession enums. Dataset-specific sample, source URL, and assay examples remain
local, as do
enums and other constraints that differ across datasets.
