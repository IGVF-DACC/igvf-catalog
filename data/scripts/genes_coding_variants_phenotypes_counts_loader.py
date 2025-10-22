# Script to create genes_coding_variants_phenotypes_counts collection in ArangoDB
# It aggregates variant scores from different sources for each gene.
# The list of genes is read from a file where each line contains a JSON array with gene ID and gene name.

# Usage:
# 1. Ensure you have the ArangoDB Python driver installed: pip install python-arango
# 2. Create the input file with gene IDs and names using arangoexport as described in the comments.
# 3. Update the DB connection parameters as needed.
# 4. Run the script: python genes_coding_variants_phenotypes_counts_loader.py

from arango import ArangoClient
from arango.http import DefaultHTTPClient
import json

DB_NAME = 'igvf'
COLLECTION_NAME = 'genes_coding_variants_phenotypes_counts'
ARANGODB_URL = 'http://localhost:8529'
USERNAME = 'username'
PASSWORD = 'password'

GENES = 'list_of_gene_ids_per_line.txt'
# use arangoexport to create this file from genes collection:
# $ arangoexport --custom-query "FOR g in genes RETURN g._key" --output-file list_of_gene_ids_per_line.txt --server.database igvf --server.username username

# example of genes file:
# "ENSG00000290825"
# "ENSG00000223972"
# "ENSG00000227232"
# "ENSG00000278267"
# "ENSG00000243485"
# "ENSG00000284332"
# "ENSG00000237613"

client = ArangoClient(http_client=DefaultHTTPClient(request_timeout=999999))
db = client.db(DB_NAME, username=USERNAME, password=PASSWORD)
collection = db.collection(COLLECTION_NAME)

with open(GENES, 'r') as file:
    i = 1
    for line in file:
        key = line.strip()[1:-1]
        if not key:
            continue  # skip empty lines
        i += 1

        is_there = db.aql.execute(
            'FOR g in ' + COLLECTION_NAME + ' FILTER g._key == \''+key+'\' RETURN 1')
        results = [doc for doc in is_there]
        if len(results) > 0 and results[0] == 1:
            continue

        print(i)
        query = """
                LET gene_name = DOCUMENT(@id).name
                LET codingVariants = ( FOR record IN coding_variants FILTER record.gene_name == gene_name RETURN DISTINCT record._id )
                LET sge = ( FOR v IN variants_phenotypes_coding_variants FILTER v._to IN codingVariants COLLECT fileset_id = v.files_filesets WITH COUNT INTO count RETURN { method: 'SGE', count: count } )
                LET others = ( FOR phenoEdges IN coding_variants_phenotypes FILTER phenoEdges._from IN codingVariants COLLECT src = phenoEdges.method WITH COUNT INTO count RETURN { method: src, count: count } )
                RETURN {
                  '_key': @key,
                  'counts':  UNION(sge, others)
                }
        """

        try:
            cursor = db.aql.execute(
                query, bind_vars={'id': 'genes/' + key, 'key': key})
            results = [doc for doc in cursor]
            collection.insert(results[0])
        except:
            print('Failed ' + key + ' \n')
