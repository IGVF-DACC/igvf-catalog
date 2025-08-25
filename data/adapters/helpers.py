import hashlib

from inspect import getfullargspec
from math import log10, floor, isinf
import re

from db.arango_db import ArangoDB

import hgvs.dataproviders.uta

from biocommons.seqrepo import SeqRepo
from ga4gh.vrs import models
from ga4gh.vrs.dataproxy import DataProxyValidationError
from ga4gh.vrs.dataproxy import SeqRepoDataProxy
from ga4gh.vrs.extras.translator import AlleleTranslator
from hgvs import parser
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
        '24': 'NC_000024.10',
        'M': 'NC_012920.1'
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

AA_TABLE = {
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

AA_TABLE_REV = {'A': 'Ala',
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
                '*': 'Ter'
                }


def build_allele(chr, pos, ref, alt, translator, seq_repo, assembly='GRCh38', correct_ref_allele=True):
    gnomad_exp = f'{chr}-{pos}-{ref}-{alt}'
    try:
        allele = translator.translate_from(gnomad_exp, 'gnomad')
    except DataProxyValidationError as e:
        if not correct_ref_allele:
            raise ValueError(f'Failed to translate allele {gnomad_exp}') from e
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
def build_allele_mouse(chr, pos, ref, alt, translator, assembly='GRCm39'):
    start = int(pos) - 1
    end = start + len(ref)
    refseq_id = CHR_MAP[assembly][chr]

    sequence_reference = models.SequenceReference(
        refgetAccession=translator.data_proxy.derive_refget_accession(refseq_id))
    location = models.SequenceLocation(
        sequenceReference=sequence_reference, start=start, end=end)
    allele = models.Allele(
        location=location, state=models.LiteralSequenceExpression(sequence=alt))
    allele = translator._post_process_imported_allele(allele)

    return allele


def build_spdi(chr, pos, ref, alt, translator, seq_repo, assembly='GRCh38', validate_SNV=False, correct_ref_allele=True):
    # Only use translator if the ref or alt is more than one base, or validate_SNV is True
    if len(ref) == 1 and len(alt) == 1 and validate_SNV != True:
        chr_ref = CHR_MAP[assembly][chr]
        pos_spdi = int(pos) - 1
        # example SPDI: NC_000024.10:10004:C:G
        spdi = f'{chr_ref}:{pos_spdi}:{ref}:{alt}'
    else:
        if assembly == 'GRCh38':
            allele = build_allele(chr, pos, ref, alt,
                                  translator, seq_repo, assembly, correct_ref_allele)
        else:
            allele = build_allele_mouse(
                chr, pos, ref, alt, translator)
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
def build_mouse_variant_id(chr, pos_first_ref_base, ref_seq, alt_seq, spdi):
    if len(spdi) <= 256:
        return spdi
    else:
        seq_repo = get_seqrepo('mouse')
        data_proxy = SeqRepoDataProxy(seq_repo)
        translator = AlleleTranslator(data_proxy)
        allele = build_allele_mouse(
            chr, pos_first_ref_base, ref_seq, alt_seq, translator)
        allele_vrs_digest = allele.digest
        return allele_vrs_digest


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
        p = parser.Parser()
        try:
            chr, pos_start, ref, alt, type = babelfish38.hgvs_to_vcf(
                p.parse(hgvs_id))
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


def bulk_check_variants_in_arangodb(identifiers, check_by='spdi'):
    db = ArangoDB().get_igvf_connection()

    if check_by == '_key':
        query = 'FOR v IN variants FILTER v._key IN @ids RETURN v._key'
    elif check_by == 'spdi':
        query = 'FOR v IN variants FILTER v.spdi IN @ids RETURN v._key'
    else:
        raise ValueError("check_by must be '_key' or 'spdi'")

    cursor = db.aql.execute(query, bind_vars={'ids': identifiers})
    return set(cursor)


def bulk_query_coding_variants_in_arangodb(protein_aa_pairs):
    # given pairs of protein_id and hgvsp, return matched coding variants keys mapping
    db = ArangoDB().get_igvf_connection()
    valid_pairs = [
        {'protein_id': protein_id, 'hgvsp': aa_change}
        for protein_id, aa_change in protein_aa_pairs
    ]

    query = '''
    FOR pair IN @pairs
        FOR v IN coding_variants
        FILTER v.protein_id == pair.protein_id AND v.hgvsp == pair.hgvsp
        RETURN {
            variant_key: v._key,
            protein_id: v.protein_id,
            hgvsp: v.hgvsp
        }
    '''

    cursor = db.aql.execute(
        query,
        bind_vars={'pairs': valid_pairs}
    )

    results = list(cursor)
    protein_aa_pairs_mappings = {}
    for r in results:
        if (r['protein_id'], r['hgvsp']) not in protein_aa_pairs_mappings:
            protein_aa_pairs_mappings[(r['protein_id'], r['hgvsp'])] = [
                r['variant_key']]
        else:
            protein_aa_pairs_mappings[(r['protein_id'], r['hgvsp'])].append(
                r['variant_key'])

    return protein_aa_pairs_mappings


def bulk_query_coding_variants_Met1_in_arangodb(protein_aa_pairs):
    # given pairs of protein_id and aa alt e.g. ENSP00000360372:p.Met1Thr
    # _keys in coding variants for Met1 are formatted as p.Met1!, so need to do special query here
    protein_aa_alt_pairs = []
    for protein_id, aa_change in protein_aa_pairs:
        aa_alt = AA_TABLE(aa_change.split('1')[1])
        protein_aa_alt_pairs.append((protein_id, aa_alt))
    db = ArangoDB().get_igvf_connection()
    valid_pairs = [
        {'protein_id': protein_id, 'aa_alt': aa_alt}
        for protein_id, aa_alt in protein_aa_alt_pairs
    ]

    query = '''
    FOR pair IN @pairs
        FOR v IN coding_variants
        FILTER v.protein_id == pair.protein_id AND v.hgvsp == 'Met1?' AND v.alt == aa_alt
        RETURN {
            variant_key: v._key,
            protein_id: v.protein_id,
            aa_alt: v.alt
        }
    '''

    cursor = db.aql.execute(
        query,
        bind_vars={'pairs': valid_pairs}
    )

    results = list(cursor)
    protein_aa_pairs_mappings = {}
    for r in results:
        if (r['protein_id'], r['aa_alt']) not in protein_aa_pairs_mappings:
            protein_aa_pairs_mappings[(r['protein_id'], 'p.Met1' + AA_TABLE_REV(r['aa_alt']))] = [
                r['variant_key']]
        else:
            protein_aa_pairs_mappings[(r['protein_id'], 'p.Met1' + AA_TABLE_REV(r['aa_alt']))].append(
                r['variant_key'])

    return protein_aa_pairs_mappings


def bulk_query_coding_variants_from_hgvsc_in_arangodb(transcript_hgvsc):
    # given pairs of transcript_id and hgvsc, return matched coding variants keys mapping
    db = ArangoDB().get_igvf_connection()
    valid_pairs = [
        {'transcript_id': transcript_id, 'hgvsc': hgvsc}
        for transcript_id, hgvsc in transcript_hgvsc
    ]

    query = '''
    FOR pair IN @pairs
        FOR v IN coding_variants
        FILTER v.transcript_id == pair.transcript_id AND v.hgvsc == pair.hgvsc
        RETURN {
            variant_key: v._key,
            transcript_id: v.transcript_id,
            hgvsc: v.hgvsc
        }
    '''

    cursor = db.aql.execute(
        query,
        bind_vars={'pairs': valid_pairs}
    )

    results = list(cursor)
    transcript_hgvsc_mappings = {}
    for r in results:
        if (r['transcript_id'], r['hgvsc']) not in transcript_hgvsc_mappings:
            transcript_hgvsc_mappings[(r['transcript_id'], r['hgvsc'])] = [
                r['variant_key']]
        else:
            transcript_hgvsc_mappings[(r['transcript_id'], r['hgvsc'])].append(
                r['variant_key'])

    return transcript_hgvsc_mappings

# Arangodb converts a number to string if it can't be represented in signed 64-bit
# Using the approximation of a limit +/- 308 decimal points for 64 bits


def build_coding_variant_id(variant_id, protein_id, transcript_id, gene_id):
    key = variant_id + '_' + protein_id + '_' + transcript_id + '_' + gene_id
    return hashlib.sha256(key.encode()).hexdigest()


def build_variant_coding_variant_key(variant_id, coding_variant_id):
    key = f'{variant_id}_{coding_variant_id}'
    if len(key) < 254:
        return key
    else:
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
    ref_len = len(spdi_list[2])
    if ref_len == 0:
        return ''  # insertion case e.g. NC_000010.11:79347444::CCTCCTCAGG
    start = int(spdi_list[1])
    end = start + ref_len
    return seq_repo[chr_ref][start:end]


def check_illegal_base_in_spdi(spdi, error_message=None):
    spdi_list = spdi.split(':')
    if not all(base in {'A', 'C', 'T', 'G'} for base in spdi_list[2]):
        error_message = {'variant_id': spdi, 'reason': 'Ambigious ref allele'}
    elif not all(base in {'A', 'C', 'T', 'G'} for base in spdi_list[3]):
        error_message = {'variant_id': spdi, 'reason': 'Ambigious alt allele'}
    return error_message


def load_variant(variant_id, validate_SNV=True, correct_ref_allele=False, translator=None, seq_repo=None, assembly='GRCh38'):
    '''
        Validate and normalize input variant, return a json obj for loading into catalog.
        The input variant can be in spdi format: NC_000001.11:10887495:C:T (assume 0-based coordinate), or vcf format: 1-108874-TCTC-T (assume 1-based coordinate, left-aligned)
        By default: validate ref allele for both SNVs and indels, and skip those failed validation variants instead of correcting the ref allele for them automatically.
    '''
    variant_json = {}
    skipped_message = None
    format = None
    spdi = None

    if len(variant_id.split(':')) == 4:
        format = 'spdi'
        chr_spdi = variant_id.split(':')[0]
        chr, pos_start, ref, alt = split_spdi(variant_id)
    elif len(variant_id.split('-')) == 4:
        format = 'vcf'
        chr, pos_start, ref, alt = variant_id.split('-')
        pos_start = int(pos_start)
    else:
        skipped_message = {'variant_id': variant_id,
                           'reason': 'Unable to parse this variant id'}
        return variant_json, skipped_message

    # Note: we convert the position to 1-based for spdi format id here, and input format as 'gnomad' when calling translator from ga4gh.vrs, since translate_from spdi doesn't include validation step currently
    # Add special case when ref or alt is empty - they are not accepted in gnomad/vcf format, validate ref seq for them seperately and skip normalization part for now
    if format == 'spdi':
        if ref == '' and alt == '':
            skipped_message = {'variant_id': variant_id,
                               'reason': 'Ref allele and alt allele both empty'}
            return variant_json, skipped_message
        elif ref == '' or alt == '':
            ref_genome = get_ref_seq_by_spdi(variant_id)
            if ref != ref_genome:
                skipped_message = {'variant_id': variant_id,
                                   'reason': 'Ref allele mismatch'}
                return variant_json, skipped_message
            spdi = f'{chr_spdi}:{pos_start}:{ref}:{alt}'

    if spdi is None:
        # do validation and normalization for both single nucleotide variants and multiple nucleotide variants, with translator from ga4gh.vrs
        # though SNV doesn't need the normalization part
        if format == 'spdi':
            pos_start = pos_start + 1
        if seq_repo is None:
            seq_repo = get_seqrepo('human')
        if translator is None:
            translator = AlleleTranslator(SeqRepoDataProxy(seq_repo))
        try:
            spdi = build_spdi(chr, pos_start, ref,
                              alt, translator, seq_repo, assembly, validate_SNV, correct_ref_allele)
        except ValueError as e:
            skipped_message = {'variant_id': variant_id,
                               'reason': 'Ref allele mismatch'}
            return variant_json, skipped_message
    if len(spdi) < 254:
        _id = spdi
    else:
        allele = build_allele(chr, pos_start, ref,
                              alt, translator, seq_repo, assembly)
        _id = allele.digest

    variation_type = 'SNP'  # should be SNV more broadly
    if len(ref) < len(alt):
        variation_type = 'insertion'
    elif len(ref) > len(alt):
        variation_type = 'deletion'
    elif len(ref) > 1:
        # e.g. NC_000018.10:31546003:AA:TG
        variation_type = 'deletion-insertion'

    error = check_illegal_base_in_spdi(spdi)
    if error is not None:
        return variant_json, error

    variant_json = {
        '_key': _id,
        'name': spdi,
        'chr': f'chr{chr}' if not chr.startswith('chr') else chr,
        'pos': int(pos_start) - 1,  # 0-indexed
        'pos': pos_start,
        'ref': ref,
        'alt': alt,
        'variation_type': variation_type,
        'spdi': spdi,
        'hgvs': build_hgvs_from_spdi(spdi),
        'organism': 'Homo sapiens'
    }
    return variant_json, skipped_message


def check_collection_loaded(collection, record_id):
    try:
        db = ArangoDB().get_igvf_connection()
        col = db.collection(collection)
        return col.has(record_id)
    except Exception as e:
        print(f'Error checking {record_id} in {collection}: {e}')
        return False


def convert_aa_to_three_letter(aa_change):
    '''
    convert single letter code to three letter code for aa change
    e.g. Q873T -> Gln873Thr
    '''
    matches = re.findall(r'^([A-Za-z]+)(\d+)([A-Za-z]+)', aa_change)
    aa_ref, aa_pos, aa_alt = matches[0]
    aa_ref = AA_TABLE_REV[aa_ref]
    aa_alt = AA_TABLE_REV[aa_alt]
    return aa_ref + str(aa_pos) + aa_alt


def convert_aa_letter_code_and_Met1(coding_variant_id):
    # convert one letter aa code to three letter code from mapping file
    # for change from start codon Met1 e.g. Met1Ala convert to Met1! in _key, to match with coding variants loaded from dbNSFP
    # e.g. DSG2_ENST00000261590_p.Q873T_c.2617_2618delinsAC -> DSG2_ENST00000261590_p.Gln873Thr_c.2617_2618delinsAC
    aa_change = coding_variant_id.split('_')[2].split('.')[1]
    matches = re.findall(r'^([A-Za-z]+)(\d+)([A-Za-z]+)', aa_change)
    aa_ref, aa_pos, aa_alt = matches[0]
    if len(aa_ref) == 1:
        aa_ref = AA_TABLE_REV[aa_ref]
        aa_alt = AA_TABLE_REV[aa_alt]
        aa_change = aa_ref + str(aa_pos) + aa_alt
    if aa_ref == 'Met' and aa_pos == '1':
        aa_change = 'Met1!'
    converted_id = '_'.join(coding_variant_id.split(
        '_')[:2]) + '_p.' + aa_change + '_' + '_'.join(coding_variant_id.split('_')[3:])
    return converted_id
