import os
import argparse

from adapters.gencode_adapter import Gencode
from adapters.gnomad_adapter import Gnomad
from adapters.topld_adapter import TopLD
from adapters.qtl_adapter import Qtl

from db.arango_db import ArangoDB


ADAPTERS = {
  'gencode_genes': Gencode(filepath='./samples/gencode_sample.gtf', type='gene', chr='chr1'),
  'gencode_transcripts': Gencode(filepath='./samples/gencode_sample.gtf', type='transcript', chr='chr1'),
  'gnomad': Gnomad(filepath='./samples/gnomad_sample.vcf', chr='chrY'),
  'topld': TopLD(filepath='./samples/topld_sample.csv', chr='chr22', ancestry='SAS'),
  'qtl': Qtl(filepath='./samples/qtl_sample.txt', biological_context='brain_amigdala')
}

parser = argparse.ArgumentParser(
    prog='IGVF Catalog Sample Data Loader',
    description='Loads sample data into a local ArangoDB instance'
  )

parser.add_argument('--dry-run', action='store_true', help = 'Dry Run / Print ArangoDB Statements')
parser.add_argument("-a", "--adapter", nargs='*', help = "Loads the sampe adata for an adapter", choices=ADAPTERS.keys())
parser.add_argument("-i", "--create-indexes", action='store_true', help = "Creates ArangoDB indexes for a given adapter")

args = parser.parse_args()

dry_run = args.dry_run
create_indexes = args.create_indexes
adapters = args.adapter or ADAPTERS.keys()

if not dry_run:
  ArangoDB().setup_dev()

import_cmds = []
  
for a in adapters:
  adapter = ADAPTERS[a]

  if create_indexes:
    adapter.create_indexes()
  else:
    adapter.write_file()
    import_cmds.append(adapter.arangodb())

    if adapter.has_indexes():
      print('{} needs indexes. After data loading, please run: python3 dev_setup.py -i -a {}'.format(a, a))

import_cmds = sum(import_cmds, []) # [[cmd1], [cmd2]] => [cmd1, cmd2]

for cmd in import_cmds:
  if dry_run:
    print(cmd)
  else:
    os.system(cmd)
