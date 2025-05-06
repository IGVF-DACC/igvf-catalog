import os
import argparse
from sample_adapters import ADAPTERS

from db.arango_db import ArangoDB

parser = argparse.ArgumentParser(
    prog='IGVF Catalog Dev Setup',
    description='Loads sample data into a local ArangoDB instance'
)

ArangoDB().setup_dev()

import_cmds = []

for a in ADAPTERS.keys():
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
