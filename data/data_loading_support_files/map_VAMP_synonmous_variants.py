import requests
from enumerate_coding_variants_all_mappings import enumerate_coding_variant
import py2bit
import argparse
import json
import re

# This script serves as a temporary way to load an additional set of coding variants for VAMP-seq data, including:
# aa changes to Ter requiring multiple nucleotide changes
# synonymous coding variants
# they were not covered in prediction groups
# input file: skipped_coding_variants_vamp_all.txt - list of hgvsp/hgvsc from VAMP-seq (& MultiSTEP) not found in catalog
# Output files: variants_VAMP.jsonl, coding_variants_VAMP.jsonl, variants_coding_variants.jsonl used for loading into catalog

# Chromosome mapping
CHR_MAP = {
    'chr1': 'NC_000001.11',
    '1': 'NC_000001.11',
    'chr2': 'NC_000002.12',
    '2': 'NC_000002.12',
    'chr3': 'NC_000003.12',
    '3': 'NC_000003.12',
    'chr4': 'NC_000004.12',
    '4': 'NC_000004.12',
    'chr5': 'NC_000005.10',
    '5': 'NC_000005.10',
    'chr6': 'NC_000006.12',
    '6': 'NC_000006.12',
    'chr7': 'NC_000007.14',
    '7': 'NC_000007.14',
    'chr8': 'NC_000008.11',
    '8': 'NC_000008.11',
    'chr9': 'NC_000009.12',
    '9': 'NC_000009.12',
    'chr10': 'NC_000010.11',
    '10': 'NC_000010.11',
    'chr11': 'NC_000011.10',
    '11': 'NC_000011.10',
    'chr12': 'NC_000012.12',
    '12': 'NC_000012.12',
    'chr13': 'NC_000013.11',
    '13': 'NC_000013.11',
    'chr14': 'NC_000014.9',
    '14': 'NC_000014.9',
    'chr15': 'NC_000015.10',
    '15': 'NC_000015.10',
    'chr16': 'NC_000016.10',
    '16': 'NC_000016.10',
    'chr17': 'NC_000017.11',
    '17': 'NC_000017.11',
    'chr18': 'NC_000018.10',
    '18': 'NC_000018.10',
    'chr19': 'NC_000019.10',
    '19': 'NC_000019.10',
    'chr20': 'NC_000020.11',
    '20': 'NC_000020.11',
    'chr21': 'NC_000021.9',
    '21': 'NC_000021.9',
    'chr22': 'NC_000022.11',
    '22': 'NC_000022.11',
    'chrX': 'NC_000023.11',
    'X': 'NC_000023.11',
    '23': 'NC_000023.11',
    'chrY': 'NC_000024.10',
    'Y': 'NC_000024.10',
    '24': 'NC_000024.10'
}
# copied from helpers.py


def split_spdi(spdi):
    if not spdi.startswith('NC_'):
        print('Error: unsupported accession format.')
        return None

    try:
        parts = spdi.split(':')
        accession = parts[0]
        pos_start = int(parts[1])
        ref = parts[2]
        alt = parts[3]

        # Extract chromosome number from RefSeq accession
        chr_num = int(accession.split('.')[0].split('_')[1])
        if chr_num < 23:
            chr = f'chr{str(chr_num)}'
        elif chr_num == 23:
            chr = 'chrX'
        elif chr_num == 24:
            chr = 'chrY'
        else:
            print('Error: unsupported chromosome name.')
            return None

        return chr, pos_start, ref, alt

    except Exception as error:
        print(f'Error parsing SPDI: {error}')
        return None


