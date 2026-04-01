import json
from pathlib import Path
import pytest
from adapters.file_fileset_adapter import FileFileSet
from adapters.writer import SpyWriter

from unittest.mock import patch, Mock

REQUEST_FIXTURES_PATH = Path(__file__).resolve().parent / \
    'fixtures' / 'file_fileset_requests.json'


def load_request_fixtures():
    with REQUEST_FIXTURES_PATH.open('r', encoding='utf-8') as fixture_file:
        return json.load(fixture_file)


REQUEST_FIXTURES = load_request_fixtures()


def request_fixture_side_effect(url, **kwargs):
    if url not in REQUEST_FIXTURES:
        raise AssertionError(f'Missing request fixture for {url}')
    fixture = REQUEST_FIXTURES[url]
    response = Mock()
    if isinstance(fixture, dict) and '__status_code__' in fixture:
        response.status_code = fixture['__status_code__']
        response.json.return_value = fixture.get('__json__', {})
    else:
        response.status_code = 200
        response.json.return_value = fixture
    return response


@patch('adapters.file_fileset_adapter.requests.get')
def test_file_fileset_adapter_igvf_bluestarr_prediction(mock_get):
    mock_get.side_effect = request_fixture_side_effect
    writer = SpyWriter()
    adapter = FileFileSet(accessions=['IGVFFI1663LKVQ'],
                          label='igvf_file_fileset',
                          writer=writer,
                          validate=False)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    expected = {
        '_key': 'IGVFFI1663LKVQ',
        'name': 'IGVFFI1663LKVQ',
        'file_set_id': 'IGVFDS2340WJRV',
        'lab': 'bill-majoros',
        'preferred_assay_titles': None,
        'assay_term_ids': None,
        'method': 'BlueSTARR',
        'class': 'prediction',
        'software': ['BlueSTARR'],
        'samples': ['ontology_terms/EFO_0002067'],
        'sample_ids': ['IGVFSM7883WOIS'],
        'simple_sample_summaries': ['K562'],
        'donors': ['donors/IGVFDO9208RPQQ'],
        'treatments_term_ids': None,
        'publication': None,
        'collections': [
            'variants',
            'variants_genomic_elements',
        ],
        'source': 'IGVF',
        'source_url': 'https://data.igvf.org/tabular-files/IGVFFI1663LKVQ/',
        'download_link': 'https://api.data.igvf.org/tabular-files/IGVFFI1663LKVQ/@@download/IGVFFI1663LKVQ.bed.gz',
        'cell_annotation': None
    }
    for key, value in expected.items():
        assert first_item.get(key) == value


@patch('adapters.file_fileset_adapter.requests.get')
@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_igvf')
@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_encode')
def test_file_fileset_adapter_donors(mock_query_props_encode, mock_query_props_igvf, mock_request):
    mock_request.side_effect = request_fixture_side_effect

    mock_query_props_igvf.return_value = (
        {},  # props
        {'IGVFDO1756PPKO'},
        set()  # unloaded_sample_types
    )
    writer = SpyWriter()
    adapter = FileFileSet(
        accessions=['IGVFFI6913PEWI'],
        label='igvf_donor',
        writer=writer,
        validate=True
    )
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item == {
        '_key': 'IGVFDO1756PPKO',
        'name': 'IGVFDO1756PPKO',
        'sex': 'male',
        'age': None,
        'age_units': None,
        'ethnicities': ['Japanese'],
        'phenotypic_features': None,
        'source': 'IGVF',
        'source_url': 'https://data.igvf.org/human-donors/IGVFDO1756PPKO/'
    }

    mock_query_props_encode.return_value = (
        {},  # props
        {'ENCDO374BBL'},
        set(),  # unloaded_sample_types
        []  # disease_ids
    )
    writer = SpyWriter()
    adapter = FileFileSet(
        accessions=['ENCFF610AYI'],
        label='encode_donor',
        writer=writer,
        validate=True
    )
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item == {
        '_key': 'ENCDO374BBL',
        'name': 'ENCDO374BBL',
        'sex': 'male',
        'age': '35',
        'age_units': 'year',
        'ethnicities': None,
        'phenotypic_features': None,
        'source': 'ENCODE',
        'source_url': 'https://www.encodeproject.org/human-donors/ENCDO374BBL/'
    }


