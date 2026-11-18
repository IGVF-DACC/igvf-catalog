import argparse
import boto3
from active_adapters import KEY_TO_ADAPTER

from adapters.favor_adapter import Favor
from adapters.file_fileset_adapter import FileFileSet
from adapters.mpra_adapter import MPRAAdapter
from adapters.ontologies_adapter import Ontology
from adapters.writer import get_writer


parser = argparse.ArgumentParser(
    prog='IGVF Catalog Sample Data Loader',
    description='Loads sample data into a local ArangoDB instance'
)

# arguments that are not adapter creation related
parser.add_argument('--output-bucket', type=str,
                    default=None, help='The S3 bucket to use')
parser.add_argument('--output-bucket-key', type=str, default=None,
                    help='The S3 object key. Must end with .gz, for example "path/to/output.jsonl.gz".')
parser.add_argument('--output-local-path', type=str, default=None,
                    help='The local path to use, for example "path/to/output.file". For ontology, please provide the prefix of the output files.')
parser.add_argument('--adapter', help='Loads the sample data for an adapter.',
                    choices=KEY_TO_ADAPTER.keys(), required=True)
parser.add_argument('--aws-profile', type=str, default=None,
                    help='The AWS profile to use, for example "igvf-dev".')
parser.add_argument('--collections-tag', type=str, default=None,
                    help='The collections tag to use, for example "IGVF_catalog_beta_v0.4".')

# arguments that are in at least one adapter signature
parser.add_argument('--gene-alias-file-path', type=str,
                    help='Gene alias file path for GencodeGene.')
parser.add_argument('--chr', help='The chr of the adapter to load.')
parser.add_argument('--label', help='The label of the adapter to load.')
parser.add_argument('--ancestry', type=str, help='Ancestry for TopLD.')
parser.add_argument('--source', type=str)
parser.add_argument('--favor-on-disk-deduplication', action='store_true', default=False,
                    help='Use on-disk deduplication for Favor.')
parser.add_argument('--mode', type=str, default='catalog',
                    choices=['igvfd', 'catalog'], help='mode for gencode gene')
parser.add_argument('--ontology', type=str, help='Ontology name.')
parser.add_argument('--annotation-filepath', type=str,
                    help='Annotation CSV path for TopLD.')
parser.add_argument('--ca-ids-path', type=str,
                    help='The path to the HGVS->CA IDs mapping file in pickle format.')
parser.add_argument('--ca-ids-local-only', action='store_true', default=False,
                    help='Only use local CA IDs, do not use Clingen API.')
parser.add_argument('--uniprot-sprot-file-path', type=str,
                    help='The path to the dat file from uniprotKB Swiss-Prot.')
parser.add_argument('--uniprot-trembl-file-path', type=str,
                    help='The path to the dat file from uniprotKB TrEMBL.')
parser.add_argument('--sem_provenance_path', type=str,
                    help='The path to the provenance file from SEMpl.')
parser.add_argument('--phenotype_term', type=str,
                    help='The phenotype term id for VAMP-seq and MultiSTEP assays.')
parser.add_argument('--filepath', type=str,
                    help='The path to the input file or archive.')
parser.add_argument('--reference-filepath', type=str, nargs='+',
                    help='Related reference input path. MPRAAdapter accepts one or more sequence-design paths. Other adapters require one path.')
parser.add_argument('--drug-reference-filepath', type=str,
                    help='PharmGKB chemicals TSV for drug name→ID mapping (IGVFFI2997DUKO). Required for variant_drug and variant_drug_gene.')
parser.add_argument('--variant-reference-filepath', type=str,
                    help='PharmGKB variants TSV for rsID→HGVS mapping (IGVFFI7955ICXJ). Required for variant_drug and variant_drug_gene.')
parser.add_argument('--study-reference-filepath', type=str,
                    help='PharmGKB study_parameters TSV (IGVFFI1149WTCK). Required for variant_drug and variant_drug_gene.')
parser.add_argument('--gene-reference-filepath', type=str,
                    help='PharmGKB genes TSV for symbol→Ensembl mapping (IGVFFI4821BJHQ). Required for variant_drug_gene.')
parser.add_argument('--accessions', nargs='+', type=str,
                    help='One or more ENCODE or IGVF file accessions to fetch and parse data from.')