def get_exon_coordinates(transcript_id):
    transcript_id = transcript_id.split('.')[0]
    query_url = f'https://api-dev.catalog.igvf.org/api/genes-structure?transcript_id={transcript_id}&organism=Homo%20sapiens&limit=1000'
    exons_coordinates = []
    chrom = None
    chrom_refseq = None
    strand = None
    CDS = {}
    try:
        responses = requests.get(query_url).json()
    # get gene structure from KG; the exon ranges are stored in bed format
        for structure in responses:
            if structure['type'] == 'CDS':
                CDS[int(structure['exon_number'])] = structure
        # sort by exon_number, not necessarily start from 1
        for i in range(min(CDS.keys()), max(CDS.keys())+1):
            if CDS[i]['strand'] == '+':
                exons_coordinates.extend(
                    list(range(CDS[i]['start'], CDS[i]['end'])))
            else:  # on reverse strand
                exons_coordinates.extend(
                    list(reversed(range(CDS[i]['start'], CDS[i]['end']))))
        chrom = responses[0]['chr']
        chrom_refseq = CHR_MAP[chrom]
        strand = responses[0]['strand']
    except Exception as e:
        print(f'Error: {e}')

    return exons_coordinates, chrom, chrom_refseq, strand


def query_transcript_id_from_protein(protein_id):
    protein_id = protein_id.split('.')[0]
    query_url = f'https://api-dev.catalog.igvf.org/api/proteins/transcripts?protein_id={protein_id}&organism=Homo%20sapiens'
    try:
        responses = requests.get(query_url).json()
        transcript_str = responses[0].get('transcript')
        transcript_id = transcript_str.split('/')[1]
        return transcript_id
    except Exception as e:
        print(f'Error: {e}')
        return None


def query_gene_from_protein(protein_id):
    protein_id = protein_id.split('.')[0]
    query_url = f'https://api-dev.catalog.igvf.org/api/proteins/genes?protein_id={protein_id}&organism=Homo%20sapiens&verbose=true'
    try:
        responses = requests.get(query_url).json()
        gene_info = responses[0].get('gene')
        gene_name = gene_info['name']
        return gene_name
    except Exception as e:
        print(f'Error: {e}')
        return None


def query_protein_name(protein_id):
    protein_id = protein_id.split('.')[0]
    query_url = f'https://api-dev.catalog.igvf.org/api/proteins?protein_id={protein_id}&organism=Homo%20sapiens'
    try:
        responses = requests.get(query_url).json()
        protein_name = responses.get('names')[0]
        return protein_name
    except Exception as e:
        print(f'Error: {e}')
        return None


def query_hgvsc_from_clingen(hgvsc):
    # for synonymous variants represented by hgvsc id e.g. ENST00000371321.9:c.105T>C (only in CYP2C19 vamp-seq file)
    # use clinGen API to map it to hgvsp
    query_url = f'http://reg.genome.network/allele?hgvs={hgvsc}'
    res = requests.get(query_url).json()
    hgvsp = None
    if 'transcriptAlleles' not in res:
        print(res.get('description'))
        return None
    for i in res['transcriptAlleles']:
        if 'MANE' in i:  # use MANE select ones
            if i['proteinEffect']['hgvs'].startswith('ENSP'):
                hgvsp = i['proteinEffect']['hgvs']
    return hgvsp


