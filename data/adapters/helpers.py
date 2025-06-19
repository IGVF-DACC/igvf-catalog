import hashlib

from inspect import getfullargspec
from math import log10, floor, isinf

from db.arango_db import ArangoDB

import hgvs.dataproviders.uta

from biocommons.seqrepo import SeqRepo
from ga4gh.vrs import models
from ga4gh.vrs.dataproxy import DataProxyValidationError
from ga4gh.vrs.dataproxy import SeqRepoDataProxy
from ga4gh.vrs.extras.translator import AlleleTranslator
from hgvs.easy import parser
from hgvs.extras.babelfish import Babelfish
from functools import lru_cache


ALLOWED_ASSEMBLIES = ['GRCh38', 'mm10', 'GRCm39']

CHR_MAP = {
    'GRCh38': {
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
    },
    'GRCm39': {
        'chr1': 'NC_000067.7',
        '1': 'NC_000067.7',
        'chr2': 'NC_000068.8',
        '2': 'NC_000068.8',
        'chr3': 'NC_000069.7',
        '3': 'NC_000069.7',
        'chr4': 'NC_000070.7',
        '4': 'NC_000070.7',
        'chr5': 'NC_000071.7',
        '5': 'NC_000071.7',
        'chr6': 'NC_000072.7',
        '6': 'NC_000072.7',
        'chr7': 'NC_000073.7',
        '7': 'NC_000073.7',
        'chr8': 'NC_000074.7',
        '8': 'NC_000074.7',
        'chr9': 'NC_000075.7',
        '9': 'NC_000075.7',
        'chr10': 'NC_000076.7',
        '10': 'NC_000076.7',
        'chr11': 'NC_000077.7',
        '11': 'NC_000077.7',
        'chr12': 'NC_000078.7',
        '12': 'NC_000078.7',
        'chr13': 'NC_000079.7',
        '13': 'NC_000079.7',
        'chr14': 'NC_000080.7',
        '14': 'NC_000080.7',
        'chr15': 'NC_000081.7',
        '15': 'NC_000081.7',
        'chr16': 'NC_000082.7',
        '16': 'NC_000082.7',
        'chr17': 'NC_000083.7',
        '17': 'NC_000083.7',
        'chr18': 'NC_000084.7',
        '18': 'NC_000084.7',
        'chr19': 'NC_000085.7',
        '19': 'NC_000085.7',
        'chrX': 'NC_000086.8',
        'X': 'NC_000086.8',
        'chrY': 'NC_000087.8',
        'Y': 'NC_000087.8'
    }
}


def build_allele(chr, pos, ref, alt, translator, seq_repo, assembly='GRCh38'):
    gnomad_exp = f'{chr}-{pos}-{ref}-{alt}'
    try:
        allele = translator.translate_from(gnomad_exp, 'gnomad')
    except DataProxyValidationError as e:
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
        del_seq = translator.data_proxy.get_sequence(
            f'ga4gh:{allele.location.sequenceReference.refgetAccession}',
            allele.location.start,
            allele.location.end)
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
        hgvs = f'{chr_ref}: g.{pos_hgvs_start}_{pos_hgvs_end}ins{insert_seq_hgvs}'
    # delins, we will not check inversion, since using delins for inversion is valid.
    else:
        pos_hgvs_start = spdi_pos + 1
        pos_hgvs_end = spdi_pos + len(del_seq)
        if pos_hgvs_start == pos_hgvs_end:
            # one nucleotide deletion
            hgvs = hgvs = f'{chr_ref}:g.{pos_hgvs_start}delins{ins_seq}'
        else:
            # several nucleotides deletion
            hgvs = f'{chr_ref}: g.{pos_hgvs_start}_{pos_hgvs_end}delins{ins_seq}'

    return hgvs


def assembly_check(id_builder):
    def wrapper(*args, **kwargs):
        argspec = getfullargspec(id_builder)

        if 'assembly' in argspec.args:
            assembly_index = argspec.args.index('assembly')
            if assembly_index >= len(args):
                pass
            elif args[assembly_index] not in ALLOWED_ASSEMBLIES:
                raise ValueError('Assembly not supported')
        return id_builder(*args, **kwargs)

    return wrapper


@lru_cache(maxsize=None)
def get_seqrepo(species='human'):
    species_to_seqrepo_location = {
        'human': '/usr/local/share/seqrepo/2024-12-20',
        'mouse': '/usr/local/share/seqrepo/mouse'
    }
    return SeqRepo(species_to_seqrepo_location[species])


@assembly_check
def build_variant_id(chr, pos_first_ref_base, ref_seq, alt_seq, assembly='GRCh38'):
    seq_repo = get_seqrepo('human')
    data_proxy = SeqRepoDataProxy(seq_repo)
    translator = AlleleTranslator(data_proxy)
    spdi = build_spdi(chr, pos_first_ref_base, ref_seq,
                      alt_seq, translator, seq_repo, assembly)
    if len(spdi) < 254:
        return spdi

    allele = build_allele(chr, pos_first_ref_base, ref_seq,
                          alt_seq, translator, seq_repo, assembly)
    return allele.digest


