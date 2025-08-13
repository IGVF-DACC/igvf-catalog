# Creates an aggregation of variants per allele frequency divided by ancestries
# The aggregation combines the counts of frequencies in intervals of increment 0.05 from 0 to 1.
# The input is a sorted csv file with columns: frequency value, variants count, ancestry

INPUT_FREQUENCIES = 'variants_af_sorted.csv'
OUTPUT_AGGREGATION = 'variants_af_aggregation.csv'
ANCESTRIES = ['ami', 'asj', 'fin', 'oth', 'afr', 'amr', 'eas', 'nfe', 'sas']
START = 0.0
END = 1.0
INCREMENT = 0.05

afs = {}

current = START
next = round(current + INCREMENT, 3)
for line in open(INPUT_FREQUENCIES, 'r'):
    freq, count, ancestry = line.split(',')

    try:
        freq = float(freq)
    except:
        continue

    count = int(count)
    ancestry = ancestry.strip().replace('"', '')

    if freq > next:
        current = next
        next = round(next + INCREMENT, 3)

    if current not in afs:
        afs[current] = {}
        for anc in ANCESTRIES:
            afs[current][anc] = 0

    afs[current][ancestry] += count

with open(OUTPUT_AGGREGATION, 'w') as output:
    header = ['>freq'] + ANCESTRIES
    output.write(','.join(header))
    output.write('\n')

    for freq in afs.keys():
        line = [str(freq)]

        for ancestry in ANCESTRIES:
            line += [str(afs[freq][ancestry])]

        output.write(','.join(line))
        output.write('\n')
