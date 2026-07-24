import json
import pytest
from unittest.mock import patch
from adapters.encode_E2G_CRISPR_adapter import ENCODE2GCRISPR
from adapters.writer import SpyWriter


# mock get_file_fileset_by_accession_in_arangodb so files_fileset data change will not affect the test
@pytest.fixture
def mock_file_fileset():
    """Fixture to mock get_file_fileset_by_accession_in_arangodb function."""
    with patch('adapters.encode_E2G_CRISPR_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'method': 'CRISPR screen',
            'class': 'observed data',
            'crispr_modality': 'interference',
            'simple_sample_summaries': ['K562'],
            'samples': ['ontology_terms/EFO_0002067']
        }
        yield mock_get_file_fileset


# mock get_gene_map_from_arangodb so gene collection data change will not affect the test
@pytest.fixture
def mock_gene_map():
    """Fixture to mock get_gene_map_from_arangodb function."""
    with patch('adapters.encode_E2G_CRISPR_adapter.get_gene_map_from_arangodb') as mock_get_gene_map:
        mock_get_gene_map.return_value = {
            'CEP104': ['ENSG00000116198'],
            'LRRC47': ['ENSG00000130764']
        }
        yield mock_get_gene_map


@pytest.mark.external_dependency
def test_encode2gcrispr_adapter_regulatory_region(mock_file_fileset):
    writer = SpyWriter()
    adapter = ENCODE2GCRISPR(
        filepath='./samples/ENCODE_E2G_CRISPR_example.tsv', label='genomic_element', writer=writer, validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert 'chr' in first_item
    assert 'start' in first_item
    assert 'end' in first_item
    assert 'type' in first_item
    assert first_item['method'] == 'CRISPR screen'
    assert first_item['source'] == ENCODE2GCRISPR.SOURCE
    assert first_item['source_url'] == ENCODE2GCRISPR.SOURCE_URL


@pytest.mark.external_dependency
def test_encode2gcrispr_adapter_regulatory_region_gene(mock_file_fileset, mock_gene_map):
    writer = SpyWriter()
    adapter = ENCODE2GCRISPR(filepath='./samples/ENCODE_E2G_CRISPR_example.tsv',
                             label='genomic_element_gene', writer=writer, validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert 'effect_size' in first_item
    assert 'log2FC' in first_item
    assert 'p_value' in first_item
    assert 'p_value_adj' in first_item
    assert 'neg_log10_pvalue' in first_item
    assert 'neg_log10_pvalue_adj' in first_item
    assert 'significant' in first_item
    assert first_item['source'] == ENCODE2GCRISPR.SOURCE
    assert first_item['source_url'] == ENCODE2GCRISPR.SOURCE_URL
    assert first_item['biological_context'] == 'K562'
    assert first_item['biosample_term'] == 'ontology_terms/EFO_0002067'
    assert first_item['label'] == 'regulatory element effect on gene expression'
    assert first_item['method'] == 'CRISPR screen'
    assert first_item['crispr_modality'] == 'interference'
    assert first_item['class'] == 'observed data'


def test_encode2gcrispr_adapter_multiple_gene_ids(mock_file_fileset, mocker):
    """A gene symbol mapping to multiple Ensembl ids should produce an edge for each id, not just the first."""
    mocker.patch(
        'adapters.encode_E2G_CRISPR_adapter.get_gene_map_from_arangodb',
        return_value={
            'FAKEGENE': ['ENSG00000000001', 'ENSG00000000002'],
        }
    )

    import tempfile
    import os

    header = ('chrom\tchromStart\tchromEnd\tname\tEffectSize\tstrandPerturbationTarget\tPerturbationTargetID\t'
              'chrTSS\tstartTSS\tendTSS\tstrandGene\tEffectSize95ConfidenceIntervalLow\tEffectSize95ConfidenceIntervalHigh\t'
              'measuredGeneSymbol\tmeasuredEnsemblID\tguideSpacerSeq\tguideSeq\tSignificant\tpValue\tpValueAdjusted\t'
              'PowerAtEffectSize25\tPowerAtEffectSize10\tPowerAtEffectSize15\tPowerAtEffectSize20\tPowerAtEffectSize50\t'
              'ValidConnection\tNotes\tReference')
    row = ('chr1\t3774714\t3775214\tFAKEGENE|chr1:3691278-3691778:.\t-0.293431866\t.\tchr1:3691278-3691778:.\t'
           'chr1\t3857213\t3857214\t-\tNA\tNA\tFAKEGENE\tNA\tNA\tNA\tTRUE\tNA\t0.004023984\t0.825093632\tNA\tNA\tNA\tNA\t'
           'TRUE\tDataset: Nasser2021\tUlirsch et al., 2016')

    with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
        f.write(header + '\n')
        f.write(row + '\n')
        temp_file_path = f.name

    try:
        writer = SpyWriter()
        adapter = ENCODE2GCRISPR(
            filepath=temp_file_path, label='genomic_element_gene', writer=writer)
        adapter.process_file()

        gene_targets = {json.loads(item)['_to']
                        for item in writer.contents if item.startswith('{')}
        assert gene_targets == {
            'genes/ENSG00000000001', 'genes/ENSG00000000002'}
    finally:
        os.unlink(temp_file_path)


def test_encode2gcrispr_adapter_invalid_label(mock_file_fileset):
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_label. Allowed values: genomic_element, genomic_element_gene'):
        ENCODE2GCRISPR(filepath='./samples/ENCODE_E2G_CRISPR_example.tsv',
                       label='invalid_label', writer=writer)


def test_encode2gcrispr_adapter_initialization(mock_file_fileset):
    writer = SpyWriter()
    for label in ENCODE2GCRISPR.ALLOWED_LABELS:
        adapter = ENCODE2GCRISPR(
            filepath='./samples/ENCODE_E2G_CRISPR_example.tsv', label=label, writer=writer)
        assert adapter.filepath == './samples/ENCODE_E2G_CRISPR_example.tsv'
        assert adapter.label == label
        assert adapter.writer == writer
        assert adapter.files_filesets is not None


def test_encode2gcrispr_adapter_load_regulatory_region(mock_file_fileset):
    writer = SpyWriter()
    adapter = ENCODE2GCRISPR(
        filepath='./samples/ENCODE_E2G_CRISPR_example.tsv', label='genomic_element', writer=writer)
    adapter.load_genomic_element()
    assert hasattr(adapter, 'genomic_element_nodes')
    assert isinstance(adapter.genomic_element_nodes, dict)
    assert len(adapter.genomic_element_nodes) > 0


def test_encode2gcrispr_adapter_load_gene_id_mapping(mock_file_fileset, mock_gene_map):
    writer = SpyWriter()
    adapter = ENCODE2GCRISPR(filepath='./samples/ENCODE_E2G_CRISPR_example.tsv',
                             label='genomic_element_gene', writer=writer)
    adapter.load_gene_id_mapping()
    assert hasattr(adapter, 'gene_id_mapping')
    assert isinstance(adapter.gene_id_mapping, dict)
    assert len(adapter.gene_id_mapping) > 0


def test_encode2gcrispr_adapter_validate_doc_invalid(mock_file_fileset):
    writer = SpyWriter()
    adapter = ENCODE2GCRISPR(filepath='./samples/ENCODE_E2G_CRISPR_example.tsv',
                             label='genomic_element_gene', writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
