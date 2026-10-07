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

Every concrete edge schema has a top-level `threshold` string. It
documents that schema's source-specific selection/significance criteria, or
explicitly states that they are unknown or not applicable. Base schemas and
mixins do not supply a default: sharing a collection does not mean that two
adapters use the same thresholds. Node schemas do not track `threshold`,
including on individual fields.

Add a `threshold` string beside `description` on edge fields that participate in a
decision, especially `significant`, classification fields, and predictive
scores. Keep the field's meaning in `description` and the decision rule in
`threshold`. For example:

```json
"significant": {
  "title": "Significant?",
  "type": "boolean",
  "description": "Boolean indicator of the significance of the perturbation effect.",
  "threshold": "Use p_value_adj < 0.05 when available; otherwise p_value < 0.05; otherwise abs(z_score) >= 1.959963984540054. If all three are missing/null, false."
}
```

State which fields apply to each source format, the order of precedence,
strict/inclusive boundaries, and missing-value behavior. Distinguish a load
filter (rows are excluded), a significance/classification call (rows may be
retained regardless of the call), and upstream guidance (not recalculated by
the adapter). A source-supplied boolean does not imply that the adapter applies
its own p-value cutoff. Score bounds, reference anchors, and observed sample
minima are not significance thresholds.

`threshold` is documentation metadata, not a stored document property, a JSON
Schema validation constraint, or an executable adapter setting. Do not add it
to `properties`, `required`, or `accessible_via.return` as a data field. These
annotations are maintained separately from adapter constants; changing them
does not change loading behavior. Read the source-specific schema when
interpreting thresholds; a merged collection schema cannot express all
adapters' rules as one shared cutoff.

The initial audit used the adapter implementations and the supplied method-score
review. Adapter behavior takes precedence when the review describes an older
implementation. In particular, CRISPR variant-phenotype calls use confidence
intervals, CRISPR-Millipede uses posterior inclusion probability, and COXPRESdb
filters the absolute z-score. Unknown upstream cutoffs remain explicitly
undocumented, including source-supplied ENCODE/phenotype CRISPR calls, DUAL-IPA,
Variant Painting, and dataset-specific SGE/VAMP-seq classifications.

Predictive-model context comes from the
[ENCODE-rE2G model documentation](https://github.com/EngreitzLab/ENCODE_rE2G)
and [model directories](https://github.com/EngreitzLab/ENCODE_rE2G/tree/main/models),
and the [scE2G model documentation](https://github.com/EngreitzLab/scE2G)
and [model directories](https://github.com/EngreitzLab/scE2G/tree/main/models).
The review's model-specific cutoffs are recorded as upstream guidance, not
adapter constants. Confirm the model/version and source file before applying
them to a dataset. MutPred2's mechanism filter is also documented in
`data/data_loading_support_files/run_parallel_mapping_mutpred2.py`; it does
not impose a cutoff on the overall pathogenicity score.

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
