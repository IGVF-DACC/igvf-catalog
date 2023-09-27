import requests
import csv
import pickle

# pull binding regions info from api for each complex (which is not available from the tab file downloaded from the portal).


def get_binding_regions(complex_id):
    url = 'https://www.ebi.ac.uk/intact/complex-ws/complex/' + complex_id
    complex_json = requests.get(url).json()
    complex_dict = dict()

    for protein in complex_json['participants']:
        protein_id = protein['identifier']
        complex_dict[protein_id] = []

        for linked_feature in protein['linkedFeatures']:
            complex_dict[protein_id].append(
                {'participantId': linked_feature['participantId'], 'ranges': linked_feature['ranges']})

    return complex_dict


complex_dict_all = dict()
with open('9606.tsv', 'r') as complex_file:
    complex_tsv = csv.reader(complex_file, delimiter='\t')
    next(complex_tsv)
    for complex_row in complex_tsv:
        skip_flag = None
        complex_ac = complex_row[0]

        molecules = complex_row[4].split('|')
        for molecule in molecules:
            if molecule.startswith('CHEBI:') or molecule.startswith('URS'):
                skip_flag = 1

        # skip lines containing chemicals from CHEBI or RNAs from RNACentral
        # i.e. only load complexes where all participants have uniprot protein ids
        if skip_flag is not None:
            continue

        complex_dict_all[complex_ac] = get_binding_regions(complex_ac)

# save the whole dict to a pkl file
output = open('EBI_complex_linkedFeatures.pkl', 'wb')
pickle.dump(complex_dict_all, output)