@patch('adapters.file_fileset_adapter.requests.get')
@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_igvf')
@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_encode')
def test_file_fileset_adapter_sample_terms(mock_query_props_encode, mock_query_props_igvf, mock_request):
    mock_request.side_effect = request_fixture_side_effect

    mock_query_props_igvf.return_value = (
        {},  # props
        set(),  # donors
        {'CL_0000746'}
    )
    writer = SpyWriter()
    adapter = FileFileSet(
        accessions=['IGVFFI6913PEWI'],
        label='igvf_sample_term',
        writer=writer,
        validate=True
    )
    adapter.process_file()
    assert len(writer.contents) == 0

    mock_query_props_encode.return_value = (
        {},  # props
        set(),  # donors
        {'NTR_0000633'},
        []  # disease_ids
    )
    writer = SpyWriter()
    adapter = FileFileSet(
        accessions=['ENCFF202KAO'],
        label='encode_sample_term',
        writer=writer,
        validate=True
    )
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item == {
        '_key': 'NTR_0000633',
        'uri': 'https://www.encodeproject.org/biosample-types/primary_cell_NTR_0000633/',
        'term_id': 'NTR_0000633',
        'name': 'activated T-helper 1 cell',
        'synonyms': None,
        'source': 'ENCODE',
        'source_url': 'https://www.encodeproject.org/biosample-types/primary_cell_NTR_0000633/'
    }


@patch('adapters.file_fileset_adapter.requests.get')
def test_get_software_igvf_derived_manually(mock_get):
    """When file has derived_manually=True, software is collected from derived_from input files' `analysis_step_version`."""
    input_file_path = 'files/IGVFFI0000DERI/'
    mock_get.side_effect = request_fixture_side_effect

    writer = SpyWriter()
    adapter = FileFileSet(
        accessions=[],
        label='igvf_file_fileset',
        writer=writer,
    )
    file_object = {
        'derived_manually': True,
        'derived_from': [input_file_path],
    }

    software = adapter.get_software_igvf(file_object)

    assert software == {'Test Software'}


@patch('adapters.file_fileset_adapter.requests.get')
def test_parse_sample_donor_treatment_igvf_starr_seq_1000_genomes_donors(mock_get):
    """STARR-seq special case: simple_sample_summary includes 1000 Genomes donor ids from construct library sets."""
    mock_get.side_effect = request_fixture_side_effect

    # IGVF adapter with minimal setup; we only call parse_sample_donor_treatment_igvf
    writer = SpyWriter()
    adapter = FileFileSet(
        accessions=['IGVFFI0000STARR'],
        label='igvf_file_fileset',
        writer=writer,
    )
    fileset_object = {
        'samples': [
            {'@id': '/samples/IGVFSM0000STARR',
                'targeted_sample_term': True}
        ],
    }

    sample_ids, donor_ids, sample_term_ids, simple_sample_summaries, treatment_ids = (
        adapter.parse_sample_donor_treatment_igvf(fileset_object, 'STARR-seq')
    )

    assert sample_ids == {'IGVFSM0000STARR'}
    assert 'CL:0000540' in sample_term_ids
    assert simple_sample_summaries == {
        'K562 cell line induced to neuron with variants from 1000 Genomes donors: NA12345, NA67890'
    }


@patch('adapters.file_fileset_adapter.requests.get')
def test_parse_sample_donor_treatment_igvf_targeted_sample_term(mock_get):
    """Targeted sample (e.g. lentiMPRA): summary is '{sample_term_names} {classifications} induced to {targeted}'
    (matches igvfd Biosample summary order) and sample_term_ids contains only the targeted term id."""
    base_url = 'https://api.data.igvf.org/'
    # Modeled on IGVFDS9979HNMM: WTC-11 induced to cardiac muscle cell (differentiated cell specimen)
    sample_object = {
        'accession': 'IGVFSM3359VZOR',
        'donors': [{'accession': 'IGVFDO1756PPKO'}],
        'classifications': ['differentiated cell specimen'],
        'sample_terms': [{'@id': base_url + 'sample-terms/EFO_0009747/'}],
        'targeted_sample_term': {'@id': base_url + 'sample-terms/CL_0000746/'},
    }
    wtc11_term = {'term_name': 'GM25256 (WTC-11)', 'term_id': 'EFO:0009747'}
    cardiac_muscle_term = {
        'term_name': 'cardiac muscle cell', 'term_id': 'CL:0000746'}

    def mock_get_side_effect(url, **kwargs):
        response = Mock()
        if 'IGVFSM3359VZOR' in url and '@@embedded' in url:
            response.json.return_value = sample_object
        elif 'EFO_0009747' in url:
            response.json.return_value = wtc11_term
        elif 'CL_0000746' in url:
            response.json.return_value = cardiac_muscle_term
        else:
            response.json.return_value = {}
        return response

    mock_get.side_effect = mock_get_side_effect

    writer = SpyWriter()
    adapter = FileFileSet(
        accessions=['IGVFFI0708TBIQ'],
        label='igvf_file_fileset',
        writer=writer,
    )
    fileset_object = {
        'samples': [
            {'@id': base_url + 'in-vitro-systems/IGVFSM3359VZOR/',
                'targeted_sample_term': True},
        ],
    }

    sample_ids, donor_ids, sample_term_ids, simple_sample_summaries, treatment_ids = (
        adapter.parse_sample_donor_treatment_igvf(fileset_object, 'MPRA')
    )

    assert sample_ids == {'IGVFSM3359VZOR'}
    assert donor_ids == {'IGVFDO1756PPKO'}
    # only targeted term, not EFO:0009747
    assert sample_term_ids == {'CL:0000746'}
    assert simple_sample_summaries == {
        'GM25256 (WTC-11) differentiated cell specimen induced to cardiac muscle cell from IGVFDO1756PPKO',
    }


