#!/usr/bin/env python3
"""
load_genes_amino_acids.py

Streams one or more `coding_variants_phenotypes` JSONL files from S3 (never
loading a full file into memory — .gz files are decompressed on the fly) and
loads them into an ArangoDB collection called `genes_amino_acids_IGVF`.

Input record shape (one line of JSONL):
{
  "_key": "ACSF3_ENST00000317447_p.Ala17Pro_c.49G-C_BAO_0040014_IGVFFI6224HZMG",
  "class": "observed data",
  "method": "DUAL-IPA",
  "files_filesets": "files_filesets/IGVFFI6224HZMG",
  ...
}

Only records where `class == "observed data"` are processed. From `_key` we
extract:
  - gene name    -> the first underscore-delimited token, e.g. "ACSF3"
  - amino acid   -> the <RefAA><Pos> part of the embedded HGVS-p change,
                    e.g. "p.Ala17Pro" -> "Ala17"

Records are grouped per gene, then per amino acid name within that gene, and
each amino acid accumulates a list of "occurrences" (one per source record):

{
  "_key": "ACSF3",
  "amino_acids": [
    {
      "name": "Ala17",
      "occurrences": [
        {
          "_key": "ACSF3_ENST00000317447_p.Ala17Pro_c.49G-C_BAO_0040014_IGVFFI6224HZMG",
          "method": "DUAL-IPA",
          "files_filesets": "files_filesets/IGVFFI6224HZMG"
        },
        ...
      ]
    },
    ...
  ]
}

Documents/entries for the same gene coming from different lines/files/runs
are merged server-side (via AQL UPSERT) rather than overwritten — existing
amino acid names get their occurrences appended, and new amino acid names
get added to the array. This makes the script safe to re-run / run over
many files.

-------------------------------------------------------------------------
Requirements
-------------------------------------------------------------------------
    pip install smart_open[s3] python-arango boto3

AWS credentials are picked up the normal boto3 way (env vars, ~/.aws/config,
instance profile, etc.) — nothing S3-specific to configure in this script.

-------------------------------------------------------------------------
Example usage
-------------------------------------------------------------------------
    python load_genes_amino_acids.py \\
        s3://my-bucket/igvf/coding_variants_phenotypes-0001.jsonl.gz \\
        --arango-hosts http://localhost:8529 \\
        --arango-db igvf \\
        --arango-user root \\
        --arango-password secret \\
        --batch-size 5000

You can also pass a text file containing one s3:// URI per line:
    python load_genes_amino_acids.py --uri-list s3_files.txt ...

If you don't pass any URIs at all (no positional args, no --uri-list), the
script falls back to the S3_URIS constant defined below — edit that list
directly if you'd rather not pass files on the CLI.
"""

import argparse
import json
import logging
import re
from collections import defaultdict, Counter
from typing import Dict, Iterator, List

from arango import ArangoClient
from smart_open import open as smart_open

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)
log = logging.getLogger('load_genes_amino_acids')

# List of S3 URIs to process. Edit this in place, or override at the command
# line (positional args and/or --uri-list both take precedence over this).
S3_URIS: List[str] = [
    's3://igvf-catalog-parsed-collections/coding_variants_phenotypes/coding_variants_phenotypes_DUAL_IPA_IGVFFI6224HZMG.jsonl',
    's3://igvf-catalog-parsed-collections/coding_variants_phenotypes/coding_variants_phenotypes_ESM_IGVFFI8105TNNO_Met1_patched_20251211.jsonl',
    's3://igvf-catalog-parsed-collections/coding_variants_phenotypes/coding_variants_phenotypes_mutpred2_IGVFFI6893ZOAA_20251209.jsonl',
    's3://igvf-catalog-parsed-collections/coding_variants_phenotypes/coding_variants_phenotypes_SGE_IGVFFI1361XVSO.jsonl',
    's3://igvf-catalog-parsed-collections/coding_variants_phenotypes/coding_variants_phenotypes_SGE_IGVFFI2810SLAX.jsonl',
    's3://igvf-catalog-parsed-collections/coding_variants_phenotypes/coding_variants_phenotypes_SGE_IGVFFI3125FMNW.jsonl',
    's3://igvf-catalog-parsed-collections/coding_variants_phenotypes/coding_variants_phenotypes_SGE_IGVFFI7008EHEH.jsonl',
    's3://igvf-catalog-parsed-collections/coding_variants_phenotypes/coding_variants_phenotypes_SGE_IGVFFI9138TFXQ.jsonl',
    's3://igvf-catalog-parsed-collections/coding_variants_phenotypes/coding_variants_phenotypes_SGE_IGVFFI9974PZRX.jsonl',
    's3://igvf-catalog-parsed-collections/coding_variants_phenotypes/coding_variants_phenotypes_VAMP_IGVFFI0629IIQU.jsonl',
    's3://igvf-catalog-parsed-collections/coding_variants_phenotypes/coding_variants_phenotypes_VAMP_IGVFFI2574RDFO.jsonl',
    's3://igvf-catalog-parsed-collections/coding_variants_phenotypes/coding_variants_phenotypes_VAMP_MultiSTEP_IGVFFI0455SCQH.jsonl',
    's3://igvf-catalog-parsed-collections/coding_variants_phenotypes/coding_variants_phenotypes_VAMP_MultiSTEP_IGVFFI6920DGHF.jsonl',
    's3://igvf-catalog-parsed-collections/coding_variants_phenotypes/coding_variants_phenotypes_VAMP_MultiSTEP_IGVFFI8624EJBZ.jsonl',
    's3://igvf-catalog-parsed-collections/coding_variants_phenotypes/coding_variants_phenotypes_VAMP_MultiSTEP_IGVFFI8987JRZH.jsonl',
    's3://igvf-catalog-parsed-collections/coding_variants_phenotypes/coding_variants_phenotypes_VAMP_MultiSTEP_IGVFFI9355QMWI.jsonl',
    's3://igvf-catalog-parsed-collections/coding_variants_phenotypes/coding_variants_pheontypes_IGVFFI5890AHYL.jsonl'
]

