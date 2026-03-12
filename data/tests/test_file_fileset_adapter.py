import json
import pytest
from urllib.parse import urljoin
from adapters.file_fileset_adapter import FileFileSet
from adapters.writer import SpyWriter

from unittest.mock import patch, Mock


@pytest.mark.external_dependency
def test_file_fileset_adapter_encode_functional_characterization_mpra_props():
    writer = SpyWriter()
    adapter = FileFileSet(accessions=['ENCFF230JYM'],
                          label='encode_file_fileset',
                          writer=writer,
                          validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item == {
        '_key': 'ENCFF230JYM',
        'name': 'ENCFF230JYM',
        'file_set_id': 'ENCSR548AQS',
        'lab': 'nadav-ahituv',
        'preferred_assay_titles': ['MPRA'],
        'assay_term_ids': ['OBI:0002675'],
        'method': 'MPRA',
        'class': 'observed data',
        'software': ['MPRAflow tsv-to-bed'],
        'samples': ['ontology_terms/EFO_0009747'],
        'sample_ids': sorted(['ENCBS160ZPI', 'ENCBS659PKW', 'ENCBS825OJD']),
        'simple_sample_summaries': ['WTC11'],
        'donors': ['donors/ENCDO882UJI'],
        'treatments_term_ids': None,
        'publication': None,
        'collections': ['genomic_elements_biosamples', 'genomic_elements'],
        'source': 'ENCODE',
        'source_url': 'https://www.encodeproject.org/files/ENCFF230JYM/'
    }


@pytest.mark.external_dependency
def test_file_fileset_adapter_encode_E2G_annotation():
    writer = SpyWriter()
    adapter = FileFileSet(accessions=['ENCFF324XYW'],
                          label='encode_file_fileset',
                          writer=writer,
                          validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item == {
        '_key': 'ENCFF324XYW',
        'name': 'ENCFF324XYW',
        'file_set_id': 'ENCSR528UQX',
        'lab': 'jesse-engreitz',
        'preferred_assay_titles': ['DNase-seq'],
        'assay_term_ids': ['OBI:0001853'],
        'method': 'ENCODE-rE2G',
        'class': 'prediction',
        'software': ['Distal regulation ENCODE-rE2G'],
        'samples': ['ontology_terms/UBERON_0002048'],
        'sample_ids': None,
        'simple_sample_summaries': ['lung from ENCDO528BHB'],
        'donors': ['donors/ENCDO528BHB'],
        'treatments_term_ids': None,
        'collections': ['genomic_elements', 'genomic_elements_genes'],
        'publication': None,
        'source': 'ENCODE',
        'source_url': 'https://www.encodeproject.org/files/ENCFF324XYW/'
    }


@pytest.mark.external_dependency
def test_file_fileset_adapter_encode_caQTL():
    writer = SpyWriter()
    adapter = FileFileSet(accessions=['ENCFF103XRK'],
                          label='encode_file_fileset',
                          writer=writer,
                          validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item == {
        '_key': 'ENCFF103XRK',
        'name': 'ENCFF103XRK',
        'file_set_id': 'ENCSR266TOD',
        'lab': 'j-michael-cherry',
        'preferred_assay_titles': None,
        'assay_term_ids': None,
        'method': 'caQTL',
        'class': 'observed data',
        'software': None,
        'samples': ['ontology_terms/CL_0011020'],
        'sample_ids': None,
        'simple_sample_summaries': ['neural progenitor cell'],
        'donors': None,
        'treatments_term_ids': None,
        'publication': 'PMID:34017130',
        'collections': [
            'variants_genomic_elements',
            'genomic_elements',
        ],
        'source': 'ENCODE',
        'source_url': 'https://www.encodeproject.org/files/ENCFF103XRK/'
    }


@pytest.mark.external_dependency
def test_file_fileset_adapter_encode_crispr_enhancer_perturbation_screens():
    writer = SpyWriter()
    adapter = FileFileSet(accessions=['ENCFF968BZL'],
                          label='encode_file_fileset',
                          writer=writer,
                          validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item == {
        '_key': 'ENCFF968BZL',
        'name': 'ENCFF968BZL',
        'file_set_id': 'ENCSR998YDI',
        'lab': 'jesse-engreitz',
        'preferred_assay_titles': None,
        'assay_term_ids': None,
        'method': 'CRISPR enhancer perturbation screen',
        'class': 'observed data',
        'software': ['DistalRegulationCRISPRdata'],
        'samples': ['ontology_terms/EFO_0002067'],
        'sample_ids': None,
        'simple_sample_summaries': ['K562'],
        'donors': None,
        'treatments_term_ids': None,
        'publication': None,
        'collections': [
            'genomic_elements',
            'genomic_elements_genes',
        ],
        'source': 'ENCODE',
        'source_url': 'https://www.encodeproject.org/files/ENCFF968BZL/'
    }


@pytest.mark.external_dependency
def test_file_fileset_adapter_encode_ccREs():
    writer = SpyWriter()
    adapter = FileFileSet(accessions=['ENCFF420VPZ'],
                          label='encode_file_fileset',
                          writer=writer,
                          validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item == {
        '_key': 'ENCFF420VPZ',
        'name': 'ENCFF420VPZ',
        'file_set_id': 'ENCSR800VNX',
        'lab': 'zhiping-weng',
        'preferred_assay_titles': None,
        'assay_term_ids': None,
        'method': 'candidate Cis-Regulatory Elements',
        'class': 'observed data',
        'software': sorted(['BEDTools', 'bigWigAverageOverBed']),
        'samples': None,
        'sample_ids': None,
        'simple_sample_summaries': None,
        'donors': None,
        'treatments_term_ids': None,
        'publication': None,
        'collections': ['genomic_elements'],
        'source': 'ENCODE',
        'source_url': 'https://www.encodeproject.org/files/ENCFF420VPZ/'
    }


@pytest.mark.external_dependency
def test_file_fileset_adapter_igvf_bluestarr_prediction():
    writer = SpyWriter()
    adapter = FileFileSet(accessions=['IGVFFI1663LKVQ'],
                          label='igvf_file_fileset',
                          writer=writer,
                          validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item == {
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
        'source_url': 'https://data.igvf.org/tabular-files/IGVFFI1663LKVQ/'
    }


@pytest.mark.external_dependency
def test_file_fileset_adapter_igvf_sccripsr_screen():
    writer = SpyWriter()
    adapter = FileFileSet(accessions=['IGVFFI9721OCVW'],
                          label='igvf_file_fileset',
                          writer=writer,
                          validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item == {
        '_key': 'IGVFFI9721OCVW',
        'name': 'IGVFFI9721OCVW',
        'file_set_id': 'IGVFDS8364HJHL',
        'lab': 'charles-gersbach',
        'preferred_assay_titles': ['CRISPR FACS screen'],
        'assay_term_ids': ['OBI:0003661'],
        'method': 'CRISPR FACS screen',
        'class': 'observed data',
        'software': ['FRACTEL'],
        'samples': ['ontology_terms/CL_0000909'],
        'sample_ids': sorted(['IGVFSM3895SURE', 'IGVFSM7158ADKU', 'IGVFSM7887TFLH', 'IGVFSM8084QKPW']),
        'simple_sample_summaries': ['CD8-positive, alpha-beta memory T cell'],
        'donors': sorted(['donors/IGVFDO2763RVOY', 'donors/IGVFDO8306NDTY']),
        'treatments_term_ids': None,
        'publication': 'PMID:37945901',
        'collections': [
            'genomic_elements_genes',
            'genomic_elements',
        ],
        'source': 'IGVF',
        'source_url': 'https://data.igvf.org/tabular-files/IGVFFI9721OCVW/'
    }


@pytest.mark.external_dependency
def test_file_fileset_adapter_igvf_sem_prediction():
    writer = SpyWriter()
    adapter = FileFileSet(accessions=['IGVFFI2943RVII'],
                          label='igvf_file_fileset',
                          writer=writer,
                          validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item == {
        '_key': 'IGVFFI2943RVII',
        'name': 'IGVFFI2943RVII',
        'file_set_id': 'IGVFDS0298TQHQ',
        'lab': 'alan-boyle',
        'preferred_assay_titles': None,
        'assay_term_ids': None,
        'method': 'SEMVAR',
        'class': 'prediction',
        'software': ['SEMVAR'],
        'samples': None,
        'sample_ids': None,
        'simple_sample_summaries': None,
        'donors': None,
        'treatments_term_ids': None,
        'publication': None,
        'collections': ['variants_proteins'],
        'source': 'IGVF',
        'source_url': 'https://data.igvf.org/tabular-files/IGVFFI2943RVII/'
    }


@pytest.mark.external_dependency
@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_igvf')
def test_file_fileset_adapter_igvf_donor(mock_query_props):
    mock_query_props.return_value = (
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


@pytest.mark.external_dependency
@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_igvf')
def test_file_fileset_adapter_igvf_sample_term_non_NTR(mock_query_props):
    mock_query_props.return_value = (
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


@pytest.mark.external_dependency
@patch('adapters.file_fileset_adapter.requests.get')
@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_encode')
def test_file_fileset_adapter_encode_sample_term_NTR(mock_query_props, mock_request):
    mock_query_props.return_value = (
        {},  # props
        set(),  # donors
        {'NTR_0000633'},
        []  # disease_ids
    )
    mock_request.return_value.json.return_value = {
        '@id': '/biosample-types/primary_cell_NTR_0000633/',
        'term_id': 'NTR_0000633',
        'term_name': 'activated T-helper 1 cell',
        'synonyms': None
    }

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


@pytest.mark.external_dependency
@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_encode')
def test_file_fileset_adapter_encode_donor(mock_query_props):
    mock_query_props.return_value = (
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


@pytest.mark.external_dependency
@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_encode')
def test_file_fileset_adapter_encode_sample_term(mock_query_props):
    mock_query_props.return_value = (
        {},  # props
        set(),  # donors
        {'/biosample-types/primary_cell_NTR_0000633/'},
        []  # disease_ids
    )

    writer = SpyWriter()
    adapter = FileFileSet(
        accessions=['ENCFF610AYI'],
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
    api_url = 'https://api.data.igvf.org/'
    input_file_path = 'files/IGVFFI0000DERI/'
    asv_ref = api_url + 'analysis-step-versions/IGVFASV0000DERI/'
    sv_ref = api_url + 'software-versions/IGVFSVV0000DERI/'
    software_ref = api_url + 'software/IGVFSW0000DERI/'

    input_file_object = {
        'analysis_step_version': {'@id': asv_ref},
    }
    analysis_step_version_object = {
        'software_versions': [sv_ref],
    }
    software_version_object = {
        'software': software_ref,
    }
    software_object = {'title': 'Test Software'}

    # Build URLs the same way the adapter does so keys match exactly
    url_to_json = {
        urljoin(api_url, input_file_path + '/@@embedded?format=json'): input_file_object,
        urljoin(api_url, asv_ref + '/@@object?format=json'): analysis_step_version_object,
        urljoin(api_url, sv_ref + '/@@object?format=json'): software_version_object,
        urljoin(api_url, software_ref + '/@@object?format=json'): software_object,
    }

    def mock_get_side_effect(url, **kwargs):
        response = Mock()
        response.json.return_value = url_to_json.get(url, {})
        return response

    mock_get.side_effect = mock_get_side_effect

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
    base_url = 'https://api.data.igvf.org/'
    sample_embedded_url = base_url + 'samples/IGVFSM0000STARR/@@embedded?format=json'
    sample_object = {
        'accession': 'IGVFSM0000STARR',
        'donors': [{'accession': 'IGVFDO0000STARR'}],
        'classifications': ['cell line'],
        'targeted_sample_term': {'@id': base_url + 'sample-terms/EFO_0002067/'},
        'construct_library_sets': [{'@id': base_url + 'construct-library-sets/IGVFCLS0000STARR/'}],
    }
    targeted_sample_term = {'term_name': 'K562', 'term_id': 'EFO:0002067'}
    construct_library_set = {
        'integrated_content_files': [base_url + 'tabular-files/IGVFFI0000STARR/'],
    }
    integrated_content_file = {
        'file_set': base_url + 'curated-sets/IGVFCS0000STARR/'}
    curated_set = {'donors': [base_url + 'human-donors/IGVFDO1000G/']}
    donor_1000g = {'dbxrefs': ['IGSR:NA12345', 'IGSR:NA67890']}

    def mock_get_side_effect(url, **kwargs):
        response = Mock()
        if 'samples' in url and '@@embedded' in url:
            response.json.return_value = sample_object
        elif 'sample-terms' in url:
            response.json.return_value = targeted_sample_term
        elif 'construct-library-sets' in url:
            response.json.return_value = construct_library_set
        elif 'curated-sets' in url:
            response.json.return_value = curated_set
        elif 'tabular-files' in url:
            response.json.return_value = integrated_content_file
        elif 'human-donors' in url:
            response.json.return_value = donor_1000g
        else:
            response.json.return_value = {}
        return response

    mock_get.side_effect = mock_get_side_effect

    # IGVF adapter with minimal setup; we only call parse_sample_donor_treatment_igvf
    writer = SpyWriter()
    adapter = FileFileSet(
        accessions=['IGVFFI0000STARR'],
        label='igvf_file_fileset',
        writer=writer,
    )
    fileset_object = {
        'samples': [
            {'@id': base_url + 'samples/IGVFSM0000STARR/',
                'targeted_sample_term': True}
        ],
    }

    sample_ids, donor_ids, sample_term_ids, simple_sample_summaries, treatment_ids = (
        adapter.parse_sample_donor_treatment_igvf(fileset_object, 'STARR-seq')
    )

    assert sample_ids == {'IGVFSM0000STARR'}
    assert 'EFO:0002067' in sample_term_ids
    assert simple_sample_summaries == {
        'K562 cell line with variants from 1000 Genomes donors: NA12345, NA67890'
    }


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
