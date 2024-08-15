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
