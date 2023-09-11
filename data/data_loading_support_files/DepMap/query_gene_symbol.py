import requests


def query_gene_symbol(gene_symbol, gene_json=None, chrom_filter=True):
    '''
    Function for query gene ensembl id with gene symbol. Using local json obj dumped from IGVF Catalog if available, which is quicker for large queries.
    Otherwise, query through the IGVF Catalog api.
    '''

    # only return mapping on chr1, chr2, ... chr22, chrX, chrY, if chrom_filter is True
    chrom_list = ['chr' + str(i) for i in range(1, 23)] + ['chrX', 'chrY']
    gene_ids = []
    if gene_json is None:
        data_service_url = 'https://api.catalog.igvf.org/api'
        endpoint = 'genes'
        query_string = 'gene_name=' + gene_symbol
        url = data_service_url + '/' + endpoint + '?' + query_string

        responses = requests.get(url).json()
        for response in responses:
            if chrom_filter:
                if response['chr'] in chrom_list:
                    gene_ids.append(response['_id'])
            else:
                gene_ids.append(response['_id'])

    else:
        responses = []
        for record in gene_json:
            if record.get('gene_name') is not None:
                if gene_symbol == record['gene_name']:
                    responses.append(record)

        for response in responses:
            if chrom_filter:
                if response['chr'] in chrom_list:
                    gene_ids.append(response['_key'])
            else:
                gene_ids.append(response['_key'])

    return gene_ids
