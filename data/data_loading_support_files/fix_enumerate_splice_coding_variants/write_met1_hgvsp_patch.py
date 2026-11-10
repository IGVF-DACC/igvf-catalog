# Write a jsonl patch to set hgvsp of Met1 coding variants from p.Met1? to the actual aa change, e.g. p.Met1Ala,
# same as dbNSFP after DSERV-1507. _key is unchanged (Met1!).
#
# Input: met1_coding_variants_<accession>.tsv from list_met1_coding_variants.py, aa_change is p.Met1Ala (ESM) or M1A (MutPred2).
# Output: one partial document per unique coding variant, e.g.
#   {"_key": "TMEM127_ENST00000258439_p.Met1!_c.1_3delinsTTC", "hgvsp": "p.Met1Phe"}
#
# Usage (run from data/):
# python data_loading_support_files/fix_enumerate_splice_coding_variants/write_met1_hgvsp_patch.py \
#   --met1-files met1_coding_variants_IGVFFI8105TNNO.tsv met1_coding_variants_IGVFFI6893ZOAA.tsv \
#   --output met1_coding_variants_hgvsp_patch.jsonl

import argparse
import csv
import json
import os
import sys

# data/, two levels up from data_loading_support_files/fix_enumerate_splice_coding_variants/
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from adapters.helpers import convert_aa_to_three_letter  # noqa: E402


def to_hgvsp(aa_change):
    if aa_change.startswith('p.'):
        return aa_change
    return 'p.' + convert_aa_to_three_letter(aa_change)


def main():
    parser = argparse.ArgumentParser(
        description='Write a jsonl patch setting hgvsp of Met1 coding variants to the actual aa change.')
    parser.add_argument('--met1-files', nargs='+', required=True,
                        help='met1_coding_variants_<accession>.tsv files from list_met1_coding_variants.py')
    parser.add_argument('--output', required=True, help='output jsonl')
    args = parser.parse_args()

    hgvsps = {}
    conflicts = 0
    for path in args.met1_files:
        rows = 0
        with open(path) as f:
            for row in csv.DictReader(f, delimiter='\t'):
                rows += 1
                coding_variant_id = row['coding_variant_id']
                hgvsp = to_hgvsp(row['aa_change'])
                if hgvsps.setdefault(coding_variant_id, hgvsp) != hgvsp:
                    conflicts += 1
                    print(
                        f'conflict: {coding_variant_id} {hgvsps[coding_variant_id]} vs {hgvsp}', flush=True)
        print(
            f'{path}: {rows} rows, {len(hgvsps)} unique coding variants so far', flush=True)

    with open(args.output, 'w') as out:
        for coding_variant_id, hgvsp in hgvsps.items():
            out.write(json.dumps(
                {'_key': coding_variant_id, 'hgvsp': hgvsp}) + '\n')
    print(f'{len(hgvsps)} records written to {args.output}, {conflicts} conflicts')


if __name__ == '__main__':
    main()
