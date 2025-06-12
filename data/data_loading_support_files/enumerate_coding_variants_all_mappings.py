import requests
import csv
import re
import pickle
import py2bit
# import CHR_MAP
# do sanity check on ref seq & codon

# same protein/transcript/gene for this CYP2C19 VAMP-seq (IGVFFI5890AHYL) dataset,
# hard-coded those fields for now, will get protein -> gene, transcript mapping from catalog api for Mutpred2 predictions
gene = 'CYP2C19'
chrom = 'chr10'
chrom_refseq = 'NC_000010.11'
transcript_id = 'ENST00000371321'
strand = '+'


def reverse_complement(seq):
    complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}
    # return the base itself if it's not in [A,C,G,T]
    return ''.join(complement.get(base, base) for base in reversed(seq))


def normalize_mutation(codon_ref, enumerate_mutation):
    '''
    Given codon changes, normalize the representation of the genetic variant by removing common nucleotides in ref and mutation.
    Returns:
        ref, alt (after removing common nucleotides), offset, variant type (SNV or delins)
    Example:
        >>> normalize_mutation('TAA', 'GCA')
        ('TA', 'GC', 0, 'delins')
    '''

    if len(codon_ref) != 3 or len(enumerate_mutation) != 3:
        raise ValueError('Codon has wrong length.')

    if codon_ref == enumerate_mutation:
        raise ValueError('Ref and alt codons are the same: ' +
                         codon_ref + enumerate_mutation)

    # first two nucleotides same
    if codon_ref[:2] == enumerate_mutation[:2]:
        return (codon_ref[2], enumerate_mutation[2], 2, 'SNV')

    # last two nucleotides same
    if codon_ref[1:] == enumerate_mutation[1:]:
        return (codon_ref[0], enumerate_mutation[0], 0, 'SNV')

    # first and last same
    if codon_ref[0] == enumerate_mutation[0] and codon_ref[2] == enumerate_mutation[2]:
        return (codon_ref[1], enumerate_mutation[1], 1, 'SNV')

    # first nucleotide same, and last nucleotide different (middle different)
    if codon_ref[0] == enumerate_mutation[0]:
        return (codon_ref[1:], enumerate_mutation[1:], 1, 'delins')

    # last nucleotide same, and first nucleotide different (middle different)
    if codon_ref[2] == enumerate_mutation[2]:
        return (codon_ref[:2], enumerate_mutation[:2], 0, 'delins')

    # None of the above (different, same, different; different, different, different;)-> return full codon
    return (codon_ref, enumerate_mutation, 0, 'delins')