# Only records with this exact "class" value are loaded.
REQUIRED_CLASS = 'observed data'

# Matches the "p.<RefAA><Pos>" portion embedded inside a coding_variants_phenotypes
# _key, e.g. "..._p.Ala17Pro_..." -> captures "Ala17".
_AMINO_ACID_RE = re.compile(r'p\.([A-Za-z]{3}\d+)')


def extract_gene_and_amino_acid(record_key: str):
    """Extract (gene_name, amino_acid) from a coding_variants_phenotypes _key.

    "ACSF3_ENST00000317447_p.Ala17Pro_c.49G-C_BAO_0040014_IGVFFI6224HZMG"
      -> ("ACSF3", "Ala17")

    Returns (None, None) if the key doesn't have the expected shape.
    """
    if not record_key:
        return None, None

    gene_name = record_key.split('_', 1)[0] or None

    match = _AMINO_ACID_RE.search(record_key)
    amino_acid = match.group(1) if match else None

    return gene_name, amino_acid


def iter_s3_jsonl_lines(uri: str) -> Iterator[dict]:
    """Stream a single JSONL file (optionally gzip'd) from S3, line by line.

    smart_open handles the S3 GetObject streaming *and* transparent gzip
    decompression (based on the .gz extension) without ever buffering the
    whole object in memory.
    """
    log.info('Opening %s', uri)
    line_no = 0
    with smart_open(uri, 'r', encoding='utf-8') as f:
        for line in f:
            line_no += 1
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                log.warning('Skipping malformed JSON at %s:%d (%s)',
                            uri, line_no, e)
    log.info('Finished %s (%d lines)', uri, line_no)


def ensure_collection(db, name: str):
    if not db.has_collection(name):
        log.info('Creating collection %s', name)
        db.create_collection(name)
    return db.collection(name)


def batch_to_gene_docs(batch: Dict[str, Dict[str, List[dict]]]) -> List[dict]:
    """Convert the in-memory {gene: {amino_acid_name: [occurrence, ...]}}
    aggregation into the [{_key, amino_acids: [{name, occurrences}]}] shape
    the AQL query expects.
    """
    docs = []
    for gene, aa_map in batch.items():
        docs.append({
            '_key': gene,
            'amino_acids': [
                {'name': aa_name, 'occurrences': occurrences}
                for aa_name, occurrences in aa_map.items()
            ],
        })
    return docs


def flush_batch(db, collection_name: str, batch: Dict[str, Dict[str, List[dict]]]):
    """Merge a batch of gene -> amino_acid -> [occurrences] into ArangoDB.

    For each gene:
      - if the gene doc doesn't exist yet, insert it with this batch's
        amino_acids array as-is.
      - if it exists, merge amino_acids by `name`: amino acid names already
        present get their `occurrences` appended to (deduplicated via
        APPEND(..., true)); new amino acid names get added to the array.
    """
    if not batch:
        return

    genes = batch_to_gene_docs(batch)

    aql = f"""
    FOR g IN @genes
        UPSERT {{ _key: g._key }}
        INSERT {{ _key: g._key, amino_acids: g.amino_acids }}
        UPDATE {{
            amino_acids: (
                LET oldAA = (HAS(OLD, "amino_acids") AND IS_ARRAY(OLD.amino_acids)) ? OLD.amino_acids : []
                LET newAA = g.amino_acids
                LET allNames = UNIQUE(APPEND(
                    (FOR a IN oldAA RETURN a.name),
                    (FOR a IN newAA RETURN a.name)
                ))
                FOR nm IN allNames
                    LET oldOcc = FIRST(FOR a IN oldAA FILTER a.name == nm RETURN a.occurrences)
                    LET newOcc = FIRST(FOR a IN newAA FILTER a.name == nm RETURN a.occurrences)
                    RETURN {{
                        name: nm,
                        occurrences: APPEND(
                            oldOcc != null ? oldOcc : [],
                            newOcc != null ? newOcc : [],
                            true
                        )
                    }}
            )
        }}
        IN {collection_name}
    """
    db.aql.execute(aql, bind_vars={'genes': genes})

    total_aas = sum(len(aa_map) for aa_map in batch.values())
    total_occurrences = sum(
        len(occ) for aa_map in batch.values() for occ in aa_map.values()
    )
    log.info(
        'Flushed batch: %d genes, %d amino-acid names, %d occurrences',
        len(genes), total_aas, total_occurrences,
    )


