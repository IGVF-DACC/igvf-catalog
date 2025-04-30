import requests
import json

from typing import Optional
from adapters.writer import Writer


class FileFileSet:
    ALLOWED_LABELS = ['encode_file_fileset']

    def __init__(
        self,
        accession: str,
        label='encode_file_fileset',
        writer: Optional[Writer] = None,
        **kwargs
    ):
        if label not in FileFileSet.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(FileFileSet.ALLOWED_LABELS))

        self.label = label
        self.writer = writer
        self.accession = accession

    def process_file(self):
        self.writer.open()
        if self.label == 'encode_file_fileset':
            _props = query_fileset_files_props_encode(self.accession)
            self.writer.write(json.dumps(_props) + '\n')

        self.writer.close()


def none_if_empty(value):
    return sorted(list(value)) if value else None


def get_file_object(accession):
    if accession.startswith('IGVFFI'):
        igvf_file_object = requests.get(
            'https://www.data.igvf.org/' + accession + '/@@object?format=json')
        if igvf_file_object.status_code == 403:
            raise ValueError(
                f'{accession} is not publicly released or access is restricted.')
        igvf_file_object = igvf_file_object.json()
        dbxrefs = igvf_file_object.get('dbxrefs', [])
        encff_id = ''
        if not(dbxrefs) or not(any(dbxref.startswith('ENCODE') for dbxref in dbxrefs)):
            raise(ValueError(
                f'IGVF source given for ENCODE file, but there is no reference to the ENCFF ID.'))
        for dbxref in dbxrefs:
            if dbxref.startswith('ENCODE'):
                encff_id = dbxref.split(':')[1]
        if not encff_id:
            raise(ValueError(
                f'IGVF source given for ENCODE file, but there is no reference to the ENCFF ID.'))
        elif len([dbxref for dbxref in dbxrefs if dbxref.startswith('ENCODE')]) > 1:
            raise ValueError(
                'More than one ENCODE reference found in dbxrefs.')
        accession = encff_id

    elif accession.startswith('ENCFF'):
        file_source_url = f'https://www.encodeproject.org/{accession}'
    else:
        raise ValueError(f'Invalid accession given: {accession}')

    file_object = requests.get(file_source_url + '/@@embedded?format=json')
    if file_object.status_code == 403:
        raise ValueError(
            f'{accession} is not publicly released or access is restricted.')
    return file_object.json()


def get_software(file_object):
    software = set()
    software_versions = file_object.get(
        'analysis_step_version', {}).get('software_versions', [])
    software_names = [
        software_version['software']['name']
        for software_version in software_versions
        if software_version.get('software')
    ]
    software.update(software_names)
    return software


def get_annotation_info(dataset_object, portal_url, prediction, prediction_method, software, preferred_assay_titles, assay_term_ids):
    if 'prediction' in dataset_object['annotation_type']:
        prediction = True
        prediction_method = dataset_object['annotation_type']
    if not(software):
        software_used = dataset_object.get('software_used', [])
        if software_used:
            software_names = [
                software_version['software']['name']
                for software_version in software_used
                if software_version.get('software')
            ]
            software.update(software_names)
        else:
            raise(ValueError(f'Predictions require software to be loaded.'))
    for experiment in dataset_object.get('experimental_input', []):
        experiment_object = requests.get(
            portal_url + experiment + '/@@object?format=json').json()
        assay_term_name = experiment_object.get('assay_term_name', '')
        if assay_term_name:
            preferred_assay_titles.add(assay_term_name)
        assay_term_id = experiment_object.get('assay_term_id', '')
        if assay_term_id:
            assay_term_ids.add(assay_term_id)
    return prediction, prediction_method


def get_assay(dataset_object, preferred_assay_titles, assay_term_ids):
    assay_term_name = dataset_object.get('assay_term_name', [])
    if assay_term_name and not(preferred_assay_titles):
        if isinstance(assay_term_name, str):
            preferred_assay_titles.add(assay_term_name)
        else:
            preferred_assay_titles.update(assay_term_name)
    assay_term_id = dataset_object.get('assay_term_id')
    if assay_term_id:
        assay_term_ids.add(assay_term_id)
    preferred_assay_titles = sorted(list(preferred_assay_titles))
    assay_term_ids = sorted(list(assay_term_ids))
    return assay_term_ids, preferred_assay_titles


def get_publication(dataset_object):
    publication_id = None
    publications = dataset_object.get('references', [])
    if publications:
        if len(publications) > 1:
            raise(ValueError(
                f'Loading multiple publications for a single file is not supported.'))
        publication_identifiers = publications[0].get('identifiers', [])
        if publication_identifiers:
            publication_id = publication_identifiers[0]
    return publication_id


