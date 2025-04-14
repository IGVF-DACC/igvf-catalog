from inspect import getfullargspec
import hashlib
from math import log10, floor, isinf

from db.arango_db import ArangoDB

import hgvs.dataproviders.uta
from hgvs.easy import parser
from hgvs.extras.babelfish import Babelfish
from biocommons.seqrepo import SeqRepo


ALLOWED_ASSEMBLIES = ['GRCh38', 'mm10', 'GRCm39']

seq_repo_human = None
seq_repo_mouse = None


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


<<<<<<< HEAD
def get_seqrepo(species='human'):
    global seq_repo_human, seq_repo_mouse
    if species == 'human':
        if seq_repo_human is None:
            seq_repo_human = SeqRepo('/usr/local/share/seqrepo/2018-11-26')
        return seq_repo_human
    else:
        if seq_repo_mouse is None:
            seq_repo_mouse = SeqRepo('/usr/local/share/seqrepo/mouse')
        return seq_repo_mouse


def is_variant_snv(spdi):
    spdi_list = spdi.split(':')
    if len(spdi_list) == 4 and len(spdi_list[2]) == 1 and len(spdi_list[3]) == 1:
        return True
    return False
=======
def query_fileset_files_props_encode(file_source_url):
    portal_url = 'https://www.encodeproject.org/'
    if not(file_source_url.startswith(portal_url)):
        raise ValueError(f'{file_source_url} does not start with {portal_url}')
>>>>>>> efc082a (pluralize properties)


<<<<<<< HEAD
def get_ref_seq_by_spdi(spdi, species='human'):
    seq_repo = get_seqrepo(species)
    spdi_list = spdi.split(':')
    chr_ref = spdi_list[0]
    start = int(spdi_list[1])
    end = start + 1
    return seq_repo[chr_ref][start:end]
