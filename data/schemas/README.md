# Schema composition

Schemas share definitions through base schemas and `mixins.json`. Mixins are
keyed directly by field name; there are no higher-level groups.

## Importing shared fields

Put base references first, followed by one `properties` block for mixin imports,
then local definitions and overrides. Import only fields the schema uses and
that its bases do not already provide. This abbreviated example illustrates
the structure:

```json
{
  "allOf": [
    { "$ref": "edges.base.json" },
    {
      "properties": {
        "files_filesets": { "$ref": "../mixins.json#/files_filesets" },
        "biosample_term": { "$ref": "../mixins.json#/biosample_term" }
      }
    },
    {
      "properties": {
        "source": { "enum": ["GenCC"], "example": "GenCC" },
        "biosample_term": { "type": ["string", "null"] }
      },
      "required": ["files_filesets"]
    }
  ]
}
```

`source` is inherited from `edges.base.json`; only its local enum and example
are specified. Do not repeat inherited descriptions, types, patterns, examples,
collection references, or mixin imports. Remove empty property definitions and
empty import blocks after removing duplicates.

## Shared definitions and local overrides

The eleven mixins cover `files_filesets`, `biological_context`, `biosample_term`,
`treatments_term_ids`, `source`, `source_url`, `method`, `label`, `class`,
`crispr_modality`, and `organism`.

Keep every consistent attribute in the mixin. For example, file references
share a string type, the `^files_filesets/` pattern, collection metadata, and an
example. Biosample handles share the `^ontology_terms/` pattern; treatment
identifiers are nullable arrays of strings.

Keep only schema-specific differences locally: nullable type overrides,
species or dataset enums, source-specific URL patterns, and specialized
examples. Use inherited examples where possible; override them when a local
enum or constraint excludes the shared example. Required-field declarations
belong in the consuming schema or its base, not in field mixins.

Sample metadata may come from files_filesets or from source data and ontology
mappings, depending on the adapter. The files_filesets schema imports the shared
treatment definition without importing a file-reference property.

Fields such as `score`, `log2FC`, and `significant` retain adapter-specific
meanings and descriptions. Reconciliation of `pmid` and `pmids` is separate work.

## Base schemas

- `nodes/node.base.json` provides common node identity and provenance fields.
- `nodes/genomic_elements.base.json` provides genomic-element fields, including
  `method`; consumers need not import that mixin again.
- `nodes/ontology_terms.base.json` extends `node.base.json` with required string
  fields `uri` and `term_id`. All five ontology-term schemas inherit it. Synonyms,
  classification, file metadata, and adapter-specific examples remain local.
- `edges/edges.base.json` provides endpoints, directional names, provenance, and
  classification fields. Node `name` means an entity display name; edge `name`
  and `inverse_name` describe the relationship directions.

Not every edge currently inherits the edge base. Its required fields include
`class`, `method`, `label`, and `source_url`, which some existing edges do not
require or emit. Check compatibility before adding inheritance; nullable local
types and specialized endpoint constraints must be preserved.

## Loader behavior and validation

The Python loader (`registry.py`) and TypeScript loader
(`src/routers/datatypeRouters/schema.ts`) resolve JSON Pointer references and
recursively flatten nested `allOf` entries. Property attributes merge in order:
later definitions replace matching attribute keys, while `required` lists are
combined and deduplicated. This is application-specific composition, not standard
JSON Schema `allOf` intersection semantics.

Keep references and local overrides in separate entries. The current resolvers
do not preserve sibling keywords beside `$ref`. All schema files declare
JSON Schema draft 2020-12 (`https://json-schema.org/draft/2020-12/schema`).
Supporting `$ref` siblings is separate work.

When changing composition, compare resolved schemas through both loaders and
run the focused loader tests. Shared constraint changes also need affected
adapter tests: fixtures must use valid ontology/file handles and string
treatment identifiers. Changes to descriptions and examples should be reviewed
separately from changes to validation constraints.
