import csv
import hashlib
import argparse
from ga4gh.vrs.extras.translator import Translator, ValidationError
from ga4gh.vrs.dataproxy import create_dataproxy
from ga4gh.vrs import models
from biocommons.seqrepo import SeqRepo


import datetime

# There are several type of variants represented by HGVS: https://varnomen.hgvs.org/recommendations/DNA/variant/substitution/
# Substitution:a sequence change where, compared to a reference sequence, one nucleotide is replaced by one other nucleotide.
# example: NC_000023.10:g.33038255C>A
# Deletion: a sequence change where, compared to a reference sequence, one or more nucleotides are not present (deleted).
# example: NC_000023.11:g.33344591del(one nucleotide deletion), NC_000023.11:g.33344590_33344592del(several nucleotides deletion)
# Insertion: a sequence change where, compared to the reference sequence, one or more nucleotides are inserted and where the insertion is not a copy of a sequence immediately 5'
# example: NC_000023.10:g.32867861_32867862insT, NC_000023.10:g.32862923_32862924insCCT
# Duplication: a sequence change where, compared to a reference sequence, a copy of one or more nucleotides are inserted directly 3' of the original copy of that sequence.
# example: NC_000023.11:g.32343183dup(one nucleotide dup), NC_000023.11:g.33211290_33211293dup(several nucleotides dup)
# Deletion-insertion (delins):a sequence change where, compared to a reference sequence, one or more nucleotides are replaced by one or more other nucleotides and which is not a substitution, inversion or conversion.
# example: NC_000023.11:g.32386323delinsGA, NC_000021.9:g.5221743_5221745delinsGAT
# Inversion: a sequence change where, compared to a reference sequence, more than one nucleotide replacing the original sequence are the reverse complement of the original sequence.
# example: NC_000023.10:g.32361330_32361333inv

# when validating HGVS using API here: https://api.ncbi.nlm.nih.gov/variation/v0/#/HGVS/get_hgvs__hgvs__contextuals, using insertion for dup and using delins for inversion are also valid.
# So we will just use Substitution, Deletion, Insertion and Deletion-insertion for HGVS.

CHR_MAP = {
    'GRCh38': {
        '1': 'NC_000001.11',
        '2': 'NC_000002.12',
        '3': 'NC_000003.12',
        '4': 'NC_000004.12',
        '5': 'NC_000005.10',
        '6': 'NC_000006.12',
        '7': 'NC_000007.14',
        '8': 'NC_000008.11',
        '9': 'NC_000009.12',
        '10': 'NC_000010.11',
        '11': 'NC_000011.10',
        '12': 'NC_000012.12',
        '13': 'NC_000013.11',
        '14': 'NC_000014.9',
        '15': 'NC_000015.10',
        '16': 'NC_000016.10',
        '17': 'NC_000017.11',
        '18': 'NC_000018.10',
        '19': 'NC_000019.10',
        '20': 'NC_000020.11',
        '21': 'NC_000021.9',
        '22': 'NC_000022.11',
        'X': 'NC_000023.11',
        'Y': 'NC_000024.10'
    },
    'GRCm39': {
        '1': 'NC_000067.7',
        '2': 'NC_000068.8',
        '3': 'NC_000069.7',
        '4': 'NC_000070.7',
        '5': 'NC_000071.7',
        '6': 'NC_000072.7',
        '7': 'NC_000073.7',
        '8': 'NC_000074.7',
        '9': 'NC_000075.7',
        '10': 'NC_000076.7',
        '11': 'NC_000077.7',
        '12': 'NC_000078.7',
        '13': 'NC_000079.7',
        '14': 'NC_000080.7',
        '15': 'NC_000081.7',
        '16': 'NC_000082.7',
        '17': 'NC_000083.7',
        '18': 'NC_000084.7',
        '19': 'NC_000085.7',
        'X': 'NC_000086.8',
        'Y': 'NC_000087.8'
    }

}


