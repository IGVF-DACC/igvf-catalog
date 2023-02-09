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
  'qtl': Qtl('brain_amigdala', filepath='./samples/qtl_sample.txt')
}

parser = argparse.ArgumentParser(
    prog='IGVF Catalog Sample Data Loader',
    description='Loads sample data into a local ArangoDB instance'
  )

parser.add_argument('--dry-run', action='store_true', help = 'Dry Run / Print ArangoDB Statements')
parser.add_argument("-a", "--adapter", nargs='*', help = "Loads the sampe adata for an adapter", choices=ADAPTERS.keys())

args = parser.parse_args()

dry_run = args.dry_run
adapters = args.adapter or ADAPTERS.keys()

load_adapters = [ADAPTERS[a] for a in adapters]

if not dry_run:
  ArangoDB().setup_dev()

import_cmds = []
  
for adapter in load_adapters:
  adapter.write_file()
  import_cmds.append(adapter.arangodb())

import_cmds = sum(import_cmds, []) # [[cmd1], [cmd2]] => [cmd1, cmd2]

for cmd in import_cmds:
  if dry_run:
    print(cmd)
  else:
    os.system(cmd)