=======
    # get software name
    software = set()
    if 'step_run' in file_object:
        analysis_step_run_object = requests.get(
            portal_url + file_object.get('step_run') + '/@@object?format=json').json()
        analysis_step_version_object = requests.get(
            portal_url + analysis_step_run_object.get('analysis_step_version') + '/@@object?format=json').json()
        software_versions = analysis_step_version_object.get(
            'software_versions')
        for software_version in software_versions:
            software_version_object = requests.get(
                portal_url + software_version + '/@@object?format=json').json()
            software_object = requests.get(
                portal_url + software_version_object.get('software') + '/@@object?format=json').json()
            software.add(software_object.get('name'))

    dataset_object = requests.get(
        portal_url + file_object.get('dataset') + '/@@object?format=json').json()
    lab = dataset_object.get('lab')
    file_set_accession = dataset_object.get('accession')
    file_set_object_type = dataset_object.get('@type')[0]

    preferred_assay_titles = set()
    assay_term_ids = set()

    # get prediction info
    prediction = False
    prediction_method = None
    if file_set_object_type == 'Annotation':
        if 'predictions' in dataset_object.get('annotation_type'):
            prediction = True
            prediction_method = dataset_object.get('annotation_type')
            if not(software):
                raise(ValueError(f'Predictions require software to be loaded.'))
        experimental_input = dataset_object.get('experimental_input', [])
        if experimental_input:
            for experiment in experimental_input:
                experiment_object = requests.get(
                    portal_url + experiment + '/@@object?format=json').json()
                assay_term_name = experiment_object.get('assay_term_name', '')
                if assay_term_name:
                    preferred_assay_titles.add(assay_term_name)
                assay_term_id = experiment_object.get('assay_term_id', '')
                if assay_term_id:
                    assay_term_ids.add(assay_term_id)

    # get assay
    assay_term_name = dataset_object.get('assay_term_name', [])
    if assay_term_name:
        if isinstance(assay_term_name, str):
            preferred_assay_titles.add(assay_term_name)
    else:
        preferred_assay_titles.update(assay_term_name)
    assay_term_id = dataset_object.get('assay_term_id')
    if assay_term_id:
        assay_term_ids.add(assay_term_id)

    # get publication
    publication_id = None
    publications = dataset_object.get('references', [])
    if publications:
        if len(publications) > 1:
            raise(ValueError(
                f'Loading multiple publications for a single file is not supported.'))
        publication_object = requests.get(
            portal_url + publications[0] + '/@@object?format=json').json()
        publication_id = publication_object.get('identifiers', [])[0]

    # get sample and treatment metadata
    sample_ids = set()
    donor_ids = set()
    sample_term_ids = set()
    simple_sample_summaries = set()
    treatment_ids = set()
    biosample_ontology = dataset_object.get('biosample_ontology')
    if biosample_ontology:
        biosample_type_object = requests.get(
            portal_url + dataset_object.get('biosample_ontology') + '/@@object?format=json').json()
        sample_term_ids.add(biosample_type_object.get('term_id'))
        biosample_type_term = biosample_type_object.get('term_name')
    replicates = dataset_object.get('replicates', [])
    if replicates:
        for replicate in dataset_object.get('replicates'):
            replicate_object = requests.get(
                portal_url + replicate + '/@@object?format=json').json()
            library = replicate_object.get('library')
            if library:
                library_object = requests.get(
                    portal_url + replicate_object.get('library') + '/@@object?format=json').json()
                biosample = library_object.get('biosample')
                if biosample:
                    biosample_object = requests.get(
                        portal_url + library_object.get('biosample') + '/@@object?format=json').json()
                    sample_ids.add(biosample_object.get('accession'))
                    biosample_type_object = requests.get(
                        portal_url + biosample_object.get('biosample_ontology') + '/@@object?format=json').json()
                    sample_term_id = biosample_type_object.get('term_id')
                    if sample_term_ids and sample_term_id not in sample_term_ids:
                        raise(ValueError(
                            f'Biosample type of the dataset is not the same as the biosamples.'))
                    else:
                        sample_term_ids.add(
                            biosample_type_object.get('term_id'))
                    simple_sample_summary = biosample_type_object.get(
                        'term_name')
                    donor = biosample_object.get('donor')
                    if donor:
                        donor_object = requests.get(
                            portal_url + biosample_object.get('donor') + '/@@object?format=json').json()
                        donor_ids.add(donor_object.get('accession'))
                    biosample_treatments = biosample_object.get(
                        'treatments', [])
                    if biosample_treatments:
                        treatment_term_names = set()
                        for treatment in biosample_object.get('treatments', []):
                            treatment_object = requests.get(
                                portal_url + treatment + '/@@object?format=json').json()
                            treatment_id = treatment_object.get(
                                'treatment_term_id')
                            if treatment_id:
                                treatment_ids.add(treatment_id)
                            treatment_term_names.add(
                                treatment_object.get('treatment_term_name'))
                        treatment_term_names = ', '.join(
                            sorted(list(treatment_term_names)))
                        simple_sample_summary = f'{simple_sample_summary} treated with {treatment_term_names}'
                    simple_sample_summaries.add(simple_sample_summary)
    if not(simple_sample_summaries) and biosample_type_term:
        simple_sample_summaries.add(biosample_type_term)
    dataset_treatments = dataset_object.get('treatments', [])
    if dataset_treatments:
        for treatment in dataset_treatments:
            treatment_object = requests.get(
                portal_url + treatment + '/@@object?format=json').json()
            if 'treatment_term_id' in treatment_object:
                treatment_ids.add(treatment_object.get('treatment_term_id'))

    _id = file_object.get('accession')
    props = {
        '_key': _id,
        'file_set_id': file_set_accession,
        'lab': lab,
        'preferred_assay_titles': sorted(list(preferred_assay_titles)) if preferred_assay_titles else None,
        'assay_term_ids': sorted(list(assay_term_ids)) if assay_term_ids else None,
        'prediction': prediction,
        'prediction_method': prediction_method,
        'software': sorted(list(software)) if software else None,
        'samples': sorted(list(sample_term_ids)) if sample_term_ids else None,
        'sample_ids': sorted(list(sample_ids)) if sample_ids else None,
        'simple_sample_summaries': sorted(list(simple_sample_summaries)) if simple_sample_summaries else None,
        'donor_ids': sorted(list(donor_ids)) if donor_ids else None,
        'treatments_term_ids': sorted(list(treatment_ids)) if treatment_ids else None,
        'publication': publication_id
    }

    return props
>>>>>>> efc082a (pluralize properties)
