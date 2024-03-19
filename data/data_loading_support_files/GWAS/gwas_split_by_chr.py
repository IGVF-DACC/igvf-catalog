# preprocess gwas v2d tsv file:
# fix break lines and split the whole file by chromosomes, output files under samples/gwas_v2d_split_chr/

# trying to capture the breakline problem described in the comments above
def line_appears_broken(row):
    return row[-1].startswith('"[') and not row[-1].endswith(']"')


output_files = {}
for file in [str(i) for i in range(1, 23)] + ['X']:
    output_files[file] = open(
        '../../samples/gwas_v2d_split_chr/' + file + '.tsv', 'w')

header = None
trying_to_complete_line = None
tagged_variants = {}

filename = '../../samples/gwas_v2d_igvf.tsv'
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
