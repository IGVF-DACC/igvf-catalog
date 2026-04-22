import json
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from adapters.writer import SpyWriter

import pytest

from adapters.file_fileset_adapter import FileFileSet

FIXTURE_PATH = Path(__file__).parent / 'fixtures' / \
    'file_fileset_requests.json'
REQUEST_FIXTURES = json.loads(FIXTURE_PATH.read_text(encoding='utf-8'))


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    params = parse_qsl(parsed.query, keep_blank_values=True)
    grouped = {}
    for key, value in params:
        grouped.setdefault(key, []).append(value)

    normalized = []
    for key in ['accession', '@id', 'field']:
        if key in grouped:
            normalized.extend((key, value)
                              for value in sorted(grouped.pop(key)))
    for key, values in sorted(grouped.items()):
        normalized.extend((key, value) for value in values)

    return urlunparse(parsed._replace(query=urlencode(normalized, doseq=True)))


NORMALIZED_FIXTURES = {
    normalize_url(url): payload for url, payload in REQUEST_FIXTURES.items()
}


def make_response(payload):
    response = Mock()
    response.json.return_value = {
        '@graph': payload} if isinstance(payload, list) else payload
    return response


def request_side_effect(url, **_kwargs):
    normalized_url = normalize_url(url)
    if normalized_url not in NORMALIZED_FIXTURES:
        raise AssertionError(f'Missing request fixture for {url}')
    return make_response(NORMALIZED_FIXTURES[normalized_url])


def test_invalid_label():
    with pytest.raises(ValueError, match='Invalid label. Allowed values: encode_file_fileset, encode_donor, encode_sample_term, igvf_file_fileset, igvf_donor, igvf_sample_term'):
        FileFileSet(accessions=['IGVFFI8400FXRX'], label='invalid_label')


def test_none_if_empty():
    value = ['OBI:0003663', 'OBI:0003662']
    assert FileFileSet.none_if_empty(value) == ['OBI:0003662', 'OBI:0003663']
    value = []
    assert FileFileSet.none_if_empty(value) is None


def test_get_batch_objects():
    with patch('adapters.file_fileset_adapter.requests.get', side_effect=request_side_effect) as mock_get:
        objects = FileFileSet.get_batch_objects(
            ids=['IGVFFI9721OCVW', 'IGVFFI8400FXRX'],
            fields=['@id', 'accession', 'href', 'dataset', 'analysis_step_version',
                    'derived_manually', 'derived_from', 'catalog_class', 'file_set',
                    'catalog_collections'],
            id_type='accession',
            api_url='https://api.data.igvf.org/'
        )

    assert mock_get.call_args_list
    accessions = sorted(obj['accession'] for obj in objects)
    assert accessions == ['IGVFFI8400FXRX', 'IGVFFI9721OCVW']

    with patch('adapters.file_fileset_adapter.requests.get', side_effect=request_side_effect) as mock_get:
        objects = FileFileSet.get_batch_objects(
            ids={'IGVFFI9721OCVW', 'IGVFFI8400FXRX'},
            fields=['@id', 'accession', 'href', 'dataset', 'analysis_step_version',
                    'derived_manually', 'derived_from', 'catalog_class', 'file_set',
                    'catalog_collections'],
            id_type='accession',
            api_url='https://api.data.igvf.org/'
        )

    assert mock_get.call_args_list
    accessions = sorted(obj['accession'] for obj in objects)
    assert accessions == ['IGVFFI8400FXRX', 'IGVFFI9721OCVW']

    objects = FileFileSet.get_batch_objects(
        ids=[],
        fields=['accession'],
        id_type='accession',
        api_url='https://api.data.igvf.org/'
    )
    assert objects == []

    with pytest.raises(ValueError, match='id_type must be'):
        FileFileSet.get_batch_objects(
            ids=['IGVFFI9721OCVW', 'IGVFFI8400FXRX'],
            fields=['accession'],
            id_type='wrong_type',
            api_url='https://api.data.igvf.org/'
        )


def test_software_titles_from_analysis_step_version_igvf():
    analysis_step_version = {'summary': '4b52b7fa-e00e-4fc8-b653-ab0ca32174ba', 'software_versions': [
        {'summary': 'scATAC-seq processing scripts v1.0.0', '@id': '/software-versions/scATAC-processing-v1.0.0/'}], '@id': '/analysis-step-versions/4b52b7fa-e00e-4fc8-b653-ab0ca32174ba/'}
    with patch('adapters.file_fileset_adapter.requests.get', side_effect=request_side_effect):
        software_titles = FileFileSet._software_titles_from_analysis_step_version_igvf(
            analysis_step_version)
    assert 'scATAC-seq processing scripts' in software_titles


def test_get_software_igvf():
    file_object = {
        'analysis_step_version': {
            'software_versions': [
                {'@id': '/software-versions/scATAC-processing-v1.0.0/'}
            ]
        }
    }
    with patch('adapters.file_fileset_adapter.requests.get', side_effect=request_side_effect):
        software = FileFileSet.get_software_igvf(file_object)
    assert 'scATAC-seq processing scripts' in software


def test_get_software_igvf_derived_manually():
    file_object = {
        'derived_manually': True,
        'derived_from': ['/tabular-files/IGVFFI9775SYBY/']
    }
    with patch('adapters.file_fileset_adapter.requests.get', side_effect=request_side_effect):
        software = FileFileSet.get_software_igvf(file_object)
    assert 'scATAC-seq processing scripts' in software


