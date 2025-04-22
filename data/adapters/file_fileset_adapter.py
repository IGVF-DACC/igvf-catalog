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


def query_fileset_files_props_encode(accession):
    portal_url = 'https://www.encodeproject.org/'

    if accession.startswith('IGVFFI'):
        igvf_file_object = requests.get(
            'https://www.data.igvf.org/' + accession + '/@@object?format=json')
        if file_object.status_code == 403:
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
        file_source_url = f'{portal_url}{accession}'
    else:
        raise ValueError(f'Invalid accession given: {accession}')

    file_object = requests.get(file_source_url + '/@@object?format=json')
    if file_object.status_code == 403:
        raise ValueError(
            f'{accession} is not publicly released or access is restricted.')
    file_object = file_object.json()
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

    props = {
        '_key': accession,
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
