import json
import pytest
from adapters.file_fileset_adapter import FileFileSet
from adapters.writer import SpyWriter

from unittest.mock import patch


@pytest.mark.external_dependency
@patch('adapters.file_fileset_adapter.check_collection_loaded', return_value=True)
def test_file_fileset_adapter_encode_functional_characterization_mpra_props(mock_check):
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
        'source': 'ENCODE',
        'source_url': 'https://www.encodeproject.org/files/ENCFF230JYM/'
    }


@pytest.mark.external_dependency
@patch('adapters.file_fileset_adapter.check_collection_loaded', return_value=True)
def test_file_fileset_adapter_encode_E2G_annotation(mock_check):
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
        'publication': None,
        'source': 'ENCODE',
        'source_url': 'https://www.encodeproject.org/files/ENCFF324XYW/'
    }


@pytest.mark.external_dependency
@patch('adapters.file_fileset_adapter.check_collection_loaded', return_value=True)
def test_file_fileset_adapter_encode_HiC_experiment_with_treatments(mock_check):
    writer = SpyWriter()
    adapter = FileFileSet(accessions=['ENCFF610AYI'],
                          label='encode_file_fileset',
                          writer=writer,
                          validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item == {
        '_key': 'ENCFF610AYI',
        'name': 'ENCFF610AYI',
        'file_set_id': 'ENCSR902BCW',
        'lab': 'erez-aiden',
        'preferred_assay_titles': ['HiC'],
        'assay_term_ids': ['OBI:0002042'],
        'method': 'HiC',
        'class': 'observed data',
        'software': ['juicertools'],
        'samples': ['ontology_terms/NTR_0000633'],
        'sample_ids': sorted(['ENCBS951MKM']),
        'simple_sample_summaries': ['activated T-helper 1 cell from ENCDO374BBL treated with Interleukin-12 subunit alpha, Interleukin-12 subunit beta, Interleukin-2, Interleukin-4 antibody, anti-CD3 and anti-CD28 coated beads'],
        'donors': ['donors/ENCDO374BBL'],
        'treatments_term_ids': sorted(['UniProtKB:P29459', 'UniProtKB:P29460', 'UniProtKB:P60568']),
        'publication': None,
        'source': 'ENCODE',
        'source_url': 'https://www.encodeproject.org/files/ENCFF610AYI/'
    }


@pytest.mark.external_dependency
@patch('adapters.file_fileset_adapter.check_collection_loaded', return_value=True)
def test_file_fileset_adapter_encode_ccREs(mock_check):
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
        'source': 'ENCODE',
        'source_url': 'https://www.encodeproject.org/files/ENCFF420VPZ/'
    }


@pytest.mark.external_dependency
@patch('adapters.file_fileset_adapter.check_collection_loaded', return_value=True)
def test_file_fileset_adapter_igvf_bluestarr_prediction(mock_check):
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
        'source': 'IGVF',
        'source_url': 'https://data.igvf.org/tabular-files/IGVFFI1663LKVQ/'
    }


@pytest.mark.external_dependency
@patch('adapters.file_fileset_adapter.check_collection_loaded', return_value=True)
def test_file_fileset_adapter_igvf_sccripsr_screen(mock_check):
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
        'source': 'IGVF',
        'source_url': 'https://data.igvf.org/tabular-files/IGVFFI9721OCVW/'
    }


@pytest.mark.external_dependency
@patch('adapters.file_fileset_adapter.check_collection_loaded', return_value=True)
def test_file_fileset_adapter_igvf_sem_prediction(mock_check):
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
        'source': 'IGVF',
        'source_url': 'https://data.igvf.org/tabular-files/IGVFFI2943RVII/'
    }


@pytest.mark.external_dependency
@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_igvf')
@patch('adapters.file_fileset_adapter.check_collection_loaded', return_value=True)
def test_file_fileset_adapter_igvf_donor(mock_check_loaded, mock_query_props):
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
@patch('adapters.file_fileset_adapter.check_collection_loaded', return_value=True)
def test_file_fileset_adapter_igvf_sample_term(mock_check_loaded, mock_query_props):
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

    first_item = json.loads(writer.contents[0])
    assert first_item == {
        '_key': 'CL_0000746',
        'uri': 'https://data.igvf.org/sample-terms/CL_0000746/',
        'term_id': 'CL_0000746',
        'name': 'cardiac muscle cell',
        'synonyms': sorted([
            'cardiac muscle fiber',
            'cardiac myocyte',
            'heart muscle cell',
            'cardiomyocyte'
        ]),
        'source': 'IGVF',
        'source_url': 'https://data.igvf.org/sample-terms/CL_0000746/'
    }


@pytest.mark.external_dependency
@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_encode')
@patch('adapters.file_fileset_adapter.check_collection_loaded', return_value=True)
def test_file_fileset_adapter_encode_donor(mock_check_loaded, mock_query_props):
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
@patch('adapters.file_fileset_adapter.check_collection_loaded', return_value=True)
def test_file_fileset_adapter_encode_sample_term(mock_check_loaded, mock_query_props):
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
