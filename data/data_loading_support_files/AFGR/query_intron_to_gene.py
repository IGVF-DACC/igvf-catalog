# The AFGR sQTL files have intron positions in column 6, e.g. 10:100374012:100381216:clu_24627
# This script generates mapping from intron to genes
import pickle
import requests


def query_intron_to_gene(intron_region):
    '''Map intron to genes from catalog api genes endpoint
    Args:
        intron_region (str): intron feature from AFGR file (e.g. 10:100374012:100381216:clu_24627)
    Returns:
        gene_ids (list): list of gene ids
    '''
    data_service_url = 'https://api.catalog.igvf.org/api'
    endpoint = 'genes'
    intron_chr = 'chr' + intron_region.split(':')[0]
    query_string = 'region=' + intron_chr + '%3A' + \
        '-'.join(intron_region.split(':')[1:3])
    url = data_service_url + '/' + endpoint + '?' + query_string

    responses = requests.get(url).json()
    gene_ids = []
    if len(responses) > 1:  # filter out pseudogene cases for multiple mapping cases
        for response in responses:
            if response['gene_type'] != 'processed_pseudogene':
                gene_ids.append(response['_id'])
    elif len(responses) == 1:
        gene_ids.append(responses[0]['_id'])
    else:
        print(intron_region + ' no mapping')
    return gene_ids


# generate mappings and save to a pickle file
intron_mapping = dict()
with open('intron_list.txt') as f:
    for line in f:
        intron = line.strip()
        intron_mapping[intron] = query_intron_to_gene(intron)

outfile = open('AFGR_sQTL_intron_genes.pkl', 'wb')
pickle.dump(intron_mapping, outfile)
outfile.close()