def main():
    seq_reader = py2bit.open('hg38.2bit')
    source = 'IGVF'
    # just put CYP2C19 vamp-seq file source here
    source_url = 'https://data.igvf.org/tabular-files/IGVFFI0629IIQU'
    with open('variants_vamp.jsonl', 'w') as variants_out, open('variants_coding_variants_vamp.jsonl', 'w') as variants_coding_variants_out, open('coding_variants_vamp.jsonl', 'w') as coding_variants_out:
        # assume hgvsp id in each line e.g. ENSP00000218099.2:p.Glu35=
        with open('skipped_coding_variants_vamp_all.txt', 'r') as input_file:
            protein_id_last = ''
            for row in input_file:
                if 'c.' in row:
                    hgvsc = row.strip()
                    hgvsp_full_str = query_hgvsc_from_clingen(hgvsc)
                    if hgvsp_full_str:
                        transcript_id = hgvsc.split(':')[0].split('.')[0]
                        protein_id = hgvsp_full_str.split(':')[0].split('.')[0]
                        hgvsp = hgvsp_full_str.split(':')[1]
                    else:
                        continue
                elif 'p.' in row:
                    protein_id, hgvsp = row.strip().split(':')
                else:
                    print(f'invalid hgvsp: {row.strip()}')
                    continue

                if protein_id != protein_id_last:
                    transcript_id = query_transcript_id_from_protein(
                        protein_id)
                    gene = query_gene_from_protein(protein_id)
                    protein_name = query_protein_name(protein_id)
                    exons_coordinates, chrom, chrom_refseq, strand = get_exon_coordinates(
                        transcript_id)
                    protein_id_last = protein_id

                try:
                    coding_variants = enumerate_coding_variant(
                        hgvsp, gene, transcript_id, strand, chrom, chrom_refseq, exons_coordinates, seq_reader)
                    variant_ids = coding_variants['spdi_ids']
                    coding_variant_ids = coding_variants['mutation_ids']
                    # Met1 case -> revise _key to match with dbNSFP
                    if coding_variants['ref_aa'] == 'Met' and coding_variants['aa_pos'] == '1':
                        pattern = re.compile(r'p\.Met1[A-Za-z]{3}')
                        coding_variant_ids = [pattern.sub(
                            'p.Met1!', _id) for _id in coding_variants['mutation_ids']]
                        hgvsp = 'p.Met1?'

                    # variants_coding_variants
                    for coding_variant_id, variant_id in zip(coding_variant_ids, variant_ids):
                        chr, pos, ref, alt = split_spdi(variant_id)
                        _props = {
                            '_key': f'{variant_id}_{coding_variant_id}',
                            '_from': 'variants/' + variant_id,
                            '_to': 'coding_variants/' + coding_variant_id,
                            'name': 'codes for',
                            'inverse_name': 'encoded by',
                            'chr': chr,
                            'pos': pos,  # 0-indexed
                            'ref': ref,
                            'alt': alt,
                            'source': source,
                            'source_url': source_url
                        }
                        variants_coding_variants_out.write(
                            json.dumps(_props) + '\n')
                    # coding_variants
                    for i, coding_variant_id in enumerate(coding_variant_ids):
                        _props = {
                            '_key': coding_variant_id,
                            'ref': coding_variants['ref_aa'],
                            'alt': coding_variants['alt_aa'],
                            'aapos': int(coding_variants['aa_pos']),
                            'refcodon': coding_variants['codon_ref'],
                            'gene_name': coding_variant_id.split('_')[0],
                            'protein_id': protein_id.split('.')[0],
                            'protein_name': protein_name,
                            'codonpos': int(coding_variants['codon_positions'][i]),
                            'hgvsc': coding_variants['hgvsc_ids'][i].replace('-', '>'),
                            'hgvsp': hgvsp,
                            'transcript_id': transcript_id.split('.')[0],
                            'source': source,
                            'source_url': source_url,
                        }
                        coding_variants_out.write(json.dumps(_props) + '\n')
                    # variants
                    hgvsg_ids = coding_variants['hgvsg_ids']
                    for variant_id, hgvsg in zip(variant_ids, hgvsg_ids):
                        chr, pos, ref, alt = split_spdi(variant_id)
                        _props = {
                            '_key': variant_id,  # don't have long spdi to convert
                            'name': variant_id,
                            'chr': chr,
                            'pos': pos,
                            'ref': ref,
                            'alt': alt,
                            'variation_type': 'SNP' if len(ref) == 1 else 'deletion-insertion',
                            'spdi': variant_id,
                            'hgvs': hgvsg,
                            'organism': 'Homo sapiens',
                            'source': source,
                            'source_url': source_url
                        }
                        variants_out.write(json.dumps(_props) + '\n')
                except ValueError as ve:
                    print(f'{str(ve)}')
                    continue


if __name__ == '__main__':
    main()
