import os

from adapters.gencode_adapter import Gencode
from adapters.gnomad_adapter import Gnomad
from adapters.topld_adapter import TopLD

from db.arango_db import ArangoDB

adapters = [
  Gencode(filepath='./samples/gencode_sample.gtf', type='gene', chr='1'),
  Gencode(filepath='./samples/gencode_sample.gtf', type='transcript', chr='1'),
  Gnomad(filepath='./samples/gnomad_sample.vcf', chr='Y'),
  TopLD(filepath='./samples/topld_sample.csv', chr='22')
]

if __name__ == "__main__":
  ArangoDB().setup_dev()
  
  import_cmds = []
  
  for adapter in adapters:
    adapter.write_file()
    import_cmds.append(adapter.arangodb())

  import_cmds = sum(import_cmds, []) # [[cmd1], [cmd2]] => [cmd1, cmd2]
  for cmd in import_cmds:
    os.system(cmd)
