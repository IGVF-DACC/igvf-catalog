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
    }
