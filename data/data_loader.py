import argparse
import boto3
from active_adapters import LABEL_TO_ADAPTER

from adapters.writer import get_writer

parser = argparse.ArgumentParser(
    prog='IGVF Catalog Sample Data Loader',
    description='Loads sample data into a local ArangoDB instance'
)

# arguments that are not adapter creation related
parser.add_argument('--output-bucket', type=str,
                    default=None, help='The S3 bucket to use')
parser.add_argument('--output-bucket-key', type=str, default=None,
                    help='The S3 location to use, for example "path/to/output.file".')
parser.add_argument('--output-local-path', type=str, default=None,
                    help='The local path to use, for example "path/to/output.file".')
parser.add_argument('--adapter', help='Loads the sample data for an adapter.',
                    choices=LABEL_TO_ADAPTER.keys(), required=True)
parser.add_argument('--aws-profile', type=str, default=None,
                    help='The AWS profile to use, for example "igvf-dev".')

# arguments that are in at least one adapter signature
parser.add_argument('--gene-alias-file-path', type=str,
                    help='Gene alias file path for GencodeGene.')
parser.add_argument('--chr', help='The chr of the adapter to load.')
parser.add_argument('--label', help='The label of the adapter to load.')
parser.add_argument('--ancestry', type=str, help='Ancestry for TopLD.')
parser.add_argument('--source', type=str)
parser.add_argument('--source-url', type=str)
parser.add_argument('--biological-context', type=str,
                    help='Biological context for EncodeElementGeneLink.')
parser.add_argument('--gaf-type', type=str, help='GAF type for GAF.')
parser.add_argument('--variants-to-genes', type=str,
                    help='Location of variants to genes TSV for GWAS.')
parser.add_argument('--gwas-collection', type=str,
                    help='GWAS collection for GWAS.')
parser.add_argument('--type', type=str, choices=['edge', 'node'])
parser.add_argument('--collection', type=str, help='Collection for DbSNFP.')
parser.add_argument('--ontology', type=str, help='Ontology name.')
parser.add_argument('--annotation-filepath', type=str,
                    help='Annotation CSV path for TopLD.')
parser.add_argument('--filepath', type=str,
                    default=None, help='The path to the input file.', required=True)

args = parser.parse_args()

non_adapter_signature_args = [
    'output_bucket',
    'output_bucket_key',
    'output_local_path',
    'adapter',
    'aws_profile'
]

non_adapter_signature_namespace = argparse.Namespace()
adapter_signature_namespace = argparse.Namespace()

# separate args into non adapter signature and adapter signature args
for arg in vars(args):
    if arg in non_adapter_signature_args:
        setattr(non_adapter_signature_namespace, arg, getattr(args, arg))
    else:
        setattr(adapter_signature_namespace, arg, getattr(args, arg))

if non_adapter_signature_namespace.adapter == 'ontology':
    ontology_name = adapter_signature_namespace.ontology

    writer_primary = get_writer(
        filepath=non_adapter_signature_namespace.output_local_path,
        bucket=non_adapter_signature_namespace.output_bucket,
        key='ontology_terms/' + ontology_name + '-primary.jsonl',
        session=boto3.Session(
            profile_name=non_adapter_signature_namespace.aws_profile)
    )

    writer_secondary = get_writer(
        filepath=non_adapter_signature_namespace.output_local_path,
        bucket=non_adapter_signature_namespace.output_bucket,
        key='ontology_terms/' + ontology_name + '-secondary.jsonl',
        session=boto3.Session(
            profile_name=non_adapter_signature_namespace.aws_profile)
    )

    writer_edge_primary = get_writer(
        filepath=non_adapter_signature_namespace.output_local_path,
        bucket=non_adapter_signature_namespace.output_bucket,
        key='ontology_terms_ontology_terms/' + ontology_name + '-primary.jsonl',
        session=boto3.Session(
            profile_name=non_adapter_signature_namespace.aws_profile)
    )

    writer_edge_secondary = get_writer(
        filepath=non_adapter_signature_namespace.output_local_path,
        bucket=non_adapter_signature_namespace.output_bucket,
        key='ontology_terms_ontology_terms/' + ontology_name + '-secondary.jsonl',
        session=boto3.Session(
            profile_name=non_adapter_signature_namespace.aws_profile)
    )

    adapter = LABEL_TO_ADAPTER[non_adapter_signature_namespace.adapter](
        adapter_signature_namespace.filepath,
        adapter_signature_namespace.ontology,
        node_primary_writer=writer_primary,
        node_secondary_writer=writer_secondary,
        edge_primary_writer=writer_edge_primary,
        edge_secondary_writer=writer_edge_secondary
    )
else:
    writer = get_writer(
    filepath=non_adapter_signature_namespace.output_local_path,
    bucket=non_adapter_signature_namespace.output_bucket,
    key=non_adapter_signature_namespace.output_bucket_key,
    session=boto3.Session(
        profile_name=non_adapter_signature_namespace.aws_profile)
    )

    adapter = LABEL_TO_ADAPTER[non_adapter_signature_namespace.adapter](
        **vars(adapter_signature_namespace), writer=writer)

adapter.process_file()
