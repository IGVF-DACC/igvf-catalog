# This script appends a value to the 'version' tag of S3 objects in a specified bucket.
# It checks if the tag already exists and updates it accordingly.
# If the tag does not exist, it creates a new one. The script can run in dry-run mode to preview changes without applying them.
# Useful when deploying new versions of the IGVF Catalog in S3.
#
# Usage after configuring the values of: BUCKET_NAME, APPEND_VALUE, DRY_RUN accordingly:
# python tag_s3_data.py
#
#
# Requirements:
# - boto3
# - AWS credentials configured in your environment
# - Permissions to access the specified S3 bucket and modify object tags
#

import boto3


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
    BUCKET_NAME = 'igvf-catalog-parsed-collections'
    APPEND_VALUE = 'IGVF_catalog_beta_v0.4.1b'
    KEY_NAME = 'version'
    DRY_RUN = True

    append_to_version_tag(BUCKET_NAME, KEY_NAME, APPEND_VALUE, dry_run=DRY_RUN)
