import os
import argparse
import boto3
from active_adapters import ADAPTERS

from db.arango_db import ArangoDB

parser = argparse.ArgumentParser(
    prog='IGVF Catalog Sample Data Loader',
    description='Loads sample data into a local ArangoDB instance'
)

parser.add_argument('-a', '--adapter', nargs='*',
                    help='Loads the sample data for an adapter', choices=ADAPTERS.keys())
parser.add_argument('--output-bucket', type=str, default=None)

args = parser.parse_args()
adapters = args.adapter or ADAPTERS.keys()

import_cmds = []

if args.output_bucket is not None and args.output_bucket_key is not None:
    session = boto3.Session()
else:
    session = None

for a in adapters:
    adapter = ADAPTERS[a]

    # or adapter.write_file(s3_bucket=args.output_bucket, session=session) to save into S3
    adapter.write_file()
