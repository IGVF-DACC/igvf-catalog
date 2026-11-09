# Delete the invalid junction-spanning coding variants found by find_splice_spanning_coding_variants.py from the database.
#
# For every bad coding variant in splice_spanning_coding_variants_<accession>.tsv (both files are read, shared ids handled once):
#   1. coding_variants_phenotypes edges <coding_variant_id>_GO_0003674_<accession> for the ESM and MutPred2 accessions
#   2. variants_coding_variants edge from the bad SPDI
#   3. the coding_variants node, only if its source is IGVF and no other edges point to it
# After all coding variants are processed:
#   4. the variants node of each bad SPDI, only if its source is IGVF and no other edges point to it
#
# Matched SNVs (bad_coding_variant_id with matched_snv_keys) need no change, their phenotype edges are already loaded with the same score.
#
# Dry run by default: reads only, logs what would be deleted. Pass --execute to delete.
# Every deleted (or to be deleted) and kept _key is written to --log-file.
# DB connection is read from ../config/development.json, --execute needs a user with write access.
#
# Usage (run from data/):
# python data_loading_support_files/delete_splice_spanning_coding_variants.py \
#   --bad-records splice_spanning_coding_variants_IGVFFI8105TNNO.tsv.gz splice_spanning_coding_variants_IGVFFI6893ZOAA.tsv.gz \
#   --log-file delete_splice_spanning_coding_variants.log.tsv [--execute]

import argparse
import csv
import gzip
import os
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

from adapters.helpers import build_variant_coding_variant_key  # noqa: E402
from db.arango_db import ArangoDB  # noqa: E402
from find_splice_spanning_coding_variants import with_retry  # noqa: E402

PHENOTYPE_TERM = 'GO_0003674'
# ESM-1v, MutPred2
FILE_ACCESSIONS = ['IGVFFI8105TNNO', 'IGVFFI6893ZOAA']
SOURCE = 'IGVF'
BATCH_SIZE = 1000
LOG_HEADER = ['collection', '_key', 'action', 'reason']


class Deleter:
    def __init__(self, db, execute, log_writer, stats):
        self.db = db
        self.execute = execute
        self.log_writer = log_writer
        self.stats = stats
        self.variant_edge_collections = sorted(
            c['name'] for c in db.collections() if c['type'] == 'edge' and c['name'].startswith('variants_'))
        print('edge collections checked for variants: ' +
              ', '.join(self.variant_edge_collections), flush=True)

    def existing(self, collection, keys):
        '''Return {_key: source} for keys found in collection.'''
        cursor = with_retry(self.db.aql.execute, 'FOR d IN DOCUMENT(@collection, @keys) RETURN {_key: d._key, source: d.source}',
                            bind_vars={'collection': collection, 'keys': keys}, batch_size=10000)
        return {d['_key']: d['source'] for d in cursor}

    def remove(self, collection, keys, reason):
        if not keys:
            return
        action = 'deleted' if self.execute else 'to delete'
        for key in keys:
            self.log_writer.writerow([collection, key, action, reason])
        self.stats[f'{collection} {action}'] += len(keys)
        if self.execute:
            with_retry(self.db.aql.execute, 'FOR k IN @keys REMOVE k IN @@collection OPTIONS { ignoreErrors: true }',
                       bind_vars={'keys': keys, '@collection': collection})

    def keep(self, collection, key, reason):
        self.log_writer.writerow([collection, key, 'kept', reason])
        self.stats[f'{collection} kept ({reason})'] += 1

    def delete_coding_variants(self, batch):
        '''batch: list of (coding_variant_id, spdi)'''
        phenotype_keys = ['_'.join([coding_variant_id, PHENOTYPE_TERM, accession])
                          for coding_variant_id, _ in batch for accession in FILE_ACCESSIONS]
        phenotype_found = self.existing(
            'coding_variants_phenotypes', phenotype_keys)
        self.remove('coding_variants_phenotypes',
                    list(phenotype_found), 'edge of bad coding variant')

        variant_edge_keys = [build_variant_coding_variant_key(
            spdi, coding_variant_id) for coding_variant_id, spdi in batch]
        variant_edge_found = self.existing(
            'variants_coding_variants', variant_edge_keys)
        self.remove('variants_coding_variants',
                    list(variant_edge_found), 'edge of bad coding variant')

        coding_variant_ids = [
            coding_variant_id for coding_variant_id, _ in batch]
        found = self.existing('coding_variants', coding_variant_ids)
        self.stats['coding_variants not in database'] += len(
            coding_variant_ids) - len(found)
        # edges planned for deletion above are excluded, so the dry run gives the same result as --execute
        planned = set(phenotype_keys) | set(variant_edge_keys)
        cursor = with_retry(self.db.aql.execute, '''
            FOR id IN @ids
                LET edges = UNION(
                    (FOR e IN coding_variants_phenotypes FILTER e._from == CONCAT('coding_variants/', id) RETURN e._key),
                    (FOR e IN variants_coding_variants FILTER e._to == CONCAT('coding_variants/', id) RETURN e._key)
                )
                RETURN {id, edges}
        ''', bind_vars={'ids': list(found)}, batch_size=10000)
        to_delete = []
        for doc in cursor:
            other_edges = [key for key in doc['edges'] if key not in planned]
            if found[doc['id']] != SOURCE:
                self.keep('coding_variants', doc['id'],
                          f'source {found[doc["id"]]}')
            elif other_edges:
                self.keep('coding_variants', doc['id'],
                          'other edges: ' + ','.join(other_edges[:5]))
            else:
                to_delete.append(doc['id'])
        self.remove('coding_variants', to_delete, 'bad coding variant')

    def delete_variants(self, spdis, bad_coding_variant_ids):
        found = self.existing('variants', spdis)
        self.stats['variants not in database'] += len(spdis) - len(found)
        subqueries = []
        for collection in self.variant_edge_collections:
            # all variants_coding_variants edges are needed to tell edges of bad coding variants apart, one edge is enough elsewhere
            limit = '' if collection == 'variants_coding_variants' else 'LIMIT 1'
            subqueries.append(
                f"(FOR e IN {collection} FILTER e._from == v {limit} RETURN {{collection: '{collection}', _key: e._key, _to: e._to}})")
            if collection == 'variants_variants':
                subqueries.append(
                    f"(FOR e IN {collection} FILTER e._to == v LIMIT 1 RETURN {{collection: '{collection}', _key: e._key, _to: e._to}})")
        cursor = with_retry(self.db.aql.execute, f'''
            FOR id IN @ids
                LET v = CONCAT('variants/', id)
                LET edges = FLATTEN([{', '.join(subqueries)}])
                RETURN {{id, edges}}
        ''', bind_vars={'ids': list(found)}, batch_size=10000)
        to_delete = []
        for doc in cursor:
            other_edges = [e for e in doc['edges'] if not (
                e['collection'] == 'variants_coding_variants' and e['_to'].split('/', 1)[1] in bad_coding_variant_ids)]
            if found[doc['id']] != SOURCE:
                self.keep('variants', doc['id'], f'source {found[doc["id"]]}')
            elif other_edges:
                self.keep('variants', doc['id'], 'other edges: ' + ','.join(
                    f'{e["collection"]}/{e["_key"]}' for e in other_edges[:5]))
            else:
                to_delete.append(doc['id'])
        self.remove('variants', to_delete, 'variant of bad coding variant')


