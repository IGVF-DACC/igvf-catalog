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


def check_if_multiple_values(property):
    property = list(property)
    if len(property) > 1:
        raise(ValueError(
            f'Loading of multiple values for {property} is not supported.'))
    elif len(property) == 1:
        return str(property[0])
    else:
        return None


def decompose_analysis_set_to_measurement_set(portal_url, analysis_set, measurement_sets=set()):
    analysis_set_object = requests.get(
        portal_url + analysis_set + '/@@object?format=json').json()
    input_file_sets = analysis_set_object.get('input_file_sets', [])
    for input_file_set in input_file_sets:
        if input_file_set.startswith('/measurement-sets/'):
            measurement_sets.add(input_file_set)
        elif input_file_set.startswith('/auxiliary-sets/'):
            continue  # auxiliary sets are not analyzed without measurement sets so they can be skipped
        elif input_file_set.startswith('/construct-library-sets/'):
            construct_library_set_object = requests.get(
                portal_url + input_file_set + '/@@object_with_select_calculated_properties?field=applied_to_samples?format=json').json()
            for sample in construct_library_set_object.get('applied_to_samples', []):
                sample_object = requests.get(
                    portal_url + sample + '@@object_with_select_calculated_properties?field=file_sets?format=json')
                for file_set in sample_object.get('file_sets', []):
                    if file_set.startswith('/measurement-sets/'):
                        # construct library sets should be associated with some measurement set
                        measurement_sets.add(file_set)
        elif input_file_set.startswith('/analysis-sets/'):
            decompose_analysis_set_to_measurement_set(
                portal_url, input_file_set, measurement_sets)
    return measurement_sets


def query_fileset_files_props_igvf(file_accession):
    portal_url = 'https://api.data.igvf.org/'
    # get file metadata
    file_object = requests.get(
        portal_url + file_accession + '/@@object?format=json').json()
    lab = file_object.get('lab')
    software = set()
    if 'analysis_step_version' in file_object:
        analysis_step_version_object = requests.get(
            portal_url + file_object.get('analysis_step_version') + '/@@object?format=json').json()
        software_versions = analysis_step_version_object.get(
            'software_versions')
        for software_version in software_versions:
            software_version_object = requests.get(
                portal_url + software_version + '/@@object?format=json').json()
            software_object = requests.get(
                portal_url + software_version_object.get('software') + '/@@object?format=json').json()
            software.add(software_object.get('name'))

    file_set_object = requests.get(
        portal_url + file_object.get('file_set') + '/@@object?format=json').json()
    file_set_accession = file_set_object.get('accession')
    file_set_object_type = file_set_object.get('@type')[0]

    preferred_assay_titles = set()
    assay_term_ids = set()

    # get file set metadata
    prediction = False
    prediction_method = None
    if file_set_object_type == 'PredictionSet':
        prediction = True
        prediction_method = file_set_object.get('file_set_type')
        if not(software):
            raise(ValueError(f'Prediction sets require software to be loaded.'))
    elif file_set_object_type == 'AnalysisSet':
        for input_file_set in file_set_object.get('input_file_sets', []):
            measurement_sets = set()
            if input_file_set.startswith('/analysis-sets/'):
                input_file_set_object = requests.get(
                    portal_url + input_file_set + '/@@object?format=json').json()
                measurement_sets = measurement_sets | decompose_analysis_set_to_measurement_set(
                    portal_url, input_file_set)
            if input_file_set.startswith('/measurement-sets/'):
                measurement_sets.add(input_file_set)
            for measurement_set in measurement_sets:
                measurement_set_object = requests.get(
                    portal_url + measurement_set + '/@@object?format=json').json()
                preferred_assay_titles.add(
                    measurement_set_object.get('preferred_assay_title'))
                assay_term = measurement_set_object.get('assay_term')
                assay_term_object = requests.get(
                    portal_url + assay_term + '/@@object?format=json').json()
                assay_term_ids.add(assay_term_object.get('term_id'))
    # add support for ModelSet later
    else:
        raise(ValueError(
            f'Loading data from file sets other than prediction sets and analysis sets is currently unsupported.'))
    publication_id = None
    if 'publications' in file_set_object:
        publications = file_set_object.get('publications', [])
        if len(publications) > 1:
            raise(ValueError(
                f'Loading multiple publications for a single file is not supported.'))
        publication_object = requests.get(
            portal_url + publications[0] + '/@@object?format=json').json()
        publication_id = publication_object.get('publication_identifiers', [])[
            0]  # only one ID from a publication is needed

    # get samples metadata
    samples = file_set_object.get('samples', [])
    sample_ids = []
    sample_term_ids = set()
    donor_ids = set()
    simple_sample_summaries = set()
    treatment_ids = set()
    for sample in samples:
        sample_object = requests.get(
            portal_url + sample + '/@@object?format=json').json()
        sample_ids.append(sample_object.get('accession'))
        if 'donors' in sample_object:
            donors = sample_object.get('donors', [])
            for donor in donors:
                donor_object = requests.get(
                    portal_url + donor + '/@@object?format=json').json()
                donor_ids.add(donor_object.get('accession'))
        if 'targeted_sample_term' in sample_object:
            targeted_sample_term_object = requests.get(
                portal_url + sample_object.get('targeted_sample_term') + '/@@object?format=json').json()
            targeted_sample_term_name = targeted_sample_term_object.get(
                'term_name')
            classifications = ', '.join(sample_object.get('classifications'))
            simple_sample_summary = f'{targeted_sample_term_name} {classifications}'
            sample_term_ids.add(targeted_sample_term_object.get('term_id'))
        else:
            sample_terms = sample_object.get('sample_terms', [])
            sample_term_names = set()
            for sample_term in sample_terms:
                sample_term_object = requests.get(
                    portal_url + sample_term + '/@@object?format=json').json()
                sample_term_names.add(sample_term_object.get('term_name'))
                sample_term_ids.add(sample_term_object.get('term_id'))
            sample_term_names = ', '.join(list(sample_term_names))
            simple_sample_summary = f'{sample_term_names}'
        if 'treatments' in sample_object:
            treatment_term_names = set()
            for treatment in sample_object.get('treatments', []):
                treatment_object = requests.get(
                    portal_url + treatment + '/@@object?format=json').json()
                treatment_ids.add(treatment_object.get('treatment_term_id'))
                treatment_term_names.add(
                    treatment_object.get('treatment_term_name'))
            treatment_term_names = ', '.join(list(treatment_term_names))
            simple_sample_summary = f'{simple_sample_summary} treated with {treatment_term_names}'
            # Add support for treatment vs. untreated analyses later
        simple_sample_summaries.add(simple_sample_summary)

    _id = file_accession
    props = {
        '_key': _id,
        'file_set_id': file_set_accession,
        'lab': lab,
        'preferred_assay_title': check_if_multiple_values(preferred_assay_titles),
        'assay_term_id': check_if_multiple_values(assay_term_ids),
        'prediction': prediction,
        'prediction_method': prediction_method,
        'software': list(software) if software else None,
        'sample': check_if_multiple_values(sample_term_ids),
        'sample_id': sorted(sample_ids) if sample_ids else None,
        'simple_sample_summary': check_if_multiple_values(simple_sample_summaries),
        'donor_id': check_if_multiple_values(donor_ids),
        'treatments_term_ids': list(treatment_ids) if treatment_ids else None,
        'publication': publication_id
    }

    return props
