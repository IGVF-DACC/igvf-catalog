import json
from unittest.mock import patch, mock_open
from adapters.writer import SpyWriter
from adapters.variant_painting_coding_variant_scores_adapter import VariantPaintingAdapter
import pytest


SAMPLE_TSV = (
    'gene_variant\tspdi\tmislocalization_hit\tlocalization_score\thgvs_protein\n'
    'LITAF_Pro135Thr\tNC_000016.10:11549719:G:T\tTrue\t0.9606993000231892\tENSP00000483114.1:p.Pro135Thr\n'
    'GCK_Gly175Arg\tNC_000007.14:44150024:C:G\tFalse\t0.8805942309449305\tENSP00000384247.3:p.Gly175Arg\n'
    'TP53_Arg175His\tNC_000017.11:7674220:C:T\tTrue\t0.9912345678901234\tENSP00000269305.4:p.Arg175His\n'
)

MOCKED_CODING_VARIANTS = {
    ('NC_000016.10:11549719:G:T', 'ENSP00000483114', 'p.Pro135Thr'): ['LITAF_ENST00000261509_p.Pro135Thr_c.403C-A'],
    ('NC_000007.14:44150024:C:G', 'ENSP00000384247', 'p.Gly175Arg'): ['GCK_ENST00000403799_p.Gly175Arg_c.523G-C'],
    ('NC_000017.11:7674220:C:T', 'ENSP00000269305', 'p.Arg175His'): ['TP53_ENST00000269305_p.Arg175His_c.524G-A'],
}

MOCKED_FILE_FILESET = {
    'method': 'Variant painting via fluorescence',
    'class': 'observed data',
    'label': 'protein variant effect',
    'simple_sample_summaries': ['U2OS'],
    'samples': ['ontology_terms/EFO_0002869']
}


@patch('adapters.variant_painting_coding_variant_scores_adapter.get_file_fileset_by_accession_in_arangodb', return_value=MOCKED_FILE_FILESET)
@patch('adapters.variant_painting_coding_variant_scores_adapter.bulk_query_coding_variants_from_spdi_in_arangodb', return_value=MOCKED_CODING_VARIANTS)
@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_TSV)
def test_process_file_coding_variants_phenotypes(mock_gzip_open, mock_bulk_query, mock_file_fileset):
    writer = SpyWriter()
    adapter = VariantPaintingAdapter(
        'IGVFFI9499PJFU.tsv.gz',
        label='coding_variants_phenotypes',
        writer=writer,
        validate=True
    )
    adapter.process_file()

    records = [json.loads(c) for c in writer.contents if c != '\n']
    assert len(records) == 3

    first = records[0]
    assert first['_key'] == 'LITAF_ENST00000261509_p.Pro135Thr_c.403C-A_GO_0008104_IGVFFI9499PJFU'
    assert first['_from'] == 'coding_variants/LITAF_ENST00000261509_p.Pro135Thr_c.403C-A'
    assert first['_to'] == 'ontology_terms/GO_0008104'
    assert first['name'] == 'mutational effect'
    assert first['inverse_name'] == 'altered due to mutation'
    assert first['source'] == 'IGVF'
    assert first['source_url'] == 'https://data.igvf.org/tabular-files/IGVFFI9499PJFU'
    assert first['label'] == 'protein variant effect'
    assert first['method'] == 'Variant painting via fluorescence'
    assert first['class'] == 'observed data'
    assert first['biological_context'] == 'U2OS'
    assert first['biosample_term'] == 'ontology_terms/EFO_0002869'
    assert first['files_filesets'] == 'files_filesets/IGVFFI9499PJFU'
    assert first['localization_score'] == 0.9606993000231892
    assert first['mislocalization_hit'] is True

    # check both True and False mislocalization_hit values appear
    assert set(r['mislocalization_hit'] for r in records) == {True, False}


@patch('adapters.variant_painting_coding_variant_scores_adapter.get_file_fileset_by_accession_in_arangodb', return_value=MOCKED_FILE_FILESET)
@patch('adapters.variant_painting_coding_variant_scores_adapter.bulk_query_coding_variants_from_spdi_in_arangodb', return_value=MOCKED_CODING_VARIANTS)
@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_TSV)
def test_missing_variant_is_skipped(mock_gzip_open, mock_bulk_query, mock_file_fileset):
    writer = SpyWriter()
    mock_bulk_query.return_value = {}
    adapter = VariantPaintingAdapter(
        'IGVFFI9499PJFU.tsv.gz',
        label='coding_variants_phenotypes',
        writer=writer,
        validate=True
    )
    adapter.process_file()
    records = [c for c in writer.contents if c != '\n']
    assert len(records) == 0


def test_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_label. Allowed values: coding_variants_phenotypes'):
        VariantPaintingAdapter(
            'IGVFFI9499PJFU.tsv.gz',
            label='invalid_label',
            writer=writer,
        )


@patch('adapters.variant_painting_coding_variant_scores_adapter.get_file_fileset_by_accession_in_arangodb', return_value=MOCKED_FILE_FILESET)
@patch('adapters.variant_painting_coding_variant_scores_adapter.bulk_query_coding_variants_from_spdi_in_arangodb', return_value=MOCKED_CODING_VARIANTS)
@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_TSV)
def test_validate_doc_invalid(mock_gzip_open, mock_bulk_query, mock_file_fileset):
    writer = SpyWriter()
    adapter = VariantPaintingAdapter(
        'IGVFFI9499PJFU.tsv.gz',
        label='coding_variants_phenotypes',
        writer=writer,
        validate=True
    )
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc({'invalid_field': 'bad'})
