import requests
import json
from jsonschema import Draft202012Validator, ValidationError
from typing import Optional
from adapters.writer import Writer
from schemas.registry import get_schema
from urllib.parse import urljoin


class FileFileSet:
    ALLOWED_LABELS = ['encode_file_fileset', 'encode_donor',
                      'encode_sample_term', 'igvf_file_fileset', 'igvf_donor', 'igvf_sample_term']
    ENCODE_API = 'https://www.encodeproject.org/'
    IGVF_API = 'https://api.data.igvf.org/'
    ENCODE_SOURCE_URL = 'https://www.encodeproject.org/'
    IGVF_SOURCE_URL = 'https://data.igvf.org/'
    SOURCE_ENCODE = 'ENCODE'
    SOURCE_IGVF = 'IGVF'

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
        'CRISPR enhancer perturbation screen': ['genomic_elements', 'genomic_elements_genes'],
        'MPRA': ['genomic_elements_biosamples', 'genomic_elements'],
        'ENCODE-rE2G': ['genomic_elements', 'genomic_elements_genes'],
    }

    def __init__(
        self,
        accessions: list[str],
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
            self.source = FileFileSet.SOURCE_ENCODE
        elif label in ['igvf_file_fileset', 'igvf_donor', 'igvf_sample_term']:
            self.api_url = self.IGVF_API
            self.source_url = self.IGVF_SOURCE_URL
            self.source = FileFileSet.SOURCE_IGVF
        self.writer = writer
        self.accessions = accessions
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

    @staticmethod
    def get_batch_objects(
        ids: list[str],
        fields: list[str] | None = None,
        id_type: str = 'accession',
        api_url: str = IGVF_API
    ) -> list[dict]:
        if id_type not in ['accession', '@id']:
            raise ValueError('id_type must be "accession" or "@id".')
        fields = fields or []
        if not ids:
            return []
        if isinstance(ids, (set, frozenset)):
            ids = sorted(ids)
        else:
            ids = list(ids)
        batch_size = 50 if id_type == 'accession' else 20
        fields_query = '&'.join(f'field={field}' for field in fields)
        objects: list[dict] = []
        for start in range(0, len(ids), batch_size):
            batch_ids = ids[start:start + batch_size]
            ids_query = '&'.join(
                f'{id_type}={item_id}' for item_id in batch_ids)
            query = '&'.join(part for part in [
                             ids_query, fields_query] if part)
            url = f'{api_url}search/?{query}&format=json&limit=all'
            print(url)
            response = requests.get(url)
            objects.extend(response.json().get('@graph', []))
        return objects

    def process_file(self):
        self.writer.open()
        visited_donors = set()
        visited_sample_terms = set()
        file_objects = self.get_batch_objects(
            self.accessions,
            fields=[
                '@id',
                'accession',
                'href',
                'dataset',
                'analysis_step_version',
                'derived_manually',
                'derived_from',
                'catalog_class',
                'file_set',
                'catalog_collections'
            ],
            id_type='accession',
            api_url=self.api_url
        )
        for file_object in file_objects:
            print(f'Processing {file_object["accession"]}')

            if self.label in ['encode_file_fileset', 'encode_donor', 'encode_sample_term']:
                props, donors, sample_types, disease_ids = self.query_fileset_files_props_encode(
                    file_object)
            else:
                props, donors, sample_types = self.query_fileset_files_props_igvf(
                    file_object)
                disease_ids = []  # IGVF does not return this

            if self.label in ['encode_donor', 'igvf_donor']:
                for donor_props in self.get_donor_props(self.api_url, self.source_url, self.source, donors, disease_ids):
                    if donor_props['_key'] in visited_donors:
                        continue
                    visited_donors.add(donor_props['_key'])
                    if self.validate:
                        self.validate_doc(donor_props)
                    self.write_jsonl(donor_props)
            elif self.label in ['encode_sample_term', 'igvf_sample_term']:
                for sample_props in self.get_sample_term_props(self.api_url, self.source_url, self.source, sample_types):
                    if sample_props['_key'] in visited_sample_terms:
                        continue
                    visited_sample_terms.add(sample_props['_key'])
                    if self.validate:
                        self.validate_doc(sample_props)
                    self.write_jsonl(sample_props)
            else:
                if self.validate:
                    self.validate_doc(props)
                self.write_jsonl(props)

        self.writer.close()

    @staticmethod
    def get_software_encode(file_object):
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

    @staticmethod
    def _software_titles_from_analysis_step_version_igvf(analysis_step_version):
        software_titles = set()
        if analysis_step_version:
            software_versions = analysis_step_version.get(
                'software_versions', [])
            software_version_ids = [software_version['@id']
                                    for software_version in software_versions]
            if software_version_ids:
                software_version_objects = FileFileSet.get_batch_objects(
                    software_version_ids,
                    fields=['software'],
                    id_type='@id',
                    api_url=FileFileSet.IGVF_API
                )
                for software_version_object in software_version_objects:
                    software = software_version_object.get('software')
                    software_titles.add(software.get('title'))

        return software_titles

    @staticmethod
    def get_software_igvf(file_object):
        software = set()
        if 'analysis_step_version' in file_object:
            software.update(
                FileFileSet._software_titles_from_analysis_step_version_igvf(file_object.get('analysis_step_version')))
        elif file_object.get('derived_manually'):
            input_file_accessions = set()
            for input_file_id in file_object.get('derived_from', []):
                input_file_accession = input_file_id.split('/')[-2]
                input_file_accessions.add(input_file_accession)

            input_file_objects = FileFileSet.get_batch_objects(
                list(input_file_accessions), ['analysis_step_version'], api_url=FileFileSet.IGVF_API)
            for input_file_object in input_file_objects:

                software.update(
                    FileFileSet._software_titles_from_analysis_step_version_igvf(input_file_object.get('analysis_step_version')))
        return software

    @staticmethod
    def parse_annotation_encode(dataset_object, software):
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
        experiment_objects = FileFileSet.get_batch_objects(
            dataset_object.get('experimental_input', []),
            fields=['assay_term_name', 'assay_term_id'],
            id_type='@id',
            api_url=FileFileSet.ENCODE_API
        )
        for experiment_object in experiment_objects:
            assay_term_name = experiment_object.get('assay_term_name')
            if assay_term_name:
                preferred_assay_titles.add(assay_term_name)
            assay_term_id = experiment_object.get('assay_term_id')
            if assay_term_id:
                assay_term_ids.add(assay_term_id)

        disease_ids = dataset_object.get('disease_term_id', [])

        return class_type, method, disease_ids, preferred_assay_titles, assay_term_ids

    @staticmethod
    def get_assay_encode(dataset_object, preferred_assay_titles, assay_term_ids):
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

    @staticmethod
    def get_publication_encode(dataset_object):
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

    @staticmethod
    def get_publication_igvf(fileset_object):
        publication_id = None
        publications = fileset_object.get('publications', [])
        if publications:
            if len(publications) > 1:
                raise (ValueError(
                    f'Loading multiple publications for a single file is not supported.'))
            publication_id = publications[0]['publication_identifiers'][0]
        return publication_id

    @staticmethod
    def parse_sample_donor_treatment_encode(
        dataset_object
    ):
        sample_ids = set()
        donor_ids = set()
        sample_term_to_sample_type = {}
        simple_sample_summaries = set()
        treatment_term_ids = set()
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
                        treatment_term_ids = set()
                        treatment_term_names = set()
                        for treatment in biosample_treatments:
                            treatment_id = treatment.get('treatment_term_id')
                            if treatment_id:
                                treatment_term_ids.add(treatment_id)
                            treatment_term_names.add(
                                treatment['treatment_term_name'])
                        treatment_term_names = ', '.join(
                            sorted(list(treatment_term_names)))
                        simple_sample_summary = f'{simple_sample_summary} treated with {treatment_term_names}'
                    simple_sample_summaries.add(simple_sample_summary)
        if not (simple_sample_summaries) and biosample_type_term:
            simple_sample_summary = f'{biosample_type_term}'
            donor = dataset_object.get('donor')
            if donor:
                donor_object = requests.get(
                    urljoin(FileFileSet.ENCODE_API, donor + '/@@object?format=json')).json()
                donor_accession = donor_object['accession']
                donor_ids.add(donor_accession)
                if classification in ['in vitro differentiated cells', 'primary cell', 'tissue', 'organoid']:
                    simple_sample_summary = f'{simple_sample_summary} from {donor_accession}'
            treatments = dataset_object.get('treatments', [])
            treatment_term_names = set()
            for treatment in treatments:
                treatment_id = treatment.get('treatment_term_id')
                if treatment_id:
                    treatment_term_ids.add(treatment_id)
                    treatment_term_names.add(treatment['treatment_term_name'])
            if treatment_term_names:
                treatment_term_names = ', '.join(
                    sorted(list(treatment_term_names)))
                simple_sample_summary = f'{simple_sample_summary} treated with {treatment_term_names}'
            simple_sample_summaries.add(simple_sample_summary)
        return sample_ids, donor_ids, sample_term_to_sample_type, simple_sample_summaries, treatment_term_ids

    @staticmethod
    def parse_sample_donor_treatment_igvf(
        fileset_object,
        method
    ):
        sample_accessions = set()
        sample_term_ids = set()
        donor_accessions = set()
        simple_sample_summaries = set()
        treatment_term_ids = set()
        samples = fileset_object.get('samples', [])
        for sample in samples:
            sample_accessions.add(sample['accession'])
        sample_objects = FileFileSet.get_batch_objects(
            list(sample_accessions),
            ['accession', 'donors', 'sample_terms', 'targeted_sample_term',
                'classifications', 'treatments', 'construct_library_sets'],
            api_url=FileFileSet.IGVF_API
        )

        for sample_object in sample_objects:
            for donor in sample_object['donors']:
                donor_accessions.add(donor['accession'])
            targeted_sample_term_obj = sample_object.get(
                'targeted_sample_term')
            sample_term_names = set()
            for sample_term in sample_object['sample_terms']:

                sample_term_names.add(sample_term.get('term_name'))
                if not targeted_sample_term_obj:
                    sample_term_id = sample_term.get(
                        '@id').split('/')[-2].replace('_', ':')
                    sample_term_ids.add(sample_term_id)
            sample_term_names = ', '.join(sorted(list(sample_term_names)))
            if targeted_sample_term_obj:

                targeted_sample_term_name = targeted_sample_term_obj['term_name']
                classifications = ', '.join(
                    sorted(sample_object['classifications']))
                simple_sample_summary = f'{sample_term_names} {classifications} induced to {targeted_sample_term_name}'
                sample_term_ids.add(
                    targeted_sample_term_obj['@id'].split('/')[-2].replace('_', ':'))
            else:
                simple_sample_summary = f'{sample_term_names}'
            if any(classification in ['organoid', 'gastruloid', 'embryoid', 'differentiated cell specimen', 'reprogrammed cell specimen'] for classification in sample_object['classifications']):
                donor_accessions_str = ', '.join(sorted(donor_accessions))
                simple_sample_summary = f'{simple_sample_summary} from {donor_accessions_str}'
            if 'treatments' in sample_object:
                treatment_term_names = set()
                treatment_ids = set()
                for treatment in sample_object['treatments']:
                    treatment_ids.add(treatment.get('@id'))
                    treatment_term_names.add(
                        treatment['treatment_term_name'])
                treatment_term_names = ', '.join(
                    sorted(list(treatment_term_names)))
                simple_sample_summary = f'{simple_sample_summary} treated with {treatment_term_names}'
                treatment_objects = FileFileSet.get_batch_objects(
                    list(treatment_ids), ['treatment_term_id'], '@id', api_url=FileFileSet.IGVF_API)
                for treatment_object in treatment_objects:
                    treatment_term_ids.add(
                        treatment_object['treatment_term_id'])
                # Add support for treatment vs. untreated analyses later

            # special case STARR-seq for inclusion of 1000 Genomes donors in the simple sample summary
            if method == 'STARR-seq':
                thousand_genomes_ids = set()
                construct_library_set_accessions = set()
                integrated_content_files_accessions = set()
                curated_set_accessions = set()
                donors_accessions = set()

                for construct_library_set in sample_object.get('construct_library_sets', []):
                    construct_library_set_accessions.add(
                        construct_library_set['accession'])
                construct_library_set_objects = FileFileSet.get_batch_objects(
                    list(construct_library_set_accessions), ['integrated_content_files'], api_url=FileFileSet.IGVF_API)

                for construct_library_set_object in construct_library_set_objects:
                    integrated_content_files = construct_library_set_object.get(
                        'integrated_content_files', [])
                    for integrated_content_file in integrated_content_files:
                        integrated_content_files_accessions.add(
                            integrated_content_file['accession'])
                integrated_content_files_objects = FileFileSet.get_batch_objects(
                    list(integrated_content_files_accessions), ['file_set'], api_url=FileFileSet.IGVF_API)
                for integrated_content_file_object in integrated_content_files_objects:
                    curated_set = integrated_content_file_object['file_set']
                    curated_set_accessions.add(curated_set['accession'])
                curated_sets_objects = FileFileSet.get_batch_objects(
                    list(curated_set_accessions), ['donors'], api_url=FileFileSet.IGVF_API)
                for curated_set_object in curated_sets_objects:
                    for donor in curated_set_object.get('donors', []):
                        donors_accessions.add(donor['accession'])
                donors_objects = FileFileSet.get_batch_objects(
                    list(donors_accessions), ['dbxrefs'], api_url=FileFileSet.IGVF_API)
                for donor_object in donors_objects:
                    dbxrefs = donor_object.get('dbxrefs', [])
                    for dbxref in dbxrefs:
                        if dbxref.startswith('IGSR'):
                            thousand_genomes_id = dbxref.split(':')[1]
                            thousand_genomes_ids.add(thousand_genomes_id)
                if thousand_genomes_ids:
                    thousand_genomes_ids = ', '.join(
                        sorted(thousand_genomes_ids))
                    simple_sample_summary = f'{simple_sample_summary} with variants from 1000 Genomes donors: {thousand_genomes_ids}'

            simple_sample_summaries.add(simple_sample_summary)
        return sample_accessions, donor_accessions, sample_term_ids, simple_sample_summaries, treatment_term_ids

    @staticmethod
    def decompose_analysis_set_to_measurement_set_igvf(analysis_set_id, measurement_sets_accession=None):
        if measurement_sets_accession is None:
            measurement_sets_accession = set()
        analysis_set_object = requests.get(
            urljoin(FileFileSet.IGVF_API, analysis_set_id + '/@@embedded?format=json')).json()
        input_file_sets = analysis_set_object.get('input_file_sets', [])
        construct_library_set_ids = set()
        for input_file_set in input_file_sets:
            input_file_set_id = input_file_set.get('@id')
            if not input_file_set_id:
                continue
            if input_file_set_id.startswith('/measurement-sets/'):
                accession = input_file_set.get('accession') if isinstance(
                    input_file_set, dict) else None
                if not accession:
                    accession = input_file_set_id.strip('/').split('/')[-1]
                measurement_sets_accession.add(accession)
            elif input_file_set_id.startswith('/auxiliary-sets/'):
                continue  # auxiliary sets are not analyzed without measurement sets so they can be skipped
            elif input_file_set_id.startswith('/construct-library-sets/'):
                construct_library_set_ids.add(input_file_set_id)
            elif input_file_set_id.startswith('/analysis-sets/'):
                FileFileSet.decompose_analysis_set_to_measurement_set_igvf(
                    input_file_set_id, measurement_sets_accession)
        if construct_library_set_ids:
            construct_library_set_objects = FileFileSet.get_batch_objects(
                list(construct_library_set_ids),
                fields=['applied_to_samples'],
                id_type='@id',
                api_url=FileFileSet.IGVF_API
            )
            sample_ids = set()
            for construct_library_set_object in construct_library_set_objects:
                sample_ids.update(construct_library_set_object.get(
                    'applied_to_samples', []))
            if sample_ids:
                sample_objects = FileFileSet.get_batch_objects(
                    list(sample_ids),
                    fields=['file_sets'],
                    id_type='@id',
                    api_url=FileFileSet.IGVF_API
                )
                for sample_object in sample_objects:
                    for file_set in sample_object.get('file_sets', []):
                        if file_set.startswith('/measurement-sets/'):
                            # construct library sets should be associated with some measurement set
                            accession = file_set.strip('/').split('/')[-1]
                            measurement_sets_accession.add(accession)
        return measurement_sets_accession

    @staticmethod
    def parse_analysis_set_igvf(fileset_object):
        input_file_sets = fileset_object.get('input_file_sets', [])
        preferred_assay_titles = set()
        assay_term_ids = set()
        measurement_set_accessions = set()
        for input_file_set in fileset_object.get('input_file_sets', []):
            input_id = input_file_set['@id']
            if input_id.startswith('/analysis-sets/'):
                measurement_set_accessions.update(
                    FileFileSet.decompose_analysis_set_to_measurement_set_igvf(
                        input_id)
                )
            elif input_id.startswith('/measurement-sets/'):
                accession = input_file_set.get('accession') if isinstance(
                    input_file_set, dict) else None
                if not accession:
                    accession = input_id.strip('/').split('/')[-1]
                measurement_set_accessions.add(accession)
        measurement_set_objects = FileFileSet.get_batch_objects(
            list(measurement_set_accessions), ['preferred_assay_titles', 'assay_term'], api_url=FileFileSet.IGVF_API)
        for measurement_set_object in measurement_set_objects:
            preferred_assay_titles.add(
                measurement_set_object.get('preferred_assay_titles')[0])
            assay_term_obj = measurement_set_object.get('assay_term')
            assay_term_id = assay_term_obj.get(
                '@id').split('/')[-2].replace('_', ':')
            assay_term_ids.add(assay_term_id)
        return preferred_assay_titles, assay_term_ids

    @staticmethod
    def query_fileset_files_props_encode(file_object):
        source_url = urljoin(FileFileSet.ENCODE_SOURCE_URL, file_object['@id'])
        href = file_object.get('href')
        download_link = urljoin(FileFileSet.ENCODE_API, href)
        dataset_object = requests.get(
            urljoin(FileFileSet.ENCODE_API, file_object['dataset'] + '/@@embedded?format=json')).json()
        dataset_accession = dataset_object['accession']
        dataset_type = dataset_object['@type'][0]
        lab = dataset_object['lab']['name']

        software = FileFileSet.get_software_encode(file_object)

        preferred_assay_titles = set()
        assay_term_ids = set()
        method = None
        class_type = 'observed data'
        disease_ids = []
        if dataset_type == 'Annotation':
            class_type, method, disease_ids, preferred_assay_titles, assay_term_ids = FileFileSet.parse_annotation_encode(
                dataset_object, software)
            if software and method not in ['candidate Cis-Regulatory Elements', 'caQTL', 'MPRA']:
                method = list(software)[0]
                # manually set the method to ENCODE-rE2G for Distal regulation ENCODE-rE2G
                if method == 'Distal regulation ENCODE-rE2G':
                    method = 'ENCODE-rE2G'
        assay_term_ids, preferred_assay_titles = FileFileSet.get_assay_encode(
            dataset_object, preferred_assay_titles, assay_term_ids)
        if class_type == 'observed data' and preferred_assay_titles:
            if len(preferred_assay_titles) != 1:
                raise (ValueError(
                    f'Loading data from experimental data from multiple assays is unsupported.'))
            else:
                method = preferred_assay_titles[0]

        publication_id = FileFileSet.get_publication_encode(dataset_object)

        sample_ids, donor_ids, sample_term_to_sample_type, simple_sample_summaries, treatment_ids = FileFileSet.parse_sample_donor_treatment_encode(
            dataset_object)

        sample_term_ids = [sample_term_id.replace(
            ':', '_') for sample_term_id in sample_term_to_sample_type.keys()]
        all_sample_types = list(sample_term_to_sample_type.values())
        # manually set the method to ENCODE-rE2G for file ENCFF968BZL
        if file_object['accession'] == 'ENCFF968BZL':
            method = 'CRISPR enhancer perturbation screen'

        if file_object['accession'] == 'ENCFF420VPZ':
            catalog_collections = ['genomic_elements']
        elif file_object['accession'] == 'ENCFF167FJQ':
            catalog_collections = ['mm_genomic_elements']
        else:
            catalog_collections = FileFileSet.METHOD_TO_COLLECTIONS_ENCODE.get(
                method, [])
        if not catalog_collections:
            raise (ValueError(
                f'Catalog collections are required for file_fileset {dataset_accession}.'))

        props = {
            '_key': file_object['accession'],
            'name': file_object['accession'],
            'file_set_id': dataset_accession,
            'lab': lab,
            'preferred_assay_titles': FileFileSet.none_if_empty(preferred_assay_titles),
            'assay_term_ids': FileFileSet.none_if_empty(assay_term_ids),
            'method': method,
            'class': class_type,
            'software': FileFileSet.none_if_empty(software),
            'samples': [f'ontology_terms/{sample_term_id}' for sample_term_id in sample_term_ids] if sample_term_ids else None,
            'sample_ids': FileFileSet.none_if_empty(sample_ids),
            'simple_sample_summaries': FileFileSet.none_if_empty(simple_sample_summaries),
            'donors': sorted([f'donors/{donor_id}' for donor_id in donor_ids]) if donor_ids else None,
            'treatments_term_ids': FileFileSet.none_if_empty(treatment_ids),
            'publication': publication_id,
            'collections': catalog_collections,
            'source': FileFileSet.SOURCE_ENCODE,
            'source_url': source_url,
            'download_link': download_link,
            'cell_annotation': None
        }
        return props, donor_ids, all_sample_types, disease_ids

    @staticmethod
    def query_fileset_files_props_igvf(file_object):
        source_url = urljoin(FileFileSet.IGVF_SOURCE_URL, file_object['@id'])
        href = file_object.get('href')
        download_link = urljoin(FileFileSet.IGVF_API, href)
        class_type = file_object.get('catalog_class')

        fileset_object = requests.get(
            urljoin(FileFileSet.IGVF_API, file_object['file_set']['@id'] + '/@@embedded?format=json')).json()
        fileset_accession = fileset_object['accession']
        fileset_object_type = fileset_object['@type'][0]
        lab = fileset_object['lab']['@id'].split('/')[2]
        catalog_collections = file_object.get('catalog_collections', [])
        cell_annotation = None
        if fileset_object_type == 'PseudobulkSet':
            cell_qualifier = fileset_object.get('cell_qualifier')
            cell_type_term_name = fileset_object.get(
                'cell_type').get('term_name')
            # not all pseudobulk sets have a cell qualifier
            if cell_qualifier:
                cell_annotation = f'{cell_qualifier} {cell_type_term_name}'
            else:
                cell_annotation = cell_type_term_name
        if not catalog_collections and fileset_object_type != 'PseudobulkSet':
            raise (ValueError(
                f'Catalog collections are required for file_fileset {file_object["accession"]}.'))

        software = FileFileSet.get_software_igvf(file_object)
        if not software:
            print(
                f'Warning: no software found for file_fileset {file_object["accession"]}.')

        preferred_assay_titles = set()
        assay_term_ids = set()
        method = list(software)[0] if software else None

        if fileset_object_type == 'PredictionSet' and not (software):
            raise (ValueError(f'Prediction sets require software to be loaded.'))
        if fileset_object_type not in ['PredictionSet', 'AnalysisSet', 'CuratedSet', 'PseudobulkSet']:
            raise (ValueError(
                f'Loading data from file sets other than prediction sets, analysis sets, curated sets, and pseudobulk sets is currently unsupported.'))
        if fileset_object_type in ['AnalysisSet', 'PseudobulkSet']:
            preferred_assay_titles, assay_term_ids = FileFileSet.parse_analysis_set_igvf(
                fileset_object)
            if len(preferred_assay_titles) != 1:
                raise (ValueError(
                    f'Loading data from experimental data from multiple assays is unsupported.'))
            method = list(preferred_assay_titles)[0]
        if fileset_object_type == 'CuratedSet' and not method:
            method = fileset_object.get('summary')

        preferred_assay_titles = FileFileSet.none_if_empty(
            preferred_assay_titles)
        assay_term_ids = FileFileSet.none_if_empty(assay_term_ids)

        # manually set the method to MPRA, not necessary for ENCODE since preferred_assay_titles == ['MPRA']
        if assay_term_ids == ['OBI:0002675']:
            method = 'MPRA'

        publication_id = FileFileSet.get_publication_igvf(fileset_object)

        sample_ids, donor_ids, sample_term_ids, simple_sample_summaries, treatment_ids = FileFileSet.parse_sample_donor_treatment_igvf(
            fileset_object,
            method)

        sample_term_ids = [sample_term_id.replace(
            ':', '_') for sample_term_id in sample_term_ids]

        props = {
            '_key': file_object['accession'],
            'name': file_object['accession'],
            'file_set_id': fileset_accession,
            'lab': lab,
            'preferred_assay_titles': preferred_assay_titles,
            'assay_term_ids': assay_term_ids,
            'method': method,
            'class': class_type,
            'software': FileFileSet.none_if_empty(software),
            'samples': [f'ontology_terms/{sample_term_id}' for sample_term_id in sample_term_ids] if sample_term_ids else None,
            'sample_ids': FileFileSet.none_if_empty(sample_ids),
            'simple_sample_summaries': FileFileSet.none_if_empty(simple_sample_summaries),
            'donors': sorted([f'donors/{donor_id}' for donor_id in donor_ids]) if donor_ids else None,
            'treatments_term_ids': FileFileSet.none_if_empty(treatment_ids),
            'publication': publication_id,
            'collections': catalog_collections,
            'source': FileFileSet.SOURCE_IGVF,
            'source_url': source_url,
            'download_link': download_link,
            'cell_annotation': cell_annotation
        }
        return props, donor_ids, sample_term_ids

    @staticmethod
    def get_donor_props(api_url, source_url, source, donor_accessions, disease_ids=None):
        if disease_ids is None:
            disease_ids = []
        donor_accessions = list(donor_accessions)
        donor_objects = FileFileSet.get_batch_objects(
            donor_accessions,
            fields=['sex', 'age', 'age_units', 'ethnicities',
                    'ethnicity', 'phenotypic_features', 'accession'],
            id_type='accession',
            api_url=api_url
        )
        for donor_object in donor_objects:
            id = donor_object['@id']
            source_url = urljoin(source_url, id)

            accession = donor_object['accession']
            sex = donor_object.get('sex')
            age = donor_object.get('age')
            age_units = donor_object.get('age_units')

            if source == FileFileSet.SOURCE_IGVF:
                phenotypic_features = donor_object.get(
                    'phenotypic_features', [])
                phenotypic_feature_ids = FileFileSet.none_if_empty([
                    f"ontology_terms/{pf['feature']['term_id'].replace(':', '_')}"
                    for pf in phenotypic_features
                ])
                ethnicities = FileFileSet.none_if_empty(
                    donor_object.get('ethnicities', []))

            elif source == FileFileSet.SOURCE_ENCODE:
                ethnicities = FileFileSet.none_if_empty(
                    donor_object.get('ethnicity', []))
                phenotypic_feature_ids = None
                if disease_ids:
                    phenotypic_feature_ids = FileFileSet.none_if_empty([
                        f"ontology_terms/{FileFileSet.ENCODE_disease_id_mapping.get(disease_id, disease_id).replace(':', '_')}"
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
                'source': source,
                'source_url': source_url
            }

            yield doc

    @staticmethod
    def get_sample_term_props(api_url, source_url, source, sample_terms):
        # sample_term in igvf example: CL_0000679, in encode example: /biosample-types/primary_cell_CL_0002536/
        if source == FileFileSet.SOURCE_IGVF:
            sample_terms = ['/sample-terms/' + sample_term +
                            '/' for sample_term in sample_terms]
        sample_term_objects = FileFileSet.get_batch_objects(
            sample_terms,
            fields=['term_id', 'term_name', 'synonyms'],
            id_type='@id',
            api_url=api_url
        )
        for sample_term_object in sample_term_objects:
            term_id = sample_term_object['term_id'].replace(':', '_')
            if term_id.startswith('NTR'):
                uri = urljoin(source_url, sample_term_object['@id'])
                _props = {
                    '_key': term_id,
                    'uri': uri,
                    'term_id': term_id,
                    'name': sample_term_object['term_name'],
                    'synonyms': FileFileSet.none_if_empty(sample_term_object.get('synonyms', None)),
                    'source': source,
                    'source_url': uri
                }
                yield _props
