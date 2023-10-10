import gzip
import csv
import hashlib
import os
from ga4gh.vrs.extras.translator import Translator
from ga4gh.vrs.dataproxy import create_dataproxy

chr_map = {
    'chr1': 'NC_000001.11',
    'chr2': 'NC_000002.12',
    'chr3': 'NC_000003.12',
    'chr4': 'NC_000004.12',
    'chr5': 'NC_000005.10',
    'chr6': 'NC_000006.12',
    'chr7': 'NC_000007.14',
    'chr8': 'NC_000008.11',
    'chr9': 'NC_000009.12',
    'chr10': 'NC_000010.11',
    'chr11': 'NC_000011.10',
    'chr12': 'NC_000012.12',
    'chr13': 'NC_000013.11',
    'chr14': 'NC_000014.9',
    'chr15': 'NC_000015.10',
    'chr16': 'NC_000016.10',
    'chr17': 'NC_000017.11',
    'chr18': 'NC_000018.10',
    'chr19': 'NC_000019.10',
    'chr20': 'NC_000020.11',
    'chr21': 'NC_000021.9',
    'chr22': 'NC_000022.11',
    'chrx': 'NC_000023.11',
    'chry': 'NC_000024.10'

}


def build_variant_id(chr, pos_first_ref_base, ref_seq, alt_seq, assembly='GRCh38'):
    # pos_first_ref_base: 1-based position
    key = '{}_{}_{}_{}_{}'.format(str(chr).replace(
        'chr', '').lower(), pos_first_ref_base, ref_seq, alt_seq, assembly)
    return hashlib.sha256(key.encode()).hexdigest()


def convert_spdi(spdi, seq):
    ls = spdi.split(':')
    ls[2] = seq
    spdi = ':'.join(ls)
    return spdi


def get_spdi(gnomad_exp, translator):

    allele = translator.translate_from(gnomad_exp, 'gnomad')
    spdi = translator.translate_to(allele, 'spdi')
    seq = translator.data_proxy.get_sequence(str(
        allele.location.sequence_id), allele.location.interval.start.value, allele.location.interval.end.value)
    return convert_spdi(spdi, seq)


def get_hgvs(gnomad_exp, translator):
    allele = translator.translate_from(gnomad_exp, 'gnomad')
    hgvs = translator.translate_to(allele, 'hgvs')

# in order to use translator locally, need to install seqrepo and pull data to local first
# check instruction here: https://github.com/biocommons/biocommons.seqrepo


def main():
    dp = create_dataproxy('seqrepo+file:///usr/local/share/seqrepo/2018-11-26')
    translator = Translator(data_proxy=dp)
    input_folder = '/home/ubuntu/datasets/favor'
    ouput_folder = '/home/ubuntu/datasets/favor_output'
    file_list = os.listdir(input_folder)
    for file in file_list:
        chr = file.split('.')[1]
        output_name = f'{chr}_spdi.tsv'
        output_path = os.path.join(ouput_folder, output_name)
        file_path = os.path.join(input_folder, file)
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter='\t')

            with gzip.open(file_path, 'rt') as input_file:
                num = 0
                reader = csv.reader(input_file, delimiter='\t')
                is_data = False
                for row in reader:
                    if row[0] == '#CHROM':
                        is_data = True
                        continue
                    if is_data:
                        chr = row[0]
                        pos = row[1]
                        ref = row[3]
                        alt = row[4]
                        id = build_variant_id(
                            row[0],
                            row[1],
                            row[3],
                            row[4]
                        )
                        if len(ref) == 1 and len(alt) == 1:
                            chr_ref = chr_map[f'chr{chr}']
                            pos_spdi = int(pos) - 1
                            spdi = f'{chr_ref}:{pos_spdi}:{ref}:{alt}'
                            pos_hgvs = f'g.{pos}'
                            hgvs = f'{chr_ref}:{pos_hgvs}{ref}>{alt}'
                        else:
                            gnomad_exp = f'{chr}-{pos}-{ref}-{alt}'
                            allele = translator.translate_from(
                                gnomad_exp, 'gnomad')
                            spdi = translator.translate_to(allele, 'spdi')[0]
                            seq = translator.data_proxy.get_sequence(str(
                                allele.location.sequence_id), allele.location.interval.start.value, allele.location.interval.end.value)

                            spdi = convert_spdi(spdi, seq)
                            hgvs = translator.translate_to(allele, 'hgvs')[0]
                        writer.writerow([id, chr, pos, ref, alt, spdi, hgvs])
                        num += 1
                        if num % 100 == 0:
                            print(f'chr: {chr}, num: {num}')


if __name__ == '__main__':
    main()
