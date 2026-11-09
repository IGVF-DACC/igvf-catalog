# Remove the invalid junction-spanning coding variants from the parsed jsonl files of ESM / MutPred2, so they match the database
# after delete_splice_spanning_coding_variants.py.
#
# Lines are dropped by _key, using the log of delete_splice_spanning_coding_variants.py (actions 'deleted' or 'to delete'),
# so records kept in the database (e.g. variants with edges from other sources) are kept in the jsonl files too.
# A dry run log gives the same keys as --execute.
#
# The collection of each jsonl file is taken from its file name, e.g.
#   variants/variants_ESM_IGVFFI8105TNNO.jsonl
#   coding_variants/coding_variants_ESM_IGVFFI8105TNNO.jsonl
#   variants_coding_variants/variants_coding_variants_ESM_IGVFFI8105TNNO.jsonl
#   coding_variants_phenotypes/coding_variants_phenotypes_ESM_IGVFFI8105TNNO.jsonl
# and the same for mutpred2_IGVFFI6893ZOAA.
#
# Outputs <name>.patched.jsonl in --output-dir, input files are not changed.
# --jsonl-files and --output-dir can be local paths or s3:// uris (streamed, nothing stored locally; the coding_variants files are ~300GB each).
#
# Usage (run from data/):
# python data_loading_support_files/patch_splice_spanning_jsonl.py \
#   --deletion-log delete_splice_spanning_coding_variants.log.tsv \
#   --jsonl-files s3://igvf-catalog-parsed-collections/coding_variants/coding_variants_ESM_IGVFFI8105TNNO.jsonl \
#   --output-dir s3://igvf-catalog-parsed-collections/coding_variants_patched [--aws-profile default]

import argparse
import csv
import json
import os
import re
import time
from collections import Counter

import boto3
import smart_open

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


def read_deleted_keys(deletion_log, collections):
    '''Return {collection: set of _key} for deleted (or to be deleted) records.'''
    keys = {collection: set() for collection in collections}
    with open(deletion_log) as f:
        for row in csv.DictReader(f, delimiter='\t'):
            if row['action'] in DELETE_ACTIONS and row['collection'] in keys:
                keys[row['collection']].add(row['_key'])
    for collection, collection_keys in keys.items():
        print(f'{collection}: {len(collection_keys)} keys to remove', flush=True)
    return keys


def line_key(line):
    # json.dumps of _props puts _key first, read it without parsing the whole line
    start = line.find(KEY_PREFIX)
    if start != -1:
        start += len(KEY_PREFIX)
        return line[start:line.index('"', start)]
    return json.loads(line)['_key']


def open_file(path, mode, s3_client):
    transport_params = {'client': s3_client} if path.startswith(
        's3://') else None
    return smart_open.open(path, mode, transport_params=transport_params)


def patch_file(path, output_path, deleted_keys, stats, s3_client):
    name = os.path.basename(path)
    start_time = time.time()
    with open_file(path, 'r', s3_client) as infile, open_file(output_path, 'w', s3_client) as outfile:
        for line_idx, line in enumerate(infile, 1):
            if not line.strip():
                continue
            if line_key(line) in deleted_keys:
                stats[name + ' lines removed'] += 1
            else:
                outfile.write(line)
                stats[name + ' lines kept'] += 1
            if line_idx % 50000000 == 0:
                print(f'{name}: {line_idx} lines, {stats[name + " lines removed"]} removed, '
                      f'{round(time.time() - start_time)}s', flush=True)
    stats[name + ' seconds'] = round(time.time() - start_time)


def main():
    parser = argparse.ArgumentParser(
        description='Remove records deleted by delete_splice_spanning_coding_variants.py from ESM / MutPred2 jsonl files.')
    parser.add_argument('--deletion-log', required=True,
                        help='log file of delete_splice_spanning_coding_variants.py')
    parser.add_argument('--jsonl-files', nargs='+', required=True,
                        help='parsed jsonl files of variants, coding_variants, variants_coding_variants, coding_variants_phenotypes')
    parser.add_argument('--output-dir', required=True,
                        help='directory (local or s3://bucket/prefix) for <name>.patched.jsonl')
    parser.add_argument('--aws-profile', default=None,
                        help='aws profile for s3:// paths')
    args = parser.parse_args()

    collections = {path: collection_of(path) for path in args.jsonl_files}
    deleted_keys = read_deleted_keys(
        args.deletion_log, set(collections.values()))
    uses_s3 = args.output_dir.startswith(
        's3://') or any(path.startswith('s3://') for path in args.jsonl_files)
    s3_client = boto3.Session(profile_name=args.aws_profile).client(
        's3') if uses_s3 else None
    if not args.output_dir.startswith('s3://'):
        os.makedirs(args.output_dir, exist_ok=True)
    stats = Counter()

    for path, collection in collections.items():
        output_path = args.output_dir.rstrip('/') + '/' + re.sub(
            r'\.jsonl$', '', os.path.basename(path)) + '.patched.jsonl'
        print(f'{path} ({collection}) -> {output_path}', flush=True)
        patch_file(path, output_path,
                   deleted_keys[collection], stats, s3_client)

    for name, count in sorted(stats.items()):
        print(f'{name}: {count}')


if __name__ == '__main__':
    main()