parser.add_argument(
    '--excluded-file-accessions',
    nargs='*',
    type=str,
    help='Optional. One or more IGVF file accessions whose entries, for example variants, (if previously loaded) should be ignored for "already loaded" checks. '
)
parser.add_argument('--validate', action=argparse.BooleanOptionalAction, default=None,
                    help='Enable schema validation for parsed records. Defaults to enabled, '
                         'except for Favor, which defaults to disabled due to known '
                         'pre-existing schema mismatches in its source data. Pass --validate '
                         'or --no-validate to override the default for any adapter.')

args = parser.parse_args()
# Preserve the scalar contract for adapters other than MPRAAdapter.
if args.reference_filepath is not None and args.adapter != MPRAAdapter.__name__:
    if len(args.reference_filepath) != 1:
        parser.error(
            'Multiple --reference-filepath values are supported only by MPRAAdapter')
    args.reference_filepath = args.reference_filepath[0]

if args.adapter != FileFileSet.__name__ and not args.filepath:
    parser.error(
        '--filepath is required unless using the FileFileSet adapter')

# Validation defaults to on, except for the variant-loading adapters, whose source data is
# known to contain records that currently fail schema validation (see base_adapter.py's
# validate_doc, which raises rather than skips -- turning validation on by default for these
# would abort the entire load on the first bad record). --validate/--no-validate always wins
# when explicitly passed, for any adapter.
VARIANT_LOADING_ADAPTERS = {Favor.__name__}
if args.validate is None:
    args.validate = args.adapter not in VARIANT_LOADING_ADAPTERS

non_adapter_signature_args = [
    'output_bucket',
    'output_bucket_key',
    'output_local_path',
    'adapter',
    'aws_profile',
    'collections_tag',
]

non_adapter_signature_namespace = argparse.Namespace()
adapter_signature_namespace = argparse.Namespace()

# separate args into non adapter signature and adapter signature args
for arg in vars(args):
    if arg in non_adapter_signature_args:
        setattr(non_adapter_signature_namespace, arg, getattr(args, arg))
    else:
        setattr(adapter_signature_namespace, arg, getattr(args, arg))

if non_adapter_signature_namespace.adapter == Ontology.__name__:
    ontology_name = adapter_signature_namespace.ontology
    # A local prefix and an S3 bucket are different destinations. Pass only the
    # one in use so get_writer can reject a run that asks for both.
    local_prefix = non_adapter_signature_namespace.output_local_path
    session = boto3.Session(
        profile_name=non_adapter_signature_namespace.aws_profile)
    collections_tag = non_adapter_signature_namespace.collections_tag
    bucket = non_adapter_signature_namespace.output_bucket

    def ontology_writer(suffix: str, key: str):
        filepath = None if local_prefix is None else f'{local_prefix}{suffix}'
        return get_writer(
            filepath=filepath,
            bucket=bucket,
            key=None if filepath is not None and bucket is None else key,
            session=session,
            collections_tag=collections_tag,
        )

    writer_primary = ontology_writer(
        '-ontology-terms-primary.jsonl',
        'ontology_terms/' + ontology_name + '-primary.jsonl.gz',
    )
    writer_secondary = ontology_writer(
        '-ontology-terms-secondary.jsonl',
        'ontology_terms/' + ontology_name + '-secondary.jsonl.gz',
    )
    writer_edge_primary = ontology_writer(
        '-ontology-terms-edge-primary.jsonl',
        'ontology_terms_ontology_terms/' + ontology_name + '-primary.jsonl.gz',
    )
    writer_edge_secondary = ontology_writer(
        '-ontology-terms-edge-secondary.jsonl',
        'ontology_terms_ontology_terms/' + ontology_name + '-secondary.jsonl.gz',
    )

    adapter = KEY_TO_ADAPTER[non_adapter_signature_namespace.adapter](
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
            profile_name=non_adapter_signature_namespace.aws_profile),
        collections_tag=non_adapter_signature_namespace.collections_tag
    )

    adapter_kwargs = {
        k: v for k, v in vars(adapter_signature_namespace).items() if v is not None
    }
    adapter = KEY_TO_ADAPTER[non_adapter_signature_namespace.adapter](
        **adapter_kwargs, writer=writer)

adapter.process_file()