def build_variant_id(chr, pos_first_ref_base, ref_seq, alt_seq, assembly='GRCh38'):
    key = '{}_{}_{}_{}_{}'.format(str(chr).replace(
        'chr', '').lower(), pos_first_ref_base, ref_seq, alt_seq, assembly)
    return hashlib.sha256(key.encode()).hexdigest()


def build_allele(chr, pos, ref, alt, translator, seq_repo, assembly='GRCh38'):
    gnomad_exp = f'{chr}-{pos}-{ref}-{alt}'
    try:
        allele = translator.translate_from(gnomad_exp, 'gnomad')
    except ValidationError as e:
        print(e)
        chr_ref = CHR_MAP[assembly][chr]
        start = int(pos) - 1
        end = start + len(ref)
        ref = seq_repo[chr_ref][start:end]
        gnomad_exp = f'{chr}-{pos}-{ref}-{alt}'
        print('correct gnomad_exp:', gnomad_exp)
        allele = translator.translate_from(gnomad_exp, 'gnomad')
    return allele

# for buidling mouse allele, we will assume the ref is acurate and not validate it.


def build_allele_mouse(chr, pos, ref, alt, translator, seq_repo, assembly='GRCm39'):
    sequence_id = 'refseq:' + CHR_MAP['GRCm39'][chr]
    start = int(pos) - 1
    end = start + len(ref)
    interval = models.SequenceInterval(start=models.Number(value=start),
                                       end=models.Number(value=end))
    location = models.SequenceLocation(
        sequence_id=sequence_id, interval=interval)
    sstate = models.LiteralSequenceExpression(sequence=alt)
    allele = models.Allele(location=location, state=sstate)
    allele = translator._post_process_imported_allele(allele)
    return allele


def build_spdi(chr, pos, ref, alt, translator, seq_repo, assembly='GRCh38'):
    # Only use translator if the ref or alt is more than one base.
    if len(ref) == 1 and len(alt) == 1:
        chr_ref = CHR_MAP[assembly][chr]
        pos_spdi = int(pos) - 1
        # example SPDI: NC_000024.10:10004:C:G
        spdi = f'{chr_ref}:{pos_spdi}:{ref}:{alt}'
    else:
        if assembly == 'GRCh38':
            allele = build_allele(chr, pos, ref, alt,
                                  translator, seq_repo, assembly)
        else:
            allele = build_allele_mouse(
                chr, pos, ref, alt, translator, seq_repo)
        spdi = translator.translate_to(allele, 'spdi')[0]
        del_seq = translator.data_proxy.get_sequence(str(
            allele.location.sequence_id), allele.location.interval.start.value, allele.location.interval.end.value)
        spdi = convert_spdi(spdi, del_seq)
    return spdi

# the spdi generated by vrs is in this format: SEQUENCE-ID:POSITION:DEL-LEN:INS-SEQUENCE
# need to convert to this format for igvf catalog: SEQUENCE-ID:POSITION:DEL-SEQUENCE:INS-SEQUENCE


def convert_spdi(spdi, seq):
    ls = spdi.split(':')
    ls[2] = seq
    spdi = ':'.join(ls)
    return spdi