def enumerate_coding_variant(hgvsp, gene, transcript_id, strand, chrom, chrom_refseq, exons_coordinates, seq_reader):
    '''
        Function for maping coding variant (from hgvsp id) to all possible genetic variants.
        Args:
            hgvsp (str): hgvsp representation of the coding variant, e.g. p.Glu415Lys or Glu415Lys or E415K
            strand (str)
            chrom (str)
            chrom_refseq (str)
            exon_coordinates (list)
            seq_reader

        Returns:
            A dict containing the following info on the coding variant and its mapped genetic variants:
                aa_pos,ref_pos, codon_ref, ref_aa, alt_aa, alt_seqs, hgvsc_ids, mutation_ids, hgvsg_ids, spdi_ids

        Example:
            Output of mapping results from ENSP00000360372.3:p.Glu415Lys
            ('415',94850009,'GAA','E','K',['AAA', 'AAG'],['c.1243G-A', 'c.1243_1245delinsAAG'],['CYP2C19_ENST00000371321_Glu415Lys_c.1243G-A','CYP2C19_ENST00000371321_Glu415Lys_c.1243_1245delinsAAG'],
             ['NC_000010.11:g.94850010G>A', 'NC_000010.11:g.94850010_94850012delinsAAG'],['NC_000010.11:94850009:G:A', 'NC_000010.11:94850009:GAA:AAG'])

    '''
    # aa mapping tables
    amino_table = {'S': ['TCA', 'TCC', 'TCG', 'TCT', 'AGC', 'AGT'],
                   'F': ['TTC', 'TTT'],
                   'L': ['TTA', 'TTG', 'CTA', 'CTC', 'CTG', 'CTT'],
                   'Y': ['TAC', 'TAT'],
                   '*': ['TAA', 'TAG', 'TGA'],
                   'C': ['TGC', 'TGT'],
                   'W': ['TGG'],
                   'P': ['CCA', 'CCC', 'CCG', 'CCT'],
                   'H': ['CAC', 'CAT'],
                   'Q': ['CAA', 'CAG'],
                   'R': ['CGA', 'CGC', 'CGG', 'CGT', 'AGA', 'AGG'],
                   'I': ['ATA', 'ATC', 'ATT'],
                   'M': ['ATG'],
                   'T': ['ACA', 'ACC', 'ACG', 'ACT'],
                   'N': ['AAC', 'AAT'],
                   'K': ['AAA', 'AAG'],
                   'V': ['GTA', 'GTC', 'GTG', 'GTT'],
                   'A': ['GCA', 'GCC', 'GCG', 'GCT'],
                   'D': ['GAC', 'GAT'],
                   'E': ['GAA', 'GAG'],
                   'G': ['GGA', 'GGC', 'GGG', 'GGT']}

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
    aa_table_rev = {'A': 'Ala',
                    'R': 'Arg',
                    'N': 'Asn',
                    'D': 'Asp',
                    'C': 'Cys',
                    'E': 'Glu',
                    'Q': 'Gln',
                    'G': 'Gly',
                    'H': 'His',
                    'I': 'Ile',
                    'L': 'Leu',
                    'K': 'Lys',
                    'M': 'Met',
                    'F': 'Phe',
                    'P': 'Pro',
                    'S': 'Ser',
                    'T': 'Thr',
                    'W': 'Trp',
                    'Y': 'Tyr',
                    'V': 'Val',
                    '*': 'Ter'}
    coding_variants_enumerated_ids = {}

    hgvsp = re.sub('p\.', '', hgvsp)
    matches = re.findall(r'^([A-Za-z]+)(\d+)([A-Za-z]+)', hgvsp)
    if not matches:
        print('invalid hgvsp id: ' + hgvsp)
        return
    aa_ref, aa_pos, aa_alt = matches[0]
    if aa_ref == aa_alt:
        print('Warning: ' + transcript_id + hgvsp +
              ' has same aa_ref and aa_alt, skipping.')
        return

    if len(aa_ref) == 1:
        if aa_ref in aa_table_rev and aa_alt in aa_table_rev:
            aa_ref = aa_table_rev[aa_ref]
            aa_alt = aa_table_rev[aa_alt]
        else:
            print('Warning: ' + transcript_id +
                  ' has invalid amino acid code ' + hgvsp)
            return
    else:
        if aa_ref not in aa_table or aa_alt not in aa_table:
            print('Warning: ' + transcript_id +
                  ' has invalid amino acid code ' + hgvsp)
            return
    hgvsp_id = 'p.' + aa_ref + aa_pos + aa_alt
    c_start = (int(aa_pos)-1)*3 + 1  # transcript start position; 1-based
    splice = False

    # genome start position
    if abs(exons_coordinates[c_start - 1] - exons_coordinates[c_start + 1]) != 2:
        # here includes a splicing site, exon cooridnates are not contiguous integers
        splice = True

    g_start = exons_coordinates[c_start - 1]  # 0-based index; 0-based
    if strand == '-':
        g_start = g_start - 2
    # get ref seq from genome
    if splice:
        if strand == '+':
            codon_ref = ''.join([seq_reader.sequence(
                chrom, exons_coordinates[i], exons_coordinates[i]+1) for i in range(c_start - 1, c_start+2)])
        else:
            codon_ref = ''.join([seq_reader.sequence(
                chrom, exons_coordinates[i], exons_coordinates[i]+1) for i in range(c_start+1, c_start-2, -1)])
            codon_ref = reverse_complement(codon_ref)
    else:
        # from reference genome; [inclusive, exclusive)
        codon_ref = seq_reader.sequence(chrom, g_start, g_start + 3)
        if strand == '-':
            # reverse complement for '-' strand
            codon_ref = reverse_complement(codon_ref)

    # sanity check on aa ref VS condon ref from genome sequence file
    aa_ref_dna_list = amino_table[aa_table[aa_ref]]
    if codon_ref not in aa_ref_dna_list:
        print('reference not matching: ' + aa_ref + aa_pos + transcript_id)
        return

    ref_aa = aa_table[aa_ref]  # one letter aa
    alt_aa = aa_table[aa_alt]  # one letter aa
    # keep all possible genomic variants here
    alt_codons = amino_table[alt_aa]
    hgvsc_ids = []
    mutation_ids = []
    hgvsg_ids = []
    spdi_ids = []
    codon_positions = []
    for mutation in alt_codons:
        # remove common nucleotides from ref & alt seqs
        ref, alt, offset, variant_type = normalize_mutation(
            codon_ref, mutation)
        codon_positions.append(offset + 1)
        # 0-based; the first pos on ref
        ref_pos = exons_coordinates[c_start - 2 + offset + len(
            alt)] if strand == '-' else exons_coordinates[c_start - 1 + offset]
        g_alt = reverse_complement(alt) if strand == '-' else alt
        g_ref = reverse_complement(ref) if strand == '-' else ref
        c_pos = c_start + offset  # 1-based
        if variant_type == 'SNV':
            hgvsc = 'c.' + str(c_pos) + ref + '-' + alt  # e.g. c.1153C-G
            hgvsc_ids.append(hgvsc)
            # id used in catalog for coding variants
            mutation_ids.append(gene + '_' + transcript_id +
                                '_p.' + hgvsp + '_' + hgvsc)
            # e.g. NC_000001.11:g.10007T>C
            hgvsg_ids.append(chrom_refseq + ':g.' +
                             str(ref_pos + 1) + g_ref + '>' + g_alt)
            # e.g. NC_000001.11:10006:T:C
            spdi_ids.append(chrom_refseq + ':' +
                            str(ref_pos) + ':' + g_ref + ':' + g_alt)
        else:
            # e.g. c.307_309delinsATT
            hgvsc = 'c.' + str(c_pos) + '_' + str(c_pos +
                                                  len(alt) - 1) + 'delins' + alt
            hgvsc_ids.append(hgvsc)
            # id used in catalog for coding variants
            mutation_ids.append(gene + '_' + transcript_id +
                                '_p.' + hgvsp + '_' + hgvsc)
            hgvsg_ids.append(chrom_refseq + ':g.' + str(ref_pos + 1) + '_' + str(ref_pos + len(
                g_alt)) + 'delins' + g_alt)  # e.g. NC_000010.11:g.94775196_94775198delinsATT
            # e.g. NC_000010.11:94775195:GC:AT
            # didn't do any normalization on spdi, might want to add
            spdi_ids.append(chrom_refseq + ':' +
                            str(ref_pos) + ':' + g_ref + ':' + g_alt)
    coding_variants_enumerated_ids = {
        'aa_pos': aa_pos,
        'ref_pos': ref_pos,
        'codon_ref': codon_ref,
        'ref_aa': ref_aa,
        'alt_aa': alt_aa,
        'alt_codons': alt_codons,
        'codon_positions': codon_positions,
        'hgvsc_ids': hgvsc_ids,
        'hgvsp_id': hgvsp_id,
        'hgvsg_ids': hgvsg_ids,
        'mutation_ids': mutation_ids,
        'spdi_ids': spdi_ids
    }
    return coding_variants_enumerated_ids