def run(uris: List[str], db, collection_name: str, batch_size: int):
    ensure_collection(db, collection_name)

    # gene -> amino_acid_name -> [occurrence, ...]
    batch: Dict[str, Dict[str, List[dict]]] = defaultdict(
        lambda: defaultdict(list))
    batch_count = 0
    total_records = 0
    skipped_wrong_class = 0
    skipped_unparsable = 0

    class_value_counts: Counter = Counter()
    sample_unparsable_keys: List[str] = []

    for uri in uris:
        file_loaded = 0
        file_skipped_class = 0
        file_skipped_unparsable = 0

        for record in iter_s3_jsonl_lines(uri):
            class_value_counts[record.get('class')] += 1

            if record.get('class') != REQUIRED_CLASS:
                skipped_wrong_class += 1
                file_skipped_class += 1
                continue

            record_key = record.get('_key')
            gene_name, amino_acid = extract_gene_and_amino_acid(record_key)

            if not gene_name or not amino_acid:
                skipped_unparsable += 1
                file_skipped_unparsable += 1
                if len(sample_unparsable_keys) < 10:
                    sample_unparsable_keys.append(record_key)
                log.debug('Skipping unparsable _key: %r', record_key)
                continue

            occurrence = {
                '_key': record_key,
                'method': record.get('method'),
                'files_filesets': record.get('files_filesets'),
            }

            batch[gene_name][amino_acid].append(occurrence)
            batch_count += 1
            total_records += 1
            file_loaded += 1

            if batch_count >= batch_size:
                flush_batch(db, collection_name, batch)
                batch.clear()
                batch_count = 0

        # Flush at the end of every file, even if batch_size wasn't reached,
        # so progress is visible and durable file-by-file rather than only
        # at the very end of the whole run.
        if batch:
            flush_batch(db, collection_name, batch)
            batch.clear()
            batch_count = 0

        log.info(
            'File done: %s -> loaded %d, skipped %d (wrong class), %d (unparsable _key)',
            uri, file_loaded, file_skipped_class, file_skipped_unparsable,
        )

    log.info(
        'Done. Loaded %d records total. Skipped %d (class != %r), %d (unparsable _key).',
        total_records, skipped_wrong_class, REQUIRED_CLASS, skipped_unparsable,
    )

    if total_records == 0:
        log.warning(
            "Nothing was ingested! Distinct 'class' values seen in the input: %s",
            dict(class_value_counts),
        )
        if sample_unparsable_keys:
            log.warning('Sample _key values that failed gene/amino-acid extraction: %s',
                        sample_unparsable_keys)


def load_uri_list(path: str) -> List[str]:
    with open(path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('s3_uris', nargs='*',
                        help='s3://bucket/key.jsonl(.gz) paths (defaults to the S3_URIS constant if omitted)')
    parser.add_argument(
        '--uri-list', help='Path to a text file with one s3:// URI per line')

    parser.add_argument('--arango-hosts', default='http://localhost:8529')
    parser.add_argument('--arango-db', default='_system')
    parser.add_argument('--arango-user', default='root')
    parser.add_argument('--arango-password', default='')
    parser.add_argument('--collection', default='genes_amino_acids_IGVF')
    parser.add_argument('--batch-size', type=int, default=5000,
                        help='Number of input records to accumulate before writing to ArangoDB')

    args = parser.parse_args()

    uris = list(args.s3_uris)
    if args.uri_list:
        uris.extend(load_uri_list(args.uri_list))

    if not uris:
        uris = list(S3_URIS)

    if not uris:
        parser.error('No S3 URIs provided (pass them positionally, via --uri-list, '
                     'or set the S3_URIS constant in this script)')

    client = ArangoClient(hosts=args.arango_hosts)
    db = client.db(args.arango_db, username=args.arango_user,
                   password=args.arango_password)

    run(uris, db, args.collection, args.batch_size)


if __name__ == '__main__':
    main()
