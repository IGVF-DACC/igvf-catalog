import json
import gzip
from unittest.mock import patch

import pytest

from adapters.igvf_E2G_CRISPR_adapter import IGVFE2GCRISPR
from adapters.writer import SpyWriter


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
            filepath='./samples/igvf_E2G_CRISPR_perturb_seq_example.txt.gz', source_url='https://api.data.igvf.org/tabular-files/IGVFFI3069QCRA/', label='genomic_element', writer=writer, validate=True)
        adapter.process_file()
        first_item = json.loads(writer.contents[0])
        assert len(writer.contents) > 0
        assert first_item['_key'] == 'CRISPR_chr1_212699339_212700840_GRCh38_IGVFFI3069QCRA'
        assert first_item['name'] == 'CRISPR_chr1_212699339_212700840_GRCh38_IGVFFI3069QCRA'
        assert first_item['chr'] == 'chr1'
        assert first_item['start'] == 212699339
        assert first_item['end'] == 212700840
        assert first_item['type'] == 'tested elements'
        assert first_item['method'] == 'Perturb-seq'
        assert first_item['promoter_of'] == 'genes/ENSG00000123685'
        assert first_item['source_annotation'] == 'promoter'
        assert first_item['source'] == 'IGVF'
        assert first_item['source_url'] == 'https://api.data.igvf.org/tabular-files/IGVFFI3069QCRA/'
        assert first_item['files_filesets'] == 'files_filesets/IGVFFI3069QCRA'


def test_igvf_e2g_crispr_adapter_perturb_seq_genomic_elements_genes(mock_file_fileset_perturb_seq, mocker):
    writer = SpyWriter()
    with patch('adapters.igvf_E2G_CRISPR_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True

        adapter = IGVFE2GCRISPR(
            filepath='./samples/igvf_E2G_CRISPR_perturb_seq_example.txt.gz', source_url='https://api.data.igvf.org/tabular-files/IGVFFI3069QCRA/', label='genomic_element_gene', writer=writer, validate=True)
        adapter.process_file()
        first_item = json.loads(writer.contents[0])
        assert first_item['_key'] == 'CRISPR_chr1_212699339_212700840_GRCh38_ENSG00000123685_IGVFFI3069QCRA'
        assert first_item['_from'] == 'genomic_elements/CRISPR_chr1_212699339_212700840_GRCh38_IGVFFI3069QCRA'
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
        assert first_item['source_url'] == 'https://api.data.igvf.org/tabular-files/IGVFFI3069QCRA/'
        assert first_item['files_filesets'] == 'files_filesets/IGVFFI3069QCRA'


def test_igvf_e2g_crispr_adapter_perturb_seq_enhancer_only_genomic_elements(mock_file_fileset_perturb_seq, tmp_path):
    writer = SpyWriter()
    test_file = tmp_path / 'igvf_E2G_CRISPR_enhancer_only_perturb_seq.txt.gz'
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
            source_url='https://api.data.igvf.org/tabular-files/IGVFFI6296RCJK/',
            label='genomic_element',
            writer=writer,
            validate=True
        )
        adapter.process_file()

    parsed = [json.loads(item) for item in writer.contents if item.strip()]
    assert len(parsed) == 1
    first_item = parsed[0]
    assert first_item['_key'] == 'CRISPR_chr22_36387779_36388133_GRCh38_IGVFFI6296RCJK'
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
            source_url='https://api.data.igvf.org/tabular-files/IGVFFI6296RCJK/',
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
            source_url='https://api.data.igvf.org/tabular-files/IGVFFI6296RCJK/',
            label='genomic_element_gene',
            writer=writer,
            validate=True
        )
        adapter.process_file()

    parsed = [json.loads(item) for item in writer.contents if item.strip()]
    assert len(parsed) == 1
    first_item = parsed[0]
    assert first_item['_to'] == 'genes/ENSG00000174038'


