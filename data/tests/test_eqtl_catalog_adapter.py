import pytest
import csv
import gzip
import json
from unittest.mock import MagicMock, patch, mock_open
from adapters.eqtl_catalog_adapter import EQTLCatalog

EQTL_SAMPLE_DATA = """# molecular_trait_id	gene_id	cs_id	variant	rsid	cs_size	pip	pvalue	beta	se	z	cs_min_r2	region
ENSG00000230489	ENSG00000230489	ENSG00000230489_L1	chr1_108004887_G_T	rs1936009	53	0.0197781278649429	7.46541e-09	0.767387	0.116543	7.19210214446939	0.945192225726688	chr1:106964443-108964443
ENSG00000230489	ENSG00000230489	ENSG00000230489_L1	chr1_108006349_TAAG_T	rs149029272	53	0.0197781278649429	7.46541e-09	0.767387	0.116543	7.19210214446939	0.945192225726688	chr1:106964443-108964443
ENSG00000230489	ENSG00000230489	ENSG00000230489_L1	chr1_108006349_TAAG_T	rs752693742	53	0.0197781278649429	7.46541e-09	0.767387	0.116543	7.19210214446939	0.945192225726688	chr1:106964443-108964443
ENSG00000230489	ENSG00000230489	ENSG00000230489_L1	chr1_108006349_TAAG_T	rs564865200	53	0.0197781278649429	7.46541e-09	0.767387	0.116543	7.19210214446939	0.945192225726688	chr1:106964443-108964443
"""

STUDY_SAMPLE_DATA = """#study_id	dataset_id	study_label	sample_group	tissue_id	tissue_label	condition_label	sample_size	quant_method	pmid	study_type
QTS000001	QTD000001	Alasoo_2018	macrophage_naive	CL_0000235	macrophage	naive	84	ge	29379200	bulk
QTS000001	QTD000002	Alasoo_2018	macrophage_naive	CL_0000235	macrophage	naive	84	exon	29379200	bulk
QTS000001	QTD000003	Alasoo_2018	macrophage_naive	CL_0000235	macrophage	naive	84	tx	29379200	bulk
QTS000001	QTD000004	Alasoo_2018	macrophage_naive	CL_0000235	macrophage	naive	84	txrev	29379200	bulk
"""


@pytest.fixture
def mock_writer():
    return MagicMock()


@pytest.fixture
def eqtl_catalog_qtl(mock_writer):
    with patch('adapters.eqtl_catalog_adapter.GeneValidator') as MockGeneValidator:
        gene_validator = MockGeneValidator.return_value
        return EQTLCatalog(filepath='dummy_path/QTD000001.tsv.gz', label='qtl', writer=mock_writer)


@pytest.fixture
def eqtl_catalog_study(mock_writer):
    with patch('adapters.eqtl_catalog_adapter.GeneValidator') as MockGeneValidator:
        gene_validator = MockGeneValidator.return_value
        return EQTLCatalog(filepath='dummy_path/study.tsv', label='study', writer=mock_writer)


def test_init_invalid_label(mock_writer):
    with pytest.raises(ValueError):
        EQTLCatalog(filepath='dummy', label='invalid', writer=mock_writer)


@patch('builtins.open', new_callable=mock_open, read_data=(STUDY_SAMPLE_DATA))
@patch('gzip.open')
@patch('adapters.eqtl_catalog_adapter.build_variant_id', return_value='chr1_108004887_G_T')
@patch('adapters.eqtl_catalog_adapter.to_float', side_effect=lambda x: float(x) if 'e' in x or '.' in x else x)
def test_process_qtl_writes_json(mock_to_float, mock_build_variant_id, mock_gzip_open, mock_open_file, eqtl_catalog_qtl, mock_writer):
    # Simulate QTL file content
    qtl_content = (EQTL_SAMPLE_DATA)
    mock_gzip_open.return_value.__enter__.return_value = qtl_content.strip().split('\n')
    eqtl_catalog_qtl.gene_validator.validate.return_value = True

    eqtl_catalog_qtl.process_qtl()
    assert mock_writer.open.called
    assert mock_writer.write.call_count > 0
    assert mock_writer.close.called


@patch('builtins.open', new_callable=mock_open, read_data=(STUDY_SAMPLE_DATA))
@patch('gzip.open')
@patch('adapters.eqtl_catalog_adapter.build_variant_id', return_value='chr1_108004887_G_T')
@patch('adapters.eqtl_catalog_adapter.to_float', side_effect=lambda x: float(x) if 'e' in x or '.' in x else x)
def test_process_qtl_skips_invalid_gene(mock_to_float, mock_build_variant_id, mock_gzip_open, mock_open_file, eqtl_catalog_qtl, mock_writer):
    qtl_content = (EQTL_SAMPLE_DATA)
    mock_gzip_open.return_value.__enter__.return_value = qtl_content.strip().split('\n')
    eqtl_catalog_qtl.gene_validator.validate.return_value = False

    eqtl_catalog_qtl.process_qtl()
    # Should not write anything if gene is invalid
    assert mock_writer.write.call_count == 0


@patch('builtins.open', new_callable=mock_open, read_data=(
    'study_id\tdataset_id\tstudy_label\tsample_group\ttissue_id\ttissue_label\tcondition_label\tsample_size\tquant_method\tftp_path\tftp_cs_path\tftp_lbf_path\n'
))
@patch('gzip.open', new_callable=mock_open, read_data='')
def test_process_qtl_raises_if_no_metadata(mock_gzip_open, mock_open_file, eqtl_catalog_qtl):
    with pytest.raises(ValueError):
        eqtl_catalog_qtl.process_qtl()


@patch('builtins.open', new_callable=mock_open, read_data=(STUDY_SAMPLE_DATA))
def test_process_study_writes_json(mock_open_file, eqtl_catalog_study, mock_writer):
    study_content = (STUDY_SAMPLE_DATA)

    with patch('builtins.open', mock_open(read_data=study_content)) as study_open:
        eqtl_catalog_study.process_study()
        assert mock_writer.open.called
        assert mock_writer.write.call_count > 0
        assert mock_writer.close.called


def test_process_file_dispatches_to_correct_method(eqtl_catalog_qtl, eqtl_catalog_study):
    with patch.object(eqtl_catalog_qtl, 'process_qtl') as pq, \
            patch.object(eqtl_catalog_study, 'process_study') as ps:
        eqtl_catalog_qtl.process_file()
        pq.assert_called_once()
        eqtl_catalog_study.process_file()
        ps.assert_called_once()
