import os
import argparse
from adapters.gtex_adapter import Gtex

parser = argparse.ArgumentParser(
    prog='IGVF Catalog Sample Data Loader',
    description='Loads sample data into a local ArangoDB instance'
)

parser.add_argument('--dry-run', action='store_true',
                    help='Dry Run / Print ArangoDB Statements')
parser.add_argument('-i', '--create-indexes', action='store_true',
                    help='Creates ArangoDB indexes for a given adapter')
parser.add_argument('-l', '--create-aliases', action='store_true',
                    help='Creates ArangoDB fuzzy search alisases for a given adapter')

args = parser.parse_args()

dry_run = args.dry_run
create_indexes = args.create_indexes
create_aliases = args.create_aliases

folder = '/home/ubuntu/datasets/GTEx_Analysis_v8_sQTL'
# folder = 'dist/GTEx_Analysis_v8_sQTL'
import_cmds = []

for file in os.listdir(folder):
    if file.endswith('sqtl_signifpairs.txt.gz'):
        tissue = file.split('.')[0]
        filepath = os.path.join(folder, file)
        print(f'loading file for tissue {tissue}: {filepath}')
        adapter = Gtex(filepath, tissue)
        adapter.write_file()
        import_cmds.append(adapter.arangodb())

import_cmds = sum(import_cmds, [])  # [[cmd1], [cmd2]] => [cmd1, cmd2]

for cmd in import_cmds:
    if dry_run:
        print(cmd)
    else:
        os.system(cmd)
