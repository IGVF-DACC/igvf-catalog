from inspect import getfullargspec
import hashlib

import hgvs.dataproviders.uta
from hgvs.easy import parser
from hgvs.extras.babelfish import Babelfish

ALLOWED_ASSEMBLIES = ['GRCh38']


def assembly_check(id_builder):
    def wrapper(*args, **kwargs):
        argspec = getfullargspec(id_builder)

        if 'assembly' in argspec.args:
            assembly_index = argspec.args.index('assembly')
            if assembly_index >= len(args):
                pass
            elif args[assembly_index] not in ALLOWED_ASSEMBLIES:
                raise ValueError('Assembly not supported')
        return id_builder(*args, *kwargs)

    return wrapper


@assembly_check
def build_variant_id(chr, pos_first_ref_base, ref_seq, alt_seq, assembly='GRCh38'):
    # pos_first_ref_base: 1-based position
    key = '{}_{}_{}_{}_{}'.format(str(chr).replace(
        'chr', '').lower(), pos_first_ref_base, ref_seq, alt_seq, assembly)
    return hashlib.sha256(key.encode()).hexdigest()


@assembly_check
def build_regulatory_region_id(class_name, chr, pos_start, pos_end, assembly='GRCh38'):
    return '{}_{}_{}_{}_{}'.format(class_name, chr, pos_start, pos_end, assembly)


@assembly_check
def build_variant_id_from_hgvs(hgvs_id, assembly='GRCh38', validate=True):
    # translate hgvs naming to vcf format e.g. NC_000003.12:g.183917980C>T -> 3_183917980_C_T
    if validate:  # use tools from hgvs, which corrects ref allele if it's wrong
        # got connection time error occasionally, could add a retry function
        hdp = hgvs.dataproviders.uta.connect()
        babelfish38 = Babelfish(hdp, assembly_name=assembly)
        try:
            chr, pos_start, ref, alt, type = babelfish38.hgvs_to_vcf(
                parser.parse(hgvs_id))
        except Exception as e:
            print(e)
            return None

        if type == 'sub':
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