@patch('adapters.file_fileset_adapter.requests.get')
@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_encode')
def test_process_file_skips_duplicates(mock_query_props, mock_get):
    mock_get.side_effect = request_fixture_side_effect
    mock_query_props.return_value = (
        {},  # props
        {'ENCDO374BBL'},
        set(),
        []
    )
    writer = SpyWriter()
    adapter = FileFileSet(
        accessions=['ENCFF230JYM', 'ENCFF324XYW'],
        label='encode_donor',
        writer=writer,
        validate=False
    )
    adapter.process_file()
    assert len(writer.contents) == 1

    mock_query_props.return_value = (
        {},  # props
        set(),
        {'NTR_0000633'},
        []
    )
    writer = SpyWriter()
    adapter = FileFileSet(
        accessions=['ENCFF230JYM', 'ENCFF324XYW'],
        label='encode_sample_term',
        writer=writer,
        validate=False
    )
    adapter.process_file()
    assert len(writer.contents) == 1


@patch('adapters.file_fileset_adapter.requests.get')
def test_get_file_object_forbidden(mock_get):
    mock_get.side_effect = request_fixture_side_effect
    adapter = FileFileSet(
        accessions=[],
        label='encode_file_fileset',
        writer=SpyWriter()
    )
    with pytest.raises(ValueError, match='not publicly released'):
        adapter.get_file_object('ENCFF000403')


@patch('adapters.file_fileset_adapter.requests.get')
def test_file_fileset_adapter_encode_file_fileset_validate_true(mock_get):
    mock_get.side_effect = request_fixture_side_effect
    writer = SpyWriter()
    adapter = FileFileSet(
        accessions=['ENCFF230JYM'],
        label='encode_file_fileset',
        writer=writer,
        validate=True
    )
    adapter.process_file()
    assert len(writer.contents) == 1


@patch('adapters.file_fileset_adapter.requests.get')
def test_parse_annotation_encode_variants(mock_get):
    mock_get.side_effect = request_fixture_side_effect
    adapter = FileFileSet(accessions=[], label='encode_file_fileset')

    software = set()
    dataset_object = {
        'annotation_type': 'prediction',
        'software_used': [
            {'software': {'title': 'PredictorSoft'}}
        ],
        'experimental_input': []
    }
    class_type, method, _, _, _ = adapter.parse_annotation_encode(
        dataset_object, software
    )
    assert class_type == 'prediction'
    assert method == 'prediction'
    assert 'PredictorSoft' in software

    with pytest.raises(ValueError, match='Predictions require software'):
        adapter.parse_annotation_encode(
            {'annotation_type': 'prediction'}, set())

    observed_object = {
        'annotation_type': 'caQTLs',
        'experimental_input': ['/experiments/EXP_DNASE'],
        'disease_term_id': []
    }
    class_type, method, _, preferred_assay_titles, assay_term_ids = (
        adapter.parse_annotation_encode(observed_object, set())
    )
    assert class_type == 'observed data'
    assert method == 'caQTL'
    assert preferred_assay_titles == {'DNase-seq'}
    assert assay_term_ids == {'OBI:0001853'}


def test_get_assay_encode_list():
    adapter = FileFileSet(accessions=[], label='encode_file_fileset')
    dataset_object = {
        'assay_term_name': ['Assay A', 'Assay B'],
        'assay_term_id': 'OBI:0000001'
    }
    assay_term_ids, preferred_assay_titles = adapter.get_assay_encode(
        dataset_object, set(), set())
    assert preferred_assay_titles == ['Assay A', 'Assay B']
    assert assay_term_ids == ['OBI:0000001']


