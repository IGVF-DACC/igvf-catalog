# Update hgvsp of Met1 coding variants in arangodb from p.Met1? to the actual aa change, e.g. p.Met1Ala,
# same as dbNSFP after DSERV-1507. _key is unchanged (Met1!).
#
# Input: met1_coding_variants_hgvsp_patch.jsonl from write_met1_hgvsp_patch.py, one {"_key", "hgvsp"} per line.
# Only existing coding_variants with a different hgvsp are updated, missing keys are skipped (never created).
#
# Dry run by default: reads only, logs what would be updated. Pass --execute to update.
# Every updated (or to be updated) _key is written to --log-file with the old and new hgvsp.
# DB connection is read from ../config/development.json, --execute needs a user with write access.
#
# Usage (run from data/):
# python data_loading_support_files/fix_enumerate_splice_coding_variants/update_met1_hgvsp.py \
#   --patch-file met1_coding_variants_hgvsp_patch.jsonl \
#   --log-file update_met1_hgvsp.log.tsv [--execute]

import argparse
import csv
import json
import os
import sys
import time
from collections import Counter

# data/, two levels up from data_loading_support_files/fix_enumerate_splice_coding_variants/
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from db.arango_db import ArangoDB  # noqa: E402
from find_splice_spanning_coding_variants import with_retry  # noqa: E402

COLLECTION = 'coding_variants'
BATCH_SIZE = 1000
LOG_HEADER = ['collection', '_key', 'source',
              'old_hgvsp', 'new_hgvsp', 'action']


def update_batch(db, docs, execute, log_writer, stats):
    cursor = with_retry(db.aql.execute, '''
        FOR d IN DOCUMENT(@@collection, @keys)
            RETURN {_key: d._key, source: d.source, hgvsp: d.hgvsp}
    ''', bind_vars={'@collection': COLLECTION, 'keys': [d['_key'] for d in docs]}, batch_size=10000)
    found = {d['_key']: d for d in cursor}
    stats['not in database'] += len(docs) - len(found)

    to_update = []
    for doc in docs:
        current = found.get(doc['_key'])
        if current is None:
            continue
        if current['hgvsp'] == doc['hgvsp']:
            stats['already up to date'] += 1
            continue
        to_update.append(doc)
        stats[f'old hgvsp {current["hgvsp"]}, source {current["source"]}'] += 1
        log_writer.writerow([COLLECTION, doc['_key'], current['source'], current['hgvsp'], doc['hgvsp'],
                             'updated' if execute else 'to update'])

    stats['updated' if execute else 'to update'] += len(to_update)
    if execute and to_update:
        with_retry(db.aql.execute, '''
            FOR d IN @docs
                UPDATE {_key: d._key} WITH {hgvsp: d.hgvsp} IN @@collection OPTIONS { ignoreErrors: true }
        ''', bind_vars={'docs': to_update, '@collection': COLLECTION})


def main():
    parser = argparse.ArgumentParser(
        description='Update hgvsp of Met1 coding variants to the actual aa change in arangodb. Dry run by default.')
    parser.add_argument('--patch-file', required=True,
                        help='met1_coding_variants_hgvsp_patch.jsonl from write_met1_hgvsp_patch.py')
    parser.add_argument('--log-file', required=True,
                        help='TSV log of every updated (or to be updated) _key')
    parser.add_argument('--execute', action='store_true',
                        help='update records, otherwise only report what would be updated')
    parser.add_argument('--max-rows', type=int, default=None,
                        help='only read the first N lines of the patch file, for testing')
    args = parser.parse_args()

    with open(args.patch_file) as f:
        docs = [json.loads(line) for line_idx, line in enumerate(f)
                if args.max_rows is None or line_idx < args.max_rows]

    db = ArangoDB().get_igvf_connection()
    stats = Counter()
    start_time = time.time()
    print(('EXECUTE: updating' if args.execute else 'DRY RUN: nothing is updated,') +
          f' {len(docs)} Met1 coding variants', flush=True)

    with open(args.log_file, 'w', newline='') as log:
        log_writer = csv.writer(log, delimiter='\t')
        log_writer.writerow(LOG_HEADER)
        for i in range(0, len(docs), BATCH_SIZE):
            update_batch(db, docs[i:i + BATCH_SIZE],
                         args.execute, log_writer, stats)
            if (i // BATCH_SIZE) % 100 == 0:
                print(
                    f'{COLLECTION}: {min(i + BATCH_SIZE, len(docs))}/{len(docs)} processed', flush=True)

    stats['seconds'] = round(time.time() - start_time)
    for name, count in sorted(stats.items()):
        print(f'{name}: {count}')


if __name__ == '__main__':
    main()
