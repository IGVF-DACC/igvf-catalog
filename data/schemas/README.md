# Shared property definitions

`mixins.json` contains reusable definitions keyed directly by field name.
Schemas import only the fields they use, combining imports in one `properties`
block after base-schema references and before local overrides:

```json
"allOf": [
  { "$ref": "edges.base.json" },
  {
    "properties": {
      "source": { "$ref": "../mixins.json#/source" },
      "files_filesets": { "$ref": "../mixins.json#/files_filesets" },
      "biosample_term": { "$ref": "../mixins.json#/biosample_term" }
    }
  },
  {
    "properties": {
      "source": { "enum": ["GenCC"] }
    }
  }
]
```

The Python and TypeScript loaders resolve JSON Pointer references and merge
property attributes across `allOf` entries in order. Nested `allOf` entries
allow base schemas to compose mixins as well. Fields already inherited from a
base do not need another import unless a local definition is needed.

Mixins hold shared descriptions, types, patterns, collection references, item
types, and examples. Local definitions retain only differences: nullable type
overrides, dataset-specific enums, source URL patterns, and sample or assay
examples. Required fields remain in the consuming schema or its base.
File references use a shared example, with local overrides for fixed accession
enums that exclude it. Organism definitions retain species enums locally.

Sample metadata may come from files_filesets or from source data and ontology
mappings, depending on the adapter. The files_filesets schema imports the shared
treatment definition without importing a file-reference property.

Fields such as `score`, `log2FC`, and `significant` retain adapter-specific
meanings and descriptions.

## Ontology-term base

`nodes/ontology_terms.base.json` extends `node.base.json` with the shared string
properties `uri` and `term_id`, both required. All five ontology-term schemas
inherit this base and keep examples and adapter-specific properties locally.
The base does not add synonyms, classification, or file metadata because those
are not shared by every ontology-term schema.
