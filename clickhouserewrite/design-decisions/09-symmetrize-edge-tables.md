# Symmetrize edge tables when the access pattern is bidirectional

For edge tables where the relationship is semantically symmetric (LD pairs, gene-gene similarity, protein-protein interactions, etc.), the natural lookup pattern is "find all neighbours of node V". In a single-row-per-edge layout, this becomes:

```sql
WHERE from_id = V OR to_id = V
```

ClickHouse has no good indexing for this OR-on-two-columns shape: a `MergeTree` PK only sorts by one tuple, and projections are heavyweight at scale. With `variants_variants` (~6B unique LD pairs), the OR query is a full-table scan.

## The fix: store each edge twice at import time

Each edge `(A, B, …)` is stored as **two rows**: `(variants_1_id=A, variants_2_id=B, …)` and `(variants_1_id=B, variants_2_id=A, …)`, with the per-direction fields (`variant_1_rsid` / `variant_2_rsid`, etc.) and `name` / `inverse_name` swapped on the reverse row.

Result: the lookup becomes a single-column equality:

```sql
WHERE variants_1_id = V
```

…which hits the PK directly when the table is `ORDER BY (variants_1_id, ancestry, variants_2_id)`.

## Trade-offs

| Aspect | Cost / benefit |
|---|---|
| Row count | ~2× the un-symmetrized form |
| On-disk footprint | ~1.4× after `LowCardinality` + Float32 wins on the duplicated rows. Most large-cardinality strings (RSIDs, IDs) compress well, and the LowCardinality columns dedupe identical values across the two directions essentially for free. |
| Router code | Trivial — no projection juggling, no UNION ALL, no two-step lookup, single-query pagination. |
| Import code | Tiny change — one extra `INSERT ... SELECT _to AS variants_1_id, _from AS variants_2_id, …` per source file. |
| Query latency | Sub-100ms warm for point lookups regardless of input variant. Pagination is a continued range scan (page=1 ≈ page=100). |

## When to apply this pattern

The decision tree for any new edge table:

1. **Is the relationship semantically symmetric?** If yes, candidate.
2. **Is the table large enough that full scans hurt?** Below ~100M rows, you can usually get away with a projection on the second column. Above that, symmetrize.
3. **Does the schema have direction-specific fields** (e.g. `name` vs `inverse_name`, source-specific stats)? If yes, ensure the import swaps them correctly on the reverse row.

For `variants_variants` (~6B → 12B rows), all three boxes ticked.

## When NOT to apply

- The relationship is genuinely asymmetric (e.g. variant→gene, where the gene lookup means something different from the variant lookup). One direction is enough.
- The table fits comfortably in a projection. For tables under ~100M rows, `ADD PROJECTION proj_by_other_id (… ORDER BY other_id)` is simpler.
- You can't change the import script.

## See also

- [`routers/variants_variants.md`](../routers/variants_variants.md) — the router that benefits from this layout.
- [`collections.md`](../collections.md) — table inventory (note the `~12B` count vs the un-symmetrized `~6B`).