def test_get_publication_helpers():
    encode_adapter = FileFileSet(accessions=[], label='encode_file_fileset')
    with pytest.raises(ValueError, match='multiple publications'):
        encode_adapter.get_publication_encode(
            {'references': [{'identifiers': ['PMID:1']},
                            {'identifiers': ['PMID:2']}]}
        )
    assert encode_adapter.get_publication_encode(
        {'references': [{'identifiers': ['PMID:123']}]}
    ) == 'PMID:123'

    igvf_adapter = FileFileSet(accessions=[], label='igvf_file_fileset')
    with pytest.raises(ValueError, match='multiple publications'):
        igvf_adapter.get_publication_igvf(
            {'publications': [{'publication_identifiers': ['PMID:1']},
                              {'publication_identifiers': ['PMID:2']}]}
        )
    assert igvf_adapter.get_publication_igvf(
        {'publications': [{'publication_identifiers': ['PMID:456']}]}
    ) == 'PMID:456'


def test_parse_sample_donor_treatment_encode_mismatch_raises():
    adapter = FileFileSet(accessions=[], label='encode_file_fileset')
    dataset_object = {
        'biosample_ontology': {
            'term_id': 'EFO:1',
            'term_name': 'Type A',
            'classification': 'tissue',
            '@id': '/biosample-types/EFO_1/'
        },
        'replicates': [
            {
                'library': {
                    'biosample': {
                        'accession': 'ENCBS1',
                        'biosample_ontology': {
                            '@id': '/biosample-types/EFO_2/',
                            'term_id': 'EFO:2',
                            'term_name': 'Type B',
                            'classification': 'tissue'
                        }
                    }
                }
            }
        ]
    }
    with pytest.raises(ValueError, match='Biosample type'):
        adapter.parse_sample_donor_treatment_encode(dataset_object)


def test_parse_sample_donor_treatment_encode_with_treatments():
    adapter = FileFileSet(accessions=[], label='encode_file_fileset')
    dataset_object = {
        'replicates': [
            {
                'library': {
                    'biosample': {
                        'accession': 'ENCBS1',
                        'biosample_ontology': {
                            '@id': '/biosample-types/EFO_1/',
                            'term_id': 'EFO:1',
                            'term_name': 'Type A',
                            'classification': 'tissue'
                        },
                        'donor': {'accession': 'ENCDO1'},
                        'treatments': [
                            {'treatment_term_id': 'CHEBI:1',
                             'treatment_term_name': 'Drug A'}
                        ]
                    }
                }
            }
        ]
    }
    _, donor_ids, _, simple_sample_summaries, treatment_ids = (
        adapter.parse_sample_donor_treatment_encode(dataset_object)
    )
    assert donor_ids == {'ENCDO1'}
    assert treatment_ids == {'CHEBI:1'}
    assert simple_sample_summaries == {
        'Type A from ENCDO1 treated with Drug A'}


@patch('adapters.file_fileset_adapter.requests.get')
def test_parse_sample_donor_treatment_encode_fallback_donor(mock_get):
    mock_get.side_effect = request_fixture_side_effect
    adapter = FileFileSet(accessions=[], label='encode_file_fileset')
    dataset_object = {
        'biosample_ontology': {
            'term_id': 'EFO:1',
            'term_name': 'Type A',
            'classification': 'tissue',
            '@id': '/biosample-types/EFO_1/'
        },
        'donor': '/human-donors/ENCDO000TEST',
        'treatments': [
            {'treatment_term_id': 'CHEBI:2', 'treatment_term_name': 'Drug B'}
        ]
    }
    _, donor_ids, _, simple_sample_summaries, treatment_ids = (
        adapter.parse_sample_donor_treatment_encode(dataset_object)
    )
    assert donor_ids == {'ENCDO000TEST'}
    assert treatment_ids == {'CHEBI:2'}
    assert simple_sample_summaries == {
        'Type A from ENCDO000TEST treated with Drug B'}


@patch('adapters.file_fileset_adapter.requests.get')
def test_parse_sample_donor_treatment_igvf_classification_treatment(mock_get):
    mock_get.side_effect = request_fixture_side_effect
    adapter = FileFileSet(accessions=[], label='igvf_file_fileset')
    fileset_object = {
        'samples': [
            {
                '@id': '/samples/IGVFSM0000TRET',
                'treatments': [
                    {'@id': '/treatments/IGVFTT0000'}
                ]
            }
        ]
    }
    _, donor_ids, sample_term_ids, simple_sample_summaries, treatment_ids = (
        adapter.parse_sample_donor_treatment_igvf(fileset_object, 'Method')
    )
    assert donor_ids == {'IGVFDO0000TRET'}
    assert sample_term_ids == {'CL:0000001'}
    assert treatment_ids == {'CHEBI:123'}
    assert simple_sample_summaries == {
        'organoid cell from IGVFDO0000TRET treated with Drug'
    }


