# API Timing Comparison: ClickHouse vs ArangoDB

- **ClickHouse (CH)**: `http://localhost:2023/api`
- **ArangoDB  (AR)**: `https://api.catalogkg.igvf.org/api`
- **Runs per query**: 5 timed (+ 1 warmup)

Ratio < 1.00 means ClickHouse is faster (marked **bold ✓**).


## variants
| Query | CH min | CH med | CH max | AR min | AR med | AR max | CH/AR |
|---|---|---|---|---|---|---|---|
| rsid – APOE ε4 (chr19) | 94ms | 99ms | 100ms | 32ms | 35ms | 40ms | 2.81x |
| rsid – APOE ε2 (chr19, same region) | 93ms | 97ms | 98ms | 36ms | 38ms | 44ms | 2.51x |
| rsid – HFE C282Y (chr6) | 94ms | 96ms | 100ms | 35ms | 37ms | 44ms | 2.61x |
| rsid – FTO obesity (chr16) | 119ms | 124ms | 131ms | 35ms | 39ms | 45ms | 3.20x |
| rsid – TCF7L2 T2D (chr10) | 116ms | 119ms | 132ms | 32ms | 33ms | 38ms | 3.56x |
| variant_id – direct primary key (APOE ε4) | 86ms | 95ms | 111ms | 39ms | 39ms | 46ms | 2.41x |
| spdi – lean projection lookup (APOE ε4) | 121ms | 121ms | 130ms | 37ms | 41ms | 48ms | 2.97x |
| hgvs – lean projection lookup (APOE ε4) | 127ms | 127ms | 129ms | 35ms | 36ms | 39ms | 3.50x |
| ca_id – lean projection lookup (TCF7L2) | 122ms | 127ms | 139ms | 30ms | 36ms | 50ms | 3.53x |
| region – 1 kb around APOE (chr19, common variants) | 170ms | 176ms | 183ms | 39ms | 43ms | 44ms | 4.14x |
| region – 5 kb on chr7 (moderate density) | 397ms | 426ms | 492ms | 36ms | 39ms | 49ms | 11.07x |
| region – 10 kb near BRCA1 (chr17, high annotation) | 210ms | 224ms | 259ms | 37ms | 40ms | 48ms | 5.65x |

## variants/summary
| Query | CH min | CH med | CH max | AR min | AR med | AR max | CH/AR |
|---|---|---|---|---|---|---|---|
| summary – variant_id (APOE ε4) | 86ms | 92ms | 101ms | 34ms | 36ms | 47ms | 2.54x |
| summary – rsid (APOE ε4) | 119ms | 120ms | 124ms | 39ms | 42ms | 44ms | 2.85x |
| summary – spdi | 127ms | 129ms | 132ms | 39ms | 40ms | 45ms | 3.27x |
| summary – region 1 kb (APOE) | 113ms | 125ms | 130ms | 35ms | 39ms | 55ms | 3.24x |

## variants/phenotypes
| Query | CH min | CH med | CH max | AR min | AR med | AR max | CH/AR |
|---|---|---|---|---|---|---|---|
| phenotypes – APOE ε4, all methods | 130ms | 132ms | 135ms | 37ms | 39ms | 44ms | 3.41x |
| phenotypes – APOE ε4, cV2F only | 106ms | 109ms | 112ms | 35ms | 36ms | 42ms | 2.99x |
| phenotypes – APOE ε4, verbose (variant join) | 151ms | 154ms | 158ms | 34ms | 40ms | 44ms | 3.85x |
| phenotypes – FTO obesity, rsid input (chr16) | 138ms | 139ms | 146ms | 39ms | 40ms | 42ms | 3.47x |
| phenotypes – TCF7L2 T2D (chr10) | 62ms | 63ms | 66ms | 35ms | 39ms | 48ms | 1.62x |
| phenotypes – CAD risk variant (chr9) | 65ms | 66ms | 67ms | 32ms | 36ms | 41ms | 1.84x |
| phenotypes – region 1 kb (APOE, multi-variant) | 79ms | 88ms | 131ms | 38ms | 39ms | 45ms | 2.23x |