def test_get_publication_igvf():
    file_set_object = {
        'publications': [
            {'publication_identifiers': ['PMID:40245860']},
        ]
    }
    publication_id = FileFileSet.get_publication_igvf(file_set_object)
    assert publication_id == 'PMID:40245860'

    file_set_object = {
        'publications': [
            {'publication_identifiers': ['PMID:40245860']},
            {'publication_identifiers': ['PMID:40245860']}
        ]
    }
    with pytest.raises(ValueError, match='Loading multiple publications for a single file is not supported.'):
        FileFileSet.get_publication_igvf(file_set_object)


def test_parse_sample_donor_treatment_igvf():
    samples = [{
        'status': 'released',
        'aliases': ['jay-shendure:scATAC_mEBs_rep2_10XlaneB'],
        'accession': 'IGVFSM4284RDJK',
        'sample_terms': [{
            'status': 'released',
            'term_name': 'mouse embryonic stem cell',
            '@id': '/sample-terms/EFO_0004038/',
            '@type': ['SampleTerm', 'OntologyTerm', 'Item'],
            'summary': 'mouse embryonic stem cell'
        }],
        'classifications': ['differentiated cell specimen'],
        'cellular_sub_pool': '10XlaneB',
        'targeted_sample_term': {
            'status': 'released',
            'term_name': 'embryoid body',
            '@id': '/sample-terms/UBERON_0014374/'
        },
        '@id': '/in-vitro-systems/IGVFSM4284RDJK/',
        '@type': ['InVitroSystem', 'Biosample', 'Sample', 'Item'],
        'summary': 'Mus musculus WD44 (male) mouse embryonic stem differentiated cell specimen induced to embryoid body for 21 days, (cellular sub pool: 10XlaneB)',
        'taxa': 'Mus musculus'
    }]
    method = 'scATAC-seq'
    sample_objects = [{
        'accession': 'IGVFSM4284RDJK',
        'donors': [{'accession': 'IGVFDO3898MNLZ'}],
        'sample_terms': [{
            'term_name': 'mouse embryonic stem cell',
            '@id': '/sample-terms/EFO_0004038/'
        }],
        'targeted_sample_term': {
            'term_name': 'embryoid body',
            '@id': '/sample-terms/UBERON_0014374/'
        },
        'classifications': ['differentiated cell specimen'],
        'treatments': [
            {
                '@id': '/treatments/TRT0002/',
                'treatment_term_name': 'drug b'
            },
            {
                '@id': '/treatments/TRT0001/',
                'treatment_term_name': 'drug a'
            }
        ]
    }]
    treatment_objects = [
        {'treatment_term_id': 'CHEBI:11111'},
        {'treatment_term_id': 'CHEBI:22222'}
    ]
    with patch.object(FileFileSet, 'get_batch_objects', side_effect=[sample_objects, treatment_objects]):
        sample_ids, donor_ids, sample_term_ids, simple_sample_summaries, treatment_ids, modality = FileFileSet.parse_sample_donor_treatment_igvf(
            samples,
            method)
    assert sample_ids == {'IGVFSM4284RDJK'}
    assert donor_ids == {'IGVFDO3898MNLZ'}
    assert sample_term_ids == {'UBERON:0014374'}
    assert simple_sample_summaries == {
        'mouse embryonic stem cell differentiated cell specimen induced to embryoid body from IGVFDO3898MNLZ treated with drug a, drug b'
    }
    assert treatment_ids == {'CHEBI:11111', 'CHEBI:22222'}
    assert modality is None


def test_parse_sample_donor_treatment_igvf_crispr_modality():
    samples = [{'accession': 'IGVFSM0001AAAA'}]
    method = 'CRISPR FACS screen'
    sample_objects = [{
        'accession': 'IGVFSM0001AAAA',
        'donors': [{'accession': 'IGVFDO0001AAAA'}],
        'sample_terms': [{
            'term_name': 'K562',
            '@id': '/sample-terms/EFO_0002067/'
        }],
        'classifications': ['cell line'],
        'construct_library_sets': [],
        'modifications': [
            {
                '@type': ['CrisprModification', 'Modification', 'Item'],
                'modality': 'interference'
            },
            {
                '@type': ['ProteinModification', 'Modification', 'Item'],
                'modality': 'ignored'
            }
        ]
    }]
    with patch.object(FileFileSet, 'get_batch_objects', return_value=sample_objects):
        *_unused, modality = FileFileSet.parse_sample_donor_treatment_igvf(
            samples,
            method)
    assert modality == 'interference'


def test_parse_sample_donor_treatment_igvf_multiple_crispr_modalities_error():
    samples = [{'accession': 'IGVFSM0001AAAA'},
               {'accession': 'IGVFSM0002BBBB'}]
    method = 'CRISPR FACS screen'
    sample_objects = [
        {
            'accession': 'IGVFSM0001AAAA',
            'donors': [{'accession': 'IGVFDO0001AAAA'}],
            'sample_terms': [{'term_name': 'K562', '@id': '/sample-terms/EFO_0002067/'}],
            'classifications': ['cell line'],
            'construct_library_sets': [],
            'modifications': [{'@type': ['CrisprModification', 'Modification', 'Item'], 'modality': 'interference'}]
        },
        {
            'accession': 'IGVFSM0002BBBB',
            'donors': [{'accession': 'IGVFDO0002BBBB'}],
            'sample_terms': [{'term_name': 'K562', '@id': '/sample-terms/EFO_0002067/'}],
            'classifications': ['cell line'],
            'construct_library_sets': [],
            'modifications': [{'@type': ['CrisprModification', 'Modification', 'Item'], 'modality': 'activation'}]
        }
    ]
    with patch.object(FileFileSet, 'get_batch_objects', return_value=sample_objects):
        with pytest.raises(ValueError, match='multiple CRISPR modalities'):
            FileFileSet.parse_sample_donor_treatment_igvf(samples, method)


