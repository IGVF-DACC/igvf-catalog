# API Timing Comparison: ClickHouse vs ArangoDB

- **ClickHouse (CH)**: `http://localhost:2023/api`
- **ArangoDB  (AR)**: `https://catalog-api-timing-test.demo.igvf.org/api`
- **Runs per query**: 5 timed (+ 1 warmup)

Ratio < 1.00 means ClickHouse is faster (marked **bold ✓**).


## variants
| Query | CH min | CH med | CH max | AR min | AR med | AR max | CH/AR |
|---|---|---|---|---|---|---|---|
| rsid – APOE ε4 (chr19) | 96ms | 97ms | 101ms | 118ms | 127ms | 135ms | **0.76x** ✓ |
| rsid – APOE ε2 (chr19, same region) | 92ms | 97ms | 106ms | 115ms | 120ms | 126ms | **0.81x** ✓ |
| rsid – HFE C282Y (chr6) | 95ms | 98ms | 102ms | 122ms | 125ms | 131ms | **0.79x** ✓ |
| rsid – FTO obesity (chr16) | 122ms | 126ms | 140ms | 127ms | 128ms | 140ms | **0.98x** ✓ |
| rsid – TCF7L2 T2D (chr10) | 120ms | 121ms | 134ms | 116ms | 124ms | 127ms | **0.98x** ✓ |
| variant_id – direct primary key (APOE ε4) | 90ms | 98ms | 99ms | 121ms | 124ms | 128ms | **0.79x** ✓ |
| spdi – lean projection lookup (APOE ε4) | 127ms | 127ms | 128ms | 124ms | 126ms | 127ms | 1.01x |
| hgvs – lean projection lookup (APOE ε4) | 123ms | 126ms | 138ms | 119ms | 123ms | 128ms | 1.03x |
| ca_id – lean projection lookup (TCF7L2) | 115ms | 122ms | 126ms | 120ms | 123ms | 126ms | **0.99x** ✓ |
| region – 1 kb around APOE (chr19, common variants) | 151ms | 217ms | 755ms | 142ms | 155ms | 155ms | 1.40x |
| region – 5 kb on chr7 (moderate density) | 196ms | 408ms | 721ms | 158ms | 168ms | 173ms | 2.43x |
| region – 10 kb near BRCA1 (chr17, high annotation) | 279ms | 378ms | 633ms | 285ms | 294ms | 297ms | 1.28x |

## variants/summary
| Query | CH min | CH med | CH max | AR min | AR med | AR max | CH/AR |
|---|---|---|---|---|---|---|---|
| summary – variant_id (APOE ε4) | 91ms | 93ms | 97ms | 136ms | 145ms | 148ms | **0.64x** ✓ |
| summary – rsid (APOE ε4) | 118ms | 120ms | 124ms | 143ms | 147ms | 154ms | **0.81x** ✓ |
| summary – spdi | 123ms | 126ms | 130ms | 142ms | 147ms | 149ms | **0.86x** ✓ |
| summary – region 1 kb (APOE) | 117ms | 124ms | 129ms | 134ms | 150ms | 153ms | **0.83x** ✓ |

## variants/phenotypes
| Query | CH min | CH med | CH max | AR min | AR med | AR max | CH/AR |
|---|---|---|---|---|---|---|---|
| phenotypes – APOE ε4, all methods | 129ms | 133ms | 138ms | 135ms | 136ms | 154ms | **0.98x** ✓ |
| phenotypes – APOE ε4, cV2F only | 104ms | 109ms | 111ms | 124ms | 129ms | 133ms | **0.85x** ✓ |
| phenotypes – APOE ε4, verbose (variant join) | 151ms | 153ms | 157ms | 126ms | 137ms | 140ms | 1.12x |
| phenotypes – FTO obesity, rsid input (chr16) | 138ms | 142ms | 142ms | 138ms | 139ms | 143ms | 1.02x |
| phenotypes – TCF7L2 T2D (chr10) | 62ms | 65ms | 67ms | 128ms | 128ms | 144ms | **0.51x** ✓ |
| phenotypes – CAD risk variant (chr9) | 64ms | 67ms | 69ms | 123ms | 131ms | 133ms | **0.51x** ✓ |
| phenotypes – region 1 kb (APOE, multi-variant) | 79ms | 82ms | 126ms | 229ms | 261ms | 308ms | **0.32x** ✓ |