def build_hgvs_from_spdi(spdi):
    ins_seq = spdi.split(':')[-1]
    del_seq = spdi.split(':')[2]
    spdi_pos = int(spdi.split(':')[1])
    chr_ref = spdi.split(':')[0]
    # check if this variant is a substitution
    if len(ins_seq) == 1 and len(del_seq) == 1:
        hgvs = f'{chr_ref}:g.{spdi_pos + 1}{del_seq}>{ins_seq}'
    # check if this variant is a deletion
    elif del_seq.startswith(ins_seq):
        pos_hgvs_start = spdi_pos + 1 + len(ins_seq)
        pos_hgvs_end = spdi_pos + len(del_seq)
        if pos_hgvs_start == pos_hgvs_end:
            # one nucleotide deletion
            hgvs = f'{chr_ref}:g.{pos_hgvs_start}del'
        else:
            # several nucleotides deletion
            hgvs = f'{chr_ref}:g.{pos_hgvs_start}_{pos_hgvs_end}del'
    # it is a insertion. We will not generate specail case hgvs - duplication, since using insertion for dup is valid.
    # you can check if the hgvs is valid here: https://api.ncbi.nlm.nih.gov/variation/v0/#/HGVS/get_hgvs__hgvs__contextuals
    elif ins_seq.startswith(del_seq):
        pos_hgvs_start = spdi_pos + len(del_seq)
        pos_hgvs_end = pos_hgvs_start + 1
        insert_seq_hgvs = ins_seq[len(del_seq):]
        hgvs = f'{chr_ref}:g.{pos_hgvs_start}_{pos_hgvs_end}ins{insert_seq_hgvs}'
    # delins, we will not check inversion, since using delins for inversion is valid.
    else:
        pos_hgvs_start = spdi_pos + 1
        pos_hgvs_end = spdi_pos + len(del_seq)
        if pos_hgvs_start == pos_hgvs_end:
            # one nucleotide deletion
            hgvs = hgvs = f'{chr_ref}:g.{pos_hgvs_start}delins{ins_seq}'
        else:
            # several nucleotides deletion
            hgvs = f'{chr_ref}:g.{pos_hgvs_start}_{pos_hgvs_end}delins{ins_seq}'

    return hgvs

# in order to use translator locally, need to install seqrepo and pull data to local first
# check instruction here for pulling human genome sequence data: https://github.com/biocommons/biocommons.seqrepo
# for mouse, we download Genome sequences (FASTA) files here: https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_000001635.27/
# for each file, an output file will be genereated.
# each row in output file cotains: id in catalog, chr, pos, ref, alt, spdi, hgvs
# download input file from here: https://drive.google.com/drive/folders/1LKH6b_izU4291PTDwnr3n_le8gLxr4fv
# we need the file ends with vcf.gz format. Extract it first before using it.


def main():
    parser = argparse.ArgumentParser(
        prog='Variants SPDI generator',
        description='Generate SPDI for variants'
    )
    parser.add_argument('-i', '--input', required=True,
                        help='input file path')
    parser.add_argument('-o', '--output', required=True,
                        help='output file path')
    parser.add_argument('-a', '--assembly', default='GRCh38',
                        choices=['GRCh38', 'GRCm39'])
    args = parser.parse_args()
    input_file_path = args.input
    output_path = args.output
    assembly = args.assembly
    if assembly == 'GRCh38':
        dp = create_dataproxy(
            'seqrepo+file:///usr/local/share/seqrepo/2018-11-26')
        seq_repo = SeqRepo('/usr/local/share/seqrepo/2018-11-26')

    else:
        dp = create_dataproxy('seqrepo+file:///usr/local/share/seqrepo/mouse')
        seq_repo = SeqRepo('/usr/local/share/seqrepo/mouse')
    translator = Translator(data_proxy=dp, default_assembly_name=assembly)
    start_time = datetime.datetime.now()
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter='\t')

        with open(input_file_path, 'rt') as input_file:
            num = 0
            reader = csv.reader(input_file, delimiter='\t')
            row = next(reader)
            while not (row[0].startswith('#Chrom') or row[0].startswith('#CHROM')):
                row = next(reader)
            for row in reader:
                chr = row[0]
                pos = row[1]
                ref = row[3]
                alt = row[4]
                if chr not in CHR_MAP[assembly].keys():
                    continue
                id = build_variant_id(
                    chr,
                    pos,
                    ref,
                    alt
                )
                spdi = build_spdi(chr, pos, ref, alt, translator,
                                  seq_repo, assembly=assembly)
                hgvs = build_hgvs_from_spdi(spdi)
                writer.writerow([id, chr, pos, ref, alt, spdi, hgvs])
                num += 1
                if num % 1000000 == 0:
                    print(f'chr: {chr}, num: {num}', datetime.datetime.now())
        print('start time:', start_time)
        print('end time:', datetime.datetime.now())


if __name__ == '__main__':
    main()
