import pickle
import requests
import csv
import re

import py2bit
# need 2bit file for hg38 seq
seq_reader = py2bit.open('hg38.2bit')

# load the mapping dict generated before, with existing coding variants from dbSNFP
coding_variant_id_file = open('VAMP_coding_variants_ids.pkl', 'rb')
coding_variant_id = pickle.load(coding_variant_id_file)

# same protein/transcript/gene for this CYP2C19 VAMP-seq (IGVFFI5890AHYL) dataset,
# hard-coded those fields for now
gene = 'CYP2C19'
chrom = 'chr10'
chrom_refseq = 'NC_000010.11'
transcript_id = 'ENST00000371321'
strand = '+'
query_url = 'https://api-dev.catalog.igvf.org/api/genes-structure?transcript_id=' + \
    transcript_id + '&organism=Homo%20sapiens&limit=1000'
responses = requests.get(query_url).json()

# get gene structure from KG
exons_coordinates = []
for structure in responses:
    if structure['type'] == 'CDS':
        if strand == '+':
            # print (structure['exon_number'])
            exons_coordinates.extend(
                list(range(structure['start'], structure['end'])))
        else:  # on reverse strand
            exons_coordinates.extend(
                list(reversed(range(structure['start'], structure['end']))))

aa_table = {
    'Ala': 'A',
    'Arg': 'R',
    'Asn': 'N',
    'Asp': 'D',
    'Cys': 'C',
    'Glu': 'E',
    'Gln': 'Q',
    'Gly': 'G',
    'His': 'H',
    'Ile': 'I',
    'Leu': 'L',
    'Lys': 'K',
    'Met': 'M',
    'Phe': 'F',
    'Pro': 'P',
    'Ser': 'S',
    'Thr': 'T',
    'Trp': 'W',
    'Tyr': 'Y',
    'Val': 'V',
    'Ter': '*'
}

# https://gist.github.com/juanfal/09d7fb53bd367742127e17284b9c47bf
codon_table = {
    'TCA': 'S',    # Serina
    'TCC': 'S',    # Serina
    'TCG': 'S',    # Serina
    'TCT': 'S',    # Serina
    'TTC': 'F',    # Fenilalanina
    'TTT': 'F',    # Fenilalanina
    'TTA': 'L',    # Leucina
    'TTG': 'L',    # Leucina
    'TAC': 'Y',    # Tirosina
    'TAT': 'Y',    # Tirosina
    'TAA': '*',    # Stop
    'TAG': '*',    # Stop
    'TGC': 'C',    # Cisteina
    'TGT': 'C',    # Cisteina
    'TGA': '*',    # Stop
    'TGG': 'W',    # Triptofano
    'CTA': 'L',    # Leucina
    'CTC': 'L',    # Leucina
    'CTG': 'L',    # Leucina
    'CTT': 'L',    # Leucina
    'CCA': 'P',    # Prolina
    'CCC': 'P',    # Prolina
    'CCG': 'P',    # Prolina
    'CCT': 'P',    # Prolina
    'CAC': 'H',    # Histidina
    'CAT': 'H',    # Histidina
    'CAA': 'Q',    # Glutamina
    'CAG': 'Q',    # Glutamina
    'CGA': 'R',    # Arginina
    'CGC': 'R',    # Arginina
    'CGG': 'R',    # Arginina
    'CGT': 'R',    # Arginina
    'ATA': 'I',    # Isoleucina
    'ATC': 'I',    # Isoleucina
    'ATT': 'I',    # Isoleucina
    'ATG': 'M',    # Methionina
    'ACA': 'T',    # Treonina
    'ACC': 'T',    # Treonina
    'ACG': 'T',    # Treonina
    'ACT': 'T',    # Treonina
    'AAC': 'N',    # Asparagina
    'AAT': 'N',    # Asparagina
    'AAA': 'K',    # Lisina
    'AAG': 'K',    # Lisina
    'AGC': 'S',    # Serina
    'AGT': 'S',    # Serina
    'AGA': 'R',    # Arginina
    'AGG': 'R',    # Arginina
    'GTA': 'V',    # Valina
    'GTC': 'V',    # Valina
    'GTG': 'V',    # Valina
    'GTT': 'V',    # Valina
    'GCA': 'A',    # Alanina
    'GCC': 'A',    # Alanina
    'GCG': 'A',    # Alanina
    'GCT': 'A',    # Alanina
    'GAC': 'D',    # Acido Aspartico
    'GAT': 'D',    # Acido Aspartico
    'GAA': 'E',    # Acido Glutamico
    'GAG': 'E',    # Acido Glutamico
    'GGA': 'G',    # Glicina
    'GGC': 'G',    # Glicina
    'GGG': 'G',    # Glicina
    'GGT': 'G'     # Glicina
}

