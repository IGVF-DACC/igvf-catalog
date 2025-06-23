import json
from adapters.gvatdb_asb_adapter import ASB_GVATDB
from adapters.writer import SpyWriter


def test_asb_gvatdb_adapter_process(mocker):
    mocker.patch('adapters.gvatdb_asb_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    adapter = ASB_GVATDB(filepath='./samples/GVATdb_sample.csv',
                         writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert 'log10pvalue' in first_item
    assert 'p_value' in first_item
    assert 'hg19_coordinate' in first_item
    assert first_item['source'] == ASB_GVATDB.SOURCE
    assert first_item['source_url'] == ASB_GVATDB.SOURCE_URL
    assert first_item['label'] == 'allele-specific binding'
    assert first_item['name'] == 'modulates binding of'
    assert first_item['inverse_name'] == 'binding modulated by'
    assert first_item['biological_process'] == 'ontology_terms/GO_0051101'


def test_asb_gvatdb_adapter_initialization():
    writer = SpyWriter()
    adapter = ASB_GVATDB(filepath='./samples/GVATdb_sample.csv',
                         writer=writer)
    assert adapter.filepath == './samples/GVATdb_sample.csv'
    assert adapter.writer == writer


def test_asb_gvatdb_adapter_load_tf_uniprot_id_mapping():
    adapter = ASB_GVATDB(filepath='./samples/GVATdb_sample.csv')
    adapter.load_tf_uniprot_id_mapping()
    assert hasattr(adapter, 'tf_uniprot_id_mapping')
    assert isinstance(adapter.tf_uniprot_id_mapping, dict)
    assert len(adapter.tf_uniprot_id_mapping) > 0
