# Remove the invalid junction-spanning coding variants from the parsed jsonl files of ESM / MutPred2 / VAMP-seq, so they match the database
# after delete_splice_spanning_coding_variants.py, and set hgvsp of Met1 coding variants to the actual aa change (update_met1_hgvsp.py).
#
# One jsonl file per run (--jsonl-file) of one collection (--collection), only the log rows of that collection are read.
# Lines are dropped by _key, using the logs of delete_splice_spanning_coding_variants.py (actions 'deleted' or 'to delete'),
# so records kept in the database (e.g. variants with edges from other sources) are kept in the jsonl files too.
# A dry run log gives the same keys as --execute. Logs of other collections can be passed too, their rows are skipped.
#
# --hgvsp-patch (met1_coding_variants_hgvsp_patch.jsonl from write_met1_hgvsp_patch.py) only applies to coding_variants:
# lines with a _key in the patch get its hgvsp, e.g. p.Met1? -> p.Met1Ala, all other fields and their order are unchanged.
#
# The collection of each jsonl file is taken from its file name and must match --collection, e.g.
#   variants_ESM_IGVFFI8105TNNO.jsonl
#   coding_variants_ESM_IGVFFI8105TNNO.jsonl
#   variants_coding_variants_ESM_IGVFFI8105TNNO.jsonl
#   coding_variants_phenotypes_mutpred2_IGVFFI6893ZOAA.jsonl
# and the same for mutpred2_IGVFFI6893ZOAA, and VAMP-seq e.g. coding_variants_vamp_uniq.jsonl.
#
# Local files only (download from s3 first). Writes --output-file, the input file is not changed.
#
# Usage (run from data/):
# python data_loading_support_files/fix_enumerate_splice_coding_variants/patch_splice_spanning_jsonl.py \
#   --collection coding_variants \
#   --deletion-log delete_splice_spanning_coding_variants.coding_variants.log.tsv delete_splice_spanning_coding_variants.VAMP.coding_variants.log.tsv \
#   --hgvsp-patch met1_coding_variants_hgvsp_patch.jsonl \
#   --jsonl-file coding_variants_ESM_IGVFFI8105TNNO.jsonl \
#   --output-file coding_variants_ESM_IGVFFI8105TNNO.patched.jsonl

import argparse
import csv
import json
import os
import time
from collections import Counter

# longest prefix first: variants_coding_variants_ also starts with variants_
COLLECTIONS = ['variants_coding_variants', 'coding_variants_phenotypes',
               'coding_variants', 'variants']
DELETE_ACTIONS = {'deleted', 'to delete'}
KEY_PREFIX = '"_key": "'


def collection_of(path):
    name = os.path.basename(path)
    for collection in COLLECTIONS:
        if name.startswith(collection + '_'):
            return collection
    raise ValueError(f'can not tell the collection of {path}')


def read_deleted_keys(deletion_logs, collection):
    '''Return set of _key for deleted (or to be deleted) records of collection.'''
    keys = set()
    for deletion_log in deletion_logs:
        with open(deletion_log) as f:
            for row in csv.DictReader(f, delimiter='\t'):
                if row['action'] in DELETE_ACTIONS and row['collection'] == collection:
                    keys.add(row['_key'])
        print(
            f'{deletion_log}: {len(keys)} {collection} keys to remove so far', flush=True)
    return keys


def read_hgvsp_patch(hgvsp_patch):
    '''Return {_key: hgvsp}.'''
    patch = {}
    with open(hgvsp_patch) as f:
        for line in f:
            doc = json.loads(line)
            patch[doc['_key']] = doc['hgvsp']
    print(f'{hgvsp_patch}: {len(patch)} keys to update hgvsp', flush=True)
    return patch


def line_key(line):
    # json.dumps of _props puts _key first, read it without parsing the whole line
    start = line.find(KEY_PREFIX)
    if start != -1:
        start += len(KEY_PREFIX)
        return line[start:line.index('"', start)]
    return json.loads(line)['_key']


def patch_file(path, output_path, deleted_keys, hgvsp_patch, stats):
    start_time = time.time()
    with open(path) as infile, open(output_path, 'w') as outfile:
        for line_idx, line in enumerate(infile, 1):
            if not line.strip():
                continue
            key = line_key(line)
            if key in deleted_keys:
                stats['lines removed'] += 1
                continue
            if key in hgvsp_patch:
                doc = json.loads(line)
                if doc.get('hgvsp') != hgvsp_patch[key]:
                    stats[f'hgvsp {doc.get("hgvsp")} updated'] += 1
                    doc['hgvsp'] = hgvsp_patch[key]
                    line = json.dumps(doc) + '\n'
                else:
                    stats['hgvsp already up to date'] += 1
            outfile.write(line)
            stats['lines kept'] += 1
            if line_idx % 50000000 == 0:
                print(f'{line_idx} lines, {stats["lines removed"]} removed, '
                      f'{round(time.time() - start_time)}s', flush=True)
    stats['seconds'] = round(time.time() - start_time)


def main():
    parser = argparse.ArgumentParser(
        description='Remove records deleted by delete_splice_spanning_coding_variants.py from ESM / MutPred2 / VAMP-seq jsonl files, '
        'and update Met1 hgvsp in coding_variants files. One file per run.')
    parser.add_argument('--collection', required=True, choices=COLLECTIONS,
                        help='collection of the jsonl file')
    parser.add_argument('--deletion-log', nargs='+', required=True,
                        help='log files of delete_splice_spanning_coding_variants.py, only rows of --collection are used')
    parser.add_argument('--hgvsp-patch', default=None,
                        help='met1_coding_variants_hgvsp_patch.jsonl, {"_key", "hgvsp"} per line, only for coding_variants')
    parser.add_argument('--jsonl-file', required=True,
                        help='local parsed jsonl file of --collection')
    parser.add_argument('--output-file', required=True,
                        help='local patched jsonl file')
    args = parser.parse_args()

    if collection_of(args.jsonl_file) != args.collection:
        parser.error(
            f'{args.jsonl_file} is a {collection_of(args.jsonl_file)} file, not {args.collection}')
    if os.path.abspath(args.output_file) == os.path.abspath(args.jsonl_file):
        parser.error('--output-file would overwrite --jsonl-file')
    if args.hgvsp_patch and args.collection != 'coding_variants':
        parser.error('--hgvsp-patch only applies to coding_variants')

    deleted_keys = read_deleted_keys(args.deletion_log, args.collection)
    hgvsp_patch = read_hgvsp_patch(
        args.hgvsp_patch) if args.hgvsp_patch else {}
    stats = Counter()
    print(f'{args.jsonl_file} -> {args.output_file}', flush=True)
    patch_file(args.jsonl_file, args.output_file,
               deleted_keys, hgvsp_patch, stats)

    for name, count in sorted(stats.items()):
        print(f'{name}: {count}')


if __name__ == '__main__':
    main()
