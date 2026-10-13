# This script appends a value to one or more specified tags (key_name, repeatable) of S3 objects
# in a specified bucket. For each key_name, it checks if the tag already exists and updates it
# accordingly. If the tag does not exist, it creates a new one. The script can run in dry-run mode
# to preview changes without applying them. Useful when deploying new versions of the IGVF Catalog
# in S3 - pass --key_name version --key_name collections to apply the same logic to both tags.
#
# Optionally, pass --replace_value to retire an old version tag as part of the same pass: if a
# tag's existing value contains --replace_value, that token is swapped for --append_value instead
# of appending a second token. Without --replace_value, behavior is unchanged (pure append-if-missing).
#
# Usage:
# python tag_s3_data.py --bucket_name <bucket_name> --append_value <append_value> --key_name <key_name> --profile <aws_profile> --dry_run
# python tag_s3_data.py --append_value IGVF_catalog_v1.3 --replace_value IGVF_catalog_v2.0 --key_name version --key_name collections --dry_run
#
#
# Requirements:
# - boto3
# - AWS credentials configured in your environment, or an AWS profile passed via --profile
# - Permissions to access the specified S3 bucket and modify object tags
#
# For catalog deployments, use: python3 tag_s3_data.py --dry_run // to preview changes with default values

import boto3
import argparse

# default values:
BUCKET_NAME = 'igvf-catalog-parsed-collections'
APPEND_VALUE = 'IGVF_catalog_v1.0.0'
KEY_NAME = 'version'


TAG_VALUE_SEPARATOR = ' '


def compute_updated_value(existing_value, append_value, replace_value):
    # Multiple versions accumulate in one tag as a space-separated list (S3 only allows a
    # single value per tag key), so the tag is parsed/rebuilt as tokens rather than treated
    # as an opaque string.
    existing_values = existing_value.split()

    if replace_value is not None and replace_value in existing_values:
        existing_values = [
            append_value if v == replace_value else v for v in existing_values]
        # Replacing could coincidentally produce a duplicate if append_value was already
        # present alongside replace_value - dedupe while preserving first-seen order.
        seen = set()
        deduped = []
        for v in existing_values:
            if v not in seen:
                seen.add(v)
                deduped.append(v)
        return TAG_VALUE_SEPARATOR.join(deduped), 'replaced'

    if append_value in existing_values:
        return existing_value, 'unchanged'

    existing_values.append(append_value)
    return TAG_VALUE_SEPARATOR.join(existing_values), 'appended'


def append_to_tag(bucket_name, key_names, append_value, replace_value=None, dry_run=True, profile=None):
    session = boto3.Session(
        profile_name=profile) if profile else boto3.Session()
    s3 = session.client('s3')
    paginator = s3.get_paginator('list_objects_v2')

    for page in paginator.paginate(Bucket=bucket_name):
        if 'Contents' not in page:
            print('No objects found in bucket.')
            return

        for obj in page['Contents']:
            key = obj['Key']
            print(f'\nProcessing: {key}')

            # Get existing tags
            try:
                current_tags = s3.get_object_tagging(
                    Bucket=bucket_name, Key=key)['TagSet']
            except s3.exceptions.ClientError as e:
                print(f'Error getting tags for {key}: {e}')
                continue

            updated_tags = []
            found_key_names = set()

            for tag in current_tags:
                if tag['Key'] in key_names:
                    new_value, action = compute_updated_value(
                        tag['Value'], append_value, replace_value)
                    if action == 'unchanged':
                        print(
                            f"Tag '{tag['Key']}' already contains the value '{append_value}'. No update needed.")
                    elif action == 'replaced':
                        print(
                            f"Replaced '{replace_value}' with '{append_value}' in {tag['Key']} tag: {new_value}")
                    else:
                        print(f"Updated {tag['Key']} tag to: {new_value}")
                    tag['Value'] = new_value
                    found_key_names.add(tag['Key'])
                updated_tags.append(tag)

            for key_name in key_names:
                if key_name not in found_key_names:
                    new_value = append_value.lstrip(' ')
                    updated_tags.append({'Key': key_name, 'Value': new_value})
                    print(f'Added new {key_name} tag with value: {new_value}')

            if dry_run:
                print(f'[DRY RUN] Would apply tags to {key}: {updated_tags}')
            else:
                try:
                    s3.put_object_tagging(
                        Bucket=bucket_name,
                        Key=key,
                        Tagging={'TagSet': updated_tags}
                    )
                    print(f'Applied updated tags to {key}')
                except s3.exceptions.ClientError as e:
                    print(f'Failed to tag {key}: {e}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Append a value to the tag specified by key_name of S3 objects.')
    parser.add_argument(
        '--bucket_name', help='The name of the S3 bucket.', default=BUCKET_NAME)
    parser.add_argument(
        '--append_value', help='The value to append to the tag specified by key_name.', default=APPEND_VALUE)
    parser.add_argument(
        '--replace_value', help='If this value is present in the existing tag, swap it for --append_value instead of appending a second token.', default=None)
    parser.add_argument(
        '--key_name', action='append', dest='key_names',
        help=f'The key name for a tag to append to. Repeat to apply the same logic to multiple '
             f'tags, e.g. --key_name version --key_name collections. Defaults to {KEY_NAME!r} '
             'if omitted.', default=None)
    parser.add_argument('--dry-run', action='store_true',
                        help='If set, will not apply changes.', default=False)
    parser.add_argument(
        '--profile', help='Optional AWS profile name to use. If omitted, credentials are read from the environment.', default=None)

    args = parser.parse_args()
    key_names = args.key_names if args.key_names else [KEY_NAME]

    append_to_tag(args.bucket_name, key_names, args.append_value,
                  replace_value=args.replace_value, dry_run=args.dry_run, profile=args.profile)
