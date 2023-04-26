import os
import argparse
from adapters.uniprot_adapter import Uniprot


file = '/home/ubuntu/datasets/uniprot/uniprot_sprot_human.dat.gz'
ADAPTERS = {
    'UniProtKB_protein': Uniprot(filepath=file),
    'UniProtKB_Translates_To': Uniprot(filepath=file, type='translates to', label='UniProtKB_Translates_To'),
    'UniProtKB_Translation_Of': Uniprot(filepath=file, type='translation of', label='UniProtKB_Translation_Of'),
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