def decompose_analysis_set_to_measurement_set_igvf():
    analysis_set_id = '/analysis-sets/IGVFDS7801YPEU/'
    with patch('adapters.file_fileset_adapter.requests.get', side_effect=request_side_effect):
        measurement_sets = FileFileSet.decompose_analysis_set_to_measurement_set_igvf(
            analysis_set_id
        )
    assert measurement_sets == ['IGVFMS2190NKLE']


def test_parse_analysis_set_igvf():
    file_set_object = {
        'input_file_sets': [{
            'accession': 'IGVFDS1560LMQZ',
            '@id': '/measurement-sets/IGVFDS1560LMQZ/'
        }]
    }
    with patch('adapters.file_fileset_adapter.requests.get', side_effect=request_side_effect):
        preferred_assay_titles, assay_term_ids = FileFileSet.parse_analysis_set_igvf(
            file_set_object)
    assert preferred_assay_titles == {'scATAC-seq'}
    assert assay_term_ids == {'OBI:0002764'}


def test_fileset_query_files_props_igvf():
    file_object = {'@id': '/signal-files/IGVFFI8400FXRX/', '@type': ['SignalFile', 'File', 'Item'], 'accession': 'IGVFFI8400FXRX', 'analysis_step_version': {'summary': '4b52b7fa-e00e-4fc8-b653-ab0ca32174ba', 'software_versions': [{'summary': 'scATAC-seq processing scripts v1.0.0', '@id': '/software-versions/scATAC-processing-v1.0.0/'}], '@id': '/analysis-step-versions/4b52b7fa-e00e-4fc8-b653-ab0ca32174ba/'}, 'catalog_class': 'observed data', 'derived_from': ['/tabular-files/IGVFFI9775SYBY/'], 'derived_manually': False, 'file_set': {'summary': 'Pseudobulk of pluripotent epiblast cell derived from mouse embryonic stem cell', 'file_set_type': 'pseudobulk analysis', 'data_use_limitation_summaries': ['no certificate'], '@type': ['PseudobulkSet', 'FileSet', 'Item'], 'accession': 'IGVFDS2190NKLE', '@id': '/pseudobulk-sets/IGVFDS2190NKLE/', 'lab': {'@id': '/labs/jay-shendure/', 'title': 'Jay Shendure, UW'}, 'samples': [{'summary': 'Mus musculus WD44 (male) mouse embryonic stem differentiated cell specimen induced to embryoid body for 21 days, (cellular sub pool: 10XlaneB)', 'taxa': 'Mus musculus', 'classifications': ['differentiated cell specimen'], '@type': ['InVitroSystem', 'Biosample', 'Sample', 'Item'], 'accession': 'IGVFSM4284RDJK', 'targeted_sample_term': {'term_name': 'embryoid body', '@id': '/sample-terms/UBERON_0014374/', 'status': 'released'}, '@id': '/in-vitro-systems/IGVFSM4284RDJK/', 'status': 'released', 'sample_terms': [{'term_name': 'mouse embryonic stem cell', '@id': '/sample-terms/EFO_0004038/', 'status': 'released'}]}, {'summary': 'Mus musculus WD44 (male) mouse embryonic stem differentiated cell specimen induced to embryoid body for 21 days, (cellular sub pool: 10XlaneB)', 'taxa': 'Mus musculus', 'classifications': [
        'differentiated cell specimen'], '@type': ['InVitroSystem', 'Biosample', 'Sample', 'Item'], 'accession': 'IGVFSM6820XJKR', 'targeted_sample_term': {'term_name': 'embryoid body', '@id': '/sample-terms/UBERON_0014374/', 'status': 'released'}, '@id': '/in-vitro-systems/IGVFSM6820XJKR/', 'status': 'released', 'sample_terms': [{'term_name': 'mouse embryonic stem cell', '@id': '/sample-terms/EFO_0004038/', 'status': 'released'}]}, {'summary': 'Mus musculus WD44 (male) mouse embryonic stem differentiated cell specimen induced to embryoid body for 21 days, (cellular sub pool: 10XlaneA)', 'taxa': 'Mus musculus', 'classifications': ['differentiated cell specimen'], '@type': ['InVitroSystem', 'Biosample', 'Sample', 'Item'], 'accession': 'IGVFSM7126ZMPT', 'targeted_sample_term': {'term_name': 'embryoid body', '@id': '/sample-terms/UBERON_0014374/', 'status': 'released'}, '@id': '/in-vitro-systems/IGVFSM7126ZMPT/', 'status': 'released', 'sample_terms': [{'term_name': 'mouse embryonic stem cell', '@id': '/sample-terms/EFO_0004038/', 'status': 'released'}]}, {'summary': 'Mus musculus WD44 (male) mouse embryonic stem differentiated cell specimen induced to embryoid body for 21 days, (cellular sub pool: 10XlaneA)', 'taxa': 'Mus musculus', 'classifications': ['differentiated cell specimen'], '@type': ['InVitroSystem', 'Biosample', 'Sample', 'Item'], 'accession': 'IGVFSM9475FJUV', 'targeted_sample_term': {'term_name': 'embryoid body', '@id': '/sample-terms/UBERON_0014374/', 'status': 'released'}, '@id': '/in-vitro-systems/IGVFSM9475FJUV/', 'status': 'released', 'sample_terms': [{'term_name': 'mouse embryonic stem cell', '@id': '/sample-terms/EFO_0004038/', 'status': 'released'}]}]}, 'href': '/signal-files/IGVFFI8400FXRX/@@download/IGVFFI8400FXRX.bigWig'}
    with patch('adapters.file_fileset_adapter.requests.get', side_effect=request_side_effect):
        props, donor_ids, sample_term_ids = FileFileSet.query_fileset_files_props_igvf(
            file_object)
    assert props['preferred_assay_titles'] == ['scATAC-seq']
    assert props['assay_term_ids'] == ['OBI:0002764']
    assert props['method'] == 'scATAC-seq'
    assert props['class'] == 'observed data'
    assert props['software'] == ['scATAC-seq processing scripts']
    assert props['genome_browser_link'] == (
        'https://api.data.igvf.org/signal-files/IGVFFI8400FXRX/@@download/'
        'IGVFFI8400FXRX.bigWig'
    )
    assert donor_ids == {'IGVFDO3898MNLZ'}
    assert sample_term_ids == ['UBERON_0014374']


