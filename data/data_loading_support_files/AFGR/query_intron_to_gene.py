# The AFGR sQTL files have intron positions in column 6, e.g. 10:100374012:100381216:clu_24627
# This script generates mapping from intron to genes
import pickle


def query_intron_to_gene(intron_region):
    '''Map intron to genes from catalog api transcripts/genes endpoint
    Args:
        intron_region (str): intron feature from AFGR file (e.g. 10:100374012:100381216:clu_24627)
    Returns:
        gene_ids (list): list of unique gene ids
    '''
    data_service_url = 'https://api-dev.catalog.igvf.org/api'
    endpoint = 'transcripts/genes'
    intron_chr = 'chr' + intron_region.split(':')[0]
    query_string = 'region=' + intron_chr + '%3A' + \
        '-'.join(intron_region.split(':')[1:3])
    url = data_service_url + '/' + endpoint + '?' + query_string

    responses = requests.get(url).json()
    gene_ids = []
    for response in responses:
        gene_ids.append(response['gene'].split('/')[-1])

    return list(set(gene_ids))


# generate mappings and save to a pickle file
intron_mapping = dict()
with open('intron_list.txt') as f:
    for line in f:
        intron = line.strip()
        intron_mapping[intron] = query_intron_to_gene(intron)

outfile = open('AFGR_sQTL_intron_genes.pkl', 'wb')
pickle.dump(intron_mapping, outfile)
outfile.close()
