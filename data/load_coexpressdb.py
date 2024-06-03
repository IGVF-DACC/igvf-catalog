import os
import argparse
from adapters.coxpresdb_adapter import Coxpresdb
import pickle


# gencode file: https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_43/gencode.v43.chr_patch_hapl_scaff.annotation.gtf.gz
# Homo_sapiens.gene_info.gz file: https://ftp.ncbi.nih.gov/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz

parser = argparse.ArgumentParser(
    prog='IGVF Catalog Sample Data Loader',
    description='Loads sample data into a local ArangoDB instance'
)

parser.add_argument('-i', '--create-indexes', action='store_true',
                    help='Creates ArangoDB indexes for a given adapter')

args = parser.parse_args()

import_cmds = []

folder_path = '/home/ubuntu/datasets/coxpresdb'
index = 1
with open('./samples/entrez_ensembl.pkl', 'rb') as f:
    entrez_ensembl_dict = pickle.load(f)
for entrez_id in os.listdir(folder_path):
    print('entrez id', entrez_id)
    ensembl_id = entrez_ensembl_dict.get(entrez_id)
    if ensembl_id:
        file_path = os.path.join(folder_path, entrez_id)
        adapter = Coxpresdb(file_path)
        print('Write data file', index, 'entrez id',
              entrez_id, 'ensembl id', ensembl_id)
        adapter.write_file()

        if getattr(adapter, 'SKIP_BIOCYPHER', None):
            exit(0)
        index += 1

import_cmds.append(adapter.arangodb())

import_cmds = sum(import_cmds, [])  # [[cmd1], [cmd2]] => [cmd1, cmd2]

for cmd in import_cmds:
    print(cmd)