def test_query_fileset_files_props_igvf_with_crispr_modality():
    file_object = {
        '@id': '/tabular-files/IGVFFI0000TEST/',
        'accession': 'IGVFFI0000TEST',
        'catalog_class': 'observed data',
        'catalog_collections': ['genomic_elements'],
        'file_set': {
            '@id': '/analysis-sets/IGVFDS0000TEST/'
        },
        'href': '/tabular-files/IGVFFI0000TEST/@@download/IGVFFI0000TEST.tsv.gz'
    }
    fileset_object = {
        'accession': 'IGVFDS0000TEST',
        '@type': ['AnalysisSet', 'FileSet', 'Item'],
        'lab': {'@id': '/labs/tim-reddy/'},
        'samples': [{'accession': 'IGVFSM0000TEST'}],
        'publications': [],
        'input_file_sets': [{'@id': '/measurement-sets/IGVFMS0000TEST/'}]
    }
    with patch('adapters.file_fileset_adapter.requests.get', return_value=make_response(fileset_object)):
        with patch.object(FileFileSet, 'get_software_igvf', return_value={'Sceptre'}):
            with patch.object(FileFileSet, 'parse_analysis_set_igvf', return_value=({'CRISPR FACS screen'}, {'OBI:0003662'})):
                with patch.object(FileFileSet, 'get_publication_igvf', return_value=None):
                    with patch.object(
                        FileFileSet,
                        'parse_sample_donor_treatment_igvf',
                        return_value=(
                            {'IGVFSM0000TEST'},
                            {'IGVFDO0000TEST'},
                            {'EFO:0002067'},
                            {'K562'},
                            set(),
                            'interference'
                        )
                    ):
                        props, donor_ids, sample_term_ids = FileFileSet.query_fileset_files_props_igvf(
                            file_object)
    assert props['crispr_modality'] == 'interference'
    assert props['method'] == 'CRISPR screen'
    assert donor_ids == {'IGVFDO0000TEST'}
    assert sample_term_ids == ['EFO_0002067']


def test_get_donor_props():
    api_url = 'https://api.data.igvf.org/'
    source_url = 'https://data.igvf.org/'
    source = 'IGVF'
    donor_accessions = ['IGVFDO3898MNLZ']
    disease_ids = None
    with patch('adapters.file_fileset_adapter.requests.get', side_effect=request_side_effect):
        donor_props = list(FileFileSet.get_donor_props(
            api_url, source_url, source, donor_accessions, disease_ids
        ))
    assert donor_props[0]['_key'] == 'IGVFDO3898MNLZ'
    assert donor_props[0]['sex'] == 'male'
    assert donor_props[0]['age'] == '21'
    assert donor_props[0]['age_units'] == 'day'
    assert donor_props[0]['ethnicities'] is None
    assert donor_props[0]['phenotypic_features'] is None
    assert donor_props[0]['source'] == 'IGVF'
    assert donor_props[0]['source_url'] == 'https://data.igvf.org/rodent-donors/IGVFDO3898MNLZ/'


def test_get_sample_term_props():
    api_url = 'https://api.data.igvf.org/'
    source_url = 'https://data.igvf.org/'
    source = 'IGVF'
    sample_terms = ['UBERON_0014374']
    with patch('adapters.file_fileset_adapter.requests.get', side_effect=request_side_effect):
        sample_term_props = list(FileFileSet.get_sample_term_props(
            api_url, source_url, source, sample_terms))
    # no sample term for igvf
    assert sample_term_props == []
    sample_terms = ['NTR_0000856']
    with patch('adapters.file_fileset_adapter.requests.get', side_effect=request_side_effect):
        sample_term_props = list(FileFileSet.get_sample_term_props(
            api_url, source_url, source, sample_terms))
    assert sample_term_props[0]['_key'] == 'NTR_0000856'
    assert sample_term_props[0]['term_id'] == 'NTR_0000856'
    assert sample_term_props[0]['name'] == 'test sample term'
    assert sample_term_props[0]['synonyms'] is None
    assert sample_term_props[0]['source'] == 'IGVF'
    assert sample_term_props[0]['source_url'] == 'https://data.igvf.org/sample-terms/NTR_0000856/'


def test_get_software_encode():
    file_object = {
        'analysis_step_version': {
            'software_versions': [
                {'software': {'title': 'scATAC-seq processing scripts'}}
            ]
        }
    }
    software = FileFileSet.get_software_encode(file_object)
    assert software == {'scATAC-seq processing scripts'}


