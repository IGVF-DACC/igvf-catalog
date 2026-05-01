import json
import gzip
from unittest.mock import patch
from adapters.igvf_E2G_CRISPR_adapter import IGVFE2GCRISPR
from adapters.writer import SpyWriter
import pytest


# mock get_file_fileset_by_accession_in_arangodb so files_fileset data change will not affect the test
@pytest.fixture
def mock_file_fileset_perturb_seq():
    """Fixture to mock get_file_fileset_by_accession_in_arangodb function for Perturb-seq method."""
    with patch('adapters.igvf_E2G_CRISPR_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'method': 'Perturb-seq',
            'class': 'observed data',
            'crispr_modality': 'interference',
            'simple_sample_summaries': ['CD8-positive, alpha-beta memory T cell'],
            'samples': ['ontology_terms/CL_0000909'],
            'treatments_term_ids': None
        }
        yield mock_get_file_fileset


@pytest.fixture
def mock_file_fileset_facs_screen():
    """Fixture to mock get_file_fileset_by_accession_in_arangodb function for CRISPR screen method."""
    with patch('adapters.igvf_E2G_CRISPR_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'method': 'CRISPR screen',
            'class': 'observed data',
            'crispr_modality': 'activation',
            'simple_sample_summaries': ['CD8-positive, alpha-beta memory T cell'],
            'samples': ['ontology_terms/CL_0000909'],
            'treatments_term_ids': None
        }
        yield mock_get_file_fileset