@assembly_check
def build_mouse_variant_id(chr, pos_first_ref_base, ref_seq, alt_seq, assembly='GRCm39'):
    seq_repo = get_seqrepo('mouse')
    data_proxy = SeqRepoDataProxy(seq_repo)
    translator = AlleleTranslator(data_proxy)
    spdi = build_spdi(chr, pos_first_ref_base, ref_seq,
                      alt_seq, translator, seq_repo, assembly)
    allele = build_allele_mouse(
        chr, pos_first_ref_base, ref_seq, alt_seq, assembly)
    allele_vrs_digest = allele.digest
    return spdi if len(spdi) <= 256 else allele_vrs_digest


@assembly_check
def build_regulatory_region_id(chr, pos_start, pos_end, class_name=None, assembly='GRCh38'):
    if class_name:
        return '{}_{}_{}_{}_{}'.format(class_name, chr, pos_start, pos_end, assembly)
    else:
        return '{}_{}_{}_{}'.format(chr, pos_start, pos_end, assembly)


@assembly_check
def build_variant_id_from_hgvs(hgvs_id, validate=True, assembly='GRCh38'):
    # translate hgvs naming to vcf format e.g. NC_000003.12:g.183917980C>T -> 3_183917980_C_T
    if validate:  # use tools from hgvs, which corrects ref allele if it's wrong
        # got connection timed out error occasionally, could add a retry function
        hdp = hgvs.dataproviders.uta.connect()
        babelfish38 = Babelfish(hdp, assembly_name=assembly)
        try:
            chr, pos_start, ref, alt, type = babelfish38.hgvs_to_vcf(
                parser.parse(hgvs_id))
        except Exception as e:
            print(e)
            return None

        if type == 'sub' or type == 'delins':
            return build_variant_id(chr, pos_start+1, ref[1:], alt[1:])
        else:
            return build_variant_id(chr, pos_start, ref, alt)

    # if no need to validate/query ref allele (e.g. single position substitutions) -> use regex match is quicker
    else:
        if hgvs_id.startswith('NC_'):
            chr = int(hgvs_id.split('.')[0].split('_')[1])
            if chr < 23:
                chr = str(chr)
            elif chr == 23:
                chr = 'X'
            elif chr == 24:
                chr = 'Y'
            else:
                print('Error: unsupported chromosome name.')
                return None

            pos_start = hgvs_id.split('.')[2].split('>')[0][:-1]
            if pos_start.isnumeric():
                ref = hgvs_id.split('.')[2].split('>')[0][-1]
                alt = hgvs_id.split('.')[2].split('>')[1]
                return build_variant_id(chr, pos_start, ref, alt)
            else:
                print('Error: wrong hgvs format.')
                return None
        else:
            print('Error: wrong hgvs format.')
            return None


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


def bulk_check_spdis_in_arangodb(spdis):
    db = ArangoDB().get_igvf_connection()
    cursor = db.aql.execute(
        'FOR v IN variants FILTER v.spdi IN @spdis RETURN v.spdi',
        bind_vars={'spdis': spdis}
    )
    return set(cursor)

# Arangodb converts a number to string if it can't be represented in signed 64-bit
# Using the approximation of a limit +/- 308 decimal points for 64 bits


def build_coding_variant_id(variant_id, protein_id, transcript_id, gene_id):
    key = variant_id + '_' + protein_id + '_' + transcript_id + '_' + gene_id
    return hashlib.sha256(key.encode()).hexdigest()


def to_float(str):
    MAX_EXPONENT = 307

    number = float(str)

    if number == 0:
        return number

    if isinf(number) and number > 0:
        return float('1e307')

    if isinf(number) and number < 0:
        return float('1e-307')

    base10 = log10(abs(number))
    exponent = floor(base10)

    if abs(exponent) > MAX_EXPONENT:
        if exponent < 0:
            number = number * float(f'1e{abs(exponent) - MAX_EXPONENT}')
        else:
            number = number / float(f'1e{abs(exponent) - MAX_EXPONENT}')

    return number


def is_variant_snv(spdi):
    spdi_list = spdi.split(':')
    if len(spdi_list) == 4 and len(spdi_list[2]) == 1 and len(spdi_list[3]) == 1:
        return True
    return False


def get_ref_seq_by_spdi(spdi, species='human'):
    seq_repo = get_seqrepo(species)
    spdi_list = spdi.split(':')
    chr_ref = spdi_list[0]
    start = int(spdi_list[1])
    end = start + 1
    return seq_repo[chr_ref][start:end]


def check_collection_loaded(collection, record_id):
    try:
        db = ArangoDB().get_igvf_connection()
        col = db.collection(collection)
        return col.has(record_id)
    except Exception as e:
        print(f'Error checking {record_id} in {collection}: {e}')
        return False
