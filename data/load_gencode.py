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
    'gencode_genes': Gencode(filepath='/home/ubuntu/datasets/gencode/gencode.v43.chr_patch_hapl_scaff.annotation.gtf', type='gene', label='gencode_gene'),
    'gencode_transcripts': Gencode(filepath='/home/ubuntu/datasets/gencode/gencode.v43.chr_patch_hapl_scaff.annotation.gtf', type='transcript', label='gencode_transcript'),
    'transcribed_to': Gencode(filepath='/home/ubuntu/datasets/gencode/gencode.v43.chr_patch_hapl_scaff.annotation.gtf', type='transcribed to', label='transcribed_to'),
    'transcribed_from': Gencode(filepath='/home/ubuntu/datasets/gencode/gencode.v43.chr_patch_hapl_scaff.annotation.gtf', type='transcribed from', label='transcribed_from'),
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

import_cmds = []

for a in adapters:
    adapter = ADAPTERS[a]

    if create_indexes:
        adapter.create_indexes()
    elif create_aliases:
        adapter.create_aliases()
    else:
        adapter.write_file()
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