def get_sample_and_donor(
    dataset_object,
    portal_url,
    sample_ids,
    donor_ids,
    sample_term_ids,
    simple_sample_summaries,
    treatment_ids
):
    biosample_ontology = dataset_object.get('biosample_ontology')
    biosample_type_term = ''
    if biosample_ontology:
        sample_term_ids.add(biosample_ontology['term_id'])
        biosample_type_term = biosample_ontology['term_name']
    for replicate in dataset_object.get('replicates', []):
        library = replicate.get('library')
        if library:
            biosample = library.get('biosample')
            if biosample:
                sample_ids.add(biosample['accession'])
                sample_term_id = biosample['biosample_ontology']['term_id']
                if sample_term_ids and sample_term_id not in sample_term_ids:
                    raise(ValueError(
                        f'Biosample type of the dataset is not the same as the biosamples.'))
                else:
                    sample_term_ids.add(sample_term_id)
                simple_sample_summary = biosample['biosample_ontology']['term_name']
                donor = biosample.get('donor')
                if donor:
                    donor_accession = donor['accession']
                    donor_ids.add(donor_accession)
                    if biosample['biosample_ontology']['classification'] in ['in vitro differentiated cells', 'primary cell', 'tissue', 'organoid']:
                        simple_sample_summary = f'{simple_sample_summary} from {donor_accession}'
                biosample_treatments = biosample.get('treatments', [])
                if biosample_treatments:
                    treatment_term_names = set()
                    for treatment in biosample_treatments:
                        treatment_id = treatment.get('treatment_term_id')
                        if treatment_id:
                            treatment_ids.add(treatment_id)
                        treatment_term_names.add(
                            treatment['treatment_term_name'])
                    treatment_term_names = ', '.join(
                        sorted(list(treatment_term_names)))
                    simple_sample_summary = f'{simple_sample_summary} treated with {treatment_term_names}'
                simple_sample_summaries.add(simple_sample_summary)
    if not(simple_sample_summaries) and biosample_type_term:
        simple_sample_summary = f'{biosample_type_term}'
        donor = dataset_object.get('donor', '')
        if donor:
            donor_object = requests.get(
                portal_url + donor + '/@@object?format=json').json()
            donor_accession = donor_object['accession']
            donor_ids.add(donor_accession)
            simple_sample_summary = f'{simple_sample_summary} from {donor_accession}'
        treatments = dataset_object.get('treatments', [])
        treatment_term_names = set()
        for treatment in treatments:
            treatment_id = treatment.get('treatment_term_id')
            if treatment_id:
                treatment_ids.add(treatment_id)
                treatment_term_names.add(treatment['treatment_term_name'])
        if treatment_term_names:
            treatment_term_names = ', '.join(
                sorted(list(treatment_term_names)))
            simple_sample_summary = f'{simple_sample_summary} treated with {treatment_term_names}'
        simple_sample_summaries.add(simple_sample_summary)


def query_fileset_files_props_encode(accession):
    portal_url = 'https://www.encodeproject.org/'
    file_object = get_file_object(accession)

    dataset_object = requests.get(
        portal_url + file_object.get('dataset') + '/@@embedded?format=json').json()
    lab = dataset_object['lab']['name']
    file_set_accession = dataset_object['accession']
    file_set_object_type = dataset_object['@type'][0]

    software = get_software(file_object)

    preferred_assay_titles = set()
    assay_term_ids = set()
    prediction = False
    prediction_method = None
    if file_set_object_type == 'Annotation':
        prediction, prediction_method = get_annotation_info(
            dataset_object, portal_url, prediction, prediction_method, software, preferred_assay_titles, assay_term_ids)
    assay_term_ids, preferred_assay_titles = get_assay(
        dataset_object, preferred_assay_titles, assay_term_ids)
    publication_id = get_publication(dataset_object)

    sample_ids = set()
    donor_ids = set()
    sample_term_ids = set()
    simple_sample_summaries = set()
    treatment_ids = set()
    get_sample_and_donor(dataset_object, portal_url, sample_ids, donor_ids,
                         sample_term_ids, simple_sample_summaries, treatment_ids)

    props = {
        '_key': accession,
        'file_set_id': file_set_accession,
        'lab': lab,
        'preferred_assay_titles': none_if_empty(preferred_assay_titles),
        'assay_term_ids': none_if_empty(assay_term_ids),
        'prediction': prediction,
        'prediction_method': prediction_method,
        'software': none_if_empty(software),
        'samples': none_if_empty(sample_term_ids),
        'sample_ids': none_if_empty(sample_ids),
        'simple_sample_summaries': none_if_empty(simple_sample_summaries),
        'donor_ids': none_if_empty(donor_ids),
        'treatments_term_ids': none_if_empty(treatment_ids),
        'publication': publication_id
    }

    return props
