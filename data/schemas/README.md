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
`perturbation`, and `organism`.

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

Use a field-level `threshold` string to document rules that select records or
items, assign significance, or classify scores. These annotations belong in
source-specific **edge schemas**, including nested item properties. Do not add
`threshold` to node schemas or at the schema root.

### Which fields to annotate

Document a rule on both the decision field (`significant` or its equivalent)
and each input field directly compared against a cutoff. For example, a rule
based on adjusted p-value belongs on both `significant` and `p_value_adj`.
For directional significance, annotate the decision, adjusted p-value, and
fold-change fields when both p-value and fold-change sign determine the call.

For row selection without a separate decision field, annotate the field used
to select rows. For selection within an array, annotate the array property and
the nested input fields used to select its items. Keep selection rules separate
from significance rules when they serve different purposes.

Do not automatically annotate every related statistic. Alternate representations
and fields used only to calculate a decision statistic do not need `threshold`
unless they are themselves compared against a cutoff or are plausible inputs
to an unresolved rule. For example, an interval-based significance call belongs
on the decision and interval-bound fields, not automatically on the effect
estimate or an accompanying p-value.

Choose the annotation according to the available evidence:

| Evidence | Annotation |
| --- | --- |
| The rule and cutoff are established. | A concise statement of the rule. |
| A thresholding decision is identified, but its cutoff is unresolved; or the field is a plausible input whose role is unresolved. | `"threshold": "unknown"` |
| No applicable rule or plausible role has been identified for the field. | Omit `threshold`. |

Do not use `"none"` or `"not applicable"`. `"unknown"` does not assert that a
candidate input is definitely thresholded. Omission does not establish that
the source data are unfiltered.

### How to write the rule

Keep the field's meaning in `description`; place the rule in `threshold` beside
it. State the exact comparison (`<`, `<=`, `>`, or `>=`), any joint conditions,
and the scope needed to interpret it. Preserve source-format distinctions,
statistic precedence, fallback behavior, and missing/null behavior where they
apply. Do not describe a format-specific choice as a fallback between fields.
Do not invent a missing-value result when the input is required or invalid
values are rejected before the decision.

Repeat the complete rule on contributing fields when necessary to avoid implying
that one condition alone is sufficient. For example, if a call requires both
adjusted p-value < 0.05 and log2FC < 0, retain the AND condition on all three
fields. Keep repeated annotations consistent when the rule changes.

Use wording that distinguishes selection from labeling:

| Purpose | Example `threshold` text |
| --- | --- |
| Select source rows | `Source row retained when gene_dependency >= 0.5.` |
| Select items within a row | `Mechanism retained when its Posterior Probability >= 0.25 and P-value < 0.05.` |
| Assign significance | `True when p_value_adj is available and < 0.05; otherwise false.` |
| Assign a classification | `Binding called when ref_score > 2^SEMpl_baseline for the motif.` |

Use row-retention wording only when the rule determines row inclusion. A
significance or classification rule may label rows without excluding them.
Include file accessions or model versions when needed to limit the rule's scope.
Keep implementation references such as “by the adapter” or “upstream,” source
citations, and investigation history in the evidence notes rather than the
annotation.

### Evidence and scope

Record supporting sources, file accessions, model/workflow versions, the extent
of data inspection, and unresolved questions in
[threshold-evidence.md](threshold-evidence.md). Distinguish source-file selection,
catalog preparation/loading filters, and decisions that only label retained
records. For unresolved inputs, record why the field is a candidate and what
still needs verification.

Check the relevant adapter or preparation code, source-file headers, portal
metadata, format specifications, and versioned generating workflows. An absent
adapter filter does not rule out prior source filtering. A declared cutoff in
a header does not by itself prove that the file was filtered. A score range or
observed sample minimum alone does not establish a threshold or its boundary.
Treat preliminary reviews as research leads, not authoritative evidence.

`threshold` is documentation metadata, not a stored document field, JSON Schema
validation constraint, or executable setting. Add it as a keyword on the field
schema, not as a data property in `properties`, `required`, or
`accessible_via.return`. It does not change loading behavior. Consult the
source-specific schema: a merged collection schema cannot express every
source's cutoff as one shared rule.

## Log10 p-value maxima

Use a numeric `applied_maximum` annotation on negative-log10 p-value fields for
a source-specific reference maximum supported by adapter output rules or
observed source values. Keep it separate from `threshold` and `description`;
omit it when no supported value has been established.

`applied_maximum` is documentation metadata, not JSON Schema's `maximum`
constraint. Values above it remain valid. It does not clip scores, change
adapter output, or guarantee an upper bound on future data. In particular, a
zero-p-value replacement need not be the largest score: positive p-values and
source-provided log scores can exceed it.

In `threshold-evidence.md`, distinguish an adapter replacement value from an
observed maximum or a rounded reference value. Record the inspected file/version,
scan scope, observed maxima, zero replacement, and any rounding. For example,
the standard human IGVF CRISPR fields use a rounded reference value of 324,
and the mouse fields use 250 based on IGVFFI9159XDOS; the shared adapter's
zero-p-value replacement remains 240. These annotations are not significance
thresholds or clipping settings.

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
