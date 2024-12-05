# Examples:
#
# Import all files in the parsed-files folder into the genes collection
# python3 data_ingestion.py --collection genes --file parsed-files/*
#
# Import genes collection from S3
# python3 data_ingestion.py --collection genes --s3
#
# Import genes collection from S3 from custom bucket
# python3 data_ingestion.py --collection genes --s3 --s3-bucket genes-bucket

import os
import argparse
from db.s3 import S3
from adapters.storage import Storage
from adapters.writer import get_writer

DEFAULT_BUCKET = 'igvf-catalog-parsed-collections'
AWS_PROFILE_NAME = 'igvf-dev'

parser = argparse.ArgumentParser(
    prog='IGVF Catalog Data Ingestion',
    description='Loads data into ArangoDB or Clickhouse'
)

parser.add_argument('--collection', help='Loads the sample data for an adapter.',
                    choices=Storage.all_collections(), required=True)
parser.add_argument('--database', type=str, choices=['arangodb', 'clickhouse'],
                    default='arangodb', help='Database to ingest the data')
parser.add_argument('--dry-run', type=bool,
                    default=False, help='Dry-run database insertion. True will only print inserting commands, False will execute them.')
parser.add_argument('--files', nargs='+', default=[],
                    help='Local JSONL for ingestion')
parser.add_argument('--s3', type=bool,
                    default=False, help='S3 bucket')
parser.add_argument('--s3-bucket', type=str,
                    default=DEFAULT_BUCKET, help='S3 bucket')
parser.add_argument('--output-folder', type=str,
                    default='./parsed-data', help='Folder to temporarily store parsed data from S3. Default: local folder ./parsed-data')
parser.add_argument('--aws-profile', type=str, default=AWS_PROFILE_NAME,
                    help='The AWS profile to use, for example "igvf-dev".')
parser.add_argument('--keep-file', action='store_true',
                    help='Keep the files after ingestion')

args = parser.parse_args()
keep_file = args.keep_file

if (args.files):
    files = args.files
else:
    s3 = S3(aws_profile=args.aws_profile, bucket=args.s3_bucket,
            output_folder=args.output_folder)
    if os.path.isfile(args.collection + '.jsonl'):
        print('Using local file: ' + args.collection + '.jsonl')
        files = [args.collection + '.jsonl']
    else:
        files = s3.download_s3_files(args.collection)

storage = Storage(args.collection, db=args.database, dry_run=args.dry_run)
for f in files:
    storage.save(f, keep_file)
