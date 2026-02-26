# Script to create genes_coding_variants_scores collection in ArangoDB
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
COLLECTION_NAME = 'genes_coding_variants_scores'
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

        # BRCA2, TTN, and NEB time out because of the huge number of coding variants associated with it.
        # It must be handled separately. Check comments at the end of this file.
        if data[1] in ['BRCA2', 'TTN', 'NEB']:
            print('Skipping ' + data[1] + ' for now...')
            continue

        is_there = db.aql.execute(
            'FOR g in ' + COLLECTION_NAME + ' FILTER g._key == \''+data[0]+'\' RETURN 1')
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
                    [v._id]: {_id: v._key, 'chr': v['chr'], 'pos': v['pos'], 'rsid': v['rsid'], 'ref': v['ref'], 'alt': v['alt'], 'spdi': v['spdi'], 'hgvs': v['hgvs'], 'ca_id': v['ca_id']}
                }
                )
                LET variantDict = MERGE(variantData)
                LET variantLookup = (
                FOR map IN variantMap
                    RETURN { [map.codingVariant]: variantDict[map.variantId] }
                )
                LET variantByCodingVariant = MERGE(variantLookup)
                LET results = (
                    FOR p IN coding_variants_phenotypes
                    FILTER p._from IN codingVariants
                    RETURN {
                        codingVariant: p._from,
                        variant: variantByCodingVariant[p._from],
                        score: p.pathogenicity_score OR p.esm_1v_score OR p.score,
                        method: p.method,
                        source_url: p.source_url
                    }
                )

                LET allResults = (
                    FOR doc IN results
                    LET cvDoc = DOCUMENT(doc.codingVariant)
                    RETURN MERGE(doc, {
                        cvDoc: cvDoc,
                        protein_change: cvDoc.hgvsp
                    })
                )

                LET variantWithScores = (
                    FOR result IN allResults
                    COLLECT variant = result.variant INTO variantGroup = result
                    RETURN {
                        variant: variant,
                        scores: variantGroup[* RETURN { method: CURRENT.method, score: CURRENT.score, source_url: CURRENT.source_url }],
                        maxScore: MAX(variantGroup[*].score),
                        protein_change: FIRST(variantGroup).protein_change,
                        cvDoc: FIRST(variantGroup).cvDoc
                    }
                )

                RETURN {
                    '_key': @key,
                    'variant_scores': (
                        FOR vws IN variantWithScores
                        COLLECT protein_change = vws.protein_change INTO grouped = vws
                        LET maxScore = MAX(grouped[*].maxScore)
                        SORT maxScore DESC
                        LIMIT ${page as number * limit}, ${limit}
                        LET firstCvDoc = FIRST(grouped).cvDoc
                        RETURN {
                            protein_change: {
                                coding_variant_id: firstCvDoc._key,
                                protein_id: firstCvDoc.protein_id,
                                protein_name: firstCvDoc.protein_name,
                                transcript_id: firstCvDoc.transcript_id,
                                hgvsp: protein_change,
                                aapos: firstCvDoc.aapos,
                                ref: firstCvDoc.ref,
                                alt: firstCvDoc.alt
                            },
                            variants: grouped[* RETURN {
                                variant: CURRENT.variant,
                                scores: CURRENT.scores
                            }]
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


# The query above times out for BRCA2 (ENSG00000139618), TTN (ENSG00000155657), and NEB (ENSG00000183091) due to the large number of coding variants.
# Below are the steps to handle BRCA2 separately. Similar steps can be followed for TTN and NEB.

# Step 1: Run this query using arangoexport and output the file to brca2_variants_scores.json:

# FOR cv IN coding_variants
# FILTER cv.gene_name == 'BRCA2'
# RETURN {
#   variant: (
#     FOR v IN variants
#     FILTER v._id == (
#     FOR vcv IN variants_coding_variants
#     FILTER vcv._to == cv._id
#     RETURN vcv._from
#     )[0]
#     RETURN {
#         _id: v._key, 'chr': v['chr'], 'pos': v['pos'], 'rsid': v['rsid'], 'ref': v['ref'], 'alt': v['alt'], 'spdi': v['spdi'], 'hgvs': v['hgvs']
#     }
#   )[0],
#   protein_change: {
#     coding_variant_id: cv._key,
#     protein_id: cv.protein_id,
#     protein_name: cv.protein_name,
#     transcript_id: cv.transcript_id,
#     hgvsp: cv.hgvsp,
#     aapos: cv.aapos,
#     ref: cv.ref,
#     alt: cv.alt
#   },
#   scores:FLATTEN([
#     (
#        FOR v IN variants_phenotypes_coding_variants
#        FILTER v._to == cv._id
#        LET phenotype = DOCUMENT(v._from)
#        LET fileset = DOCUMENT(v.files_filesets)
#        RETURN {
#          score: phenotype.score,
#          method: fileset.preferred_assay_titles[0],
#          source_url: v.source_url
#        }
#     ),
#     (
#        FOR p IN coding_variants_phenotypes
#        FILTER p._from == cv._id
#        RETURN {
#          score: p.pathogenicity_score OR p.esm_1v_score OR p.score,
#          method: p.method,
#          source_url: p.source_url
#        }
#     )
#   ])
# }

# Step 2: Process the output file (e.g., brca2_variants_scores.json) to create the final document for BRCA2 and insert it into the collection.

# Processing script (filters out empty scores and sorts by max score):

# import json
# from arango import ArangoClient
# from arango.http import DefaultHTTPClient
# input_file = "brca2_variants_scores.json"
# gene_key = "ENSG00000139618"
# records = []
# with open(input_file, "r") as f:
#     for line in f:
#         line = line.strip()
#         obj = json.loads(line)
#         scores = obj.get("scores", [])
#         if len(scores) == 0:
#             continue
#         max_score = max((s.get("score", 0) for s in scores), default=0)
#         records.append((max_score, obj))
# records.sort(key=lambda x: x[0], reverse=True)
# records = [r[1] for r in records]
# client = ArangoClient(http_client=DefaultHTTPClient(request_timeout=999999))
# db = client.db('igvf', username='USERNAME', password='PASSWORD')
# collection = db.collection('genes_coding_variants_scores')
# doc = {
#     '_key': gene_key,
#     'variant_scores': records
# }
# collection.insert(doc)
