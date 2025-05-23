import requests
import json

from typing import Optional
from adapters.writer import Writer

from adapters.helpers import check_collection_loaded


class FileFileSet:
    ALLOWED_LABELS = ['encode_file_fileset', 'encode_donor',
                      'encode_sample_term', 'igvf_file_fileset', 'igvf_donor', 'igvf_sample_term']

    def __init__(
        self,
        accessions: list[str],
        replace: bool = False,
        label='encode_file_fileset',
        writer: Optional[Writer] = None,
        **kwargs
    ):
        if label not in FileFileSet.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(FileFileSet.ALLOWED_LABELS))

        self.label = label
        self.writer = writer
        self.accessions = accessions
        # argument for replacing existing donor and sample term collections
        self.replace = replace

    @staticmethod
    def none_if_empty(value):
        return sorted(list(value)) if value else None

    def process_file(self):
        self.writer.open()
        for accession in self.accessions:
            print(f'Processing {accession}')
            if self.label in ['encode_file_fileset', 'encode_donor', 'encode_sample_term']:
                props, donors, sample_types = self.query_fileset_files_props_encode(
                    accession, self.replace)
                if self.label == 'encode_donor':
                    for donor_props in self.get_donor_props(donors, portal_url='https://www.encodeproject.org/', source='ENCODE'):
                        self.writer.write(json.dumps(donor_props) + '\n')
                elif self.label == 'encode_sample_term':
                    for sample_props in self.get_sample_term_props(sample_types, portal_url='https://www.encodeproject.org/', source='ENCODE'):
                        self.writer.write(json.dumps(sample_props) + '\n')
                else:
                    self.writer.write(json.dumps(props) + '\n')

            elif self.label in ['igvf_file_fileset', 'igvf_donor', 'igvf_sample_term']:
                props, donors, sample_terms = self.query_fileset_files_props_igvf(
                    accession, self.replace)
                if self.label == 'igvf_donor':
                    for donor_props in self.get_donor_props(donors, portal_url='https://api.data.igvf.org/', source='IGVF'):
                        self.writer.write(json.dumps(donor_props) + '\n')
                elif self.label == 'igvf_sample_term':
                    for sample_props in self.get_sample_term_props(sample_terms, portal_url='https://api.data.igvf.org/', source='IGVF'):
                        self.writer.write(json.dumps(sample_props) + '\n')
                else:
                    self.writer.write(json.dumps(props) + '\n')

        self.writer.close()

    def get_file_object(self, portal_url, accession):
        file_object = requests.get(
            portal_url + accession + '/@@embedded?format=json')
        if file_object.status_code == 403:
            raise ValueError(
                f'{accession} is not publicly released or access is restricted.')
        return file_object.json()

    def get_software_encode(self, file_object):
        software = set()
        software_versions = file_object.get(
            'analysis_step_version', {}).get('software_versions', [])
        software_titles = [
            software_version['software']['title']
            for software_version in software_versions
            if software_version.get('software')
        ]
        software.update(software_titles)
        return software

    def get_software_igvf(self, file_object, portal_url):
        software = set()
        if 'analysis_step_version' in file_object:
            analysis_step_version_object = requests.get(
                portal_url + file_object['analysis_step_version'] + '/@@object?format=json').json()
            software_versions = analysis_step_version_object['software_versions']
            for software_version in software_versions:
                software_version_object = requests.get(
                    portal_url + software_version + '/@@object?format=json').json()
                software_object = requests.get(
                    portal_url + software_version_object['software'] + '/@@object?format=json').json()
                software.add(software_object['title'])
        return software

    def parse_annotation(self, dataset_object, portal_url, class_type, method, software, preferred_assay_titles, assay_term_ids):
        method = dataset_object['annotation_type']
        if 'prediction' in dataset_object['annotation_type']:
            class_type = 'prediction'
            if not (software):
                software_used = dataset_object.get('software_used', [])
                if software_used:
                    software_titles = [
                        software_version['software']['title']
                        for software_version in software_used
                        if software_version.get('software')
                    ]
                    software.update(software_titles)
                else:
                    raise (ValueError(f'Predictions require software to be loaded.'))
        else:
            class_type = 'integrative analysis'
        for experiment in dataset_object.get('experimental_input', []):
            experiment_object = requests.get(
                portal_url + experiment + '/@@object?format=json').json()
            assay_term_name = experiment_object.get('assay_term_name', '')
            if assay_term_name:
                preferred_assay_titles.add(assay_term_name)
            assay_term_id = experiment_object.get('assay_term_id', '')
            if assay_term_id:
                assay_term_ids.add(assay_term_id)
        return class_type, method

    def get_assay_encode(self, dataset_object, preferred_assay_titles, assay_term_ids):
        assay_term_name = dataset_object.get('assay_term_name', [])
        if assay_term_name and not (preferred_assay_titles):
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

    def get_publication_encode(self, dataset_object):
        publication_id = None
        publications = dataset_object.get('references', [])
        if publications:
            if len(publications) > 1:
                raise (ValueError(
                    f'Loading multiple publications for a single file is not supported.'))
            publication_identifiers = publications[0].get('identifiers', [])
            if publication_identifiers:
                publication_id = publication_identifiers[0]
        return publication_id

    def get_publication_igvf(self, fileset_object, portal_url):
        publication_id = None
        publications = fileset_object.get('publications', [])
        if publications:
            if len(publications) > 1:
                raise (ValueError(
                    f'Loading multiple publications for a single file is not supported.'))
            publication_id = publications[0]['publication_identifiers'][0]
        return publication_id

    def parse_sample_donor_treatment_encode(
        self,
        dataset_object,
        portal_url,
        sample_ids,
        donor_ids,
        sample_term_to_sample_type,
        simple_sample_summaries,
        treatment_ids
    ):
        biosample_ontology = dataset_object.get('biosample_ontology')
        biosample_type_term = ''
        if biosample_ontology:
            sample_term_to_sample_type[biosample_ontology['term_id']
                                       ] = biosample_ontology['@id']
            biosample_type_term = biosample_ontology['term_name']
        for replicate in dataset_object.get('replicates', []):
            library = replicate.get('library')
            if library:
                biosample = library.get('biosample')
                if biosample:
                    sample_ids.add(biosample['accession'])
                    biosample_type_id = biosample['biosample_ontology']['@id']
                    sample_term_id = biosample['biosample_ontology']['term_id']
                    dataset_term_id = dataset_object.get(
                        'biosample_ontology', {}).get('term_id')
                    if dataset_term_id and sample_term_id != dataset_term_id:
                        raise ValueError(
                            'Biosample type of the dataset is not the same as the biosamples.')
                    if biosample_type_id not in sample_term_to_sample_type:
                        sample_term_to_sample_type[sample_term_id] = biosample_type_id
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
        if not (simple_sample_summaries) and biosample_type_term:
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

    def parse_sample_donor_treatment_igvf(
        self,
        fileset_object,
        portal_url,
        sample_ids,
        donor_ids,
        sample_term_ids,
        simple_sample_summaries,
        treatment_ids
    ):
        for sample in fileset_object.get('samples', []):
            sample_object = requests.get(
                portal_url + sample['@id'] + '/@@embedded?format=json').json()
            sample_ids.add(sample_object['accession'])
            donor_accessions = [donor['accession']
                                for donor in sample_object['donors']]
            donor_ids.update(donor_accessions)
            if 'targeted_sample_term' in sample:
                targeted_sample_term_object = requests.get(
                    portal_url + sample_object['targeted_sample_term']['@id'] + '/@@object?format=json').json()
                targeted_sample_term_name = targeted_sample_term_object['term_name']
                classifications = ', '.join(
                    sorted(sample_object['classifications']))
                simple_sample_summary = f'{targeted_sample_term_name} {classifications}'
                sample_term_ids.add(targeted_sample_term_object['term_id'])
            else:
                sample_terms = sample_object['sample_terms']
                sample_term_names = set()
                for sample_term in sample_terms:
                    sample_term_object = requests.get(
                        portal_url + sample_term['@id'] + '/@@object?format=json').json()
                    sample_term_names.add(sample_term_object.get('term_name'))
                    sample_term_ids.add(sample_term_object.get('term_id'))
                sample_term_names = ', '.join(sorted(list(sample_term_names)))
                simple_sample_summary = f'{sample_term_names}'
            if any(classification in ['organoid', 'gastruloid', 'embryoid', 'differentiated cell specimen', 'reprogrammed cell specimen'] for classification in sample_object['classifications']):
                donor_accessions = ', '.join(sorted(donor_accessions))
                simple_sample_summary = f'{simple_sample_summary} from {donor_accessions}'
            if 'treatments' in sample_object:
                treatment_term_names = set()
                for treatment in sample['treatments']:
                    treatment_object = requests.get(
                        portal_url + treatment['@id'] + '/@@object?format=json').json()
                    treatment_ids.add(treatment_object['treatment_term_id'])
                    treatment_term_names.add(
                        treatment_object['treatment_term_name'])
                treatment_term_names = ', '.join(
                    sorted(list(treatment_term_names)))
                simple_sample_summary = f'{simple_sample_summary} treated with {treatment_term_names}'
                # Add support for treatment vs. untreated analyses later
            simple_sample_summaries.add(simple_sample_summary)

    def decompose_analysis_set_to_measurement_set(self, portal_url, analysis_set_id, measurement_sets=set()):
        analysis_set_object = requests.get(
            portal_url + analysis_set_id + '/@@embedded?format=json').json()
        input_file_sets = analysis_set_object.get('input_file_sets', [])
        for input_file_set in input_file_sets:
            if input_file_set['@id'].startswith('/measurement-sets/'):
                measurement_sets.add(input_file_set['@id'])
            elif input_file_set['@id'].startswith('/auxiliary-sets/'):
                continue  # auxiliary sets are not analyzed without measurement sets so they can be skipped
            elif input_file_set['@id'].startswith('/construct-library-sets/'):
                construct_library_set_object = requests.get(
                    portal_url + input_file_set['@id'] + '/@@object_with_select_calculated_properties?field=applied_to_samples?format=json').json()
                for sample in construct_library_set_object.get('applied_to_samples', []):
                    sample_object = requests.get(
                        portal_url + sample + '@@object_with_select_calculated_properties?field=file_sets?format=json')
                    for file_set in sample_object.get('file_sets', []):
                        if file_set.startswith('/measurement-sets/'):
                            # construct library sets should be associated with some measurement set
                            measurement_sets.add(file_set)
            elif input_file_set['@id'].startswith('/analysis-sets/'):
                self.decompose_analysis_set_to_measurement_set(
                    portal_url, input_file_set['@id'], measurement_sets)
        return measurement_sets

    def parse_analysis_set(self, portal_url, fileset_object, preferred_assay_titles, assay_term_ids):
        for input_file_set in fileset_object.get('input_file_sets', []):
            measurement_sets = set()
            if input_file_set['@id'].startswith('/analysis-sets/'):
                measurement_sets = measurement_sets | self.decompose_analysis_set_to_measurement_set(
                    portal_url, input_file_set['@id'])
            if input_file_set['@id'].startswith('/measurement-sets/'):
                measurement_sets.add(input_file_set['@id'])
            for measurement_set in measurement_sets:
                measurement_set_object = requests.get(
                    portal_url + measurement_set + '/@@object?format=json').json()
                preferred_assay_titles.add(
                    measurement_set_object.get('preferred_assay_title'))
                assay_term = measurement_set_object.get('assay_term')
                assay_term_object = requests.get(
                    portal_url + assay_term + '/@@object?format=json').json()
                assay_term_ids.add(assay_term_object.get('term_id'))

    def check_hyperedges(self, donor_ids, sample_term_ids):
        unloaded_sample_terms = set()
        unloaded_donors = set()
        for donor_id in donor_ids:
            if not (check_collection_loaded('donors', donor_id)):
                print(f'{donor_id} not loaded in donor_ids')
                unloaded_donors.add(donor_id)
        for sample_term_id in sample_term_ids:
            if sample_term_id.startswith('NTR'):
                if not (check_collection_loaded('ontology_terms', sample_term_id)):
                    print(f'{sample_term_id} not loaded in ontology_terms')
                    unloaded_sample_terms.add(sample_term_id)
        return unloaded_donors, unloaded_sample_terms

    def query_fileset_files_props_encode(self, accession, replace):
        portal_url = 'https://www.encodeproject.org/'
        file_object = self.get_file_object(portal_url, accession)

        dataset_object = requests.get(
            portal_url + file_object['dataset'] + '/@@embedded?format=json').json()
        dataset_accession = dataset_object['accession']
        dataset_type = dataset_object['@type'][0]
        lab = dataset_object['lab']['name']

        software = self.get_software_encode(file_object)

        preferred_assay_titles = set()
        assay_term_ids = set()
        method = None
        class_type = None
        if dataset_type == 'Annotation':
            class_type, method = self.parse_annotation(
                dataset_object, portal_url, class_type, method, software, preferred_assay_titles, assay_term_ids)
            software_titles = ', '.join([software for software in software])
            method = f'{method} using {software_titles}'
        else:
            class_type = 'experimental'
        assay_term_ids, preferred_assay_titles = self.get_assay_encode(
            dataset_object, preferred_assay_titles, assay_term_ids)
        if class_type == 'experimental':
            if len(preferred_assay_titles) != 1:
                raise (ValueError(
                    f'Loading data from experimental data from multiple assays is unsupported.'))
            else:
                method = preferred_assay_titles[0]

        publication_id = self.get_publication_encode(dataset_object)

        sample_ids = set()
        donor_ids = set()
        sample_term_to_sample_type = {}
        simple_sample_summaries = set()
        treatment_ids = set()
        self.parse_sample_donor_treatment_encode(dataset_object, portal_url, sample_ids, donor_ids,
                                                 sample_term_to_sample_type, simple_sample_summaries, treatment_ids)

        sample_term_ids = [sample_term_id.replace(
            ':', '_') for sample_term_id in sample_term_to_sample_type.keys()]
        all_sample_types = list(sample_term_to_sample_type.values())
        unloaded_donors, unloaded_sample_terms = self.check_hyperedges(
            donor_ids, sample_term_ids)
        unloaded_sample_types = [sample_term_to_sample_type[unloaded_sample_term]
                                 for unloaded_sample_term in unloaded_sample_terms]

        props = {
            '_key': accession,
            'file_set_id': dataset_accession,
            'lab': lab,
            'preferred_assay_titles': self.none_if_empty(preferred_assay_titles),
            'assay_term_ids': self.none_if_empty(assay_term_ids),
            'method': method,
            'class': class_type,
            'software': self.none_if_empty(software),
            'samples': [f'ontology_terms/{sample_term_id}' for sample_term_id in sample_term_ids] if sample_term_ids else None,
            'sample_ids': self.none_if_empty(sample_ids),
            'simple_sample_summaries': self.none_if_empty(simple_sample_summaries),
            'donors': [f'donors/{donor_id}' for donor_id in donor_ids] if donor_ids else None,
            'treatments_term_ids': self.none_if_empty(treatment_ids),
            'publication': publication_id,
            'source': 'ENCODE'
        }
        if replace:
            return props, donor_ids, all_sample_types
        else:
            return props, unloaded_donors, unloaded_sample_types

    def query_fileset_files_props_igvf(self, accession, replace):
        portal_url = 'https://api.data.igvf.org/'
        file_object = self.get_file_object(portal_url, accession)

        fileset_object = requests.get(
            portal_url + file_object['file_set']['@id'] + '/@@embedded?format=json').json()
        fileset_accession = fileset_object['accession']
        fileset_object_type = fileset_object['@type'][0]
        lab = fileset_object['lab']['@id'].split('/')[2]

        software = self.get_software_igvf(file_object, portal_url)

        preferred_assay_titles = set()
        assay_term_ids = set()
        method = None
        class_type = None

        if fileset_object_type == 'PredictionSet':
            method = fileset_object.get('summary')
            class_type = 'prediction'
            if not (software):
                raise (ValueError(f'Prediction sets require software to be loaded.'))
            # Add prediction set assay info later when predictions from assays are submitted & loaded
        elif fileset_object_type == 'AnalysisSet':
            class_type = 'experimental'
            self.parse_analysis_set(
                portal_url, fileset_object, preferred_assay_titles, assay_term_ids)
        # add support for ModelSet later
        else:
            raise (ValueError(
                f'Loading data from file sets other than prediction sets and analysis sets is currently unsupported.'))
        preferred_assay_titles = self.none_if_empty(preferred_assay_titles)
        assay_term_ids = self.none_if_empty(assay_term_ids)
        if class_type == 'experimental':
            if len(preferred_assay_titles) != 1:
                raise (ValueError(
                    f'Loading data from experimental data from multiple assays is unsupported.'))
            else:
                method = preferred_assay_titles[0]

        publication_id = self.get_publication_igvf(fileset_object, portal_url)

        sample_ids = set()
        sample_term_ids = set()
        donor_ids = set()
        simple_sample_summaries = set()
        treatment_ids = set()
        self.parse_sample_donor_treatment_igvf(
            fileset_object, portal_url, sample_ids, donor_ids, sample_term_ids, simple_sample_summaries, treatment_ids)

        sample_term_ids = [sample_term_id.replace(
            ':', '_') for sample_term_id in sample_term_ids]
        unloaded_donors, unloaded_sample_terms = self.check_hyperedges(
            donor_ids, sample_term_ids)

        props = {
            '_key': accession,
            'file_set_id': fileset_accession,
            'lab': lab,
            'preferred_assay_titles': preferred_assay_titles,
            'assay_term_ids': assay_term_ids,
            'method': method,
            'class': class_type,
            'software': self.none_if_empty(software),
            'samples': [f'ontology_terms/{sample_term_id}' for sample_term_id in sample_term_ids] if sample_term_ids else None,
            'sample_ids': self.none_if_empty(sample_ids),
            'simple_sample_summaries': self.none_if_empty(simple_sample_summaries),
            'donors': [f'donors/{donor_id}' for donor_id in donor_ids] if donor_ids else None,
            'treatments_term_ids': self.none_if_empty(treatment_ids),
            'publication': publication_id,
            'source': 'IGVF'
        }
        if replace:
            return props, donor_ids, sample_term_ids
        else:
            return props, unloaded_donors, unloaded_sample_terms

    def get_donor_props(self, donors, portal_url, source):
        for donor in donors:
            donor_object = requests.get(
                portal_url + donor + '/@@embedded?format=json').json()
            phenotypic_feature_ids = None
            phenotypic_feature_names = None
            if source == 'IGVF':
                phenotypic_features = donor_object.get(
                    'phenotypic_features', [])
                if phenotypic_features:
                    phenotypic_feature_ids = self.none_if_empty(
                        [f"ontology_terms/{phenotypic_feature['feature']['term_id'].replace(':', '_')}" for phenotypic_feature in phenotypic_features])
                    phenotypic_feature_names = self.none_if_empty(
                        [phenotypic_feature['feature']['term_name'] for phenotypic_feature in phenotypic_features])
            if source == 'ENCODE':
                phenotypic_feature_names = donor_object.get(
                    'health_status', None)
                if phenotypic_feature_names:
                    phenotypic_feature_names = [phenotypic_feature_names]
            age = donor_object.get('age', None)
            if age:
                age = int(age)
            _props = {
                '_key': donor_object['accession'],
                'name': donor_object['accession'],
                'sex': donor_object.get('sex', None),
                'age': age,
                'age_units': donor_object.get('age_units', None),
                'ethnicities': self.none_if_empty(donor_object.get('ethnicity', None)),
                'phenotypic_features': phenotypic_feature_ids,
                'phenotypic_feature_names': phenotypic_feature_names,
                'source': source
            }
            yield _props

    def get_sample_term_props(self, sample_terms, portal_url, source):
        for sample_term in sample_terms:
            if source == 'IGVF':
                sample_term_object = requests.get(
                    portal_url + '/sample-terms/' + sample_term + '/@@embedded?format=json').json()
            else:
                sample_term_object = requests.get(
                    portal_url + sample_term + '/@@embedded?format=json').json()
            _props = {
                '_key': sample_term_object['term_id'].replace(':', '_'),
                'uri': portal_url[:-1] + sample_term_object['@id'],
                'name': sample_term_object['term_name'],
                'synonyms': self.none_if_empty(sample_term_object.get('synonyms', None)),
                'source': source
            }
            yield _props
