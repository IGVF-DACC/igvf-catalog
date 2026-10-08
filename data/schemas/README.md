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

Give every public property a human-readable `title` in Title Case, including
nested properties. Internal fields whose names start with `_` must not have a
title. Use the same title for the same field name across all schemas.
Expand terse abbreviations (for example, `chr` becomes `Chromosome`) while
preserving scientific acronyms and names such as HGVS and AlphaMissense.
Define shared titles in bases or mixins and inherit them rather than repeating
them in local overrides.

Use `enum_descriptions` for coded or otherwise non-obvious values, following
IGVFD's format: an object mapping each value to its explanation. Put the mapping
beside `enum` (inside `items` for array item enums). JSON object keys are strings,
so use `"null"` or `"0"` to document null or numeric values. Keep field descriptions
focused on the field's meaning; explain individual values in `enum_descriptions`.
Self-explanatory names, URLs, and accessions do not need redundant explanations.

Keep shared value explanations in mixins. A consuming schema can narrow its enum
while inheriting the shared mapping; only entries for its allowed values apply.
For existing coded fields without an enum constraint, the mapping documents known
values without restricting validation. The loaders preserve this metadata.

Interaction terminology comes from the bundled
`data/data_loading_support_files/Biogrid_gene_gene/psi-mi.obo`. Biotype and evidence
code explanations follow [GENCODE](https://www.gencodegenes.org/pages/biotypes.html)
and [Gene Ontology](https://geneontology.org/docs/guide-go-evidence-codes/);
gene–disease classifications follow [GenCC](https://thegencc.org/faq).

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

## Threshold and significance documentation

Use an optional field-level `threshold` string for selection, significance, or
score-based classification rules on edge fields. Use `"threshold": "unknown"`
when such a rule is identified but its cutoff still needs investigation. Omit
the property when no cutoff applies or there is no evidence that the field is
thresholded. Do not use "none" or "not applicable". Node schemas, including
their fields, do not track `threshold`.

Keep the field's meaning in `description`; put the cutoff in `threshold` beside
it. When a significance call uses multiple fields, document which source formats
use each field, their precedence, strict/inclusive boundaries, and missing-value
behavior on the decision field. Do not add schema-level `threshold` annotations
or annotate unrelated fields merely to say they are not used in that decision.
Omit `threshold` on alternate representations and supporting fields when the
cutoff is applied to another field; document it on the tested field and the
resulting decision field instead.

A missing adapter filter does not establish that a dataset is unthresholded.
Predictive files may already be selected upstream. Investigate source-file
headers, portal metadata, format specifications, and the versioned generating
workflow before recording a cutoff. Distinguish upstream file selection,
catalog preparation/load filters, and significance calls that retain all rows.
A score range or observed sample minimum alone does not establish a threshold.
The supplied method-score review is a set of research leads, not authoritative
threshold documentation.

Record supporting sources, file accessions, model versions, the scope of data
checks, and unresolved questions in [threshold-evidence.md](threshold-evidence.md).
Omission of `threshold` must not be interpreted as proof that no upstream filter
exists. Keep detailed investigation notes in that evidence document; use the
concise `"unknown"` marker on fields with unresolved rules.

`threshold` is documentation metadata, not a stored document field, JSON Schema
validation constraint, or executable adapter setting. Do not add a data property
named `threshold` to `properties`, `required`, or `accessible_via.return`.
Annotations remain separate from adapter constants and do not change loading
behavior. Consult the source-specific schema; a merged collection schema cannot
represent all adapters' cutoffs as one shared rule.

## Base schemas

- `nodes/node.base.json` provides common node identity and provenance fields.
- `nodes/genomic_elements.base.json` provides genomic-element fields, including
  `method`; consumers need not import that mixin again.
- `nodes/ontology_terms.base.json` extends `node.base.json` with required string
  fields `uri` and `term_id`. All five ontology-term schemas inherit it. Synonyms,
  classification, file metadata, and adapter-specific examples remain local.
- `edges/edges.base.json` provides the required string `_key`, endpoints,
  directional names, provenance, and classification fields. Keep adapter-specific
  key descriptions and examples locally. Node `name` means an entity display name; edge `name`
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

Keep mixin `$ref`s and local overrides on the same property object when both
apply, for example `"source": { "$ref": "../mixins.json#/source", "enum": ["GenCC"] }`.
Both loaders preserve sibling keywords beside `$ref` (siblings override the
resolved mixin). Split the same property across separate `allOf` entries only
when you intentionally rely on sequential merge without an inline `$ref`.
All schema files declare JSON Schema draft 2020-12
(`https://json-schema.org/draft/2020-12/schema`).

When changing composition, compare resolved schemas through both loaders and
run the focused loader tests. Shared constraint changes also need affected
adapter tests: fixtures must use valid ontology/file handles and string
treatment identifiers. Changes to descriptions and examples should be reviewed
separately from changes to validation constraints.