def test_parse_annotation_encode():
    dataset_object = {
        'accession': 'ENCSR297HTV',
        'annotation_type': 'element gene regulatory interaction predictions',
        'software_used': [
            {
                'date_created': '2024-05-28T04:29:01.090382+00:00',
                'submitted_by': '/users/6667a92a-d202-493a-8c7d-7a56d1380356/',
                'status': 'released',
                'aliases': [
                    'encode:rE2g_v2'
                ],
                'schema_version': '4',
                'software': {
                    'lab': '/labs/jesse-engreitz/',
                    'award': '/awards/UM1HG009436/',
                    'references': [],
                    'date_created': '2023-06-27T19:00:41.613175+00:00',
                    'submitted_by': '/users/8c832fff-23ec-4589-81c9-49a1c0020e46/',
                    'status': 'released',
                    'aliases': [
                        'encode:re2g_model'
                    ],
                    'schema_version': '10',
                    'name': 'distal-regulation-encode_re2g',
                    'title': 'Distal regulation ENCODE-rE2G',
                    'source_url': 'https://github.com/EngreitzLab/ENCODE_rE2G',
                    'used_by': [
                        'ENCODE'
                    ],
                    'description': 'Train ENCODE-rE2G models on CRISPR enhancer screen data and apply to generate genome-wide predictions of enhancer-gene regulatory connections.',
                    '@id': '/software/distal-regulation-encode_re2g/',
                    '@type': [
                        'Software',
                        'Item'
                    ],
                    'uuid': '11d1fe31-2784-449a-a3d8-e1fd41116a1d',
                    'versions': [
                        '/software-versions/db685a75-a35c-4052-bc9b-dc1f9da977e3/',
                        '/software-versions/5b51197d-5cb0-4f54-afe6-d270665c9fbe/'
                    ]
                },
                'version': '1.0.0',
                'downloaded_url': 'https://github.com/EngreitzLab/ENCODE_rE2G/releases/tag/v1.0.0',
                '@id': '/software-versions/5b51197d-5cb0-4f54-afe6-d270665c9fbe/',
                '@type': [
                    'SoftwareVersion',
                    'Item'
                ],
                'uuid': '5b51197d-5cb0-4f54-afe6-d270665c9fbe'
            },
            {
                'date_created': '2024-05-28T04:27:12.431257+00:00',
                'submitted_by': '/users/6667a92a-d202-493a-8c7d-7a56d1380356/',
                'status': 'released',
                'aliases': [
                    'encode:abc_v1.1.2'
                ],
                'schema_version': '4',
                'software': {
                    'lab': '/labs/jesse-engreitz/',
                    'award': '/awards/UM1HG009436/',
                    'references': [],
                    'date_created': '2023-01-19T22:08:27.343997+00:00',
                    'submitted_by': '/users/8c832fff-23ec-4589-81c9-49a1c0020e46/',
                    'status': 'released',
                    'aliases': [
                        'jesse-engreitz:ABC-Enhancer-Gene-Prediction-encode_v1'
                    ],
                    'schema_version': '10',
                    'name': 'abc-enhancer-gene-prediction-encode',
                    'title': 'ABC-Enhancer-Gene-Prediction',
                    'source_url': 'https://github.com/broadinstitute/ABC-Enhancer-Gene-Prediction/',
                    'used_by': [
                        'ENCODE'
                    ],
                    'description': 'Cell type specific enhancer-gene predictions using ABC model (Fulco, Nasser et al, Nature Genetics 2019)',
                    '@id': '/software/abc-enhancer-gene-prediction-encode/',
                    '@type': [
                        'Software',
                        'Item'
                    ],
                    'uuid': 'bc9d0807-8280-4ccd-b223-ff90e9014ab8',
                    'versions': [
                        '/software-versions/81b93de0-64a6-45c2-aabc-f38a6a66b247/',
                        '/software-versions/0cb1d362-f501-4fcf-98ce-defc3ff57ca1/'
                    ]
                },
                'version': '1.1.2',
                'downloaded_url': 'https://github.com/broadinstitute/ABC-Enhancer-Gene-Prediction/releases/tag/v1.1.2',
                '@id': '/software-versions/0cb1d362-f501-4fcf-98ce-defc3ff57ca1/',
                '@type': [
                    'SoftwareVersion',
                    'Item'
                ],
                'uuid': '0cb1d362-f501-4fcf-98ce-defc3ff57ca1'
            }
        ],
        'experimental_input': [
            '/experiments/ENCSR297WRG/'
        ],
        '@id': '/annotations/ENCSR297HTV/',
    }
    software = {'Distal regulation ENCODE-rE2G'}
    with patch('adapters.file_fileset_adapter.requests.get', side_effect=request_side_effect):
        class_type, method, disease_ids, preferred_assay_titles, assay_term_ids = FileFileSet.parse_annotation_encode(
            dataset_object, software)
    assert class_type == 'prediction'
    assert method == 'element gene regulatory interaction predictions'
    assert disease_ids == []
    assert preferred_assay_titles == {'DNase-seq'}
    assert assay_term_ids == {'OBI:0001853'}

    software = set()
    with patch('adapters.file_fileset_adapter.requests.get', side_effect=request_side_effect):
        class_type, method, disease_ids, preferred_assay_titles, assay_term_ids = FileFileSet.parse_annotation_encode(
            dataset_object, software)
    assert class_type == 'prediction'
    assert method == 'element gene regulatory interaction predictions'
    assert disease_ids == []
    assert preferred_assay_titles == {'DNase-seq'}
    assert assay_term_ids == {'OBI:0001853'}

    dataset_object['software_used'] = []
    with pytest.raises(ValueError, match='Predictions require software to be loaded.'):
        class_type, method, disease_ids, preferred_assay_titles, assay_term_ids = FileFileSet.parse_annotation_encode(
            dataset_object, set())

    dataset_object['annotation_type'] = 'caQTL'
    with patch('adapters.file_fileset_adapter.requests.get', side_effect=request_side_effect):
        class_type, method, disease_ids, preferred_assay_titles, assay_term_ids = FileFileSet.parse_annotation_encode(
            dataset_object, software)
    assert class_type == 'observed data'
    assert method == 'caQTL'
    assert disease_ids == []
    assert preferred_assay_titles == {'DNase-seq'}
    assert assay_term_ids == {'OBI:0001853'}


