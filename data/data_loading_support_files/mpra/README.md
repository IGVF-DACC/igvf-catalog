# MPRA file exceptions

Name each exception list `<accession>_exception_list.tsv`. The accession must be
an exact effect-file or sequence-design accession. Replacements do not inherit
an older file's exceptions. Lists are optional; malformed lists fail parsing.

Use tab-separated columns `kind`, `identifier`, `reason`:

```tsv
kind	identifier	reason
variant_without_reference_element	NC_000009.12:133278859:T:C	Reference tile is supplied only in GRCh37
```

- `element`: exact BED element name. When attached to a design accession, also
  removes the exact matching design row. Both element nodes and activity edges
  respect the list. Put each alias on a separate row.
- `variant`: exact identifier from BED column 4. Applies to variant nodes,
  variant activity edges, and variant-derived element generation. Other retained
  variants can still contribute a shared element node.
- `variant_without_reference_element`: exact BED variant identifier permitted to
  lack a reference design tile. Retains the variant node and activity effect,
  emitting `genomic_element: null` when no mapping exists. A valid mapping, when
  available, is still used. No placeholder element node is created. The effect's
  BED strand is retained; null-link keys include strand and variant position.
  Variant normalization and database node checks still apply. An identifier
  cannot also have a `variant` exclusion.
- `variant_deduplicate`: retain one identical effect per variant–element–biosample
  key for this listed variant. Any differing emitted value still fails.
- `variant_deduplicate_first_bed_score`: deduplicate this listed variant's effects,
  retaining the first BED score when every other emitted value agrees. Other
  conflicts still fail. This retains the effect; it is not a full exclusion.
- `reason`: required explanation suitable for following up with submitters.

Prefer an effect accession when the problem is confined to that effect file.
Use a design accession only when every analysis using that design is affected.
Do not add broad filters or infer an assembly, strand, or reference sequence
from element names. Unlisted missing reference tiles fail activity-edge parsing;
review them before adding an exclusion. Reference sequence validation continues
to reject invalid variants through the shared variant loader.

The retired `IGVFFI1436TRIH` exclusion list has been removed. The active 80K
design `IGVFFI1228ETWH` and its four replacement effects need **no exclusion
list**. Historical audit results describe the retired inputs at review time;
they do not imply ongoing support for replaying retired files.

The adapter also contains explicit accession allowlists for SatMut coordinate
containment, the `IGVFFI7237HYCA` GRCh38.p13 assembly spelling, and reviewed
identical duplicate reference effects in IGVF-reformatted ENCODE files.
Duplicates with conflicting emitted metrics always fail, even in reviewed files.

See [the review](../../../docs/qa/mpra-2026-10-28.md) for evidence and remaining blockers.

## UNC Library duplicate rules

- IGVFFI4828YSPS (Library1.1) and IGVFFI4797FSIV (Library1.3): individual
  variants are explicitly listed as `variant_deduplicate` or
  `variant_deduplicate_first_bed_score`. There is no file-wide deduplication rule for
  these two files. The lists contain 10 and 16 variants, respectively, with one
  first-BED-score exception in each.
- IGVFFI6587LCPK (Library1.4): exclude the 76 explicitly listed conflicting
  variants, then collapse exact duplicate effects. Replacement design IGVFFI1144FUYP
  resolves the twelve formerly missing references; their null-link permissions were removed.

Unexpected measurement conflicts still fail. Rules are accession-specific and
persist across parsing chunks; replacements do not inherit them.

## CD MPRA corrections

The adapter's `CD_EFFECT_DESIGNS` explicitly pairs IGVFFI2909LNFX and
IGVFFI4623ATHV with IGVFFI5857RBRC. No other file uses these corrections.
Variant identifiers resolve through a unique design SPDI at the exact tile and
strand, with checks on the original identifier, ref/alt alleles, and the known
one-base position discrepancy. The reported position is replaced with the design
position. Named element effects resolve by exact tile, strand, and allele suffix.
Unknown or ambiguous mappings fail. IGVFFI4623ATHV's `element` exception for `NA`
excludes 948 ambiguous rows before name correction.

## Reformatted ENCODE variant duplicates

IGVFFI7911XJRB, IGVFFI2880GNLL, IGVFFI2064FJPL, and IGVFFI5864KSZH each have an
explicit `variant_deduplicate` entry for `NC_000018.10:45198868:T:` (a deletion;
the trailing colon is intentional). The repeated emitted edge is identical in
all fields. One copy is retained per edge key; other element associations for
the same variant remain distinct. Conflicting values still fail.

For the reviewed two-design pair IGVFFI5128MGTU / IGVFFI3757JVGI, the adapter
explicitly assigns shared reference tiles to IGVFFI3757JVGI after confirming equal
fully-reference sequence sets. Other overlapping pairs fail. IGVFFI9022VCNU is
also explicitly listed for identical element-effect deduplication; conflicting
scores fail. These are file-level rules in `MPRAAdapter`, not per-variant exceptions.

Identical reference-element activity edges are deduplicated only for accessions
in `ELEMENT_EFFECT_DEDUPLICATION_FILES`. Conflicting output properties and
duplicates in unlisted files still raise an error.

MPRA element nodes preserve a single `name` and expose sorted, unique `aliases`
including that name and every eligible reference-design name for the same tile.
Shared tiles collect aliases from both designs without changing ownership or IDs.
UNC Library1.1–1.4 designs (IGVFFI4997GUQE, IGVFFI0358RUFK, IGVFFI8319ZOLO, IGVFFI1144FUYP)
also contribute semicolon-separated names from `info`; their hash remains `name`.
Library1.4 uses replacement design IGVFFI1144FUYP, which supersedes IGVFFI7706JKWK.
ALT-only construct names are not reference aliases.