# generate a reversed table
amino_table = {}
for codon, aa in codon_table.items():
    if aa in amino_table:
        amino_table[aa].append(codon)
    else:
        amino_table[aa] = [codon]


def hamming_distance(s1, s2):
    if len(s1) != len(s2):
        raise ValueError('Strand lengths are not equal!')
    return sum(ch1 != ch2 for ch1, ch2 in zip(s1, s2))


complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}


def reverse_complement(seq):
    # return the base itself if it's not in [A,C,G,T]
    return ''.join(complement.get(base, base) for base in reversed(seq))


def enumerate_mutations(aa_ref, aa_pos, aa_alt, codon_ref, strand='+'):
    aa_alt_dna_list = amino_table[aa_table[aa_alt]]

    distances = []
    enumerated_mutations = []
    # only keep alt seq(s) with the fewest mutations compared to ref sequence
    for aa_alt_dna in aa_alt_dna_list:
        distances.append(hamming_distance(codon_ref, aa_alt_dna))
    min_distance = min(distances)
    min_indices = [index for index, value in enumerate(
        distances) if value == min_distance]
    enumerated_mutations = [aa_alt_dna_list[i] for i in min_indices]
    if strand == '-':
        enumerated_mutations = [reverse_complement(
            seq) for seq in enumberated_mutations]
    return enumerated_mutations


coding_variant_id_enumerated = dict()
with open('CYP2C19_DMS_scores.csv') as f:
    next(f)
    f_csv = csv.reader(f)
    for row in f_csv:
        if row[0] in coding_variant_id:  # skip those already mapped to existing variants
            continue
        hgvsp = row[0].split(':')[1]  # e.g. p.Glu415Lys
        if hgvsp.startswith('p'):
            matches = re.findall(
                r'^([A-Za-z]+)(\d+)([A-Za-z]+)', hgvsp.split('.')[1])
            if not matches:
                print('invalid hgvsp id in: ' + row[0])
            else:
                # store all needed properties in a dict
                coding_variant_id_enumerated[row[0]] = dict()

                aa_ref, aa_pos, aa_alt = matches[0]
                if strand == '+':
                    # transcript start position; 1-based
                    c_start = (int(aa_pos)-1)*3 + 1
                else:
                    c_start = (int(aa_pos)-1)*3 - 2  # check!!
                # genome start position
                # 0-based index; 0-based
                g_start = exons_coordinates[c_start - 1]

                # get ref seq from genome
                # from reference genome; [inclusive, exclusive)
                codon_ref = seq_reader.sequence(chrom, g_start, g_start + 3)
                if strand != '+':
                    # reverse complement for '-' strand
                    codon_ref = reverse_complement(codon_ref)

                coding_variant_id_enumerated[row[0]]['hgvsp'] = hgvsp
                coding_variant_id_enumerated[row[0]]['aa_pos'] = aa_pos
                coding_variant_id_enumerated[row[0]]['refcodon'] = codon_ref
                coding_variant_id_enumerated[row[0]
                                             ]['ref_aa'] = aa_table[aa_ref]
                coding_variant_id_enumerated[row[0]
                                             ]['alt_aa'] = aa_table[aa_alt]
                coding_variant_id_enumerated[row[0]
                                             ]['ref_pos'] = g_start  # 0-based

                # get all possible enumerated mutations with the given aa_ref to aa_alt, only record those with min substitutions
                # the enumerated mutations will all be represented as 3-base substitutions (delinsXXX)
                enumerated_mutations = enumerate_mutations(
                    aa_ref, aa_pos, aa_alt, codon_ref, strand)
                hgvsc_ids = ['c.' + str(c_start) + '_' + str(c_start + 2) +
                             'delins' + mutation for mutation in enumerated_mutations]
                coding_variant_id_enumerated[row[0]
                                             ]['alt_seqs'] = enumerated_mutations
                coding_variant_id_enumerated[row[0]]['hgvsc_ids'] = hgvsc_ids
                coding_variant_id_enumerated[row[0]]['mutation_ids'] = [
                    gene + '_' + transcript_id + '_' + hgvsp + '_' + hgvsc for hgvsc in hgvsc_ids]
                coding_variant_id_enumerated[row[0]]['hgvsg_ids'] = [chrom_refseq + ':g.' + str(
                    g_start + 1) + '_' + str(g_start + 3) + 'delins' + mutation for mutation in enumerated_mutations]
                coding_variant_id_enumerated[row[0]]['spdi_ids'] = [chrom_refseq + ':g.' + str(
                    g_start) + ':' + codon_ref + ':' + mutation for mutation in enumerated_mutations]

output = open('VAMP_coding_variants_enumerated_mutation_ids.pkl', 'wb')
pickle.dump(coding_variant_id_enumerated, output)
output.close()
