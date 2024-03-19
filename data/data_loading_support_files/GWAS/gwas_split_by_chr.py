# preprocess gwas v2d tsv file:
# fix break lines and split the whole file by chromosomes

import hashlib
# trying to capture the breakline problem described in the comments above


def line_appears_broken(row):
    return row[-1].startswith('"[') and not row[-1].endswith(']"')


def studies_variants_key(row):
    variant_id = build_variant_id(row[4], row[5], row[6], row[7])
    study_id = row[3]

    return hashlib.sha256((variant_id + '_' + study_id).encode()).hexdigest()


output_files = {}
for file in [str(i) for i in range(1, 23)] + ['X']:
    output_files[file] = open('v2d_' + file + '.tsv', 'w')

header = None
trying_to_complete_line = None
tagged_variants = {}

for record in open(filename, 'r'):
    if header is None:
        header = record.strip().split('\t')
        continue

    if trying_to_complete_line:
        record = trying_to_complete_line + record
        trying_to_complete_line = None

    row = record.strip().split('\t')

    if line_appears_broken(row):
        trying_to_complete_line = record.strip()
        continue

    # skip rows with no ontology terms
    if row[1] == 'NA' and row[2] == '':
        continue

    # a few rows are incomplete. Filling empty values with None
    row = row + ['NA'] * (len(header) - len(row))

    output_files[row[4]].write('\t'.join(row) + '\n')

for file in output_files.keys():
    output_files[file].close()