def test_get_assay_encode():
    dataset_object = {
        'assay_term_name': ['DNase-seq'],
        'assay_term_id': 'OBI:0001853'
    }
    preferred_assay_titles = set()
    assay_term_ids = {'OBI:0001853'}
    with patch('adapters.file_fileset_adapter.requests.get', side_effect=request_side_effect):
        assay_term_ids, preferred_assay_titles = FileFileSet.get_assay_encode(
            dataset_object, preferred_assay_titles, assay_term_ids)
    assert assay_term_ids == ['OBI:0001853']
    assert preferred_assay_titles == ['DNase-seq']

    dataset_object = {
        'assay_term_name': 'DNase-seq',
        'assay_term_id': 'OBI:0001853'
    }
    preferred_assay_titles = set()
    assay_term_ids = {'OBI:0001853'}
    with patch('adapters.file_fileset_adapter.requests.get', side_effect=request_side_effect):
        assay_term_ids, preferred_assay_titles = FileFileSet.get_assay_encode(
            dataset_object, preferred_assay_titles, assay_term_ids)
    assert assay_term_ids == ['OBI:0001853']
    assert preferred_assay_titles == ['DNase-seq']


def test_get_publication_encode():
    dataset_object = {
        'references': [
            {'identifiers': ['PMID:40245860']}
        ]
    }
    publication_id = FileFileSet.get_publication_encode(dataset_object)
    assert publication_id == 'PMID:40245860'

    dataset_object = {
        'references': [
            {'identifiers': ['PMID:40245860']},
            {'identifiers': ['PMID:40245860']}
        ]
    }
    with pytest.raises(ValueError, match='Loading multiple publications for a single file is not supported.'):
        FileFileSet.get_publication_encode(dataset_object)


def test_parse_sample_donor_treatment_encode():
    library = {
        'biosample': {
            'accession': 'ENCBS123ABC',
            'biosample_ontology': {
                'term_name': 'head of caudate nucleus',
                'term_id': 'UBERON:0002626',
                'classification': 'tissue',
                '@id': '/biosample-types/tissue_UBERON_0002626/'
            },
            'donor': {
                'accession': 'ENCDO948PMW'
            },
            'treatments': [
                {
                    'treatment_term_id': 'CHEBI:12345',
                    'treatment_term_name': 'drug a'
                },
                {
                    'treatment_term_name': 'drug b'
                }
            ]
        }
    }
    dataset_object = {
        'biosample_ontology': {
            'term_name': 'head of caudate nucleus',
            'term_id': 'UBERON:0002626',
            'classification': 'tissue',
            '@id': '/biosample-types/tissue_UBERON_0002626/',
            'name': 'tissue_UBERON_0002626'
        },
        'replicates': [
            {
                'library': library
            }
        ]
    }
    with patch('adapters.file_fileset_adapter.requests.get', side_effect=request_side_effect):
        sample_ids, donor_ids, sample_term_to_sample_type, simple_sample_summaries, treatment_ids = FileFileSet.parse_sample_donor_treatment_encode(
            dataset_object)
    assert sample_ids == {'ENCBS123ABC'}
    assert donor_ids == {'ENCDO948PMW'}
    assert sample_term_to_sample_type == {
        'UBERON:0002626': '/biosample-types/tissue_UBERON_0002626/'}
    assert simple_sample_summaries == {
        'head of caudate nucleus from ENCDO948PMW treated with drug a, drug b'}
    assert treatment_ids == {'CHEBI:12345'}

    dataset_object = {
        'biosample_ontology': {
            'term_name': 'head of caudate nucleus',
            'term_id': 'UBERON:0002626',
            'classification': 'tissue',
            '@id': '/biosample-types/tissue_UBERON_0002626/',
            'name': 'tissue_UBERON_0002626'
        },
        'donor': '/human-donors/ENCDO948PMW/',
        'treatments': [
            {
                'treatment_term_id': 'CHEBI:67890',
                'treatment_term_name': 'drug c'
            }
        ]
    }
    with patch('adapters.file_fileset_adapter.requests.get', side_effect=request_side_effect):
        sample_ids, donor_ids, sample_term_to_sample_type, simple_sample_summaries, treatment_ids = FileFileSet.parse_sample_donor_treatment_encode(
            dataset_object)
    assert sample_ids == set()
    assert donor_ids == {'ENCDO948PMW'}
    assert sample_term_to_sample_type == {
        'UBERON:0002626': '/biosample-types/tissue_UBERON_0002626/'}
    assert simple_sample_summaries == {
        'head of caudate nucleus from ENCDO948PMW treated with drug c'}
    assert treatment_ids == {'CHEBI:67890'}