def main():
    # upload to s3
    seq_reader = py2bit.open('hg38.2bit')
    query_url = 'https://api-dev.catalog.igvf.org/api/genes-structure?transcript_id=' + \
        transcript_id + '&organism=Homo%20sapiens&limit=1000'
    responses = requests.get(query_url).json()

    # get gene structure from KG; the exon ranges are stored in bed format
    exons_coordinates = []
    for structure in responses:
        if structure['type'] == 'CDS':
            if strand == '+':
                exons_coordinates.extend(
                    list(range(structure['start'], structure['end'])))
            else:  # on reverse strand
                exons_coordinates.extend(
                    list(reversed(range(structure['start'], structure['end']))))

    coding_variant_id_enumerated = dict()

    outfile = open('VAMP_coding_variants_mappings.tsv', 'w')
    outfile.write('\t'.join(['hgvsp', 'hgvsg', 'spdi',
                  'coding_variant_catalog_id']) + '\n')
    with open('CYP2C19_DMS_scores.csv') as f:
        next(f)
        f_csv = csv.reader(f)
        for row in f_csv:
            hgvsp = row[0].split(':')[1]  # e.g. p.Glu415Lys
            hgvsp = re.sub('p\.', '', hgvsp)
            matches = re.findall(r'^([A-Za-z]+)(\d+)([A-Za-z]+)', hgvsp)
            if not matches:
                print('invalid hgvsp id: ' + hgvsp)
                continue
            try:
                coding_variant_mapped = enumerate_coding_variant(
                    hgvsp, gene, transcript_id, strand, chrom, chrom_refseq, exons_coordinates, seq_reader)
                coding_variant_id_enumerated[row[0]] = dict()
                for field, value in coding_variant_mapped.items():
                    coding_variant_id_enumerated[row[0]][field] = value
                # write mapping results to a table
                outfile.write('\t'.join([row[0], ','.join(coding_variant_id_enumerated[row[0]]['hgvsg_ids']), ','.join(
                    coding_variant_id_enumerated[row[0]]['spdi_ids']), ','.join(coding_variant_id_enumerated[row[0]]['mutation_ids'])]) + '\n')
            except ValueError:
                continue

    outfile.close()
    # also save mapping dict to a pkl file
    output = open('VAMP_coding_variants_enumerated_mutation_ids.pkl', 'wb')
    pickle.dump(coding_variant_id_enumerated, output)
    output.close()


if __name__ == '__main__':
    main()
