# Delete the invalid junction-spanning coding variants found by find_splice_spanning_coding_variants.py from the database.
#
# One collection per run (--collection), for every bad coding variant in splice_spanning_coding_variants_<accession>.tsv
# (both files are read, shared ids handled once):
#   coding_variants_phenotypes: edges <coding_variant_id>_GO_0003674_<accession> for the ESM and MutPred2 accessions
#   variants_coding_variants: edge from the bad SPDI
#   coding_variants: the node, only if its source is IGVF
#   variants: the node of each bad SPDI, only if its source is IGVF and no variants_coding_variants edge links it
#             to a coding variant outside the bad records (the SPDI can be valid for another transcript)
# coding_variants are deleted without checking edges, their ids are unique to the bad aa change.
# Collections can be deleted independently in any order.
# TODO after all collections are deleted: check no edges are left pointing to the deleted coding_variants and variants.
#
# Input tsv (tab-separated, header row first), e.g.:
#   source_file	transcript_id	aa_change	bad_coding_variant_id	bad_spdi	phenotype_edge_key	codon_ref	alt_codon	candidate_snv_hgvsg	matched_snv_keys	matched_snv_sources
#   ESM_1v_IGVFFI8105TNNO_mappings.tsv.gz	ENST00000370460	p.Cys16Ala	AFF2_ENST00000370460_p.Cys16Ala_c.46_48delinsGCA	NC_000023.11:148501142:TGT:GCA	AFF2_ENST00000370460_p.Cys16Ala_c.46_48delinsGCA_GO_0003674_IGVFFI8105TNNO	TGT	GCA
# Only bad_coding_variant_id and bad_spdi are used.
#
# Matched SNVs (bad_coding_variant_id with matched_snv_keys) need no change, their phenotype edges are already loaded with the same score.
#
# Dry run by default: reads only, logs what would be deleted. Pass --execute to delete.
# Every deleted (or to be deleted) and kept _key is written to --log-file.
# DB connection is read from ../config/development.json, --execute needs a user with write access.
#
# Usage (run from data/):
# python data_loading_support_files/fix_enumerate_splice_coding_variants/delete_splice_spanning_coding_variants.py \
#   --bad-records splice_spanning_coding_variants_IGVFFI8105TNNO.tsv.gz splice_spanning_coding_variants_IGVFFI6893ZOAA.tsv.gz \
#   --collection coding_variants_phenotypes \
#   --log-file delete_splice_spanning_coding_variants.coding_variants_phenotypes.log.tsv [--execute]

import argparse
import csv
import gzip
import os
import sys
import time
from collections import Counter

# data/, two levels up from data_loading_support_files/fix_enumerate_splice_coding_variants/
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from adapters.helpers import build_variant_coding_variant_key  # noqa: E402
from db.arango_db import ArangoDB  # noqa: E402
from find_splice_spanning_coding_variants import with_retry  # noqa: E402

PHENOTYPE_TERM = 'GO_0003674'
# ESM-1v, MutPred2
FILE_ACCESSIONS = ['IGVFFI8105TNNO', 'IGVFFI6893ZOAA']
SOURCE = 'IGVF'
BATCH_SIZE = 1000
LOG_HEADER = ['collection', '_key', 'action', 'reason']
COLLECTIONS = ['coding_variants_phenotypes',
               'variants_coding_variants', 'coding_variants', 'variants']


