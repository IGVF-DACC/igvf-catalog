import os
import argparse

from adapters.gencode_adapter import Gencode
from adapters.topld_adapter import TopLD
from adapters.eqtl_adapter import EQtl
from adapters.encode_caqtl_adapter import CAQtl
from adapters.ccre_adapter import CCRE
from adapters.ontologies_adapter import Ontology
from adapters.uniprot_adapter import Uniprot
from adapters.favor_adapter import Favor

from db.arango_db import ArangoDB


ADAPTERS = {
    'gencode_genes': Gencode(filepath='./samples/gencode_sample.gtf', type='gene', label='gencode_gene'),
    'gencode_transcripts': Gencode(filepath='./samples/gencode_sample.gtf', type='transcript', label='gencode_transcript'),
    'transcribed_to': Gencode(filepath='./samples/gencode_sample.gtf', type='transcribed to', label='transcribed_to'),
    'transcribed_from': Gencode(filepath='./samples/gencode_sample.gtf', type='transcribed from', label='transcribed_from'),
    'topld': TopLD(filepath='./samples/topld_sample.csv', chr='chr22', ancestry='SAS'),
    'eqtl': EQtl(filepath='./samples/qtl_sample.txt', biological_context='brain_amigdala'),
    'caqtl': CAQtl(filepath='./samples/caqtl-sample.bed'),
    'caqtl_ocr': CAQtl(filepath='./samples/caqtl-sample.bed', type='accessible_dna_region'),
    'ccre': CCRE(filepath='./samples/ccre_example.bed.gz'),
    'clo_nodes': Ontology(ontology='CLO', type='node'),
    'clo_edges': Ontology(ontology='CLO', type='edge'),
    'uberon_nodes': Ontology(ontology='UBERON', type='node'),
    'uberon_edges': Ontology(ontology='UBERON', type='edge'),
    'cl_nodes': Ontology(ontology='CL', type='node'),
    'cl_edges': Ontology(ontology='CL', type='edge'),
    'hpo_nodes': Ontology(ontology='HPO', type='node'),
    'hpo_edges': Ontology(ontology='HPO', type='edge'),
    'mondo_nodes': Ontology(ontology='MONDO', type='node'),
    'mondo_edges': Ontology(ontology='MONDO', type='edge'),
    'go_nodes': Ontology(ontology='GO', type='node'),
    'go_edges': Ontology(ontology='GO', type='edge'),
    'efo_nodes': Ontology(ontology='EFO', type='node'),
    'efo_edges': Ontology(ontology='EFO', type='edge'),
    'ccre': CCRE(filepath='./samples/ccre_example.bed.gz'),
    'UniProtKB_protein': Uniprot(filepath='./samples/uniprot_sprot_human_sample.dat.gz'),
    'UniProtKB_Translates_To': Uniprot(filepath='./samples/uniprot_sprot_human_sample.dat.gz', type='translates to', label='UniProtKB_Translates_To'),
    'UniProtKB_Translation_Of': Uniprot(filepath='./samples/uniprot_sprot_human_sample.dat.gz', type='translation of', label='UniProtKB_Translation_Of'),
    'favor': Favor(filepath='./samples/favor_sample.vcf')
}

parser = argparse.ArgumentParser(
    prog='IGVF Catalog Sample Data Loader',
    description='Loads sample data into a local ArangoDB instance'
)

parser.add_argument('--dry-run', action='store_true',
                    help='Dry Run / Print ArangoDB Statements')
parser.add_argument('-a', '--adapter', nargs='*',
                    help='Loads the sampe adata for an adapter', choices=ADAPTERS.keys())
parser.add_argument('-i', '--create-indexes', action='store_true',
                    help='Creates ArangoDB indexes for a given adapter')
parser.add_argument('-l', '--create-aliases', action='store_true',
                    help='Creates ArangoDB fuzzy search alisases for a given adapter')

args = parser.parse_args()

dry_run = args.dry_run
create_indexes = args.create_indexes
create_aliases = args.create_aliases
adapters = args.adapter or ADAPTERS.keys()

if not dry_run:
    ArangoDB().setup_dev()

import_cmds = []

for a in adapters:
    adapter = ADAPTERS[a]

    if create_indexes:
        adapter.create_indexes()
    elif create_aliases:
        adapter.create_aliases()
    else:
        adapter.write_file()

        if getattr(adapter, 'SKIP_BIOCYPHER', None):
            exit(0)

        import_cmds.append(adapter.arangodb())

        if adapter.has_indexes():
            print(
                '{} needs indexes. After data loading, please run: python3 dev_setup.py -i -a {}'.format(a, a))

import_cmds = sum(import_cmds, [])  # [[cmd1], [cmd2]] => [cmd1, cmd2]

for cmd in import_cmds:
    if dry_run:
        print(cmd)
    else:
        os.system(cmd)
