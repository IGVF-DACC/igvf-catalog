import csv
import hashlib
import json
import os
import gzip
from math import log10
from typing import Optional
import urllib.request

METADATA_PATH = 'data_loading_support_files/eqtl_catalog/tabix_ftp_paths.tsv'
OUTPUT_DIR = 'data_loading_support_files/eqtl_catalog/qtl_files'

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
with open(METADATA_PATH, 'r') as f:
    metadata_reader = csv.reader(f, delimiter='\t')
    next(metadata_reader)
    for row in metadata_reader:
        if row[8] in ['ge', 'leafcutter'] and row[6] == 'naive':

            biological_context = f'ontology_terms/{row[4]}'
            simple_sample_summaries = [row[5]]
            # example: ftp://ftp.ebi.ac.uk/pub/databases/spot/eQTL/susie/QTS000001/QTD000001/QTD000001.credible_sets.tsv.gz
            source_url = row[10]
            # get the file name from the source_url
            file_name = source_url.split('/')[-1]
            file_path = os.path.join(OUTPUT_DIR, file_name)
            # check if the file already exists in data_loading_support_files/eqtl_catalog/
            if not os.path.exists(file_path):
                # download the file
                # Use urllib for FTP URLs
                urllib.request.urlretrieve(source_url, file_path)
