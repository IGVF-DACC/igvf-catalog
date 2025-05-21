# This script appends a value to the 'version' tag of S3 objects in a specified bucket.
# It checks if the tag already exists and updates it accordingly.
# If the tag does not exist, it creates a new one. The script can run in dry-run mode to preview changes without applying them.
# Useful when deploying new versions of the IGVF Catalog in S3.
#
# Usage:
# python tag_s3_data.py --bucket_name <bucket_name> --append_value <append_value> --key_name <key_name> --dry_run
#
#
# Requirements:
# - boto3
# - AWS credentials configured in your environment
# - Permissions to access the specified S3 bucket and modify object tags
#

import boto3
import argparse

# default values:
BUCKET_NAME = 'igvf-catalog-parsed-collections'
APPEND_VALUE = 'IGVF_catalog_beta_v0.4.1b'
KEY_NAME = 'version'
DRY_RUN = True


def append_to_version_tag(bucket_name, key_name, append_value, dry_run=True):
    s3 = boto3.client('s3')
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
            version_found = False

            for tag in current_tags:
                if tag['Key'] == key_name:
                    if tag['Value'] == append_value:
                        print(
                            f"Tag '{key_name}' already has the value '{append_value}'. No update needed.")
                    else:
                        tag['Value'] = '-'.join([tag['Value'], append_value])
                        print(f"Updated 'version' tag to: {tag['Value']}")
                    version_found = True
                updated_tags.append(tag)

            if not version_found:
                new_version = append_value.lstrip('-')
                updated_tags.append({'Key': 'version', 'Value': new_version})
                print(f"Added new 'version' tag with value: {new_version}")

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
        description='Append a value to the version tag of S3 objects.')
    parser.add_argument('--bucket_name', required=True,
                        help='The name of the S3 bucket.', default=BUCKET_NAME)
    parser.add_argument('--append_value', required=True,
                        help='The value to append to the version tag.', default=APPEND_VALUE)
    parser.add_argument('--key_name', default='version', help='The key name for the version tag.', default=KEY_NAME)
    parser.add_argument('--dry_run', action='store_true',
                        help='If set, will not apply changes.', default=DRY_RUN)

    args = parser.parse_args()

    append_to_version_tag(args.bucket_name, args.key_name,
                          args.append_value, dry_run=args.dry_run)
