# Router architecture notes

One file per ported router with its end-to-end flow, key design choices, and a pointer to the underlying ClickHouse tables.

| Router | File | Endpoints |
|---|---|---|
| [`variants`](variants.md) | `src/routers/datatypeRouters/nodes/variants.ts` | `GET /variants`, `GET /variants/summary` (broken — see [limitations.md](../limitations.md)) |
| [`variants_phenotypes`](variants_phenotypes.md) | `src/routers/datatypeRouters/edges/variants_phenotypes.ts` | `GET /phenotypes/variants`, `GET /variants/phenotypes` |
| [`genes_coding_variants`](genes_coding_variants.md) | `src/routers/datatypeRouters/edges/genes_coding_variants.ts` | `GET /genes/coding-variants/scores`, `GET /genes/coding-variants/all-scores` |

For the full status of every endpoint, see [`endpoints/README.md`](../endpoints/README.md).
