#!/usr/bin/env python3
"""
Timing comparison: ClickHouse API (localhost) vs ArangoDB API (timing test instance).

Each query runs RUNS+1 times — the first is a warmup (discarded). Subsequent
runs capture warm-cache behaviour on both backends.

Usage:
    python3 timing_comparison.py                       # 5 runs, print to stdout
    python3 timing_comparison.py --runs 10             # 10 runs
    python3 timing_comparison.py --endpoint variants   # filter by endpoint group
    python3 timing_comparison.py --output results.md   # save to file
    python3 timing_comparison.py --list                # list all test cases

Endpoint groups: variants, variants_summary, variants_phenotypes,
                 phenotypes_variants, coding_variants_scores, coding_variants_all_scores
"""

import argparse
import statistics
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

try:
    import requests
except ImportError:
    print('pip install requests', file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CH_BASE = 'http://localhost:2023/api'
AR_BASE = 'https://catalog-api-timing-test.demo.igvf.org/api'
DEFAULT_RUNS = 5
DEFAULT_TIMEOUT = 90  # seconds

# ---------------------------------------------------------------------------
# Test cases
# Each case: (group, description, path, params)
#
# Test inputs are chosen to cover:
#   - Different lookup paths (rsid, spdi, hgvs, ca_id, region, variant_id)
#   - Different chromosomes (to exercise different PK ranges)
#   - Genes of different sizes (small: ERAP2/XRCC2; large: BRCA2/TP53)
#   - Different filter combinations (method, fileset, source, verbose)
#   - Pagination (page=0 vs page=1)
#   - Both IGVF and GWAS phenotype associations
# ---------------------------------------------------------------------------


@dataclass
class TestCase:
    group: str
    description: str
    path: str
    params: str
    # Known variants used as inputs (for documentation):
    #   rs429358  → NC_000019.10:44908683:T:C  (APOE ε4, chr19)
    #   rs7412    → NC_000019.10:44908821:C:T  (APOE ε2, chr19)
    #   rs1800562 → NC_000006.12:26092912:G:A  (HFE C282Y, hemochromatosis, chr6)
    #   rs9939609 → NC_000016.10:53786614:T:A  (FTO obesity, chr16)
    #   rs7903146 → NC_000010.11:112998589:C:G (TCF7L2 T2D, chr10; ca_id=CA660043206)
    #   rs1333049 → NC_000009.12:22125503:G:A  (CDKN2A/B CAD risk, chr9)
    #   rs762551  → NC_000015.10:74749575:C:A  (CYP1A2 caffeine, chr15)


TEST_CASES: list[TestCase] = [
    # ------------------------------------------------------------------
    # /variants — tests all five lookup paths + region queries
    # ------------------------------------------------------------------
    TestCase('variants', 'rsid – APOE ε4 (chr19)',
             '/variants', 'rsid=rs429358&limit=1'),
    TestCase('variants', 'rsid – APOE ε2 (chr19, same region)',
             '/variants', 'rsid=rs7412&limit=1'),
    TestCase('variants', 'rsid – HFE C282Y (chr6)',
             '/variants', 'rsid=rs1800562&limit=1'),
    TestCase('variants', 'rsid – FTO obesity (chr16)',
             '/variants', 'rsid=rs9939609&limit=1'),
    TestCase('variants', 'rsid – TCF7L2 T2D (chr10)',
             '/variants', 'rsid=rs7903146&limit=1'),
    TestCase('variants', 'variant_id – direct primary key (APOE ε4)',
             '/variants', 'variant_id=NC_000019.10:44908683:T:C'),
    TestCase('variants', 'spdi – lean projection lookup (APOE ε4)',
             '/variants', 'spdi=NC_000019.10:44908683:T:C'),
    TestCase('variants', 'hgvs – lean projection lookup (APOE ε4)',
             '/variants', 'hgvs=NC_000019.10:g.44908684T>C'),
    TestCase('variants', 'ca_id – lean projection lookup (TCF7L2)',
             '/variants', 'ca_id=CA660043206'),
    TestCase('variants', 'region – 1 kb around APOE (chr19, common variants)',
             '/variants', 'region=chr19:44908100-44909100&limit=25'),
    TestCase('variants', 'region – 5 kb on chr7 (moderate density)',
             '/variants', 'region=chr7:94025000-94030000&limit=25'),
    TestCase('variants', 'region – 10 kb near BRCA1 (chr17, high annotation)',
             '/variants', 'region=chr17:43044000-43054000&limit=25'),

    # ------------------------------------------------------------------
    # /variants/summary
    # ------------------------------------------------------------------
    TestCase('variants_summary', 'summary – variant_id (APOE ε4)',
             '/variants/summary', 'variant_id=NC_000019.10:44908683:T:C'),
    TestCase('variants_summary', 'summary – rsid (APOE ε4)',
             '/variants/summary', 'rsid=rs429358'),
    TestCase('variants_summary', 'summary – spdi',
             '/variants/summary', 'spdi=NC_000019.10:44908683:T:C'),
    TestCase('variants_summary', 'summary – region 1 kb (APOE)',
             '/variants/summary', 'region=chr19:44908100-44909100'),

    # ------------------------------------------------------------------
    # /variants/phenotypes — exercises both GWAS and IGVF (cV2F) paths
    # ------------------------------------------------------------------
    TestCase('variants_phenotypes', 'phenotypes – APOE ε4, all methods',
             '/variants/phenotypes', 'variant_id=NC_000019.10:44908683:T:C&limit=25'),
    TestCase('variants_phenotypes', 'phenotypes – APOE ε4, cV2F only',
             '/variants/phenotypes', 'variant_id=NC_000019.10:44908683:T:C&method=cV2F&limit=25'),
    TestCase('variants_phenotypes', 'phenotypes – APOE ε4, verbose (variant join)',
             '/variants/phenotypes', 'variant_id=NC_000019.10:44908683:T:C&verbose=true&limit=5'),
    TestCase('variants_phenotypes', 'phenotypes – FTO obesity, rsid input (chr16)',
             '/variants/phenotypes', 'rsid=rs9939609&limit=25'),
    TestCase('variants_phenotypes', 'phenotypes – TCF7L2 T2D (chr10)',
             '/variants/phenotypes', 'variant_id=NC_000010.11:112998589:C:G&limit=25'),
    TestCase('variants_phenotypes', 'phenotypes – CAD risk variant (chr9)',
             '/variants/phenotypes', 'variant_id=NC_000009.12:22125503:G:A&limit=25'),
    TestCase('variants_phenotypes', 'phenotypes – region 1 kb (APOE, multi-variant)',
             '/variants/phenotypes', 'region=chr19:44908100-44909100&limit=25'),

    # ------------------------------------------------------------------
    # /phenotypes/variants — tests IGVF, GWAS, name lookup, filters
    # ------------------------------------------------------------------
    TestCase('phenotypes_variants', 'phenotypes→variants – GO:0003674, IGVF only',
             '/phenotypes/variants', 'phenotype_id=GO_0003674&source=IGVF&limit=25'),
    TestCase('phenotypes_variants', 'phenotypes→variants – GO:0003674, combined',
             '/phenotypes/variants', 'phenotype_id=GO_0003674&limit=25'),
    TestCase('phenotypes_variants', 'phenotypes→variants – GO:0003674, verbose',
             '/phenotypes/variants', 'phenotype_id=GO_0003674&source=IGVF&verbose=true&limit=5'),
    TestCase('phenotypes_variants', 'phenotypes→variants – GO:0003674, method=cV2F',
             '/phenotypes/variants', 'phenotype_id=GO_0003674&method=cV2F&limit=25'),
    TestCase('phenotypes_variants', 'phenotypes→variants – GO:0003674, fileset filter',
             '/phenotypes/variants', 'phenotype_id=GO_0003674&files_fileset=IGVFFI0332UGDD&limit=25'),
    TestCase('phenotypes_variants', "phenotypes→variants – name lookup 'molecular_function'",
             '/phenotypes/variants', 'phenotype_name=molecular_function&source=IGVF&limit=25'),
    TestCase('phenotypes_variants', 'phenotypes→variants – EFO:0001360 T2D, OpenTargets',
             '/phenotypes/variants', 'phenotype_id=EFO_0001360&source=OpenTargets&limit=25'),

    # ------------------------------------------------------------------
    # /genes/coding-variants/scores
    # Tests: small gene, large gene, different identifier types, filters
    # ------------------------------------------------------------------
    TestCase('coding_variants_scores', 'coding scores – ERAP2 (small, chr5)',
             '/genes/coding-variants/scores', 'gene_id=ENSG00000164308&limit=25'),
    TestCase('coding_variants_scores', 'coding scores – TP53 (medium, chr17)',
             '/genes/coding-variants/scores', 'gene_id=ENSG00000141510&limit=25'),
    TestCase('coding_variants_scores', 'coding scores – BRCA2 (large, chr13)',
             '/genes/coding-variants/scores', 'gene_id=ENSG00000139618&limit=25'),
    TestCase('coding_variants_scores', 'coding scores – XRCC2 via hgnc_id',
             '/genes/coding-variants/scores', 'hgnc_id=HGNC%3A12829&limit=25'),
    TestCase('coding_variants_scores', 'coding scores – BRCA2 via gene_name',
             '/genes/coding-variants/scores', 'gene_name=BRCA2&limit=25'),
    TestCase('coding_variants_scores', 'coding scores – ERAP2, method=MutPred2',
             '/genes/coding-variants/scores', 'gene_id=ENSG00000164308&method=MutPred2&limit=25'),
    TestCase('coding_variants_scores', 'coding scores – BRCA2, method=ESM-1v',
             '/genes/coding-variants/scores', 'gene_id=ENSG00000139618&method=ESM-1v&limit=25'),
    TestCase('coding_variants_scores', 'coding scores – ERAP2, fileset=ESM-1v file',
             '/genes/coding-variants/scores', 'gene_id=ENSG00000164308&files_fileset=IGVFFI8105TNNO&limit=25'),
    TestCase('coding_variants_scores', 'coding scores – ERAP2, page=1 (pagination)',
             '/genes/coding-variants/scores', 'gene_id=ENSG00000164308&page=1&limit=25'),

    # ------------------------------------------------------------------
    # /genes/coding-variants/all-scores
    # Tests: score-sorted descent, different datasets, gene sizes
    # ------------------------------------------------------------------
    TestCase('coding_variants_all_scores', 'all-scores – ERAP2, ESM-1v, limit=500',
             '/genes/coding-variants/all-scores', 'gene_id=ENSG00000164308&dataset=ESM-1v&limit=500'),
    TestCase('coding_variants_all_scores', 'all-scores – ERAP2, MutPred2, limit=500',
             '/genes/coding-variants/all-scores', 'gene_id=ENSG00000164308&dataset=MutPred2&limit=500'),
    TestCase('coding_variants_all_scores', 'all-scores – TP53, MutPred2, limit=500',
             '/genes/coding-variants/all-scores', 'gene_id=ENSG00000141510&dataset=MutPred2&limit=500'),
    TestCase('coding_variants_all_scores', 'all-scores – BRCA2, MutPred2, limit=500',
             '/genes/coding-variants/all-scores', 'gene_id=ENSG00000139618&dataset=MutPred2&limit=500'),
    TestCase('coding_variants_all_scores', 'all-scores – BRCA2, ESM-1v, limit=500',
             '/genes/coding-variants/all-scores', 'gene_id=ENSG00000139618&dataset=ESM-1v&limit=500'),
]

# ---------------------------------------------------------------------------
# Timing helpers
# ---------------------------------------------------------------------------


def time_request(url: str, n_warmup: int = 1, n_runs: int = DEFAULT_RUNS,
                 timeout: int = DEFAULT_TIMEOUT) -> dict:
    """Run a GET request n_warmup+n_runs times; return stats over the last n_runs."""
    times_ms: list[float] = []
    status: Optional[int] = None
    error: Optional[str] = None

    for i in range(n_warmup + n_runs):
        try:
            t0 = time.perf_counter()
            r = requests.get(url, timeout=timeout)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            status = r.status_code
            if i >= n_warmup:
                times_ms.append(elapsed_ms)
        except Exception as e:
            error = str(e)
            if i >= n_warmup:
                times_ms.append(float('nan'))

    valid = [t for t in times_ms if t == t]  # filter NaN
    if not valid:
        return {'error': error, 'status': status, 'n': 0}

    return {
        'status': status,
        'n': len(valid),
        'min': min(valid),
        'mean': statistics.mean(valid),
        'median': statistics.median(valid),
        'max': max(valid),
        'stdev': statistics.stdev(valid) if len(valid) > 1 else 0.0,
        'runs': valid,
    }


def fmt_ms(v: Optional[float]) -> str:
    if v is None or v != v:  # None or NaN
        return 'ERR'
    if v >= 10_000:
        return f'{v/1000:.1f}s'
    if v >= 1_000:
        return f'{v/1000:.2f}s'
    return f'{v:.0f}ms'


def fmt_ratio(ch_med: Optional[float], ar_med: Optional[float]) -> str:
    if not ch_med or not ar_med:
        return 'N/A'
    r = ch_med / ar_med
    if r < 1:
        return f'**{r:.2f}x** ✓'   # CH faster
    return f'{r:.2f}x'


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_comparison(
    cases: list[TestCase],
    n_runs: int = DEFAULT_RUNS,
    output_file: Optional[str] = None,
) -> None:
    lines: list[str] = []
    sep = '-' * 60

    header = [
        '# API Timing Comparison: ClickHouse vs ArangoDB\n',
        f'- **ClickHouse (CH)**: `{CH_BASE}`',
        f'- **ArangoDB  (AR)**: `{AR_BASE}`',
        f'- **Runs per query**: {n_runs} timed (+ 1 warmup)\n',
        'Ratio < 1.00 means ClickHouse is faster (marked **bold ✓**).\n',
    ]
    lines.extend(header)
    print('\n'.join(header))

    groups: dict[str, list[TestCase]] = {}
    for tc in cases:
        groups.setdefault(tc.group, []).append(tc)

    for group, group_cases in groups.items():
        section = f"\n## {group.replace('_', '/')}\n"
        table_header = (
            '| Query | CH min | CH med | CH max | AR min | AR med | AR max | CH/AR |\n'
            '|---|---|---|---|---|---|---|---|'
        )
        lines.append(section + table_header)
        print(sep)
        print(f'  {group}')
        print(sep)

        for tc in group_cases:
            url_ch = f'{CH_BASE}{tc.path}?{tc.params}'
            url_ar = f'{AR_BASE}{tc.path}?{tc.params}'

            print(f'  {tc.description}', end=' ', flush=True)

            ch = time_request(url_ch, n_runs=n_runs)
            ar = time_request(url_ar, n_runs=n_runs)

            ch_med = ch.get('median')
            ar_med = ar.get('median')

            ch_ok = f"[{ch.get('status', 'ERR')}]"
            ar_ok = f"[{ar.get('status', 'ERR')}]"

            row = (
                f'| {tc.description} '
                f"| {fmt_ms(ch.get('min'))} "
                f'| {fmt_ms(ch_med)} '
                f"| {fmt_ms(ch.get('max'))} "
                f"| {fmt_ms(ar.get('min'))} "
                f'| {fmt_ms(ar_med)} '
                f"| {fmt_ms(ar.get('max'))} "
                f'| {fmt_ratio(ch_med, ar_med)} |'
            )
            lines.append(row)
            print(f'→ CH {fmt_ms(ch_med)} {ch_ok}  AR {fmt_ms(ar_med)} {ar_ok}')

    result = '\n'.join(lines)
    if output_file:
        with open(output_file, 'w') as f:
            f.write(result + '\n')
        print(f'\nResults saved to {output_file}')
    else:
        print('\n' + result)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

ALL_GROUPS = sorted({tc.group for tc in TEST_CASES})

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--runs', type=int, default=DEFAULT_RUNS,
                        help=f'Timed runs per query (default {DEFAULT_RUNS})')
    parser.add_argument('--endpoint', choices=ALL_GROUPS,
                        help='Run only one endpoint group')
    parser.add_argument('--output', type=str,
                        help='Write markdown results to this file')
    parser.add_argument('--list', action='store_true',
                        help='List all test cases and exit')
    args = parser.parse_args()

    if args.list:
        for tc in TEST_CASES:
            print(f'[{tc.group}] {tc.description}')
            print(f'  CH: {CH_BASE}{tc.path}?{tc.params}')
            print(f'  AR: {AR_BASE}{tc.path}?{tc.params}')
        sys.exit(0)

    cases = [
        tc for tc in TEST_CASES if args.endpoint is None or tc.group == args.endpoint]
    total = len(cases) * (args.runs + 1) * 2
    print(
        f'Running {len(cases)} queries × {args.runs} runs × 2 backends = {total} requests')
    print(f'  CH: {CH_BASE}')
    print(f'  AR: {AR_BASE}\n')

    run_comparison(cases, n_runs=args.runs, output_file=args.output)