class Deleter:
    def __init__(self, db, execute, log_writer, stats):
        self.db = db
        self.execute = execute
        self.log_writer = log_writer
        self.stats = stats

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

    def delete_edges(self, collection, keys):
        found = self.existing(collection, keys)
        self.stats[f'{collection} not in database'] += len(keys) - len(found)
        self.remove(collection, list(found), 'edge of bad coding variant')

    def delete_phenotype_edges(self, batch):
        '''batch: list of (coding_variant_id, spdi)'''
        self.delete_edges('coding_variants_phenotypes',
                          phenotype_edge_keys(batch))

    def delete_variant_coding_variant_edges(self, batch):
        self.delete_edges('variants_coding_variants',
                          variant_edge_keys(batch))

    def delete_nodes(self, collection, keys, reason, valid_links=None):
        '''valid_links: {key: [ids of valid records linked to it]}, those keys are kept'''
        found = self.existing(collection, keys)
        self.stats[f'{collection} not in database'] += len(keys) - len(found)
        to_delete = []
        for key, source in found.items():
            if source != SOURCE:
                self.keep(collection, key, f'source {source}')
            elif valid_links and valid_links.get(key):
                self.keep(collection, key, 'valid coding variant: ' +
                          ','.join(valid_links[key][:5]))
            else:
                to_delete.append(key)
        self.remove(collection, to_delete, reason)

    def delete_coding_variants(self, batch):
        # no edge check: coding variant ids are unique to the bad aa change, no valid record links to them
        self.delete_nodes('coding_variants', [
                          coding_variant_id for coding_variant_id, _ in batch], 'bad coding variant')

    def delete_variants(self, spdis, bad_coding_variant_ids):
        # only coding variants are linked to these variants, so only variants_coding_variants is checked:
        # a bad SPDI can also be the correct SPDI of a valid coding variant on another transcript, keep those.
        # edges to bad coding variants are ignored whether or not they are deleted yet, so the order does not matter
        cursor = with_retry(self.db.aql.execute, '''
            FOR spdi IN @spdis
                RETURN {spdi, to: (FOR e IN variants_coding_variants
                                     FILTER e._from == CONCAT('variants/', spdi)
                                     RETURN e._to)}
        ''', bind_vars={'spdis': spdis}, batch_size=10000)
        valid_links = {}
        for doc in cursor:
            valid = [to.split('/', 1)[1] for to in doc['to']
                     if to.split('/', 1)[1] not in bad_coding_variant_ids]
            if valid:
                valid_links[doc['spdi']] = valid
        self.delete_nodes('variants', spdis,
                          'variant of bad coding variant', valid_links)


def phenotype_edge_keys(batch):
    return ['_'.join([coding_variant_id, PHENOTYPE_TERM, accession])
            for coding_variant_id, _ in batch for accession in FILE_ACCESSIONS]


def variant_edge_keys(batch):
    return [build_variant_coding_variant_key(spdi, coding_variant_id) for coding_variant_id, spdi in batch]


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
    parser.add_argument('--collection', required=True, choices=COLLECTIONS,
                        help='collection to delete bad records from, collections can be run in any order')
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
    print(('EXECUTE: deleting from' if args.execute else 'DRY RUN: nothing is deleted from') +
          f' {args.collection}, {len(bad)} bad coding variants', flush=True)

    with open(args.log_file, 'w', newline='') as log:
        log_writer = csv.writer(log, delimiter='\t')
        log_writer.writerow(LOG_HEADER)
        deleter = Deleter(db, args.execute, log_writer, stats)

        if args.collection == 'variants':
            # bad SPDIs can be shared by several bad coding variants
            items = list(dict.fromkeys(bad.values()))
            bad_coding_variant_ids = set(bad)

            def delete(batch):
                deleter.delete_variants(batch, bad_coding_variant_ids)
        else:
            items = list(bad.items())
            delete = {
                'coding_variants_phenotypes': deleter.delete_phenotype_edges,
                'variants_coding_variants': deleter.delete_variant_coding_variant_edges,
                'coding_variants': deleter.delete_coding_variants,
            }[args.collection]

        for i in range(0, len(items), BATCH_SIZE):
            delete(items[i:i + BATCH_SIZE])
            if (i // BATCH_SIZE) % 100 == 0:
                print(
                    f'{args.collection}: {min(i + BATCH_SIZE, len(items))}/{len(items)} processed', flush=True)

    stats['seconds'] = round(time.time() - start_time)
    for name, count in sorted(stats.items()):
        print(f'{name}: {count}')


if __name__ == '__main__':
    main()
