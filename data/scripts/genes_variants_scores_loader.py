# Script to create genes_variants_scores collection in ArangoDB
# It aggregates variant scores from different sources for each gene.
# The list of genes is read from a file where each line contains a JSON array with gene ID and gene name.

# Usage:
# 1. Ensure you have the ArangoDB Python driver installed: pip install python-arango
# 2. Create the input file with gene IDs and names using arangoexport as described in the comments.
# 3. Update the DB connection parameters as needed.
# 4. Run the script: python genes_variants_scores_loader.py

from arango import ArangoClient
from arango.http import DefaultHTTPClient
import json

DB_NAME = 'igvf'
COLLECTION_NAME = 'genes_variants_scores'
ARANGODB_URL = 'http://localhost:8529'
USERNAME = 'username'
PASSWORD = 'password'

GENES = 'list_of_gene_ids_and_names_per_line.txt'
# use arangoexport to create this file from genes collection:
# $ arangoexport --custom-query "FOR g in genes RETURN [g._key, g.gene_name]" --output-file list_of_gene_ids_and_names_per_line.txt --server.database igvf --server.username username

# example of genes file:
# ["ENSG00000290825","DDX11L2"]
# ["ENSG00000223972","DDX11L1"]
# ["ENSG00000227232","WASH7P"]
# ["ENSG00000278267","MIR6859-1"]
# ["ENSG00000243485","MIR1302-2HG"]
# ["ENSG00000284332","MIR1302-2"]
# ["ENSG00000237613","FAM138A"]

client = ArangoClient(http_client=DefaultHTTPClient(request_timeout=999999))
db = client.db(DB_NAME, username=USERNAME, password=PASSWORD)
collection = db.collection(COLLECTION_NAME)

with open(GENES, 'r') as file:
    i = 1
    for line in file:
        key = line.strip()
        if not key:
            continue  # skip empty lines
        data = json.loads(key)
        i += 1

        # BRCA2 times out because of the huge number of coding variants associated with it. It must be handled separately.
        if data[1] == 'BRCA2':
            print('Skipping BRCA2 for now...')
            continue

        is_there = db.aql.execute(
            'FOR g in genes_variants_scores FILTER g._key == \''+data[0]+'\' RETURN 1')
        results = [doc for doc in is_there]
        if len(results) > 0 and results[0] == 1:
            continue

        query = """
                LET codingVariants = (
                    FOR cv IN coding_variants
                    FILTER cv.gene_name == @name
                    RETURN cv._id
                )

                LET variantMap = (
                    FOR vcv IN variants_coding_variants
                    FILTER vcv._to IN codingVariants
                    RETURN { codingVariant: vcv._to, variantId: vcv._from }
                )

                LET variantIds = UNIQUE(variantMap[*].variantId)

                LET variantData = (
                    FOR v IN variants
                    FILTER v._id IN variantIds
                    RETURN {
                        [v._id]: {_id: v._key, 'chr': v['chr'], 'pos': v['pos'], 'rsid': v['rsid'], 'ref': v['ref'], 'alt': v['alt'], 'spdi': v['spdi'], 'hgvs': v['hgvs']}
                    }
                )

                LET variantDict = MERGE(variantData)

                LET variantLookup = (
                    FOR map IN variantMap
                    RETURN { [map.codingVariant]: variantDict[map.variantId] }
                )

                LET variantByCodingVariant = MERGE(variantLookup)

                LET sgeResults = (
                    FOR v IN variants_phenotypes_coding_variants
                    FILTER v._to IN codingVariants
                    LET phenotype = DOCUMENT(v._from)
                    LET fileset = DOCUMENT(v.files_filesets)
                    RETURN {
                        variant: variantByCodingVariant[v._to],
                        score: phenotype.score,
                        source: fileset.preferred_assay_titles[0]
                    }
                )

                LET otherResults = (
                    FOR p IN coding_variants_phenotypes
                    FILTER p._from IN codingVariants
                    RETURN {
                        variant: variantByCodingVariant[p._from],
                        score: p.pathogenicity_score OR p.esm_1v_score OR p.score,
                        source: p.method
                    }
                )

                RETURN {
                    '_key': @key,
                    'variant_scores': (
                        FOR doc IN UNION(sgeResults, otherResults)
                        COLLECT variant = doc.variant INTO grouped = doc
                        LET maxScore = MAX(grouped[*].score)
                        SORT maxScore DESC
                        RETURN {
                            variant,
                            scores: grouped[* RETURN { source: CURRENT.source, score: CURRENT.score }]
                        }
                    )
                }
        """

        try:
            cursor = db.aql.execute(
                query, bind_vars={'key': data[0], 'name': data[1]})
            results = [doc for doc in cursor]
            collection.insert(results[0])
            print(i)
        except:
            print('Failed ' + data[0] + ' \n')