@patch('adapters.file_fileset_adapter.requests.get')
def test_decompose_analysis_set_to_measurement_set_igvf(mock_get):
    mock_get.side_effect = request_fixture_side_effect
    adapter = FileFileSet(accessions=[], label='igvf_file_fileset')
    measurement_sets = adapter.decompose_analysis_set_to_measurement_set_igvf(
        '/analysis-sets/IGVFDS0000ANAL'
    )
    assert measurement_sets == {
        '/measurement-sets/IGVFMS0000A',
        '/measurement-sets/IGVFMS0000B',
        '/measurement-sets/IGVFMS0000C'
    }


@patch('adapters.file_fileset_adapter.requests.get')
def test_parse_analysis_set_igvf_with_analysis_set_input(mock_get):
    mock_get.side_effect = request_fixture_side_effect
    adapter = FileFileSet(accessions=[], label='igvf_file_fileset')
    fileset_object = {
        'input_file_sets': [
            {'@id': '/analysis-sets/IGVFDS0000ANAL2'}
        ]
    }
    preferred_assay_titles, assay_term_ids = adapter.parse_analysis_set_igvf(
        fileset_object
    )
    assert 'Assay D' in preferred_assay_titles
    assert 'OBI:0001234' in assay_term_ids


@patch('adapters.file_fileset_adapter.requests.get')
def test_query_fileset_files_props_encode_overrides(mock_get):
    mock_get.side_effect = request_fixture_side_effect
    adapter = FileFileSet(accessions=[], label='encode_file_fileset')
    props, _, _, _ = adapter.query_fileset_files_props_encode('ENCFF324XYW')
    assert props['method'] == 'ENCODE-rE2G'
    props, _, _, _ = adapter.query_fileset_files_props_encode('ENCFF968BZL')
    assert props['method'] == 'CRISPR enhancer perturbation screen'
    props, _, _, _ = adapter.query_fileset_files_props_encode('ENCFF420VPZ')
    assert props['collections'] == ['genomic_elements']
    props, _, _, _ = adapter.query_fileset_files_props_encode('ENCFF167FJQ')
    assert props['collections'] == ['mm_genomic_elements']
    with pytest.raises(ValueError, match='multiple assays'):
        adapter.query_fileset_files_props_encode('ENCFFMULTI')
    with pytest.raises(ValueError, match='Catalog collections are required'):
        adapter.query_fileset_files_props_encode('ENCFF000NOCOL')


@patch('adapters.file_fileset_adapter.requests.get')
def test_query_fileset_files_props_igvf_variants(mock_get):
    mock_get.side_effect = request_fixture_side_effect
    adapter = FileFileSet(accessions=[], label='igvf_file_fileset')
    props, _, _ = adapter.query_fileset_files_props_igvf('IGVFFI0000NOSW')
    assert props['method'] == 'Curated summary'
    with pytest.raises(ValueError, match='Catalog collections are required'):
        adapter.query_fileset_files_props_igvf('IGVFFI0000NOCOL')
    with pytest.raises(ValueError, match='Prediction sets require software'):
        adapter.query_fileset_files_props_igvf('IGVFFI0000PREDNOSW')
    with pytest.raises(ValueError, match='currently unsupported'):
        adapter.query_fileset_files_props_igvf('IGVFFI0000UNSUP')
    with pytest.raises(ValueError, match='multiple assays'):
        adapter.query_fileset_files_props_igvf('IGVFFI0000ANALM')
    props, _, _ = adapter.query_fileset_files_props_igvf('IGVFFI0000MPRA')
    assert props['method'] == 'MPRA'
    assert props['assay_term_ids'] == ['OBI:0002675']


@patch('adapters.file_fileset_adapter.requests.get')
def test_get_donor_props_with_disease_ids(mock_get):
    mock_get.side_effect = request_fixture_side_effect
    adapter = FileFileSet(accessions=[], label='encode_donor')
    donor_props = next(adapter.get_donor_props(
        {'ENCDO374BBL'}, disease_ids=['DOID:0080832']))
    assert donor_props['phenotypic_features'] == ['ontology_terms/HP_0100543']


def test_validate_doc_invalid():
    writer = SpyWriter()
    adapter = FileFileSet(
        accessions=['ENCFF610AYI'],
        label='encode_sample_term',
        writer=writer,
        validate=True
    )
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)


def test_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label. Allowed values:'):
        FileFileSet(
            accessions=['ENCFF610AYI'],
            label='invalid_label',
            writer=writer,
            validate=True
        )
