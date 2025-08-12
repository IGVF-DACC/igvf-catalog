import json
import gzip
from unittest.mock import patch, mock_open
from adapters.writer import SpyWriter
from adapters.maveDB_variant_phenotype_adapter import MAVEDB

SAMPLE_MAVE_TSV = (
    'variant_measurement_urn\tscore_set_urn\texperiment_urn\tclingen_allele_id\tenst_id\tensp_id\tscore\tassay_type\t'
    'primary_publication_id\tprimary_publication_db\tscore_range_1\tscore_range_1_name\tscore_range_1_classification\t'
    'score_range_2\tscore_range_2_name\tscore_range_2_classification\tscore_range_3\tscore_range_3_name\tscore_range_3_classification\t'
    'score_range_4\tscore_range_4_name\tscore_range_4_classification\tscore_range_5\tscore_range_5_name\tscore_range_5_classification\t'
    'experiment_title\texperiment_short_description\texperiment_abstract\texperiment_methods\t'
    'score_set_title\tscore_set_short_description\tscore_set_gene_symbols\tscore_set_abstract\tscore_set_methods\n'
    'urn:mavedb:00000001-c-1#1\turn:mavedb:00000001-c-1\turn:mavedb:00000001-c\tCA2579769722\tENST00000356978.9\t\t1.0297979489487\t'
    'functional complementation\t29269382\tPubMed\t0.8\tLow\tNon-functional\t1.0\tMedium\tPartially-functional\t'
    '1.2\tHigh\tFunctional\t\t\t\t\t\t\t'
    'Calmodulin yeast complementation\tA Deep Mutational Scan of human Calmodulin using functional complementation in yeast.\t'
    'Although we now routinely sequence human genomes...\tA Deep Mutational Scan of Calmodulin (*CALM1*) using functional complementation...\t'
    'Human Calmodulin DMS-TileSeq\tA Deep Mutational Scan of human Calmodulin using functional complementation in yeast via DMS-TileSeq.\t'
    'CALM1,CALM2,CALM3\tAlthough we now routinely sequence human genomes...\tDMS-TileSeq methodology with yeast complementation assay\n'
)

MOCKED_VARIANTS = {
    'CA2579769722': ['var_1'],
    'CA2579769723': ['var_2'],
    'CA2579769724': ['var_3', 'var_4']
}

MOCKED_FILES_FILESETS_PROP = {
    'method': 'maveDB'
}


@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_igvf',
       return_value=[MOCKED_FILES_FILESETS_PROP])
@patch('adapters.maveDB_variant_phenotype_adapter.bulk_check_caid_in_arangodb',
       return_value=MOCKED_VARIANTS)
@patch('gzip.open', new_callable=mock_open, read_data=SAMPLE_MAVE_TSV)
def test_process_file_variants_phenotypes(mock_fileset_props, mock_bulk_query, mock_gzip_open):
    writer = SpyWriter()
    adapter = MAVEDB(
        'IGVFFI0407TIWL.tsv.gz',
        label='variants_phenotypes',
        writer=writer
    )
    adapter.process_file()

    assert len(writer.contents) > 0
    first_item = json.loads(writer.contents[0])
    assert first_item['_key'] == 'var_1_urn:mavedb:00000001-c-1IGVFFI0407TIWL'
    assert first_item['_from'] == 'variants/var_1'
    assert first_item['_to'] == 'ontology_terms/GO_0003674'
    assert first_item['name'] == 'mutational effect'
    assert first_item['inverse_name'] == 'altered due to mutation'
    assert first_item['score'] == 1.0297979489487
    assert first_item['source'] == 'IGVF'
    assert first_item['source_url'] == 'https://data.igvf.org/tabular-files/IGVFFI0407TIWL'
    assert first_item['method'] == 'maveDB'
    assert first_item['files_filesets'] == 'files_filesets/IGVFFI0407TIWL'
    assert first_item['assay_type'] == 'functional complementation'
    assert first_item['transcript_id'] == 'ENST00000356978.9'