def test_query_fileset_files_props_encode():
    file_object = {'@id': '/files/ENCFF003BKC/', '@type': ['File', 'Item'], 'accession': 'ENCFF003BKC', 'analysis_step_version': {'schema_version': '4', 'aliases': ['encode:encode-re2g_enhancer_gene_predictions_step_v2_version'], 'software_versions': [{'schema_version': '4', 'aliases': ['encode:rE2g_v2'], 'software': {'aliases': ['encode:re2g_model'], 'references': [], 'date_created': '2023-06-27T19:00:41.613175+00:00', '@type': ['Software', 'Item'], 'submitted_by': '/users/8c832fff-23ec-4589-81c9-49a1c0020e46/', 'description': 'Train ENCODE-rE2G models on CRISPR enhancer screen data and apply to generate genome-wide predictions of enhancer-gene regulatory connections.', 'lab': '/labs/jesse-engreitz/', 'title': 'Distal regulation ENCODE-rE2G', 'used_by': ['ENCODE'], 'uuid': '11d1fe31-2784-449a-a3d8-e1fd41116a1d', 'source_url': 'https://github.com/EngreitzLab/ENCODE_rE2G', 'schema_version': '10', 'award': '/awards/UM1HG009436/', 'versions': ['/software-versions/db685a75-a35c-4052-bc9b-dc1f9da977e3/', '/software-versions/5b51197d-5cb0-4f54-afe6-d270665c9fbe/'], 'name': 'distal-regulation-encode_re2g', '@id': '/software/distal-regulation-encode_re2g/', 'status': 'released'}, 'date_created': '2024-05-28T04:29:01.090382+00:00', '@type': ['SoftwareVersion', 'Item'], 'submitted_by': '/users/6667a92a-d202-493a-8c7d-7a56d1380356/', '@id': '/software-versions/5b51197d-5cb0-4f54-afe6-d270665c9fbe/', 'downloaded_url': 'https://github.com/EngreitzLab/ENCODE_rE2G/releases/tag/v1.0.0', 'version': '1.0.0', 'uuid': '5b51197d-5cb0-4f54-afe6-d270665c9fbe', 'status': 'released'}], 'date_created': '2024-05-28T21:36:34.996156+00:00', 'analysis_step': {'aliases': ['encode:encode-re2g_enhancer_gene_predictions_step_v2'], 'analysis_step_types': ['element gene link prediction'], 'documents': [], 'date_created': '2024-05-28T05:30:31.599940+00:00', '@type': ['AnalysisStep', 'Item'], 'input_file_types': ['element gene links'], 'submitted_by': '/users/6667a92a-d202-493a-8c7d-7a56d1380356/', 'current_version':
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          '/analysis-step-versions/encode-e2g-enhancer-gene-predictions-step-v-2-0/', 'title': 'encode-e2g-enhancer-gene-predictions-step', 'step_label': 'encode-e2g-enhancer-gene-predictions-step', 'uuid': '689ef7b2-0553-48c5-a4ac-73a58ec4e3aa', 'schema_version': '17', 'output_file_types': ['element gene links', 'thresholded element gene links', 'thresholded links'], 'major_version': 2, 'pipelines': [{'analysis_steps': ['/analysis-steps/abc-element-gene-link-prediction-step-v-2/', '/analysis-steps/encode-e2g-enhancer-gene-predictions-step-v-2/'], 'aliases': ['encode:encode_rE2G_pipeline'], 'references': [], 'documents': [], 'assay_term_names': ['DNase-seq', 'ChIP-seq', 'CAGE', 'HiC'], 'date_created': '2024-05-28T04:23:49.891641+00:00', '@type': ['Pipeline', 'Item'], 'submitted_by': '/users/6667a92a-d202-493a-8c7d-7a56d1380356/', 'description': 'Applies ENCODE_rE2G models on chromatin accessibility assays to predict genome-wide enhancer-gene regulatory connection', 'accession': 'ENCPL835OUC', 'lab': '/labs/jesse-engreitz/', 'title': 'ENCODE_rE2G Pipeline', 'uuid': 'b3a1519f-6190-4316-ac39-8caffbf9691c', 'schema_version': '14', 'award': '/awards/UM1HG009436/', 'alternate_accessions': [], '@id': '/pipelines/ENCPL835OUC/', 'status': 'released'}], 'versions': ['/analysis-step-versions/encode-e2g-enhancer-gene-predictions-step-v-2-0/'], 'name': 'encode-e2g-enhancer-gene-predictions-step-v-2', '@id': '/analysis-steps/encode-e2g-enhancer-gene-predictions-step-v-2/', 'status': 'released', 'parents': ['/analysis-steps/abc-element-gene-link-prediction-step-v-2/']}, '@type': ['AnalysisStepVersion', 'Item'], 'name': 'encode-e2g-enhancer-gene-predictions-step-v-2-0', 'submitted_by': '/users/6667a92a-d202-493a-8c7d-7a56d1380356/', '@id': '/analysis-step-versions/encode-e2g-enhancer-gene-predictions-step-v-2-0/', 'uuid': '4e1fd6ec-7796-40e1-af89-58dc729aff6b', 'status': 'released', 'minor_version': 0}, 'dataset': '/annotations/ENCSR297HTV/', 'derived_from': ['/files/ENCFF632XQP/'], 'href': '/files/ENCFF003BKC/@@download/ENCFF003BKC.bed.gz'}
    with patch('adapters.file_fileset_adapter.requests.get', side_effect=request_side_effect):
        props, donor_ids, sample_types, disease_ids = FileFileSet.query_fileset_files_props_encode(
            file_object)
    assert props == {'_key': 'ENCFF003BKC', 'name': 'ENCFF003BKC', 'file_set_id': 'ENCSR297HTV', 'lab': 'jesse-engreitz', 'preferred_assay_titles': ['DNase-seq'], 'assay_term_ids': ['OBI:0001853'], 'method': 'ENCODE-rE2G', 'class': 'prediction', 'software': ['Distal regulation ENCODE-rE2G'], 'samples': ['ontology_terms/UBERON_0002626'], 'sample_ids': None, 'simple_sample_summaries': [
        'head of caudate nucleus from ENCDO948PMW'], 'donors': ['donors/ENCDO948PMW'], 'treatments_term_ids': None, 'publication': None, 'collections': ['genomic_elements', 'genomic_elements_genes'], 'source': 'ENCODE', 'source_url': 'https://www.encodeproject.org/files/ENCFF003BKC/', 'download_link': 'https://www.encodeproject.org/files/ENCFF003BKC/@@download/ENCFF003BKC.bed.gz', 'cell_annotation': None, 'genome_browser_link': 'https://www.encodeproject.org/files/ENCFF669BKC/@@download/ENCFF669BKC.bigInteract', 'crispr_modality': None}
    assert donor_ids == {'ENCDO948PMW'}
    assert sample_types == ['/biosample-types/tissue_UBERON_0002626/']
    assert disease_ids == []


