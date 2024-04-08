# This script is used to map the protein ids in PPI file to gene ids
# The mappings are saved as dicts in biogrid_protein_mapping.pkl (for human) and biogrid_protein_mapping_mouse.pkl (for mouse)
# The pkl files are used in GeneGeneBiogrid adapter

import requests
import csv
import pickle


def query_gene_from_protein(uniprot_id):
    data_service_url = 'https://api-dev.catalog.igvf.org/api'
    endpoint = 'proteins/genes'
    query_string = 'protein_id=' + uniprot_id
    url = data_service_url + '/' + endpoint + '?' + query_string

    responses = requests.get(url).json()
    genes = []
    # for those with multiple mappings, only keep those on chr1-22, chrX, chrY
    # (i.e. filtered out scaffold genes)
    if len(responses) > 1:
        for response in responses:
            if response['chr'].startswith('chr'):
                genes.append(response['_id'])
    elif len(responses) == 1:
        genes.append(responses[0]['_id'])

    if len(genes) > 1:
        print(uniprot_id + ' has more than one match')
    elif not genes:
        print(uniprot_id + ' has no match')
        return

    return genes


# Human mappings
protein_to_gene = {}
with open('merged_PPI.UniProt.csv', 'r') as interaction_file:
    interaction_csv = csv.reader(interaction_file)
    next(interaction_csv)
    for row in interaction_csv:
        if row[3] == 'genetic interference':
            proteins = row[:2]
            for protein in proteins:
                if protein not in protein_to_gene.keys():
                    gene = query_gene_from_protein(protein)
                    protein_to_gene[protein] = gene

# manually fix unmapped proteins
protein_to_gene['P35544'] = ['ENSG00000149806']
protein_to_gene['B1AH88'] = ['ENSG00000100300']
protein_to_gene['Q9Y2D5'] = ['ENSG00000157654']

output = open('biogrid_protein_mapping.pkl', 'wb')
pickle.dump(protein_to_gene, output)
output.close()

# Mouse mappings
protein_to_gene_mouse = {}
with open('merged_PPI_mouse.UniProt.csv', 'r') as interaction_file:
    interaction_csv = csv.reader(interaction_file)
    next(interaction_csv)
    for row in interaction_csv:
        if row[3] == 'genetic interference':
            proteins = row[:2]
            for protein in proteins:
                if protein not in protein_to_gene.keys():
                    gene = query_gene_from_protein(protein)
                    protein_to_gene_mouse[protein] = gene
output = open('biogrid_protein_mapping_mouse.pkl', 'wb')
pickle.dump(protein_to_gene_mouse, output)
output.close()
