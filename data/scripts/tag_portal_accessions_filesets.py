# This script expands the 'portal_accessions' tag of S3 objects in a bucket by adding
# the related file_set accession for each accession already present in the tag.
#
# Workflow (per object in the bucket):
#   1. Read the current value of the 'portal_accessions' tag.
#   2. Split the current value by space to get the individual accessions.
#   3. For each accession, fetch the object from the IGVF portal API
#      (https://api.data.igvf.org/{accession}) and read its 'file_set.accession'
#      (the fileset accession).
#   4. Append the resolved fileset accession(s) to the current value (space separated).
#   5. Write the combined value back into the 'portal_accessions' tag, leaving all other
#      tags unchanged.
#
# Accessions are de-duplicated while preserving order, so re-running the script is safe
# (idempotent) and an accession never appears twice. Accessions that cannot be fetched
# from the portal, or whose object has no 'file_set.accession', are warned about and skipped.
#
# All output is logged to the console, and optionally mirrored to a file via --log-file
# so a record of exactly which objects were (or would be) retagged is retained.
#
# Usage:
#   python scripts/tag_portal_accessions_filesets.py --bucket_name <bucket_name> --profile <aws_profile> --dry-run --log-file run.log
#
# Requirements:
# - boto3
# - Network access to the IGVF portal API (https://api.data.igvf.org)
# - AWS credentials configured in your environment, or an AWS profile passed via --profile
# - Permissions to access the specified S3 bucket and modify object tags

import argparse
import json
import logging
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import boto3

# default values:
BUCKET_NAME = 'igvf-catalog-parsed-collections'
TAG_KEY = 'portal_accessions'

IGVF_API_URL = 'https://api.data.igvf.org'
# Cap the request rate to the IGVF portal so we never overwhelm it.
DEFAULT_MAX_REQUESTS_PER_SECOND = 10

logger = logging.getLogger('tag_portal_accessions_filesets')


class RateLimiter:
    # Simple single-threaded rate limiter enforcing a minimum interval between calls,
    # so the portal is never hit faster than max_rps requests per second.
    def __init__(self, max_rps):
        self.min_interval = 1.0 / max_rps if max_rps and max_rps > 0 else 0.0
        self._last_call = None

    def wait(self):
        if self.min_interval <= 0:
            return
        now = time.monotonic()
        if self._last_call is not None:
            elapsed = now - self._last_call
            remaining = self.min_interval - elapsed
            if remaining > 0:
                time.sleep(remaining)
        self._last_call = time.monotonic()


