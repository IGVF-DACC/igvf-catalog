import os
import argparse
from active_adapters import ADAPTERS

from db.arango_db import ArangoDB

parser = argparse.ArgumentParser(
    prog='IGVF Catalog Sample Data Loader',
    description='Loads sample data into a local ArangoDB instance'
)

parser.add_argument('-a', '--adapter', nargs='*',
                    help='Loads the sample data for an adapter', choices=ADAPTERS.keys())

args = parser.parse_args()
adapters = args.adapter or ADAPTERS.keys()

import_cmds = []

for a in adapters:
    adapter = ADAPTERS[a]
    adapter.write_file()

    if getattr(adapter, 'SKIP_BIOCYPHER', None):
        continue

    import_cmds.append(adapter.arangodb())

import_cmds = sum(import_cmds, [])  # [[cmd1], [cmd2]] => [cmd1, cmd2]

for cmd in import_cmds:
    print(cmd)