## phenotypes/variants
| Query | CH min | CH med | CH max | AR min | AR med | AR max | CH/AR |
|---|---|---|---|---|---|---|---|
| phenotypes→variants – GO:0003674, IGVF only | 133ms | 141ms | 144ms | 6.17s | 6.39s | 6.48s | **0.02x** ✓ |
| phenotypes→variants – GO:0003674, combined | 80ms | 81ms | 83ms | 4.22s | 4.24s | 4.29s | **0.02x** ✓ |
| phenotypes→variants – GO:0003674, verbose | 188ms | 190ms | 208ms | 5.67s | 5.72s | 5.91s | **0.03x** ✓ |
| phenotypes→variants – GO:0003674, method=cV2F | 77ms | 80ms | 86ms | 5.67s | 5.75s | 5.79s | **0.01x** ✓ |
| phenotypes→variants – GO:0003674, fileset filter | 78ms | 83ms | 87ms | 4.87s | 4.92s | 4.92s | **0.02x** ✓ |
| phenotypes→variants – name lookup 'molecular_function' | 165ms | 172ms | 173ms | 5.71s | 5.84s | 5.87s | **0.03x** ✓ |
| phenotypes→variants – EFO:0001360 T2D, OpenTargets | 96ms | 97ms | 101ms | 125ms | 131ms | 136ms | **0.74x** ✓ |

## coding/variants/scores
| Query | CH min | CH med | CH max | AR min | AR med | AR max | CH/AR |
|---|---|---|---|---|---|---|---|
| coding scores – ERAP2 (small, chr5) | 766ms | 779ms | 804ms | 325ms | 362ms | 381ms | 2.15x |
| coding scores – TP53 (medium, chr17) | 228ms | 244ms | 271ms | 216ms | 222ms | 254ms | 1.10x |
| coding scores – BRCA2 (large, chr13) | 2.17s | 2.18s | 2.19s | 793ms | 865ms | 1.03s | 2.52x |
| coding scores – XRCC2 via hgnc_id | 227ms | 233ms | 260ms | 193ms | 205ms | 218ms | 1.14x |
| coding scores – BRCA2 via gene_name | 2.17s | 2.18s | 2.21s | 814ms | 864ms | 1.03s | 2.53x |
| coding scores – ERAP2, method=MutPred2 | 2.12s | 2.72s | 2.79s | 344ms | 385ms | 448ms | 7.08x |
| coding scores – BRCA2, method=ESM-1v | 472ms | 487ms | 2.16s | 845ms | 979ms | 1.11s | **0.50x** ✓ |
| coding scores – ERAP2, fileset=ESM-1v file | 2.65s | 2.76s | 4.41s | 15.4s | 18.5s | 19.2s | **0.15x** ✓ |
| coding scores – ERAP2, page=1 (pagination) | 254ms | 735ms | 745ms | 325ms | 357ms | 389ms | 2.06x |

## coding/variants/all/scores
| Query | CH min | CH med | CH max | AR min | AR med | AR max | CH/AR |
|---|---|---|---|---|---|---|---|
| all-scores – ERAP2, ESM-1v, limit=500 | 77ms | 78ms | 81ms | 2.04s | 2.07s | 2.08s | **0.04x** ✓ |
| all-scores – ERAP2, MutPred2, limit=500 | 77ms | 79ms | 81ms | 2.13s | 2.15s | 2.25s | **0.04x** ✓ |
| all-scores – TP53, MutPred2, limit=500 | 70ms | 72ms | 78ms | 2.00s | 2.05s | 2.05s | **0.04x** ✓ |
| all-scores – BRCA2, MutPred2, limit=500 | 76ms | 78ms | 85ms | 13.1s | 13.2s | 13.3s | **0.01x** ✓ |
| all-scores – BRCA2, ESM-1v, limit=500 | 74ms | 75ms | 82ms | 12.2s | 12.3s | 12.3s | **0.01x** ✓ |
