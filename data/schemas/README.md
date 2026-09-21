# Shared property definitions

`mixins.json` keeps reusable property groups in one file, following the named
property groups in igvfd's mixins.json. The `file_metadata` group contains
`files_filesets`, `biological_context`, `biosample_term`, and
`treatments_term_ids`.

Schemas using all four fields can import the group in their flat `allOf` array,
after base references and before local property definitions:

```json
{ "properties": { "$ref": "../mixins.json#/file_metadata" } }
```

Schemas using a subset should import only those fields to avoid adding properties:

```json
{
  "properties": {
    "files_filesets": { "$ref": "../mixins.json#/file_metadata/files_filesets" },
    "biological_context": { "$ref": "../mixins.json#/file_metadata/biological_context" }
  }
}
```

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
mappings. Some schemas have only a file reference, and files_filesets itself
uses the treatment description without a self-reference.

Common fields such as `score`, `log2FC`, and `significant` retain adapter-specific
meanings and descriptions.

Additional shared description groups are:

- `provenance`: `source`, `source_url`.
- `classification`: `method`, `label`, `class`.
- `assay_metadata`: `crispr_modality`.

These groups share descriptions only; existing types, enums, examples, and
required fields stay in their schemas. Import individual properties with the
same JSON Pointer syntax as `file_metadata`.

All schemas use the general data-class description and describe CRISPR modality
as the purpose or intended effect of the modification applied to the samples.

The `organism` group shares the string type and description for `organism`.
Schemas import `../mixins.json#/organism/organism` and retain their species
enums and required-field declarations locally.

## Ontology-term base

`nodes/ontology_terms.base.json` extends `node.base.json` with the shared string
properties `uri` and `term_id`, both required. All five ontology-term schemas
inherit this base and keep examples and adapter-specific properties locally.
The base does not add synonyms, classification, or file metadata because those
are not shared by every ontology-term schema.
