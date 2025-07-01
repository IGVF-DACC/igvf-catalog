import json
from unittest.mock import patch
from adapters.gersbach_E2G_perturb_seq_adapter import GersbachE2GPerturbseq
from adapters.writer import SpyWriter


def test_gersbach_e2g_perturb_seq_adapter_genomic_elements():
    writer = SpyWriter()
    with patch('adapters.gersbach_E2G_perturb_seq_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True

        adapter = GersbachE2GPerturbseq(
            filepath='./samples/gersbach_E2G_perturb_seq_example.txt.gz', source_url='https://api.data.igvf.org/tabular-files/IGVFFI6830YLEK/', label='genomic_element', writer=writer)
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


def test_gersbach_e2g_perturb_seq_adapter_genomic_elements_genes():
    writer = SpyWriter()
    with patch('adapters.gersbach_E2G_perturb_seq_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True

        adapter = GersbachE2GPerturbseq(
            filepath='./samples/gersbach_E2G_perturb_seq_example.txt.gz', source_url='https://api.data.igvf.org/tabular-files/IGVFFI6830YLEK/', label='genomic_element_gene', writer=writer)
        adapter.process_file()
        first_item = json.loads(writer.contents[0])
        assert first_item['_key'] == 'CRISPR_chr1_212699339_212700840_GRCh38_ENSG00000123685_IGVFFI6830YLEK'
        assert first_item['_from'] == 'genomic_elements/CRISPR_chr1_212699339_212700840_GRCh38_IGVFFI6830YLEK'
        assert first_item['_to'] == 'genes/ENSG00000123685'
        assert first_item['p_val'] == 0.0
        assert first_item['avg_log2FC'] == 3.608562048
        assert first_item['pct_1'] == 0.918
        assert first_item['pct_2'] == 0.282
        assert first_item['p_val_adj'] == 0.0
        assert first_item['method'] == 'Perturb-seq'
        assert first_item['simple_sample_summaries'] == [
            'CD8-positive, alpha-beta memory T cell']
        assert first_item['biological_context'] == [
            'ontology_terms/CL_0000909']
        assert first_item['treatments_term_ids'] == None
        assert first_item['label'] == 'element effect on gene expression of ENSG00000123685'
        assert first_item['name'] == 'modulates expression of'
        assert first_item['inverse_name'] == 'expression modulated by'
        assert first_item['source'] == 'IGVF'
        assert first_item['source_url'] == 'https://api.data.igvf.org/tabular-files/IGVFFI6830YLEK/'
        assert first_item['files_filesets'] == 'files_filesets/IGVFFI6830YLEK'