def setup_logging(log_file=None):
    # Log to stdout, and additionally to a file when --log-file is provided so the run
    # is retained. Uses append mode so repeated runs accumulate in the same file.
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%z')

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_file:
        file_handler = logging.FileHandler(
            log_file, mode='a', encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info(f'Writing logs to {Path(log_file).resolve()}')


def unique_preserve_order(values):
    seen = set()
    ordered = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def get_portal_object(accession, rate_limiter=None, timeout=30.0):
    # Fetch an object from the IGVF portal API by accession, as JSON.
    if rate_limiter is not None:
        rate_limiter.wait()
    params = urllib.parse.urlencode({'format': 'json'})
    request = urllib.request.Request(
        f'{IGVF_API_URL}/{accession}?{params}',
        headers={'Accept': 'application/json'})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def resolve_fileset_accessions(accessions, rate_limiter=None):
    # For each accession, fetch its object from the IGVF portal and collect the
    # 'file_set.accession'. Warns and skips accessions that can't be resolved.
    fileset_accessions = []
    for accession in accessions:
        try:
            portal_object = get_portal_object(
                accession, rate_limiter=rate_limiter)
        except urllib.error.HTTPError as e:
            logger.warning(
                f"IGVF portal lookup failed for accession '{accession}': HTTP {e.code} {e.reason}. Skipping.")
            continue
        except Exception as e:
            logger.warning(
                f"IGVF portal lookup failed for accession '{accession}': {e}. Skipping.")
            continue

        file_set = portal_object.get('file_set')
        file_set_accession = file_set.get('accession') if isinstance(
            file_set, dict) else None
        if not file_set_accession:
            logger.warning(
                f"IGVF portal object for accession '{accession}' has no 'file_set.accession'. Skipping.")
            continue

        fileset_accessions.append(file_set_accession)

    return fileset_accessions


def append_fileset_accessions(bucket_name, dry_run=True, profile=None, max_rps=DEFAULT_MAX_REQUESTS_PER_SECOND):
    session = boto3.Session(
        profile_name=profile) if profile else boto3.Session()
    s3 = session.client('s3')
    paginator = s3.get_paginator('list_objects_v2')

    rate_limiter = RateLimiter(max_rps)

    for page in paginator.paginate(Bucket=bucket_name):
        if 'Contents' not in page:
            logger.info('No objects found in bucket.')
            return

        for obj in page['Contents']:
            key = obj['Key']
            logger.info(f'Processing: {key}')

            # Get existing tags
            try:
                current_tags = s3.get_object_tagging(
                    Bucket=bucket_name, Key=key)['TagSet']
            except s3.exceptions.ClientError as e:
                logger.error(f'Error getting tags for {key}: {e}')
                continue

            portal_tag = next(
                (tag for tag in current_tags if tag['Key'] == TAG_KEY), None)
            if portal_tag is None or not portal_tag['Value'].strip():
                logger.info(
                    f"No '{TAG_KEY}' tag present on {key}. Nothing to expand. Skipping.")
                continue

            existing_accessions = portal_tag['Value'].split()
            fileset_accessions = resolve_fileset_accessions(
                existing_accessions, rate_limiter=rate_limiter)

            combined = unique_preserve_order(
                existing_accessions + fileset_accessions)
            new_value = ' '.join(combined)

            if new_value == portal_tag['Value']:
                logger.info(
                    f"'{TAG_KEY}' on {key} already contains all related fileset accessions. No update needed.")
                continue

            # Rebuild the tag set, replacing only the portal_accessions tag value and
            # keeping every other tag unchanged.
            updated_tags = []
            for tag in current_tags:
                if tag['Key'] == TAG_KEY:
                    updated_tags.append({'Key': TAG_KEY, 'Value': new_value})
                else:
                    updated_tags.append(tag)

            logger.info(f"Updated '{TAG_KEY}' tag for {key} to: {new_value}")

            if dry_run:
                logger.info(
                    f'[DRY RUN] Would apply tags to {key}: {updated_tags}')
            else:
                try:
                    s3.put_object_tagging(
                        Bucket=bucket_name,
                        Key=key,
                        Tagging={'TagSet': updated_tags}
                    )
                    logger.info(f'Applied updated tags to {key}')
                except s3.exceptions.ClientError as e:
                    logger.error(f'Failed to tag {key}: {e}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Expand the 'portal_accessions' tag of S3 objects with related file_set accessions from the IGVF portal API.")
    parser.add_argument(
        '--bucket_name', help='The name of the S3 bucket.', default=BUCKET_NAME)
    parser.add_argument('--dry-run', action='store_true',
                        help='If set, will not apply changes.', default=False)
    parser.add_argument(
        '--profile', help='Optional AWS profile name to use. If omitted, credentials are read from the environment.', default=None)
    parser.add_argument(
        '--log-file', help='Optional path to a file where logs will also be written (appended). Console output is unaffected.', default=None)
    parser.add_argument(
        '--max-rps', type=float, default=DEFAULT_MAX_REQUESTS_PER_SECOND,
        help=f'Maximum requests per second to the IGVF portal API (default: {DEFAULT_MAX_REQUESTS_PER_SECOND}). Set to 0 to disable throttling.')

    args = parser.parse_args()

    setup_logging(args.log_file)

    append_fileset_accessions(
        args.bucket_name, dry_run=args.dry_run, profile=args.profile, max_rps=args.max_rps)
