import requests
import json
from jsonschema import Draft202012Validator, ValidationError
from typing import Optional
from adapters.writer import Writer
from adapters.helpers import check_collection_loaded
from schemas.registry import get_schema
from urllib.parse import urljoin


class FileFileSet:
    ALLOWED_LABELS = ['encode_file_fileset', 'encode_donor',
                      'encode_sample_term', 'igvf_file_fileset', 'igvf_donor', 'igvf_sample_term']
    ENCODE_API = 'https://www.encodeproject.org/'
    IGVF_API = 'https://api.data.igvf.org/'
    ENCODE_SOURCE_URL = 'https://www.encodeproject.org/'
    IGVF_SOURCE_URL = 'https://data.igvf.org/'

    ENCODE_disease_id_mapping = {
        'DOID:0080832': 'HP:0100543',
        'DOID:2377': 'MONDO:0005301',
        'DOID:10652': 'MONDO:0004975',
        'DOID:0050861': 'MONDO:0005008',
        'DOID:0050873': 'MONDO:0018906',
        'DOID:0050902': 'MONDO:0007959',
        'DOID:0060318': 'MONDO:0012883',
        'DOID:0060534': 'MONDO:0006243',
        'DOID:0080199': 'MONDO:0005335',
        'DOID:0080505': 'MONDO:0007387',
        'DOID:10354': 'MONDO:0005219',
        'DOID:10907': 'MONDO:0001149',
        'DOID:11725': 'MONDO:0016033',
        'DOID:14250': 'MONDO:0008608',
        'DOID:14330': 'MONDO:0005180',
        'DOID:1749': 'MONDO:0005096',
        'DOID:1790': 'MONDO:0006292',
        'DOID:1909': 'MONDO:0005105',
        'DOID:2377': 'MONDO:0005301',
        'DOID:2526': 'MONDO:0005082',
        'DOID:2870': 'MONDO:0005461',
        'DOID:299': 'MONDO:0004970',
        'DOID:3008': 'MONDO:0004953',
        'DOID:305': 'MONDO:0004993',
        'DOID:4556': 'MONDO:0003050',
        'DOID:3068': 'MONDO:0018177',
        'DOID:3071': 'MONDO:0016681',
        'DOID:3111': 'MONDO:0005596',
        'DOID:3312': 'MONDO:0004985',
        'DOID:11758': 'MONDO:0001356',
        'DOID:3347': 'MONDO:0009807',
        'DOID:3355': 'MONDO:0005164',
        'DOID:3369': 'MONDO:0012817',
        'DOID:3412': 'MONDO:0005440',
        'DOID:3702': 'MONDO:0005153',
        'DOID:3721': 'MONDO:0005615',
        'DOID:9538': 'MONDO:0009693',
        'DOID:3910': 'MONDO:0005061',
        'DOID:4074': 'MONDO:0006047',
        'DOID:4450': 'MONDO:0005086',
        'DOID:4451': 'MONDO:0005206',
        'DOID:4905': 'MONDO:0005192',
        'DOID:5176': 'MONDO:0019004',
        'DOID:5603': 'MONDO:0003540',
        'DOID:6000': 'MONDO:0005009',
        'DOID:684': 'MONDO:0007256',
        'DOID:707': 'MONDO:0004095',
        'DOID:768': 'MONDO:0008380',
        'DOID:769': 'MONDO:0005072',
        'DOID:8552': 'MONDO:0011996',
        'DOID:8584': 'MONDO:0007243',
        'DOID:9538': 'MONDO:0009693',
        'DOID:9675': 'MONDO:0004849'
    }
    METHOD_TO_COLLECTIONS_ENCODE = {
        'caQTL': ['variants_genomic_elements', 'genomic_elements'],
        'CRISPR enhancer perturbation screens': ['genomic_elements', 'genomic_elements_genes'],
        'MPRA': ['genomic_elements_biosamples', 'genomic_elements'],
        'ENCODE-rE2G': ['genomic_elements', 'genomic_elements_genes'],
    }

    def __init__(
        self,
        accessions: list[str],
        replace: bool = False,
        label='encode_file_fileset',
        writer: Optional[Writer] = None,
        validate=False,
        **kwargs
    ):
        if label not in FileFileSet.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(FileFileSet.ALLOWED_LABELS))

        self.label = label
        if label in ['encode_file_fileset', 'encode_donor', 'encode_sample_term']:
            self.api_url = self.ENCODE_API
            self.source_url = self.ENCODE_SOURCE_URL
            self.source = 'ENCODE'
        elif label in ['igvf_file_fileset', 'igvf_donor', 'igvf_sample_term']:
            self.api_url = self.IGVF_API
            self.source_url = self.IGVF_SOURCE_URL
            self.source = 'IGVF'
        self.writer = writer
        self.accessions = accessions
        # argument for replacing existing donor and sample term collections
        self.replace = replace
        self.validate = validate
        if self.validate:
            if self.label in ['encode_donor', 'igvf_donor']:
                self.schema = get_schema(
                    'nodes', 'donors', self.__class__.__name__)
            elif self.label in ['encode_sample_term', 'igvf_sample_term']:
                self.schema = get_schema(
                    'nodes', 'ontology_terms', self.__class__.__name__)
            else:
                self.schema = get_schema(
                    'nodes', 'files_filesets', self.__class__.__name__)
            self.validator = Draft202012Validator(self.schema)

    def validate_doc(self, doc):
        try:
            self.validator.validate(doc)
        except ValidationError as e:
            raise ValueError(f'Document validation failed: {e.message}, {doc}')

    @staticmethod
    def none_if_empty(value):
        return sorted(list(value)) if value else None

    def write_jsonl(self, obj):
        self.writer.write(json.dumps(obj) + '\n')

    def process_file(self):
        self.writer.open()
        for accession in self.accessions:
            print(f'Processing {accession}')

            if self.label in ['encode_file_fileset', 'encode_donor', 'encode_sample_term']:
                props, donors, sample_types, disease_ids = self.query_fileset_files_props_encode(
                    accession)
            else:
                props, donors, sample_types = self.query_fileset_files_props_igvf(
                    accession)
                disease_ids = []  # IGVF does not return this

            if self.label in ['encode_donor', 'igvf_donor']:
                for donor_props in self.get_donor_props(donors, disease_ids):
                    if self.validate:
                        self.validate_doc(donor_props)
                    self.write_jsonl(donor_props)
            elif self.label in ['encode_sample_term', 'igvf_sample_term']:
                for sample_props in self.get_sample_term_props(sample_types):
                    if self.validate:
                        self.validate_doc(sample_props)
                    self.write_jsonl(sample_props)
            else:
                if self.validate:
                    self.validate_doc(props)
                self.write_jsonl(props)

        self.writer.close()

    def get_file_object(self, accession):
        url = urljoin(self.api_url, accession + '/@@embedded?format=json')
        response = requests.get(url)
        if response.status_code == 403:
            raise ValueError(
                f'{accession} is not publicly released or access is restricted.')
        return response.json()

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

    def get_software_igvf(self, file_object):
        software = set()
        if 'analysis_step_version' in file_object:
            analysis_step_version_object = requests.get(
                urljoin(self.api_url, file_object['analysis_step_version']['@id'] + '/@@object?format=json')).json()
            software_versions = analysis_step_version_object['software_versions']
            for software_version in software_versions:
                software_version_object = requests.get(
                    urljoin(self.api_url, software_version + '/@@object?format=json')).json()
                software_object = requests.get(
                    urljoin(self.api_url, software_version_object['software'] + '/@@object?format=json')).json()
                software.add(software_object['title'])
        return software

    def parse_annotation_encode(self, dataset_object, software):
        preferred_assay_titles = set()
        assay_term_ids = set()
        method = dataset_object['annotation_type']
        class_type = None
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
            class_type = 'observed data'
            if dataset_object['annotation_type'] == 'caQTLs':
                method = 'caQTL'

        for experiment in dataset_object.get('experimental_input', []):
            experiment_object = requests.get(
                urljoin(self.api_url, experiment + '/@@object?format=json')).json()
            assay_term_name = experiment_object.get('assay_term_name', '')
            if assay_term_name:
                preferred_assay_titles.add(assay_term_name)
            assay_term_id = experiment_object.get('assay_term_id', '')
            if assay_term_id:
                assay_term_ids.add(assay_term_id)

        disease_ids = dataset_object.get('disease_term_id', [])

        return class_type, method, disease_ids, preferred_assay_titles, assay_term_ids

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

    def get_publication_igvf(self, fileset_object):
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
        dataset_object
    ):
        sample_ids = set()
        donor_ids = set()
        sample_term_to_sample_type = {}
        simple_sample_summaries = set()
        treatment_ids = set()
        biosample_ontology = dataset_object.get('biosample_ontology')
        biosample_type_term = ''
        if biosample_ontology:
            sample_term_to_sample_type[biosample_ontology['term_id']
                                       ] = biosample_ontology['@id']
            biosample_type_term = biosample_ontology['term_name']
            classification = biosample_ontology['classification']
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
                    urljoin(self.api_url, donor + '/@@object?format=json')).json()
                donor_accession = donor_object['accession']
                donor_ids.add(donor_accession)
                if classification in ['in vitro differentiated cells', 'primary cell', 'tissue', 'organoid']:
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
        return sample_ids, donor_ids, sample_term_to_sample_type, simple_sample_summaries, treatment_ids

    def parse_sample_donor_treatment_igvf(
        self,
        fileset_object
    ):
        sample_ids = set()
        sample_term_ids = set()
        donor_ids = set()
        simple_sample_summaries = set()
        treatment_ids = set()
        for sample in fileset_object.get('samples', []):
            sample_object = requests.get(
                urljoin(self.api_url, sample['@id'] + '/@@embedded?format=json')).json()
            sample_ids.add(sample_object['accession'])
            donor_accessions = [donor['accession']
                                for donor in sample_object['donors']]
            donor_ids.update(donor_accessions)
            if 'targeted_sample_term' in sample:
                targeted_sample_term_object = requests.get(
                    urljoin(self.api_url, sample_object['targeted_sample_term']['@id'] + '/@@object?format=json')).json()
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
                        urljoin(self.api_url, sample_term['@id'] + '/@@object?format=json')).json()
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
                        urljoin(self.api_url, treatment['@id'] + '/@@object?format=json')).json()
                    treatment_ids.add(treatment_object['treatment_term_id'])
                    treatment_term_names.add(
                        treatment_object['treatment_term_name'])
                treatment_term_names = ', '.join(
                    sorted(list(treatment_term_names)))
                simple_sample_summary = f'{simple_sample_summary} treated with {treatment_term_names}'
                # Add support for treatment vs. untreated analyses later
            simple_sample_summaries.add(simple_sample_summary)
        return sample_ids, donor_ids, sample_term_ids, simple_sample_summaries, treatment_ids

    def decompose_analysis_set_to_measurement_set_igvf(self, analysis_set_id, measurement_sets=set()):
        analysis_set_object = requests.get(
            urljoin(self.api_url, analysis_set_id + '/@@embedded?format=json')).json()
        input_file_sets = analysis_set_object.get('input_file_sets', [])
        for input_file_set in input_file_sets:
            if input_file_set['@id'].startswith('/measurement-sets/'):
                measurement_sets.add(input_file_set['@id'])
            elif input_file_set['@id'].startswith('/auxiliary-sets/'):
                continue  # auxiliary sets are not analyzed without measurement sets so they can be skipped
            elif input_file_set['@id'].startswith('/construct-library-sets/'):
                construct_library_set_object = requests.get(
                    urljoin(self.api_url, input_file_set['@id'] + '/@@object_with_select_calculated_properties?field=applied_to_samples?format=json')).json()
                for sample in construct_library_set_object.get('applied_to_samples', []):
                    sample_object = requests.get(
                        urljoin(self.api_url, sample + '@@object_with_select_calculated_properties?field=file_sets?format=json')).json()
                    for file_set in sample_object.get('file_sets', []):
                        if file_set.startswith('/measurement-sets/'):
                            # construct library sets should be associated with some measurement set
                            measurement_sets.add(file_set)
            elif input_file_set['@id'].startswith('/analysis-sets/'):
                self.decompose_analysis_set_to_measurement_set_igvf(
                    input_file_set['@id'], measurement_sets)
        return measurement_sets

    def parse_analysis_set_igvf(self, fileset_object):
        preferred_assay_titles = set()
        assay_term_ids = set()
        for input_file_set in fileset_object.get('input_file_sets', []):
            measurement_sets = set()
            if input_file_set['@id'].startswith('/analysis-sets/'):
                measurement_sets = measurement_sets | self.decompose_analysis_set_to_measurement_set_igvf(
                    input_file_set['@id'])
            if input_file_set['@id'].startswith('/measurement-sets/'):
                measurement_sets.add(input_file_set['@id'])
            for measurement_set in measurement_sets:
                measurement_set_object = requests.get(
                    urljoin(self.api_url, measurement_set + '/@@object?format=json')).json()
                preferred_assay_titles.add(
                    measurement_set_object.get('preferred_assay_titles', [])[0])
                assay_term = measurement_set_object.get('assay_term')
                assay_term_object = requests.get(
                    urljoin(self.api_url, assay_term + '/@@object?format=json')).json()
                assay_term_ids.add(assay_term_object.get('term_id'))
        return preferred_assay_titles, assay_term_ids

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

    def query_fileset_files_props_encode(self, accession):
        file_object = self.get_file_object(accession)
        source_url = urljoin(self.source_url, file_object['@id'])
        dataset_object = requests.get(
            urljoin(self.api_url, file_object['dataset'] + '/@@embedded?format=json')).json()
        dataset_accession = dataset_object['accession']
        dataset_type = dataset_object['@type'][0]
        lab = dataset_object['lab']['name']

        software = self.get_software_encode(file_object)

        preferred_assay_titles = set()
        assay_term_ids = set()
        method = None
        class_type = 'observed data'
        disease_ids = []
        if dataset_type == 'Annotation':
            class_type, method, disease_ids, preferred_assay_titles, assay_term_ids = self.parse_annotation_encode(
                dataset_object, software)
            if software and method not in ['candidate Cis-Regulatory Elements', 'caQTL', 'MPRA']:
                method = list(software)[0]
                # manually set the method to ENCODE-rE2G for Distal regulation ENCODE-rE2G
                if method == 'Distal regulation ENCODE-rE2G':
                    method = 'ENCODE-rE2G'
        assay_term_ids, preferred_assay_titles = self.get_assay_encode(
            dataset_object, preferred_assay_titles, assay_term_ids)
        if class_type == 'observed data' and preferred_assay_titles:
            if len(preferred_assay_titles) != 1:
                raise (ValueError(
                    f'Loading data from experimental data from multiple assays is unsupported.'))
            else:
                method = preferred_assay_titles[0]

        publication_id = self.get_publication_encode(dataset_object)

        sample_ids, donor_ids, sample_term_to_sample_type, simple_sample_summaries, treatment_ids = self.parse_sample_donor_treatment_encode(
            dataset_object)

        sample_term_ids = [sample_term_id.replace(
            ':', '_') for sample_term_id in sample_term_to_sample_type.keys()]
        all_sample_types = list(sample_term_to_sample_type.values())
        # manually set the method to ENCODE-rE2G for file ENCFF968BZL
        if accession == 'ENCFF968BZL':
            method = 'CRISPR enhancer perturbation screens'

        if accession == 'ENCFF420VPZ':
            catalog_collections = ['genomic_elements']
        elif accession == 'ENCFF167FJQ':
            catalog_collections = ['mm_genomic_elements']
        else:
            catalog_collections = self.METHOD_TO_COLLECTIONS_ENCODE.get(
                method, [])
        if not catalog_collections:
            raise (ValueError(
                f'Catalog collections are required for file_fileset {dataset_accession}.'))

        props = {
            '_key': accession,
            'name': accession,
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
            'donors': sorted([f'donors/{donor_id}' for donor_id in donor_ids]) if donor_ids else None,
            'treatments_term_ids': self.none_if_empty(treatment_ids),
            'publication': publication_id,
            'collections': catalog_collections,
            'source': self.source,
            'source_url': source_url
        }
        if self.replace:
            return props, donor_ids, all_sample_types, disease_ids
        else:
            unloaded_donors, unloaded_sample_terms = self.check_hyperedges(
                donor_ids, sample_term_ids)
            unloaded_sample_types = [sample_term_to_sample_type[unloaded_sample_term]
                                     for unloaded_sample_term in unloaded_sample_terms]
            return props, unloaded_donors, unloaded_sample_types, disease_ids

    def query_fileset_files_props_igvf(self, accession):
        file_object = self.get_file_object(accession)
        source_url = urljoin(self.source_url, file_object['@id'])
        class_type = file_object.get('catalog_class')

        fileset_object = requests.get(
            urljoin(self.api_url, file_object['file_set']['@id'] + '/@@embedded?format=json')).json()
        fileset_accession = fileset_object['accession']
        fileset_object_type = fileset_object['@type'][0]
        lab = fileset_object['lab']['@id'].split('/')[2]
        catalog_collections = file_object.get('catalog_collections', [])
        if not catalog_collections:
            raise (ValueError(
                f'Catalog collections are required for file_fileset {fileset_accession}.'))

        software = self.get_software_igvf(file_object)

        preferred_assay_titles = set()
        assay_term_ids = set()
        method = list(software)[0] if software else None

        if fileset_object_type == 'PredictionSet' and not (software):
            raise (ValueError(f'Prediction sets require software to be loaded.'))
        if fileset_object_type not in ['PredictionSet', 'AnalysisSet', 'CuratedSet']:
            raise (ValueError(
                f'Loading data from file sets other than prediction sets, analysis sets, and curated sets is currently unsupported.'))
        if fileset_object_type == 'AnalysisSet':
            preferred_assay_titles, assay_term_ids = self.parse_analysis_set_igvf(
                fileset_object)
            if len(preferred_assay_titles) != 1:
                raise (ValueError(
                    f'Loading data from experimental data from multiple assays is unsupported.'))
            method = list(preferred_assay_titles)[0]
        if fileset_object_type == 'CuratedSet' and not method:
            method = fileset_object.get('summary')

        preferred_assay_titles = self.none_if_empty(preferred_assay_titles)
        assay_term_ids = self.none_if_empty(assay_term_ids)

        publication_id = self.get_publication_igvf(fileset_object)

        sample_ids, donor_ids, sample_term_ids, simple_sample_summaries, treatment_ids = self.parse_sample_donor_treatment_igvf(
            fileset_object)

        sample_term_ids = [sample_term_id.replace(
            ':', '_') for sample_term_id in sample_term_ids]

        props = {
            '_key': accession,
            'name': accession,
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
            'donors': sorted([f'donors/{donor_id}' for donor_id in donor_ids]) if donor_ids else None,
            'treatments_term_ids': self.none_if_empty(treatment_ids),
            'publication': publication_id,
            'collections': catalog_collections,
            'source': self.source,
            'source_url': source_url
        }
        if self.replace:
            return props, donor_ids, sample_term_ids
        else:
            unloaded_donors, unloaded_sample_terms = self.check_hyperedges(
                donor_ids, sample_term_ids)
            return props, unloaded_donors, unloaded_sample_terms

    def get_donor_props(self, donors, disease_ids=[]):
        for donor in donors:
            donor_url = urljoin(self.api_url, donor +
                                '/@@embedded?format=json')
            donor_object = requests.get(donor_url).json()
            id = donor_object['@id']
            source_url = urljoin(self.source_url, id)

            accession = donor_object['accession']
            sex = donor_object.get('sex')
            age = donor_object.get('age')
            age_units = donor_object.get('age_units')

            if self.source == 'IGVF':
                phenotypic_features = donor_object.get(
                    'phenotypic_features', [])
                phenotypic_feature_ids = self.none_if_empty([
                    f"ontology_terms/{pf['feature']['term_id'].replace(':', '_')}"
                    for pf in phenotypic_features
                ])
                ethnicities = self.none_if_empty(
                    donor_object.get('ethnicities', []))

            elif self.source == 'ENCODE':
                ethnicities = self.none_if_empty(
                    donor_object.get('ethnicity', []))
                phenotypic_feature_ids = None
                if disease_ids:
                    phenotypic_feature_ids = self.none_if_empty([
                        f"ontology_terms/{self.ENCODE_disease_id_mapping.get(disease_id, disease_id).replace(':', '_')}"
                        for disease_id in disease_ids
                    ])

            doc = {
                '_key': accession,
                'name': accession,
                'sex': sex,
                'age': age,
                'age_units': age_units,
                'ethnicities': ethnicities,
                'phenotypic_features': phenotypic_feature_ids,
                'source': self.source,
                'source_url': source_url
            }
            if self.validate:
                self.validate_doc(doc)
            yield doc

    def get_sample_term_props(self, sample_terms):
        for sample_term in sample_terms:
            if self.source == 'IGVF':
                sample_term_object = requests.get(
                    self.api_url + 'sample-terms/' + sample_term + '/@@embedded?format=json').json()
            else:
                sample_term_object = requests.get(
                    self.api_url + sample_term + '/@@embedded?format=json').json()
            term_id = sample_term_object['term_id'].replace(':', '_')
            uri = urljoin(self.source_url, sample_term_object['@id'])
            _props = {
                '_key': term_id,
                'uri': uri,
                'term_id': term_id,
                'name': sample_term_object['term_name'],
                'synonyms': self.none_if_empty(sample_term_object.get('synonyms', None)),
                'source': self.source,
                'source_url': uri
            }
            if self.validate:
                self.validate_doc(_props)
            yield _props
