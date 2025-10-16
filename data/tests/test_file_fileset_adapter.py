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
        'class': 'experiment',
        'software': ['MPRAflow tsv-to-bed'],
        'samples': ['ontology_terms/EFO_0009747'],
        'sample_ids': sorted(['ENCBS160ZPI', 'ENCBS659PKW', 'ENCBS825OJD']),
        'simple_sample_summaries': ['WTC11'],
        'donors': ['donors/ENCDO882UJI'],
        'treatments_term_ids': None,
        'publication': None,
        'source': 'ENCODE',
        'source_url': 'https://www.encodeproject.org//functional-characterization-experiments/ENCSR548AQS/'
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
        'method': 'element gene regulatory interaction predictions using Distal regulation ENCODE-rE2G',
        'class': 'prediction',
        'software': ['Distal regulation ENCODE-rE2G'],
        'samples': ['ontology_terms/UBERON_0002048'],
        'sample_ids': None,
        'simple_sample_summaries': ['lung from ENCDO528BHB'],
        'donors': ['donors/ENCDO528BHB'],
        'treatments_term_ids': None,
        'publication': None,
        'source': 'ENCODE',
        'source_url': 'https://www.encodeproject.org//annotations/ENCSR528UQX/'
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
        'class': 'experiment',
        'software': ['juicertools'],
        'samples': ['ontology_terms/NTR_0000633'],
        'sample_ids': sorted(['ENCBS951MKM']),
        'simple_sample_summaries': ['activated T-helper 1 cell from ENCDO374BBL treated with Interleukin-12 subunit alpha, Interleukin-12 subunit beta, Interleukin-2, Interleukin-4 antibody, anti-CD3 and anti-CD28 coated beads'],
        'donors': ['donors/ENCDO374BBL'],
        'treatments_term_ids': sorted(['UniProtKB:P29459', 'UniProtKB:P29460', 'UniProtKB:P60568']),
        'publication': None,
        'source': 'ENCODE',
        'source_url': 'https://www.encodeproject.org//experiments/ENCSR902BCW/'
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
        'class': 'integrative analysis',
        'software': sorted(['BEDTools', 'bigWigAverageOverBed']),
        'samples': None,
        'sample_ids': None,
        'simple_sample_summaries': None,
        'donors': None,
        'treatments_term_ids': None,
        'publication': None,
        'source': 'ENCODE',
        'source_url': 'https://www.encodeproject.org//annotations/ENCSR800VNX/'
    }


@pytest.mark.external_dependency
@patch('adapters.file_fileset_adapter.check_collection_loaded', return_value=True)
def test_file_fileset_adapter_igvf_bluestarr_prediction(mock_check):
    writer = SpyWriter()
    adapter = FileFileSet(accessions=['IGVFFI1236SEPK'],
                          label='igvf_file_fileset',
                          writer=writer,
                          validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item == {
        '_key': 'IGVFFI1236SEPK',
        'name': 'IGVFFI1236SEPK',
        'file_set_id': 'IGVFDS0257SDNV',
        'lab': 'bill-majoros',
        'preferred_assay_titles': None,
        'assay_term_ids': None,
        'method': 'functional effect prediction on scope of loci using BlueSTARR v0.1.0',
        'class': 'prediction',
        'software': ['BlueSTARR'],
        'samples': ['ontology_terms/EFO_0002067'],
        'sample_ids': ['IGVFSM7883WOIS'],
        'simple_sample_summaries': ['K562'],
        'donors': ['donors/IGVFDO9208RPQQ'],
        'treatments_term_ids': None,
        'publication': None,
        'source': 'IGVF',
        'source_url': 'https://api.data.igvf.org//prediction-sets/IGVFDS0257SDNV/'
    }


@pytest.mark.external_dependency
@patch('adapters.file_fileset_adapter.check_collection_loaded', return_value=True)
def test_file_fileset_adapter_igvf_sccripsr_screen(mock_check):
    writer = SpyWriter()
    adapter = FileFileSet(accessions=['IGVFFI4846IRZK'],
                          label='igvf_file_fileset',
                          writer=writer,
                          validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item == {
        '_key': 'IGVFFI4846IRZK',
        'name': 'IGVFFI4846IRZK',
        'file_set_id': 'IGVFDS4021XJLW',
        'lab': 'jay-shendure',
        'preferred_assay_titles': ['scCRISPR screen'],
        'assay_term_ids': ['OBI:0003660'],
        'method': 'scCRISPR screen',
        'class': 'experiment',
        'software': ['Sceptre'],
        'samples': ['ontology_terms/CL_0000540'],
        'sample_ids': sorted(['IGVFSM7750SNNY', 'IGVFSM8317ZTFV', 'IGVFSM8382KOXO', 'IGVFSM9913PXTT']),
        'simple_sample_summaries': ['neuron differentiated cell specimen from IGVFDO1756PPKO'],
        'donors': ['donors/IGVFDO1756PPKO'],
        'treatments_term_ids': None,
        'publication': 'doi:10.1038/s41467-024-52490-4',
        'source': 'IGVF',
        'source_url': 'https://api.data.igvf.org//analysis-sets/IGVFDS4021XJLW/'
    }


@pytest.mark.external_dependency
@patch('adapters.file_fileset_adapter.check_collection_loaded', return_value=True)
def test_file_fileset_adapter_igvf_hicar(mock_check):
    writer = SpyWriter()
    adapter = FileFileSet(accessions=['IGVFFI6913PEWI'],
                          label='igvf_file_fileset',
                          writer=writer,
                          validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item == {
        '_key': 'IGVFFI6913PEWI',
        'name': 'IGVFFI6913PEWI',
        'file_set_id': 'IGVFDS7797WATU',
        'lab': 'charles-gersbach',
        'preferred_assay_titles': ['HiCAR'],
        'assay_term_ids': ['OBI:0002440'],
        'method': 'HiCAR',
        'class': 'experiment',
        'software': ['DESeq2'],
        'samples': ['ontology_terms/CL_0000746'],
        'sample_ids': sorted(['IGVFSM1839OFIJ', 'IGVFSM2698DFOT', 'IGVFSM6802DUZM', 'IGVFSM7176NKKR', 'IGVFSM7610LWOV']),
        'simple_sample_summaries': ['cardiac muscle cell differentiated cell specimen from IGVFDO1756PPKO treated with Endothelin-1'],
        'donors': ['donors/IGVFDO1756PPKO'],
        'treatments_term_ids': ['CHEBI:80240'],
        'publication': 'doi:10.1101/2025.07.19.665672',
        'source': 'IGVF',
        'source_url': 'https://api.data.igvf.org//analysis-sets/IGVFDS7797WATU/'
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
        'source_url': 'https://api.data.igvf.org/IGVFDO1756PPKO'
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
        'uri': 'https://api.data.igvf.org/sample-terms/CL_0000746/',
        'term_id': 'CL_0000746',
        'name': 'cardiac muscle cell',
        'synonyms': sorted([
            'cardiac muscle fiber',
            'cardiac myocyte',
            'heart muscle cell',
            'cardiomyocyte'
        ]),
        'source': 'IGVF',
        'source_url': 'https://api.data.igvf.org/sample-terms/CL_0000746/'
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
        'source_url': 'https://www.encodeproject.org/ENCDO374BBL'
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
