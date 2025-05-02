# Modified from Mingjie's script in DSERV-202-encode-e2g
import os
import argparse
import requests
from adapters.encode_element_gene_adapter import EncodeElementGeneLink

files_url = 'https://www.encodeproject.org/report/?type=File&lab.title=Jesse+Engreitz%2C+Stanford&submitted_by.title=Andreas+Roman+Gschwind&output_type=thresholded+element+gene+links&field=%40id&field=biosample_ontology.term_id&field=s3_uri&field=dataset&limit=all&format=json'
# files_url = 'https://www.encodeproject.org/report/?type=File&status=released&file_format=bed&file_format_type=bed3%2B&lab.title=Roderic+Guigo%2C+CRG&award.project=ENCODE&output_type=thresholded+element+gene+links&field=accession&field=dataset&field=href&field=s3_uri&field=biosample_ontology.term_id&limit=all&format=json'
data = requests.get(files_url).json()['@graph']

parser = argparse.ArgumentParser(
    prog='IGVF Catalog Sample Data Loader',
    description='Loads sample data into a local ArangoDB instance'
)

parser.add_argument('--dry-run', action='store_true',
                    help='Dry Run / Print ArangoDB Statements')
parser.add_argument('-i', '--create-indexes', action='store_true',
                    help='Creates ArangoDB indexes for a given adapter')

args = parser.parse_args()
dry_run = args.dry_run
create_indexes = args.create_indexes
import_cmds = []
folder_dnase_only = '/home/ubuntu/datasets//encode_e2g_dnase_only'
folder_full = '/home/ubuntu/datasets//encode_e2g_full'
folder = '/home/ubuntu/epiraction_new_DSERV-222'


def load_by_label(label, source, folder):
    adapters = []
    files = []
    for file in data:
        file_name = file['s3_uri'].split('/')[-1]
        filepath = os.path.join(folder, file_name)
        if os.path.isfile(filepath):
            print('loading data from file:', filepath, label, source)
            term_id = file['biosample_ontology']['term_id']
            term_id = term_id.replace(':', '_')
            # e.g. https://www.encodeproject.org/files/ENCFF492KOI/
            source_url = 'https://www.encodeproject.org/' + file['@id']
            files.append(source_url)
            adapters.append(EncodeElementGeneLink(
                filepath, label, source, source_url, term_id))

    for file, adapter in zip(files, adapters):
        if create_indexes:
            adapter.create_indexes()
            adapter.create_aliases()
        else:
            try:
                adapter.write_file()
            except Exception:
                print('no file written for: ' + file)

            if getattr(adapter, 'SKIP_BIOCYPHER', None):
                exit(0)

    import_cmds.append(adapter.arangodb())


# load_by_label('regulatory_region', 'ENCODE-E2G-DNaseOnly', folder_dnase_only)
# load_by_label('regulatory_region_gene_biosample', 'ENCODE-E2G-DNaseOnly', folder_dnase_only)
# load_by_label('donor', 'ENCODE-E2G-DNaseOnly', folder_dnase_only)
# load_by_label('regulatory_region_gene_biosample_donor', 'ENCODE-E2G-DNaseOnly', folder_dnase_only)
# load_by_label('regulatory_region_gene_biosample_treatment_CHEBI', 'ENCODE-E2G-DNaseOnly', folder_dnase_only)
load_by_label('regulatory_region_gene_biosample_treatment_protein',
              'ENCODE-E2G-DNaseOnly', folder_dnase_only)
# load_by_label('regulatory_region', 'ENCODE-E2G-Full', folder_full)
# load_by_label('regulatory_region_gene_biosample', 'ENCODE-E2G-Full', folder_full)
# load_by_label('donor', 'ENCODE-E2G-Full', folder_full)
# load_by_label('regulatory_region_gene_biosample_donor', 'ENCODE-E2G-Full', folder_full)
# load_by_label('regulatory_region_gene_biosample_treatment_CHEBI', 'ENCODE-E2G-Full', folder_full)
# load_by_label('regulatory_region', 'ENCODE_EpiRaction', folder)
# load_by_label('regulatory_region_gene',
#              'ENCODE-E2G-DNaseOnly', folder_dnase_only)
# load_by_label('regulatory_region_gene', 'ENCODE-E2G-Full', folder_full)
# load_by_label('regulatory_region_gene', 'ENCODE_EpiRaction', folder)

import_cmds = sum(import_cmds, [])  # [[cmd1], [cmd2]] => [cmd1, cmd2]

for cmd in import_cmds:
    if dry_run:
        print(cmd)
    else:
        os.system(cmd)