## phenotypes/variants
| Query | CH min | CH med | CH max | AR min | AR med | AR max | CH/AR |
|---|---|---|---|---|---|---|---|
| phenotypes→variants – GO:0003674, IGVF only | 135ms | 136ms | 141ms | 39ms | 43ms | 80ms | 3.19x |
| phenotypes→variants – GO:0003674, combined | 75ms | 79ms | 80ms | 37ms | 40ms | 51ms | 1.99x |
| phenotypes→variants – GO:0003674, verbose | 166ms | 170ms | 175ms | 40ms | 41ms | 52ms | 4.19x |
| phenotypes→variants – GO:0003674, method=cV2F | 76ms | 80ms | 83ms | 39ms | 46ms | 47ms | 1.76x |
| phenotypes→variants – GO:0003674, fileset filter | 77ms | 80ms | 88ms | 35ms | 42ms | 45ms | 1.92x |
| phenotypes→variants – name lookup 'molecular_function' | 166ms | 166ms | 172ms | 40ms | 44ms | 56ms | 3.75x |
| phenotypes→variants – EFO:0001360 T2D, OpenTargets | 94ms | 97ms | 102ms | 41ms | 44ms | 49ms | 2.22x |

## coding/variants/scores
| Query | CH min | CH med | CH max | AR min | AR med | AR max | CH/AR |
|---|---|---|---|---|---|---|---|
| coding scores – ERAP2 (small, chr5) | 224ms | 240ms | 798ms | 50ms | 53ms | 62ms | 4.56x |
| coding scores – TP53 (medium, chr17) | 238ms | 239ms | 253ms | 39ms | 41ms | 72ms | 5.80x |
| coding scores – BRCA2 (large, chr13) | 2.16s | 2.18s | 2.28s | 50ms | 54ms | 74ms | 40.46x |
| coding scores – XRCC2 via hgnc_id | 219ms | 221ms | 227ms | 46ms | 52ms | 56ms | 4.28x |
| coding scores – BRCA2 via gene_name | 2.17s | 2.18s | 2.21s | 47ms | 55ms | 75ms | 39.93x |
| coding scores – ERAP2, method=MutPred2 | 2.11s | 2.16s | 2.80s | 38ms | 43ms | 50ms | 49.67x |
| coding scores – BRCA2, method=ESM-1v | 473ms | 491ms | 506ms | 47ms | 48ms | 67ms | 10.16x |
| coding scores – ERAP2, fileset=ESM-1v file | 2.12s | 2.28s | 2.64s | 39ms | 45ms | 51ms | 50.75x |
| coding scores – ERAP2, page=1 (pagination) | 230ms | 246ms | 764ms | 40ms | 42ms | 47ms | 5.84x |

## coding/variants/all/scores
| Query | CH min | CH med | CH max | AR min | AR med | AR max | CH/AR |
|---|---|---|---|---|---|---|---|
| all-scores – ERAP2, ESM-1v, limit=500 | 74ms | 77ms | 81ms | 34ms | 41ms | 47ms | 1.90x |
| all-scores – ERAP2, MutPred2, limit=500 | 77ms | 80ms | 80ms | 39ms | 40ms | 46ms | 2.02x |
| all-scores – TP53, MutPred2, limit=500 | 73ms | 75ms | 78ms | 39ms | 43ms | 47ms | 1.73x |
| all-scores – BRCA2, MutPred2, limit=500 | 72ms | 77ms | 81ms | 34ms | 40ms | 48ms | 1.93x |
| all-scores – BRCA2, ESM-1v, limit=500 | 75ms | 76ms | 82ms | 34ms | 39ms | 68ms | 1.95x |
