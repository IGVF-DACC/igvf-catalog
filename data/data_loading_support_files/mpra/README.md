# MPRA file exceptions

Name each exclusion list `<accession>_exclusion_list.tsv`. The accession must be
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
