import json
import pytest
from adapters.file_fileset_adapter import FileFileSet
from adapters.writer import SpyWriter


def test_file_fileset_adapter_encode_functional_characterization_mpra_props():
    writer = SpyWriter()
    adapter = FileFileSet(accession='ENCFF230JYM',
                          label='encode_file_fileset',
                          writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item == {
        '_key': 'ENCFF230JYM',
        'file_set_id': 'ENCSR548AQS',
        'lab': 'nadav-ahituv',
        'preferred_assay_titles': ['MPRA'],
        'assay_term_ids': ['OBI:0002675'],
        'prediction': False,
        'prediction_method': None,
        'software': ['mpraflow-tsv-to-bed'],
        'samples': ['EFO:0009747'],
        'sample_ids': sorted(['ENCBS160ZPI', 'ENCBS659PKW', 'ENCBS825OJD']),
        'simple_sample_summaries': ['WTC11'],
        'donor_ids': ['ENCDO882UJI'],
        'treatments_term_ids': None,
        'publication': None,
        'source': 'ENCODE'
    }


def test_file_fileset_adapter_encode_E2G_annotation():
    writer = SpyWriter()
    adapter = FileFileSet(accession='ENCFF324XYW',
                          label='encode_file_fileset',
                          writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item == {
        '_key': 'ENCFF324XYW',
        'file_set_id': 'ENCSR528UQX',
        'lab': 'jesse-engreitz',
        'preferred_assay_titles': ['DNase-seq'],
        'assay_term_ids': ['OBI:0001853'],
        'prediction': True,
        'prediction_method': 'element gene regulatory interaction predictions',
        'software': ['distal-regulation-encode_re2g'],
        'samples': ['UBERON:0002048'],
        'sample_ids': None,
        'simple_sample_summaries': ['lung from ENCDO528BHB'],
        'donor_ids': ['ENCDO528BHB'],
        'treatments_term_ids': None,
        'publication': None,
        'source': 'ENCODE'
    }


def test_file_fileset_adapter_encode_HiC_experiment_with_treatments():
    writer = SpyWriter()
    adapter = FileFileSet(accession='ENCFF610AYI',
                          label='encode_file_fileset',
                          writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item == {
        '_key': 'ENCFF610AYI',
        'file_set_id': 'ENCSR902BCW',
        'lab': 'erez-aiden',
        'preferred_assay_titles': ['HiC'],
        'assay_term_ids': ['OBI:0002042'],
        'prediction': False,
        'prediction_method': None,
        'software': ['juicertools'],
        'samples': ['NTR:0000633'],
        'sample_ids': sorted(['ENCBS951MKM']),
        'simple_sample_summaries': ['activated T-helper 1 cell from ENCDO374BBL treated with Interleukin-12 subunit alpha, Interleukin-12 subunit beta, Interleukin-2, Interleukin-4 antibody, anti-CD3 and anti-CD28 coated beads'],
        'donor_ids': ['ENCDO374BBL'],
        'treatments_term_ids': sorted(['UniProtKB:P29459', 'UniProtKB:P29460', 'UniProtKB:P60568']),
        'publication': None,
        'source': 'ENCODE'
    }


def test_file_fileset_adapter_igvf_bluestarr_prediction():
    writer = SpyWriter()
    adapter = FileFileSet(accession='IGVFFI1236SEPK',
                          label='igvf_file_fileset',
                          writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item == {
        '_key': 'IGVFFI1236SEPK',
        'file_set_id': 'IGVFDS0257SDNV',
        'lab': 'bill-majoros',
        'preferred_assay_titles': None,
        'assay_term_ids': None,
        'prediction': True,
        'prediction_method': 'functional effect',
        'software': ['bluestarr'],
        'samples': ['EFO:0002067'],
        'sample_ids': ['IGVFSM7883WOIS'],
        'simple_sample_summaries': ['K562'],
        'donor_ids': ['IGVFDO9208RPQQ'],
        'treatments_term_ids': None,
        'publication': None,
        'source': 'IGVF'
    }


def test_file_fileset_adapter_igvf_sccripsr_screen():
    writer = SpyWriter()
    adapter = FileFileSet(accession='IGVFFI4846IRZK',
                          label='igvf_file_fileset',
                          writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item == {
        '_key': 'IGVFFI4846IRZK',
        'file_set_id': 'IGVFDS4021XJLW',
        'lab': 'jay-shendure',
        'preferred_assay_titles': ['scCRISPR screen'],
        'assay_term_ids': ['OBI:0003660'],
        'prediction': False,
        'prediction_method': None,
        'software': ['sceptre'],
        'samples': ['CL:0000540'],
        'sample_ids': sorted(['IGVFSM7750SNNY', 'IGVFSM8317ZTFV', 'IGVFSM8382KOXO', 'IGVFSM9913PXTT']),
        'simple_sample_summaries': ['neuron differentiated cell specimen from IGVFDO1756PPKO'],
        'donor_ids': ['IGVFDO1756PPKO'],
        'treatments_term_ids': None,
        'publication': 'doi:10.1038/s41467-024-52490-4',
        'source': 'IGVF'
    }


def test_file_fileset_adapter_igvf_hicar():
    writer = SpyWriter()
    adapter = FileFileSet(accession='IGVFFI6913PEWI',
                          label='igvf_file_fileset',
                          writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item == {
        '_key': 'IGVFFI6913PEWI',
        'file_set_id': 'IGVFDS7797WATU',
        'lab': 'charles-gersbach',
        'preferred_assay_titles': ['HiCAR'],
        'assay_term_ids': ['OBI:0002440'],
        'prediction': False,
        'prediction_method': None,
        'software': ['deseq2'],
        'samples': ['CL:0000746'],
        'sample_ids': sorted(['IGVFSM1839OFIJ', 'IGVFSM2698DFOT', 'IGVFSM6802DUZM', 'IGVFSM7176NKKR', 'IGVFSM7610LWOV']),
        'simple_sample_summaries': ['cardiac muscle cell differentiated cell specimen from IGVFDO1756PPKO treated with Endothelin-1'],
        'donor_ids': ['IGVFDO1756PPKO'],
        'treatments_term_ids': ['CHEBI:80240'],
        'publication': None,
        'source': 'IGVF'
    }
