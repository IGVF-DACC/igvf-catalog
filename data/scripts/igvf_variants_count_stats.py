#!/usr/bin/env python3
"""
Query multiple variants_* collections in ArangoDB, each with its own
group-by fields (since not all collections share the same schema), time
each query, and write all results to a single CSV.

IMPORTANT -- why this uses async job submission + polling:
Long-running queries submitted as a normal synchronous AQL cursor hold a
single HTTP connection open for the entire query duration. If there's a
reverse proxy/load balancer in front of the ArangoDB coordinator (common
setup), it will typically kill that connection after its own timeout
(e.g. a 504 Gateway Time-out after 60s) -- regardless of what timeout you
configure on the client or on the query itself. This affects arangoexport
too, since it also uses a single held-open synchronous request.

The fix: submit the query as an async server-side job (returns almost
immediately), then poll for completion with short, separate requests.
None of those individual requests need to run anywhere near as long as
the query itself, so they sail through any gateway timeout untouched.

Install dependency:
    pip install python-arango --break-system-packages

Usage:
    python3 igvf_variants_count_stats.py \\
        --host https://db-dev.catalog.igvf.org \\
        --db igvf \\
        --username guest \\
        --password password_here \\
        [--output variants_igvf_counts.csv] \\
        [--request-timeout 120] \\
        [--poll-interval 60]

--request-timeout only needs to cover a single submit/poll/fetch call
(default 120s) -- not the total query runtime, which can safely run for
hours since the actual query execution happens server-side between polls.

Run with -h/--help to see all options.
"""

import argparse
import csv
import sys
import time

from arango import ArangoClient
from arango.exceptions import AQLQueryExecuteError
from arango.http import DefaultHTTPClient


# -----------------------------------------------------------------------
# COLLECTION CONFIG
# -----------------------------------------------------------------------
# Each entry defines:
#   collection : collection name
#   filter_field / filter_value : equality filter (e.g. source == "IGVF")
#   group_fields : dict mapping an OUTPUT column name -> the document field
#                  to group by for that collection. This is what lets
#                  variants_coding_variants (which uses source_url instead
#                  of files_filesets/method) plug into the same script.
#
# All output rows will have the union of output column names across every
# collection's group_fields; columns not produced by a given collection's
# query are left blank in the CSV.
# -----------------------------------------------------------------------

COLLECTIONS = [
    {
        'collection': 'variants_biosamples',
        'filter_field': 'source',
        'filter_value': 'IGVF',
        'group_fields': {'files_filesets': 'files_filesets', 'method': 'method'},
    },
    {
        'collection': 'variants_coding_variants',
        'filter_field': 'source',
        'filter_value': 'IGVF',
        # this collection has no files_filesets/method - uses source_url instead
        'group_fields': {'source_url': 'source_url'},
    },
    {
        'collection': 'variants_genes',
        'filter_field': 'source',
        'filter_value': 'IGVF',
        'group_fields': {'files_filesets': 'files_filesets', 'method': 'method'},
    },
    {
        'collection': 'variants_phenotypes',
        'filter_field': 'source',
        'filter_value': 'IGVF',
        'group_fields': {'files_filesets': 'files_filesets', 'method': 'method'},
    },
    {
        'collection': 'variants_proteins',
        'filter_field': 'source',
        'filter_value': 'IGVF',
        'group_fields': {'files_filesets': 'files_filesets', 'method': 'method'},
    },
]


def build_query(cfg):
    """Build an AQL query string from a collection config."""
    collection = cfg['collection']
    filter_field = cfg['filter_field']
    filter_value = cfg['filter_value']
    group_fields = cfg['group_fields']

    collect_clauses = ', '.join(
        f'{alias} = doc.{doc_field}' for alias, doc_field in group_fields.items()
    )
    return_fields = ', '.join(f'{alias}: {alias}' for alias in group_fields)

    if collection == 'variants_coding_variants':
        query = f"""
      FOR doc IN {collection}
        FILTER doc.{filter_field} == @filter_value
        COLLECT {collect_clauses} WITH COUNT INTO count
        RETURN {{ {return_fields}, count: count }}
      """
    else:
        query = f"""
      FOR doc IN {collection}
        FILTER doc.{filter_field} == @filter_value
        FILTER doc.class == 'observed data'
        COLLECT {collect_clauses} WITH COUNT INTO count
        RETURN {{ {return_fields}, count: count }}
      """
    return query, {'filter_value': filter_value}


