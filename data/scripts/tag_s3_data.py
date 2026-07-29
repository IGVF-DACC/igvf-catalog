# This script appends a value to a specified tag (key_name) of S3 objects in a specified bucket.
# It checks if the tag already exists and updates it accordingly.
# If the tag does not exist, it creates a new one. The script can run in dry-run mode to preview changes without applying them.
# Useful when deploying new versions of the IGVF Catalog in S3.
#
# Usage:
# python tag_s3_data.py --bucket_name <bucket_name> --append_value <append_value> --key_name <key_name> --profile <aws_profile> --dry_run
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


def append_to_tag(bucket_name, key_name, append_value, dry_run=True, profile=None):
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
            tag_found = False

            for tag in current_tags:
                if tag['Key'] == key_name:
                    existing_values = tag['Value'].split()
                    if append_value in existing_values:
                        print(
                            f"Tag '{key_name}' already contains the value '{append_value}'. No update needed.")
                    else:
                        existing_values.append(append_value)
                        tag['Value'] = ' '.join(existing_values)
                        print(f"Updated {key_name} tag to: {tag['Value']}")
                    tag_found = True
                updated_tags.append(tag)

            if not tag_found:
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
        '--key_name', help='The key name for the tag to append to.', default=KEY_NAME)
    parser.add_argument('--dry-run', action='store_true',
                        help='If set, will not apply changes.', default=False)
    parser.add_argument(
        '--profile', help='Optional AWS profile name to use. If omitted, credentials are read from the environment.', default=None)

    args = parser.parse_args()

    append_to_tag(args.bucket_name, args.key_name,
                  args.append_value, dry_run=args.dry_run, profile=args.profile)
