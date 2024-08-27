import os
import argparse
import boto3
from active_adapters import ADAPTERS
from active_adapters import LABEL_TO_ADAPTER

from adapters.writer import get_writer

parser = argparse.ArgumentParser(
    prog='IGVF Catalog Sample Data Loader',
    description='Loads sample data into a local ArangoDB instance'
)

parser.add_argument('--adapter-labels', nargs='*',
                    help='Loads the sample data for an adapter', choices=LABEL_TO_ADAPTER.keys())
parser.add_argument('--input-filepath', type=str, default=None)
parser.add_argument('--output-bucket', type=str, default=None)
parser.add_argument('--output-bucket-key', type=str, default=None)
parser.add_argument('--output-local-path', type=str, default=None)

args = parser.parse_args()

writer = get_writer(filepath=args.output_local_path,
                    bucket=args.output_bucket, key=args.output_bucket_key)

print(type(writer))

for label in args.adapter_labels:
    adapter = LABEL_TO_ADAPTER[label](
        filepath=args.input_filepath, label=label, writer=writer)
    adapter.process_file()