def test_igvf_e2g_crispr_adapter_promoter_file_uses_intended_target_gene_id(
        mock_file_fileset_perturb_seq, tmp_path):
    writer = SpyWriter()
    test_file = tmp_path / 'igvf_E2G_CRISPR_promoter_intended_target_gene_id.txt.gz'
    header = (
        'intended_target_name\tIntended_target_gene_id\tguide_id(s)\t'
        'targeting_chr\ttargeting_start\ttargeting_end\tgene_id\tgene_symbol\t'
        'sceptre_log2_fc\tsceptre_p_value\tsceptre_adj_p_value\tsignificant\ttype\n'
    )
    row = (
        'MAFB\tENSG00000204103\tMAFB_1,MAFB_2\tchr20\t40688724\t40689213\t'
        'ENSG00000000003\tTSPAN6\t-0.170553946585609\t0.152\t'
        '0.856726931297333\tFALSE\tIndirect_targeting\n'
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
            source_url='https://api.data.igvf.org/tabular-files/IGVFFI6376HTIF/',
            label='genomic_element',
            writer=writer,
            validate=True
        )
        adapter.process_file()

    parsed = [json.loads(item) for item in writer.contents if item.strip()]
    assert len(parsed) == 1
    first_item = parsed[0]
    assert first_item['source_annotation'] == 'promoter'
    assert first_item['promoter_of'] == 'genes/ENSG00000204103'


def test_igvf_e2g_crispr_adapter_tap_seq_direct_targeting_genomic_element(mock_file_fileset_perturb_seq, tmp_path):
    writer = SpyWriter()
    test_file = tmp_path / 'igvf_E2G_CRISPR_tap_seq_direct_targeting.txt.gz'
    header = (
        'intended_target_name\tguide_id(s)\ttargeting_chr\t'
        'targeting_start\ttargeting_end\ttype\tgene_id\t'
        'gene_symbol\tsceptre_log2_fc\tsceptre_p_value\tsceptre_adj_p_value\t'
        'significant\tsample_term_name\tsample_term_id\tsample_summary_short\t'
        'power_at_effect_size_15\tnotes\n'
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
            source_url='https://api.data.igvf.org/tabular-files/IGVFFI6600VCYY/',
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
        'intended_target_name\tguide_id(s)\ttargeting_chr\t'
        'targeting_start\ttargeting_end\ttype\tgene_id\t'
        'gene_symbol\tsceptre_log2_fc\tsceptre_p_value\tsceptre_adj_p_value\t'
        'significant\tsample_term_name\tsample_term_id\tsample_summary_short\t'
        'power_at_effect_size_15\tnotes\n'
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
            source_url='https://api.data.igvf.org/tabular-files/IGVFFI6600VCYY/',
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
            filepath='./samples/igvf_E2G_CRISPR_facs_screen_example.txt.gz', source_url='https://api.data.igvf.org/tabular-files/IGVFFI9100GKNS/', label='genomic_element', writer=writer, validate=True)
        adapter.process_file()
        first_item = json.loads(writer.contents[0])
        assert len(writer.contents) > 0
        assert first_item['_key'] == 'CRISPR_chr1_998962_999432_GRCh38_IGVFFI9100GKNS'
        assert first_item['name'] == 'CRISPR_chr1_998962_999432_GRCh38_IGVFFI9100GKNS'
        assert first_item['chr'] == 'chr1'
        assert first_item['start'] == 998962
        assert first_item['end'] == 999432
        assert first_item['type'] == 'tested elements'
        assert first_item['method'] == 'CRISPR screen'
        assert first_item['promoter_of'] == 'genes/ENSG00000188290'
        assert first_item['source_annotation'] == 'promoter'
        assert first_item['source'] == 'IGVF'
        assert first_item['source_url'] == 'https://api.data.igvf.org/tabular-files/IGVFFI9100GKNS/'
        assert first_item['files_filesets'] == 'files_filesets/IGVFFI9100GKNS'