def test_igvf_e2g_crispr_adapter_perturb_seq_genomic_elements(mock_file_fileset_perturb_seq, mocker):
    writer = SpyWriter()
    with patch('adapters.igvf_E2G_CRISPR_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True

        adapter = IGVFE2GCRISPR(
            filepath='./samples/igvf_E2G_CRISPR_perturb_seq_example.txt.gz', source_url='https://api.data.igvf.org/tabular-files/IGVFFI6830YLEK/', label='genomic_element', writer=writer, validate=True)
        adapter.process_file()
        first_item = json.loads(writer.contents[0])
        assert len(writer.contents) > 0
        assert first_item['_key'] == 'CRISPR_chr1_212699339_212700840_GRCh38_IGVFFI6830YLEK'
        assert first_item['name'] == 'CRISPR_chr1_212699339_212700840_GRCh38_IGVFFI6830YLEK'
        assert first_item['chr'] == 'chr1'
        assert first_item['start'] == 212699339
        assert first_item['end'] == 212700840
        assert first_item['type'] == 'tested elements'
        assert first_item['method'] == 'Perturb-seq'
        assert first_item['promoter_of'] == 'genes/ENSG00000123685'
        assert first_item['source_annotation'] == 'promoter'
        assert first_item['source'] == 'IGVF'
        assert first_item['source_url'] == 'https://api.data.igvf.org/tabular-files/IGVFFI6830YLEK/'
        assert first_item['files_filesets'] == 'files_filesets/IGVFFI6830YLEK'


def test_igvf_e2g_crispr_adapter_perturb_seq_genomic_elements_genes(mock_file_fileset_perturb_seq, mocker):
    writer = SpyWriter()
    with patch('adapters.igvf_E2G_CRISPR_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True

        adapter = IGVFE2GCRISPR(
            filepath='./samples/igvf_E2G_CRISPR_perturb_seq_example.txt.gz', source_url='https://api.data.igvf.org/tabular-files/IGVFFI6830YLEK/', label='genomic_element_gene', writer=writer, validate=True)
        adapter.process_file()
        first_item = json.loads(writer.contents[0])
        assert first_item['_key'] == 'CRISPR_chr1_212699339_212700840_GRCh38_ENSG00000123685_IGVFFI6830YLEK'
        assert first_item['_from'] == 'genomic_elements/CRISPR_chr1_212699339_212700840_GRCh38_IGVFFI6830YLEK'
        assert first_item['_to'] == 'genes/ENSG00000123685'
        assert first_item['p_value'] == 0.0
        assert first_item['log2FC'] == 3.608562048
        assert first_item['pct_1'] == 0.918
        assert first_item['pct_2'] == 0.282
        assert first_item['p_value_adj'] == 0.0
        assert first_item['method'] == 'Perturb-seq'
        assert first_item['crispr_modality'] == 'interference'
        assert first_item['biological_context'] == 'CD8-positive, alpha-beta memory T cell'
        assert first_item['biosample_term'] == 'ontology_terms/CL_0000909'
        assert first_item['treatments_term_ids'] == None
        assert first_item['label'] == IGVFE2GCRISPR.COLLECTION_LABEL
        assert first_item['class'] == 'observed data'
        assert first_item['name'] == 'modulates expression of'
        assert first_item['inverse_name'] == 'expression modulated by'
        assert first_item['source'] == 'IGVF'
        assert first_item['source_url'] == 'https://api.data.igvf.org/tabular-files/IGVFFI6830YLEK/'
        assert first_item['files_filesets'] == 'files_filesets/IGVFFI6830YLEK'


def test_igvf_e2g_crispr_adapter_perturb_seq_enhancer_only_genomic_elements(mock_file_fileset_perturb_seq, tmp_path):
    writer = SpyWriter()
    test_file = tmp_path / 'igvf_E2G_CRISPR_enhancer_only_perturb_seq.txt.gz'
    header = (
        'p_val\tavg_log2FC\tpct.1\tpct.2\tp_val_adj\tgene_symbol\t'
        'target_gene\tintended_target_name\tintended_target_chr\t'
        'intended_target_start\tintended_target_end\n'
    )
    row = (
        '0\t-0.612084335\t0.744\t0.994\t0\tMYH9\tENSG00000100345\t'
        'chr22:36387779-36388133\tchr22\t36387779\t36388133\n'
    )
    with gzip.open(test_file, 'wt') as out:
        out.write(header)
        out.write(row)

    with patch('adapters.igvf_E2G_CRISPR_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.side_effect = lambda x: x.startswith(
            'ENSG')

        adapter = IGVFE2GCRISPR(
            filepath=str(test_file),
            source_url='https://api.data.igvf.org/tabular-files/IGVFFI1215LWLH/',
            label='genomic_element',
            writer=writer,
            validate=True
        )
        adapter.process_file()

    parsed = [json.loads(item) for item in writer.contents if item.strip()]
    assert len(parsed) == 1
    first_item = parsed[0]
    assert first_item['_key'] == 'CRISPR_chr22_36387779_36388133_GRCh38_IGVFFI1215LWLH'
    assert first_item['source_annotation'] == 'enhancer'
    assert 'promoter_of' not in first_item


def test_igvf_e2g_crispr_adapter_perturb_seq_uses_ensembl_id_column(mock_file_fileset_perturb_seq, tmp_path):
    writer = SpyWriter()
    test_file = tmp_path / 'igvf_E2G_CRISPR_perturb_seq_ensembl_id_header.txt.gz'
    header = (
        'p_val\tavg_log2FC\tpct.1\tpct.2\tp_val_adj\tgene_symbol\t'
        'ensembl_id\tintended_target_name\tintended_target_chr\t'
        'intended_target_start\tintended_target_end\n'
    )
    row = (
        '0\t-0.612084335\t0.744\t0.994\t0\tMYH9\tENSG00000100345\t'
        'chr22:36387779-36388133\tchr22\t36387779\t36388133\n'
    )
    with gzip.open(test_file, 'wt') as out:
        out.write(header)
        out.write(row)

    with patch('adapters.igvf_E2G_CRISPR_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.side_effect = lambda x: x.startswith(
            'ENSG')

        adapter = IGVFE2GCRISPR(
            filepath=str(test_file),
            source_url='https://api.data.igvf.org/tabular-files/IGVFFI1215LWLH/',
            label='genomic_element_gene',
            writer=writer,
            validate=True
        )
        adapter.process_file()

    parsed = [json.loads(item) for item in writer.contents if item.strip()]
    assert len(parsed) == 1
    first_item = parsed[0]
    assert first_item['_to'] == 'genes/ENSG00000100345'
    assert first_item['log2FC'] == -0.612084335


def test_igvf_e2g_crispr_adapter_perturb_seq_strips_ensembl_version(mock_file_fileset_perturb_seq, tmp_path):
    writer = SpyWriter()
    test_file = tmp_path / 'igvf_E2G_CRISPR_perturb_seq_with_ensembl_version.txt.gz'
    header = (
        'p_val\tavg_log2FC\tpct.1\tpct.2\tp_val_adj\tgene_symbol\t'
        'ensembl_id\tintended_target_name\tintended_target_chr\t'
        'intended_target_start\tintended_target_end\n'
    )
    row = (
        '0\t-0.612084335\t0.744\t0.994\t0\tMYH9\tENSG00000174038.13\t'
        'chr22:36387779-36388133\tchr22\t36387779\t36388133\n'
    )
    with gzip.open(test_file, 'wt') as out:
        out.write(header)
        out.write(row)

    with patch('adapters.igvf_E2G_CRISPR_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.side_effect = lambda x: x == 'ENSG00000174038'

        adapter = IGVFE2GCRISPR(
            filepath=str(test_file),
            source_url='https://api.data.igvf.org/tabular-files/IGVFFI1215LWLH/',
            label='genomic_element_gene',
            writer=writer,
            validate=True
        )
        adapter.process_file()

    parsed = [json.loads(item) for item in writer.contents if item.strip()]
    assert len(parsed) == 1
    first_item = parsed[0]
    assert first_item['_to'] == 'genes/ENSG00000174038'


def test_igvf_e2g_crispr_adapter_tap_seq_direct_targeting_genomic_element(mock_file_fileset_perturb_seq, tmp_path):
    writer = SpyWriter()
    test_file = tmp_path / 'igvf_E2G_CRISPR_tap_seq_direct_targeting.txt.gz'
    header = (
        'intended_target_name\tguide_id(s)\ttargeting_chr\ttargeting_start\t'
        'targeting_end\ttype\tgene_id\tgene_symbol\tsceptre_log2_fc\t'
        'sceptre_p_value\tsceptre_adj_p_value\tsignificant\tsample_term_name\t'
        'sample_term_id\tsample_summary_short\tpower_at_effect_size_15\tnotes\n'
    )
    row = (
        'chr4:55181617-55182218\tguide-1,guide-2\tchr4\t55181617\t55182218\t'
        'Direct_targeting\tENSG00000145681\tHAPLN1\t1.60726510888607\t'
        '7.25503908439717e-29\t3.51143891684823e-26\tTRUE\twtc11_d4_ec\tNA\t'
        'ipsc_ec\tNA\tNA\n'
    )
    with gzip.open(test_file, 'wt') as out:
        out.write(header)
        out.write(row)

    with patch('adapters.igvf_E2G_CRISPR_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.side_effect = lambda x: x.startswith(
            'ENSG')

        adapter = IGVFE2GCRISPR(
            filepath=str(test_file),
            source_url='https://api.data.igvf.org/tabular-files/IGVFFI1215LWLH/',
            label='genomic_element',
            writer=writer,
            validate=True
        )
        adapter.process_file()

    parsed = [json.loads(item) for item in writer.contents if item.strip()]
    assert len(parsed) == 1
    first_item = parsed[0]
    assert first_item['source_annotation'] == 'enhancer'
    assert 'promoter_of' not in first_item


def test_igvf_e2g_crispr_adapter_tap_seq_sceptre_fields_genomic_element_gene(mock_file_fileset_perturb_seq, tmp_path):
    writer = SpyWriter()
    test_file = tmp_path / 'igvf_E2G_CRISPR_tap_seq_sceptre_metrics.txt.gz'
    header = (
        'intended_target_name\tguide_id(s)\ttargeting_chr\ttargeting_start\t'
        'targeting_end\ttype\tgene_id\tgene_symbol\tsceptre_log2_fc\t'
        'sceptre_p_value\tsceptre_adj_p_value\tsignificant\tsample_term_name\t'
        'sample_term_id\tsample_summary_short\tpower_at_effect_size_15\tnotes\n'
    )
    row = (
        'chr4:55181617-55182218\tguide-1,guide-2\tchr4\t55181617\t55182218\t'
        'targeting\tENSG00000128917\tDLL4\t-0.576747067613555\t'
        '2.13033821184895e-25\t5.15541847267446e-23\tTRUE\twtc11_d4_ec\tNA\t'
        'ipsc_ec\tNA\tNA\n'
    )
    with gzip.open(test_file, 'wt') as out:
        out.write(header)
        out.write(row)

    with patch('adapters.igvf_E2G_CRISPR_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.side_effect = lambda x: x.startswith(
            'ENSG')

        adapter = IGVFE2GCRISPR(
            filepath=str(test_file),
            source_url='https://api.data.igvf.org/tabular-files/IGVFFI1215LWLH/',
            label='genomic_element_gene',
            writer=writer,
            validate=True
        )
        adapter.process_file()

    parsed = [json.loads(item) for item in writer.contents if item.strip()]
    assert len(parsed) == 1
    first_item = parsed[0]
    assert first_item['_to'] == 'genes/ENSG00000128917'
    assert first_item['log2FC'] == -0.576747067613555
    assert first_item['p_value'] == 2.13033821184895e-25
    assert first_item['p_value_adj'] == 5.15541847267446e-23
    assert first_item['significant'] is True


def test_igvf_e2g_crispr_adapter_facs_screen_genomic_elements(mock_file_fileset_facs_screen, mocker):
    writer = SpyWriter()
    with patch('adapters.igvf_E2G_CRISPR_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True

        adapter = IGVFE2GCRISPR(
            filepath='./samples/igvf_E2G_CRISPR_facs_screen_example.txt.gz', source_url='https://api.data.igvf.org/tabular-files/IGVFFI9721OCVW/', label='genomic_element', writer=writer, validate=True)
        adapter.process_file()
        first_item = json.loads(writer.contents[0])
        assert len(writer.contents) > 0
        assert first_item['_key'] == 'CRISPR_chr1_998962_999432_GRCh38_IGVFFI9721OCVW'
        assert first_item['name'] == 'CRISPR_chr1_998962_999432_GRCh38_IGVFFI9721OCVW'
        assert first_item['chr'] == 'chr1'
        assert first_item['start'] == 998962
        assert first_item['end'] == 999432
        assert first_item['type'] == 'tested elements'
        assert first_item['method'] == 'CRISPR screen'
        assert first_item['promoter_of'] == 'genes/ENSG00000188290'
        assert first_item['source_annotation'] == 'promoter'
        assert first_item['source'] == 'IGVF'
        assert first_item['source_url'] == 'https://api.data.igvf.org/tabular-files/IGVFFI9721OCVW/'
        assert first_item['files_filesets'] == 'files_filesets/IGVFFI9721OCVW'


def test_igvf_e2g_crispr_adapter_facs_screen_genomic_elements_genes(mock_file_fileset_facs_screen, mocker):
    writer = SpyWriter()
    with patch('adapters.igvf_E2G_CRISPR_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True

        adapter = IGVFE2GCRISPR(
            filepath='./samples/igvf_E2G_CRISPR_facs_screen_example.txt.gz', source_url='https://api.data.igvf.org/tabular-files/IGVFFI9721OCVW/', label='genomic_element_gene', writer=writer, validate=True)
        adapter.process_file()
        first_item = json.loads(writer.contents[0])
        assert first_item['_key'] == 'CRISPR_chr1_998962_999432_GRCh38_ENSG00000126353_IGVFFI9721OCVW'
        assert first_item['_from'] == 'genomic_elements/CRISPR_chr1_998962_999432_GRCh38_IGVFFI9721OCVW'
        assert first_item['_to'] == 'genes/ENSG00000126353'
        assert first_item['p_value'] == 0.7264835
        assert first_item['p_value_adj'] == 0.9994257067617868
        assert first_item['effect_size'] == 0.2254047296279381
        assert first_item['method'] == 'CRISPR screen'
        assert first_item['crispr_modality'] == 'activation'
        assert first_item['biological_context'] == 'CD8-positive, alpha-beta memory T cell'
        assert first_item['biosample_term'] == 'ontology_terms/CL_0000909'
        assert first_item['treatments_term_ids'] == None
        assert first_item['label'] == IGVFE2GCRISPR.COLLECTION_LABEL
        assert first_item['class'] == 'observed data'
        assert first_item['name'] == 'modulates expression of'
        assert first_item['inverse_name'] == 'expression modulated by'
        assert first_item['source'] == 'IGVF'
        assert first_item['source_url'] == 'https://api.data.igvf.org/tabular-files/IGVFFI9721OCVW/'
        assert first_item['files_filesets'] == 'files_filesets/IGVFFI9721OCVW'


def test_igvf_e2g_crispr_adapter_invalid_label(mock_file_fileset_perturb_seq):
    writer = SpyWriter()
    with pytest.raises(ValueError):
        adapter = IGVFE2GCRISPR(
            filepath='./samples/igvf_E2G_CRISPR_perturb_seq_example.txt.gz', source_url='https://api.data.igvf.org/tabular-files/IGVFFI6830YLEK/', label='invalid_label', writer=writer, validate=True)


def test_igvf_e2g_crispr_adapter_validate_doc_invalid(mock_file_fileset_perturb_seq):
    writer = SpyWriter()
    adapter = IGVFE2GCRISPR(
        filepath='./samples/igvf_E2G_CRISPR_perturb_seq_example.txt.gz', source_url='https://api.data.igvf.org/tabular-files/IGVFFI6830YLEK/', label='genomic_element', writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError):
        adapter.validate_doc(invalid_doc)