def test_adapter_init_validate():
    writer = SpyWriter()
    adapter = FileFileSet(accessions=[
                          'ENCFF003BKC'], label='encode_file_fileset', writer=writer, validate=True)
    assert adapter.accessions == ['ENCFF003BKC']
    assert adapter.label == 'encode_file_fileset'
    assert adapter.writer == writer
    adapter = FileFileSet(accessions=[
                          'ENCFF003BKC'], label='encode_sample_term', writer=writer, validate=True)
    assert adapter.accessions == ['ENCFF003BKC']
    assert adapter.label == 'encode_sample_term'
    assert adapter.writer == writer
    adapter = FileFileSet(
        accessions=['ENCFF003BKC'], label='igvf_donor', writer=writer, validate=True)
    assert adapter.accessions == ['ENCFF003BKC']
    assert adapter.label == 'igvf_donor'
    assert adapter.writer == writer
    doc = {
        'name': 'invalid doc',
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(doc)


def test_process_file():
    writer = SpyWriter()
    adapter = FileFileSet(accessions=[
                          'ENCFF003BKC'], label='encode_file_fileset', writer=writer, validate=True)

    with patch('adapters.file_fileset_adapter.requests.get', side_effect=request_side_effect):
        adapter.process_file()
    assert len(writer.contents) == 1
    assert json.loads(writer.contents[0]) == {'_key': 'ENCFF003BKC', 'name': 'ENCFF003BKC', 'file_set_id': 'ENCSR297HTV', 'lab': 'jesse-engreitz', 'preferred_assay_titles': ['DNase-seq'], 'assay_term_ids': ['OBI:0001853'], 'method': 'ENCODE-rE2G', 'class': 'prediction', 'software': ['Distal regulation ENCODE-rE2G'], 'samples': ['ontology_terms/UBERON_0002626'], 'sample_ids': None, 'simple_sample_summaries': [
        'head of caudate nucleus from ENCDO948PMW'], 'donors': ['donors/ENCDO948PMW'], 'treatments_term_ids': None, 'publication': None, 'collections': ['genomic_elements', 'genomic_elements_genes'], 'source': 'ENCODE', 'source_url': 'https://www.encodeproject.org/files/ENCFF003BKC/', 'download_link': 'https://www.encodeproject.org/files/ENCFF003BKC/@@download/ENCFF003BKC.bed.gz', 'cell_annotation': None, 'genome_browser_link': 'https://www.encodeproject.org/files/ENCFF669BKC/@@download/ENCFF669BKC.bigInteract', 'crispr_modality': None}

    writer = SpyWriter()
    adapter = FileFileSet(accessions=[
                          'IGVFFI5688VHRS'], label='igvf_file_fileset', writer=writer, validate=True)
    with patch('adapters.file_fileset_adapter.requests.get', side_effect=request_side_effect):
        adapter.process_file()
    assert len(writer.contents) == 1
    assert json.loads(writer.contents[0]) == {'_key': 'IGVFFI5688VHRS', 'name': 'IGVFFI5688VHRS', 'file_set_id': 'IGVFDS2175LLDQ', 'lab': 'tim-reddy', 'preferred_assay_titles': ['STARR-seq'], 'assay_term_ids': ['OBI:0002041'], 'method': 'STARR-seq', 'class': 'observed data', 'software': ['BIRD', 'Samtools', 'pandas'], 'samples': ['ontology_terms/EFO_0002067'], 'sample_ids': ['IGVFSM3422QUYJ'], 'simple_sample_summaries': [
        'K562 with variants from 1000 Genomes donors: NA19108, NA19141, NA19146, NA19204, NA19235'], 'donors': ['donors/IGVFDO9208RPQQ'], 'treatments_term_ids': None, 'publication': None, 'collections': ['variants_biosamples', 'variants'], 'source': 'IGVF', 'source_url': 'https://data.igvf.org/tabular-files/IGVFFI5688VHRS/', 'download_link': 'https://api.data.igvf.org/tabular-files/IGVFFI5688VHRS/@@download/IGVFFI5688VHRS.bed.gz', 'cell_annotation': None, 'genome_browser_link': None, 'crispr_modality': None}

    write = SpyWriter()
    adapter = FileFileSet(
        accessions=['IGVFFI5688VHRS'], label='igvf_donor', writer=write, validate=True)
    with patch('adapters.file_fileset_adapter.requests.get', side_effect=request_side_effect):
        adapter.process_file()
    assert len(write.contents) == 1
    assert json.loads(write.contents[0]) == {'_key': 'IGVFDO9208RPQQ', 'name': 'IGVFDO9208RPQQ', 'sex': 'female', 'age': None, 'age_units': None,
                                             'ethnicities': None, 'phenotypic_features': None, 'source': 'IGVF', 'source_url': 'https://data.igvf.org/human-donors/IGVFDO9208RPQQ/'}

    write = SpyWriter()
    adapter = FileFileSet(accessions=[
                          'IGVFFI5688VHRS'], label='igvf_sample_term', writer=write, validate=True)
    with patch('adapters.file_fileset_adapter.requests.get', side_effect=request_side_effect):
        adapter.process_file()
    assert len(write.contents) == 1
    assert json.loads(write.contents[0]) == {'_key': 'NTR_0002067', 'name': 'K562', 'term_id': 'NTR_0002067', 'synonyms': ['GM05372', 'GM05372E', 'K-562', 'K-562 cell',
                                                                                                                           'K562 cell'], 'source': 'IGVF', 'source_url': 'https://data.igvf.org/sample-terms/NTR_0002067/', 'uri': 'https://data.igvf.org/sample-terms/NTR_0002067/'}