def read_bad_records(bad_records_files, max_rows):
    '''Return {coding_variant_id: spdi} across all files.'''
    bad = {}
    for path in bad_records_files:
        with (gzip.open(path, 'rt') if path.endswith('.gz') else open(path)) as f:
            for row_idx, row in enumerate(csv.DictReader(f, delimiter='\t')):
                if max_rows is not None and row_idx >= max_rows:
                    break
                bad.setdefault(row['bad_coding_variant_id'], row['bad_spdi'])
        print(f'{path}: {len(bad)} unique bad coding variants so far', flush=True)
    return bad


def main():
    parser = argparse.ArgumentParser(
        description='Delete invalid junction-spanning coding variants, their edges and variants from the database. Dry run by default.')
    parser.add_argument('--bad-records', nargs='+', required=True,
                        help='splice_spanning_coding_variants_<accession>.tsv(.gz) files from find_splice_spanning_coding_variants.py')
    parser.add_argument('--log-file', required=True,
                        help='TSV log of every deleted (or to be deleted) and kept _key')
    parser.add_argument('--execute', action='store_true',
                        help='delete records, otherwise only report what would be deleted')
    parser.add_argument('--max-rows', type=int, default=None,
                        help='only read the first N rows of each bad records file, for testing')
    args = parser.parse_args()

    db = ArangoDB().get_igvf_connection()
    stats = Counter()
    start_time = time.time()
    bad = read_bad_records(args.bad_records, args.max_rows)
    print(('EXECUTE: deleting' if args.execute else 'DRY RUN: nothing is deleted,') +
          f' {len(bad)} bad coding variants', flush=True)

    with open(args.log_file, 'w', newline='') as log:
        log_writer = csv.writer(log, delimiter='\t')
        log_writer.writerow(LOG_HEADER)
        deleter = Deleter(db, args.execute, log_writer, stats)

        items = list(bad.items())
        for i in range(0, len(items), BATCH_SIZE):
            deleter.delete_coding_variants(items[i:i + BATCH_SIZE])
            if (i // BATCH_SIZE) % 100 == 0:
                print(
                    f'coding variants: {i + BATCH_SIZE}/{len(items)} processed', flush=True)

        # variants last: bad SPDIs are shared by both files, and their variants_coding_variants edges must be gone first
        spdis = list(dict.fromkeys(bad.values()))
        bad_coding_variant_ids = set(bad)
        for i in range(0, len(spdis), BATCH_SIZE):
            deleter.delete_variants(
                spdis[i:i + BATCH_SIZE], bad_coding_variant_ids)
            if (i // BATCH_SIZE) % 100 == 0:
                print(
                    f'variants: {i + BATCH_SIZE}/{len(spdis)} processed', flush=True)

    stats['seconds'] = round(time.time() - start_time)
    for name, count in sorted(stats.items()):
        print(f'{name}: {count}')


if __name__ == '__main__':
    main()
