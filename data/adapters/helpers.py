from inspect import getfullargspec
import hashlib
from math import log10, floor, isinf

import hgvs.dataproviders.uta
from hgvs.easy import parser
from hgvs.extras.babelfish import Babelfish

import requests

ALLOWED_ASSEMBLIES = ['GRCh38', 'mm10', 'GRCm39']


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


@assembly_check
def build_variant_id(chr, pos_first_ref_base, ref_seq, alt_seq, assembly='GRCh38'):
    # pos_first_ref_base: 1-based position
    key = '{}_{}_{}_{}_{}'.format(str(chr).replace(
        'chr', '').lower(), pos_first_ref_base, ref_seq, alt_seq, assembly)
    return hashlib.sha256(key.encode()).hexdigest()


@assembly_check
def build_mouse_variant_id(chr, pos_first_ref_base, ref_seq, alt_seq, strain, assembly='GRCm39'):
    # pos_first_ref_base: 1-based position
    key = '{}_{}_{}_{}_{}_{}'.format(str(chr).replace(
        'chr', '').lower(), pos_first_ref_base, ref_seq, alt_seq, strain, assembly)
    return hashlib.sha256(key.encode()).hexdigest()


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


def query_fileset_files_props(file_accession, source_url, prediction=True, additional_props=None):
    # need to check if IGVF props are embedded same as in ENCODE
    # need to split by source_url
    # start with encode E2G data here
    required_props = ['fileset_id', 'lab', 'sample']
    allowed_additional_props = ['donor', 'treatment', 'pmid', 'software']
    portal_url = ''
    if 'encode' in source_url:
        portal_url = 'https://www.encodeproject.org/'
    elif 'igvf' in source_url:
        portal_url = 'https://data.igvf.org/'
    else:
        raise ValueError(
            'Invalid source_url to load into fileset_files collection.')
    # Other props: prediction_method, assay_name, preferred_assay_name
    # could prediction be calculated based on fileset type?

    # need to change dataset for igvfd
    fileset_accesion = requests.get(
        source_url + '?format=json').json()['dataset']
    fileset_json = requests.get(portal_url + fileset_accesion + '?format=json')

    _id = file_accession
    props = {
        '_key': _id,
        'fileset_id': '',
    }

    return props
