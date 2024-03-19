import os
from adapters.gwas_adapter import GWAS
folder = './samples/gwas_v2d_split_chr/'

import_cmds = []
adapters = []

files = [filepath + str(chr) + '.tsv' for chr in [str(i)
                                                  for i in range(1, 23)] + ['X']]
for file in files:
    filepath = folder + file
    if os.path.isfile(filepath):
        print('loading data from file:', filepath)
        adapters.append(GWAS(variants_to_ontology=filepath, variants_to_genes='./samples/gwas_v2g_igvf_sample.tsv',
                        gwas_collection='variants_phenotypes_studies'))

for adapter in adapters:
    adapter.write_file()

    if getattr(adapter, 'SKIP_BIOCYPHER', None):
        continue

    import_cmds.append(adapter.arangodb())

import_cmds = sum(import_cmds, [])  # [[cmd1], [cmd2]] => [cmd1, cmd2]

for cmd in import_cmds:
    print(cmd)
