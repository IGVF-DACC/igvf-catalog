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

parser.add_argument('--adapter', help='Loads the sample data for an adapter',
                    choices=LABEL_TO_ADAPTER.keys())
parser.add_argument('--label', help='The label of the adapter to load')
parser.add_argument('--input-filepath', type=str,
                    default=None, help='The path to the input file')
parser.add_argument('--aws-profile', type=str, default=None,
                    help='The AWS profile to use, for example "igvf-dev"')
parser.add_argument('--output-bucket', type=str,
                    default=None, help='The S3 bucket to use')
parser.add_argument('--output-bucket-key', type=str, default=None,
                    help='The S3 location to use, for example path/to/output.file')
parser.add_argument('--output-local-path', type=str, default=None,
                    help='The local path to use, for example path/to/output.file')

args = parser.parse_args()

writer = get_writer(
    filepath=args.output_local_path,
    bucket=args.output_bucket,
    key=args.output_bucket_key,
    session=boto3.Session(profile_name=args.aws_profile)
)


adapter = LABEL_TO_ADAPTER[args.adapter](
    filepath=args.input_filepath, label=args.label, writer=writer)
adapter.process_file()
