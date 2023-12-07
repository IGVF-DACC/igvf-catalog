import os
import argparse
from active_adapters import ADAPTERS

from db.arango_db import ArangoDB

parser = argparse.ArgumentParser(
    prog='IGVF Catalog DB Index Setup',
    description='Creates indexes in the development.json IGVF Catalog ArangoDB collections'
)

parser.add_argument('-a', '--adapter', nargs='*',
                    help='Creates collection indexes in the development.json DB', choices=ADAPTERS.keys())

args = parser.parse_args()
adapters = args.adapter or ADAPTERS.keys()

for a in adapters:
    adapter = ADAPTERS[a]

    if adapter.has_indexes():
        print(('{} - creating...').format(a))

        try:
            adapter.create_indexes()
            adapter.create_aliases()
        except Exception as error:
            print('{} - index creation failed. {}'.format(a, error))
    else:
        print('{} - skipping... there are no indexes registered in schema_config.yml.'.format(a))
