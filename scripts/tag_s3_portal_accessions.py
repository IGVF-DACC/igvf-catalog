#!/usr/bin/env python3
"""One-off: tag S3 objects with their IGVF portal accession(s).

Extracts the source accession from each object key under a given prefix and
writes it as the `portal_accessions` tag on the object.

Two flavours of source accession are understood:

  * IGVF file accessions (`IGVFFI...`) are used directly.
  * ENCODE file accessions (`ENCFF...`) are resolved to the corresponding
    IGVF accession via the IGVF search API. ENCODE file metadata is mirrored
    on the IGVF portal, cross-referenced through the `dbxrefs` property, so
    we look the file up by `dbxrefs=ENCODE:<ENCFF...>` and read the IGVF
    `accession` off each hit.

The source token sits right before the `.jsonl` suffix or before a trailing
`_<date>` segment. Examples:

    bluestarr_variants_biosamples_IGVFFI0818FMCC.jsonl          -> IGVFFI0818FMCC
    mpra_variants_biosamples_IGVFFI2950PCZI_20260612.jsonl      -> IGVFFI2950PCZI
    encode_crispr_e2g_genomic_elements_ENCFF968BZL_04_30_26.jsonl
                              -> ENCFF968BZL -> (resolved) IGVFFI2331IRGH

When a token resolves to several IGVF accessions the tag value is a
space-separated list (hence the plural tag key `portal_accessions`).

Usage:
    # Dry run (default): print what would be tagged, change nothing.
    python scripts/tag_s3_portal_accessions.py --profile igvf-dev --prefix variants_biosamples/

    # Actually apply the tags.
    python scripts/tag_s3_portal_accessions.py --profile igvf-dev --prefix variants_biosamples/ --apply
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

import boto3

BUCKET = 'igvf-catalog-parsed-collections'
PREFIX = 'variants_biosamples/'
TAG_KEY = 'portal_accessions'

IGVF_SEARCH_URL = 'https://api.data.igvf.org/search/'

# The source token is either a native IGVF file accession or an ENCODE file
# accession. The character class stops naturally at `_`, `.`, etc.
SOURCE_RE = re.compile(r'(?:IGVFFI|ENCFF)[0-9A-Z]+')


def extract_source_token(key: str) -> str | None:
    """Return the single source accession token in a key, or None if absent."""
    matches = SOURCE_RE.findall(key)
    if not matches:
        return None
    unique = sorted(set(matches))
    if len(unique) > 1:
        raise ValueError(
            f'Multiple source accessions found in key {key!r}: {unique}')
    return unique[0]


def resolve_encode_accession(encff: str, timeout: float = 30.0) -> list[str]:
    """Resolve an ENCODE file accession to IGVF accession(s) via the search API."""
    params = urllib.parse.urlencode(
        {'type': 'File', 'dbxrefs': f'ENCODE:{encff}', 'format': 'json'}
    )
    request = urllib.request.Request(
        f'{IGVF_SEARCH_URL}?{params}', headers={'Accept': 'application/json'}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        # The IGVF search API returns 404 (not 200 + empty @graph) when nothing
        # matches. That is a genuine "no IGVF match", not a request failure.
        if exc.code == 404:
            return []
        raise
    accessions = [hit['accession']
                  for hit in payload.get('@graph', []) if hit.get('accession')]
    return sorted(set(accessions))


def resolve_portal_accessions(token: str, cache: dict[str, list[str]]) -> list[str]:
    """Map a source token to the IGVF portal accession(s) it corresponds to."""
    if token.startswith('IGVFFI'):
        return [token]
    if token in cache:
        return cache[token]
    resolved = resolve_encode_accession(token)
    cache[token] = resolved
    return resolved


def merge_tags(existing: list[dict], value: str) -> list[dict]:
    """Return the tag set with portal_accessions set, preserving other tags."""
    tags = [t for t in existing if t['Key'] != TAG_KEY]
    tags.append({'Key': TAG_KEY, 'Value': value})
    return tags


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', default='igvf-dev',
                        help='AWS profile name')
    parser.add_argument('--bucket', default=BUCKET)
    parser.add_argument('--prefix', default=PREFIX)
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Write tags. Without this flag the script is a dry run.',
    )
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile)
    s3 = session.client('s3')

    paginator = s3.get_paginator('list_objects_v2')
    encode_cache: dict[str, list[str]] = {}
    total = tagged = skipped = 0

    for page in paginator.paginate(Bucket=args.bucket, Prefix=args.prefix):
        for obj in page.get('Contents', []):
            key = obj['Key']
            # Skip the "directory" placeholder key if present.
            if key.endswith('/'):
                continue
            total += 1

            token = extract_source_token(key)
            if not token:
                print(f'SKIP  (no accession) {key}', file=sys.stderr)
                skipped += 1
                continue

            try:
                accessions = resolve_portal_accessions(token, encode_cache)
            except Exception as exc:  # network / API failure — don't abort the run
                print(
                    f'SKIP  (resolve failed for {token}: {exc}) {key}', file=sys.stderr)
                skipped += 1
                continue

            if not accessions:
                print(
                    f'SKIP  (no IGVF match for {token}) {key}', file=sys.stderr)
                skipped += 1
                continue

            value = ' '.join(accessions)
            resolved_note = f' [resolved from {token}]' if token.startswith(
                'ENCFF') else ''

            if not args.apply:
                print(f'DRY   {key} -> {TAG_KEY}={value}{resolved_note}')
                continue

            existing = s3.get_object_tagging(
                Bucket=args.bucket, Key=key)['TagSet']
            new_tags = merge_tags(existing, value)
            s3.put_object_tagging(
                Bucket=args.bucket,
                Key=key,
                Tagging={'TagSet': new_tags},
            )
            print(f'TAGGED {key} -> {TAG_KEY}={value}{resolved_note}')
            tagged += 1

    mode = 'applied' if args.apply else 'dry-run'
    print(
        f'\nDone ({mode}). objects={total} tagged={tagged} skipped={skipped}',
        file=sys.stderr,
    )
    return 1 if skipped else 0


if __name__ == '__main__':
    raise SystemExit(main())