def run_all(db, collections, poll_interval=5):
    """Run each collection's query as an async ArangoDB job, polling until
    done via short requests, so a proxy/gateway timeout in front of the
    server can never kill a query mid-flight.
    """
    all_rows = []
    all_group_columns = []
    timings = []  # list of (collection, elapsed_seconds, status)
    for cfg in collections:
        for col in cfg['group_fields']:
            if col not in all_group_columns:
                all_group_columns.append(col)

    # async_db submits jobs that run server-side; we poll for completion
    # with short requests instead of blocking on one long-held HTTP request.
    async_db = db.begin_async_execution(return_result=True)

    for cfg in collections:
        collection = cfg['collection']
        query, bind_vars = build_query(cfg)

        print(f'Querying {collection} ...', flush=True)
        print(f'  Query:\n{query.strip()}')
        print(f'  Bind vars: {bind_vars}', flush=True)

        start = time.perf_counter()
        try:
            job = async_db.aql.execute(query, bind_vars=bind_vars)

            # poll until the server-side job finishes; each status check
            # is a short, separate request -- immune to a gateway timeout
            # that would kill one long-held synchronous request.
            while job.status() != 'done':
                time.sleep(poll_interval)
                elapsed_so_far = time.perf_counter() - start
                print(
                    f'  ... still running ({elapsed_so_far:,.0f}s elapsed)', flush=True)

            results = list(job.result())
            elapsed = time.perf_counter() - start
            print(f'  -> {len(results)} groups in {elapsed:.3f}s')
            timings.append((collection, elapsed, 'OK'))
        except AQLQueryExecuteError as e:
            elapsed = time.perf_counter() - start
            print(f'  !! ERROR after {elapsed:.3f}s: {e}', file=sys.stderr)
            timings.append((collection, elapsed, 'ERROR'))
            all_rows.append(
                {
                    'collection': collection,
                    'error': str(e),
                }
            )
            continue
        except Exception as e:
            # covers connection/timeout errors etc. so one bad collection
            # doesn't kill the whole run
            elapsed = time.perf_counter() - start
            print(
                f'  !! UNEXPECTED ERROR after {elapsed:.3f}s: {e}', file=sys.stderr)
            timings.append((collection, elapsed, 'ERROR'))
            all_rows.append(
                {
                    'collection': collection,
                    'error': str(e),
                }
            )
            continue

        if not results:
            all_rows.append(
                {
                    'collection': collection,
                    'count': 0,
                    'error': '',
                }
            )
            continue

        for row in results:
            flat = {'collection': collection, 'error': ''}
            for col in all_group_columns:
                flat[col] = row.get(col, '')
            flat['count'] = row.get('count', '')
            all_rows.append(flat)

    return all_rows, all_group_columns, timings


def write_csv(rows, group_columns, out_path):
    fieldnames = ['collection'] + group_columns + ['count', 'error']
    with open(out_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, '') for k in fieldnames})
    print(f'\nWrote {len(rows)} rows to {out_path}')


def parse_args():
    parser = argparse.ArgumentParser(
        description='Query variants_* collections in ArangoDB for IGVF counts, '
        'time each query, and write results to CSV.'
    )
    parser.add_argument(
        '--host',
        required=True,
        help='ArangoDB host URL, e.g. http://localhost:8529',
    )
    parser.add_argument(
        '--db',
        dest='db_name',
        required=True,
        help='Database name',
    )
    parser.add_argument(
        '--username',
        required=True,
        help='ArangoDB username',
    )
    parser.add_argument(
        '--password',
        required=True,
        help='ArangoDB password',
    )
    parser.add_argument(
        '--output',
        default='variants_igvf_counts.csv',
        help='Path to output CSV file (default: variants_igvf_counts.csv)',
    )
    parser.add_argument(
        '--request-timeout',
        type=float,
        default=120,
        help='HTTP request timeout in seconds for each call to ArangoDB '
        '(default: 120). This applies to individual requests (job submit, '
        'poll, fetch result) -- not the total query runtime, which can '
        'safely run far longer since queries run as async server-side jobs.',
    )
    parser.add_argument(
        '--poll-interval',
        type=float,
        default=60,
        help='Seconds to wait between polls while a query is still running '
        'server-side (default: 60).',
    )
    return parser.parse_args()


def main():
    args = parse_args()

    http_client = DefaultHTTPClient()
    # set directly rather than via constructor -- older python-arango
    # versions don't accept request_timeout as a constructor argument,
    # but the attribute itself is respected either way.
    http_client.request_timeout = args.request_timeout
    client = ArangoClient(hosts=args.host, http_client=http_client)
    db = client.db(args.db_name, username=args.username,
                   password=args.password)

    rows, group_columns, timings = run_all(
        db, COLLECTIONS, poll_interval=args.poll_interval)

    write_csv(rows, group_columns, args.output)

    print('\nSummary (query time per collection):')
    for collection, elapsed, status in timings:
        print(f'  {collection}: {elapsed:.3f}s [{status}]')


if __name__ == '__main__':
    main()