def test_igvf_e2g_crispr_adapter_facs_screen_genomic_elements_genes(mock_file_fileset_facs_screen, mocker):
    writer = SpyWriter()
    with patch('adapters.igvf_E2G_CRISPR_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True

        adapter = IGVFE2GCRISPR(
            filepath='./samples/igvf_E2G_CRISPR_facs_screen_example.txt.gz', source_url='https://api.data.igvf.org/tabular-files/IGVFFI9100GKNS/', label='genomic_element_gene', writer=writer, validate=True)
        adapter.process_file()
        first_item = json.loads(writer.contents[0])
        assert first_item['_key'] == 'CRISPR_chr1_998962_999432_GRCh38_ENSG00000126353_IGVFFI9100GKNS'
        assert first_item['_from'] == 'genomic_elements/CRISPR_chr1_998962_999432_GRCh38_IGVFFI9100GKNS'
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
        assert first_item['source_url'] == 'https://api.data.igvf.org/tabular-files/IGVFFI9100GKNS/'
        assert first_item['files_filesets'] == 'files_filesets/IGVFFI9100GKNS'


def test_igvf_e2g_scaled_screen_keeps_best_passing_guide_per_element_gene(
        mock_file_fileset_perturb_seq, tmp_path):
    writer = SpyWriter()
    test_file = tmp_path / 'igvf_E2G_CRISPR_scaled_screen.txt.gz'
    header = (
        'guide_id\tspacer_g_start\tprotospacer\ttargeting\ttype\tguide_chr\t'
        'guide_start\tguide_end\tstrand\tpam\tgenomic_element\t'
        'intended_target_chr\tintended_target_start\tintended_target_end\t'
        'response_id\thgnc_symbol\tn_nonzero_trt\tn_nonzero_cntrl\tpass_qc\t'
        'p_value\tlog_2_fold_change\tfull_piggyflex_oligo\tputative_target_genes\t'
        'putative_target_genes_hgnc\n'
    )
    rows = (
        'guide-1\tG\tAAA\tTRUE\ttargeting\tchr10\t1\t20\t+\tNGG\tenhancer\t'
        'chr10\t102117347\t102118205\tENSG00000171206\tTRIM8\t41\t91619\t'
        'TRUE\t0.05\t-0.2\toligo\t["ENSG00000171206"]\t["TRIM8"]\n'
        'guide-2\tG\tCCC\tTRUE\ttargeting\tchr10\t21\t40\t+\tNGG\tenhancer\t'
        'chr10\t102117347\t102118205\tENSG00000171206\tTRIM8\t41\t91619\t'
        'TRUE\t0.01\t-0.7\toligo\t["ENSG00000171206"]\t["TRIM8"]\n'
        'guide-3\tG\tGGG\tTRUE\ttargeting\tchr10\t41\t60\t+\tNGG\tenhancer\t'
        'chr10\t102117347\t102118205\tENSG00000171206\tTRIM8\t41\t91619\t'
        'FALSE\t0.001\t-1.1\toligo\t["ENSG00000171206"]\t["TRIM8"]\n'
        'guide-4\tG\tTTT\tTRUE\ttargeting\tchr10\t61\t80\t+\tNGG\tpromoter\t'
        'NaN\tNaN\tNaN\tENSG00000171206\tTRIM8\t41\t91619\t'
        'TRUE\t0.0005\t-1.3\toligo\t["ENSG00000171206"]\t["TRIM8"]\n'
        'guide-5\tG\tTTA\tFALSE\tnon-targeting\tchr10\t81\t100\t+\tNGG\t'
        'non-targeting\tchr10\t102117347\t102118205\tENSG00000171206\tTRIM8\t'
        '41\t91619\tTRUE\t0.0001\t-1.5\toligo\t[]\t[]\n'
    )
    with gzip.open(test_file, 'wt') as out:
        out.write(header)
        out.write(rows)

    with patch('adapters.igvf_E2G_CRISPR_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.side_effect = lambda x: x.startswith(
            'ENSG')

        adapter = IGVFE2GCRISPR(
            filepath=str(test_file),
            source_url='https://api.data.igvf.org/tabular-files/IGVFFI4544JMWL/',
            label='genomic_element_gene',
            writer=writer,
            validate=True,
        )
        adapter.process_file()

    parsed = [json.loads(item) for item in writer.contents if item.strip()]
    assert len(parsed) == 1
    first_item = parsed[0]
    assert first_item['_to'] == 'genes/ENSG00000171206'
    assert first_item['p_value'] == 0.01
    assert 'p_value_adj' not in first_item
    assert first_item['log2FC'] == -0.7


def test_igvf_e2g_scaled_screen_uses_genomic_element_for_source_annotation(
        mock_file_fileset_perturb_seq, tmp_path):
    writer = SpyWriter()
    test_file = tmp_path / 'igvf_E2G_CRISPR_scaled_screen_elements.txt.gz'
    header = (
        'guide_id\tspacer_g_start\tprotospacer\ttargeting\ttype\tguide_chr\t'
        'guide_start\tguide_end\tstrand\tpam\tgenomic_element\t'
        'intended_target_chr\tintended_target_start\tintended_target_end\t'
        'response_id\thgnc_symbol\tn_nonzero_trt\tn_nonzero_cntrl\tpass_qc\t'
        'p_value\tlog_2_fold_change\tfull_piggyflex_oligo\tputative_target_genes\t'
        'putative_target_genes_hgnc\n'
    )
    rows = (
        'enh-guide\tG\tAAA\tTRUE\ttargeting\tchr10\t1\t20\t+\tNGG\tenhancer\t'
        'chr10\t102117347\t102118205\tENSG00000171206\tTRIM8\t41\t91619\t'
        'TRUE\t0.01\t-0.7\toligo\t["ENSG00000171206"]\t["TRIM8"]\n'
        'prom-guide\tG\tCCC\tTRUE\ttargeting\tchr9\t21\t40\t+\tNGG\tpromoter\t'
        'chr9\t130834753\t130835253\tENSG00000097007\tABL1\t41\t91619\t'
        'TRUE\t0.02\t-0.4\toligo\t"ENSG00000097007"\t["ABL1"]\n'
    )
    with gzip.open(test_file, 'wt') as out:
        out.write(header)
        out.write(rows)

    with patch('adapters.igvf_E2G_CRISPR_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.side_effect = lambda x: x.startswith(
            'ENSG')

        adapter = IGVFE2GCRISPR(
            filepath=str(test_file),
            source_url='https://api.data.igvf.org/tabular-files/IGVFFI4544JMWL/',
            label='genomic_element',
            writer=writer,
            validate=True,
        )
        adapter.process_file()

    parsed = [json.loads(item) for item in writer.contents if item.strip()]
    enhancer = next(item for item in parsed if item['chr'] == 'chr10')
    promoter = next(item for item in parsed if item['chr'] == 'chr9')
    assert enhancer['source_annotation'] == 'enhancer'
    assert 'promoter_of' not in enhancer
    assert promoter['source_annotation'] == 'promoter'
    assert promoter['promoter_of'] == 'genes/ENSG00000097007'


def test_igvf_e2g_wtc11_uses_genomic_element_for_source_annotation(
        mock_file_fileset_perturb_seq, tmp_path):
    writer = SpyWriter()
    test_file = tmp_path / 'igvf_E2G_CRISPR_wtc11.csv.gz'
    header = (
        'idx,gene_names,gene_name_ensembl,chromosome,pos,strand,color_idx,chr_idx,'
        'genomic_element,region,intended_target_name,intended_target_name_ensmbl,'
        'num_cell,bin,log(pval)-hypergeom,fc,Significance_score,'
        'fc_by_rand_dist_cpm,pval-empirical,cpm_perturb,cpm_bg,log2fc\n'
    )
    rows = (
        '34767,IGFBP6,ENSG00000167779,chr12,1996865109,+,1,11,'
        'promoter,chr10:133238114-133238378,VENTX,ENSG00000151650,741,750,'
        '-11.04346999,1.39047496,-10.84371703,1.386921525,0,85.3643997,'
        '61.54676304,0.4755777642\n'
        '28347,VIM,ENSG00000026025,chr10,1692111888,+,1,9,'
        'enhancer,chr1:248558995-248559995,,,627,750,-13.6796195,'
        '0.7971788932,-15.06310882,0.797804645,0,986.8602186,'
        '1236.972292,-0.3270245822\n'
    )
    with gzip.open(test_file, 'wt') as out:
        out.write(header)
        out.write(rows)

    with patch('adapters.igvf_E2G_CRISPR_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.side_effect = lambda x: x.startswith(
            'ENSG')

        adapter = IGVFE2GCRISPR(
            filepath=str(test_file),
            source_url='https://api.data.igvf.org/tabular-files/IGVFFI0830FXFI/',
            label='genomic_element',
            writer=writer,
            validate=True,
        )
        adapter.process_file()

    parsed = [json.loads(item) for item in writer.contents if item.strip()]
    promoter = next(item for item in parsed if item['chr'] == 'chr10')
    enhancer = next(item for item in parsed if item['chr'] == 'chr1')
    assert promoter['source_annotation'] == 'promoter'
    assert promoter['promoter_of'] == 'genes/ENSG00000151650'
    assert enhancer['source_annotation'] == 'enhancer'
    assert 'promoter_of' not in enhancer


def test_igvf_e2g_crispr_adapter_crudo_tap_seq_skips_negative_control_and_maps_tss(
        mock_file_fileset_perturb_seq, tmp_path):
    """IGVFFI5903QAWP (CRUDO): aggregated metrics only; skip negative_control; TSS -> hardcoded promoter."""
    writer = SpyWriter()
    test_file = tmp_path / 'igvf_E2G_CRISPR_crudo_example.tsv.gz'
    header = (
        'name_hg38\ttype\tn\tTargetGene\tTargetGeneID\tEnhancerEff\t'
        'EnhancerEff.r1\tEnhancerEff.pval\tEnhancerEff.pval.adj\tSignificant\n'
    )
    rows = (
        # negative_control — skipped entirely
        'chr1:1-2\tnegative_control\t10\tnegative_control\tENSG00000000000\t'
        '0\t0.99\t0.5\t0.5\tFALSE\n'
        # putative enhancer
        'chr22:36387779-36388133\tputative_enhancer\t10\tMYH9\tENSG00000100345\t'
        '0.25\t0.1\t0.01\t0.02\tFALSE\n'
        # TSS — promoter from CRUDO_TSS_PROMOTER_GENE
        'chr11:694042-694160\tCCND1_TSS\t10\tCCND1\tENSG00000110092\t'
        '-0.1\t0.2\t0.03\t0.04\tTRUE\n'
    )
    with gzip.open(test_file, 'wt') as out:
        out.write(header)
        out.write(rows)

    with patch('adapters.igvf_E2G_CRISPR_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True

        adapter = IGVFE2GCRISPR(
            filepath=str(test_file),
            source_url='https://api.data.igvf.org/tabular-files/IGVFFI5903QAWP/',
            label='genomic_element_gene',
            writer=writer,
            validate=True,
        )
        adapter.process_file()

    parsed = [json.loads(line) for line in writer.contents if line.strip()]
    assert len(parsed) == 2
    enh = next(e for e in parsed if e['_to'] == 'genes/ENSG00000100345')
    assert enh['effect_size'] == 0.25
    assert enh['p_value'] == 0.01
    assert enh['p_value_adj'] == 0.02
    assert enh['significant'] is False
    tss = next(e for e in parsed if e['effect_size'] == -0.1)
    assert tss['_to'] == 'genes/ENSG00000110092'
    assert tss['significant'] is True


def test_igvf_e2g_crudo_real_sample_skips_negative_control_and_emits_expected_edge_count(
        mock_file_fileset_perturb_seq):
    """IGVFFI5903QAWP CRUDO TSV: 23 negative_control rows omitted; one edge per remaining row."""
    writer = SpyWriter()
    with patch('adapters.igvf_E2G_CRISPR_adapter.GeneValidator') as MockGeneValidator:
        MockGeneValidator.return_value.validate.return_value = True
        adapter = IGVFE2GCRISPR(
            filepath='./samples/IGVFFI5903QAWP_crudo_tap_seq.tsv.gz',
            source_url='https://api.data.igvf.org/tabular-files/IGVFFI5903QAWP/',
            label='genomic_element_gene',
            writer=writer,
            validate=True,
        )
        adapter.process_file()

    parsed = [json.loads(line) for line in writer.contents if line.strip()]
    assert len(parsed) == 131


def test_igvf_e2g_crudo_real_sample_ccnd1_tss_element_is_promoter_with_hardcoded_ensembl(
        mock_file_fileset_perturb_seq):
    """CCND1_TSS rows use name_hg38 coordinates but CRUDO_TSS_PROMOTER_GENE for promoter_of."""
    writer = SpyWriter()
    with patch('adapters.igvf_E2G_CRISPR_adapter.GeneValidator') as MockGeneValidator:
        MockGeneValidator.return_value.validate.return_value = True
        adapter = IGVFE2GCRISPR(
            filepath='./samples/IGVFFI5903QAWP_crudo_tap_seq.tsv.gz',
            source_url='https://api.data.igvf.org/tabular-files/IGVFFI5903QAWP/',
            label='genomic_element',
            writer=writer,
            validate=True,
        )
        adapter.process_file()

    parsed = [json.loads(line) for line in writer.contents if line.strip()]
    tss_node = next(
        n for n in parsed
        if n['chr'] == 'chr11' and n['start'] == 69640512 and n['end'] == 69641680
    )
    assert tss_node['source_annotation'] == 'promoter'
    assert tss_node['promoter_of'] == 'genes/ENSG00000110092'


def test_igvf_e2g_crudo_real_sample_putative_enhancer_edge_uses_no_aux_columns(
        mock_file_fileset_perturb_seq):
    """First significant putative_enhancer for CCND1: pval.EnhancerEffect.noAux / EnhancerEffect.noAux."""
    writer = SpyWriter()
    with patch('adapters.igvf_E2G_CRISPR_adapter.GeneValidator') as MockGeneValidator:
        MockGeneValidator.return_value.validate.return_value = True
        adapter = IGVFE2GCRISPR(
            filepath='./samples/IGVFFI5903QAWP_crudo_tap_seq.tsv.gz',
            source_url='https://api.data.igvf.org/tabular-files/IGVFFI5903QAWP/',
            label='genomic_element_gene',
            writer=writer,
            validate=True,
        )
        adapter.process_file()

    parsed = [json.loads(line) for line in writer.contents if line.strip()]
    matches = [
        e for e in parsed
        if e['_to'] == 'genes/ENSG00000110092'
        and e.get('significant') is True
        and e['effect_size'] == pytest.approx(0.165227554)
        and e['p_value'] == pytest.approx(0.000134325)
    ]
    assert len(matches) == 1
    edge = matches[0]
    assert edge['p_value_adj'] == pytest.approx(0.001870874)
    assert edge['_from'].startswith(
        'genomic_elements/CRISPR_chr11_69637976_69639354_GRCh38_'
    )


def test_igvf_e2g_crispr_adapter_invalid_label(mock_file_fileset_perturb_seq):
    writer = SpyWriter()
    with pytest.raises(ValueError):
        adapter = IGVFE2GCRISPR(
            filepath='./samples/igvf_E2G_CRISPR_perturb_seq_example.txt.gz', source_url='https://api.data.igvf.org/tabular-files/IGVFFI3069QCRA/', label='invalid_label', writer=writer, validate=True)


def test_igvf_e2g_crispr_adapter_validate_doc_invalid(mock_file_fileset_perturb_seq):
    writer = SpyWriter()
    adapter = IGVFE2GCRISPR(
        filepath='./samples/igvf_E2G_CRISPR_perturb_seq_example.txt.gz', source_url='https://api.data.igvf.org/tabular-files/IGVFFI3069QCRA/', label='genomic_element', writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError):
        adapter.validate_doc(invalid_doc)
