import json
from unittest.mock import patch
from adapters.gersbach_E2G_CRISPR_adapter import GersbachE2GCRISPR
from adapters.writer import SpyWriter


def test_gersbach_e2g_crispr_adapter_genomic_elements():
    writer = SpyWriter()
    with patch('adapters.gersbach_E2G_CRISPR_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True

        adapter = GersbachE2GCRISPR(
            filepath='./samples/gersbach_E2G_crispr_example.tsv.gz', source_url='https://api.data.igvf.org/tabular-files/IGVFFI1152VRSY/', reference_filepath='./samples/gersbach_E2G_crispr_reference_example.tsv.gz', reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI7639UNAN/', label='genomic_element', writer=writer)
        adapter.process_file()
        first_item = json.loads(writer.contents[0])
        assert len(writer.contents) > 0
        assert first_item['_key'] == 'CRISPR_chr1_246931448_246932448_GRCh38_IGVFFI1152VRSY'
        assert first_item['name'] == 'CRISPR_chr1_246931448_246932448_GRCh38_IGVFFI1152VRSY'
        assert first_item['chr'] == 'chr1'
        assert first_item['start'] == 246931448
        assert first_item['end'] == 246932448
        assert first_item['type'] == 'tested elements'
        assert first_item['method'] == 'Homo sapiens GRCh38 custom guide RNAs'
        assert first_item['source_annotation'] == 'promoter'
        assert first_item['source'] == 'IGVF'
        assert first_item['source_url'] == 'https://api.data.igvf.org/tabular-files/IGVFFI1152VRSY/'
        assert first_item['files_filesets'] == 'files_filesets/IGVFFI1152VRSY'


def test_gersbach_e2g_crispr_adapter_genomic_elements_genes():
    writer = SpyWriter()
    with patch('adapters.gersbach_E2G_CRISPR_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True

        adapter = GersbachE2GCRISPR(
            filepath='./samples/gersbach_E2G_crispr_example.tsv.gz', source_url='https://api.data.igvf.org/tabular-files/IGVFFI1152VRSY/', reference_filepath='./samples/gersbach_E2G_crispr_reference_example.tsv.gz', reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI7639UNAN/', label='genomic_element_gene', writer=writer)
        adapter.process_file()
        first_item = json.loads(writer.contents[0])
        assert first_item['_key'] == 'CRISPR_chr1_246931448_246932448_GRCh38_ENSG00000153207_IGVFFI1152VRSY'
        assert first_item['_from'] == 'genomic_elements/CRISPR_chr1_246931448_246932448_GRCh38_IGVFFI1152VRSY'
        assert first_item['_to'] == 'genes/ENSG00000153207'
        assert first_item['baseMean'] == 403.0544398
        assert first_item['log2FC'] == -0.430896793
        assert first_item['lfcSE'] == 0.483371961
        assert first_item['stat'] == -0.891439364
        assert first_item['pvalue'] == 0.372693508
        assert first_item['padj'] == 0.842070692
        assert first_item['method'] == 'CRISPR FACS screen'
        assert first_item['simple_sample_summaries'] == [
            'CD8-positive, alpha-beta memory T cell']
        assert first_item['biological_context'] == [
            'ontology_terms/CL_0000909']
        assert first_item['treatments_term_ids'] == None
        assert first_item['label'] == 'element effect on gene expression of ENSG00000153207'
        assert first_item['name'] == 'modulates expression of'
        assert first_item['inverse_name'] == 'expression modulated by'
        assert first_item['source'] == 'IGVF'
        assert first_item['source_url'] == 'https://api.data.igvf.org/tabular-files/IGVFFI1152VRSY/'
        assert first_item['files_filesets'] == 'files_filesets/IGVFFI1152VRSY'
