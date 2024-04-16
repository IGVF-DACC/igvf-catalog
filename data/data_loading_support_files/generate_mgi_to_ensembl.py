# export the "proteins" collection using arangoexport cmd into "proteins.jsonl"

import json
import pickle

mgi_to_ensembl = {}
for protein in open('proteins.jsonl', 'r'):
    pt = json.loads(protein)

    for ref in pt['dbxrefs']:
        if ref['name'] == 'MGI':
            mgi_to_ensembl[ref['id']] = pt['_key']
            break

pickle.dump(mgi_to_ensembl, open('mgi_to_ensembl.pkl', 'wb'))
