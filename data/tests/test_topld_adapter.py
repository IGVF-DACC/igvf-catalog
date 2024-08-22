import json
from adapters.topld_adapter import TopLD
from adapters.writer import SpyWriter


def test_topld_adapter_initialization():
    writer = SpyWriter()
    adapter = TopLD(filepath='./samples/topld_sample.csv',
                    annotation_filepath='./samples/topld_info_annotation.csv',
                    chr='chr22',
                    ancestry='SAS',
                    writer=writer)

    assert adapter.filepath == './samples/topld_sample.csv'
    assert adapter.annotation_filepath == './samples/topld_info_annotation.csv'
    assert adapter.chr == 'chr22'
    assert adapter.ancestry == 'SAS'
    assert adapter.dataset == TopLD.DATASET
    assert adapter.label == TopLD.DATASET
    assert adapter.dry_run == True
    assert adapter.writer == writer


def test_topld_adapter_process_file():
    writer = SpyWriter()
    adapter = TopLD(filepath='./samples/topld_sample.csv',
                    annotation_filepath='./samples/topld_info_annotation.csv',
                    chr='chr22',
                    ancestry='SAS',
                    writer=writer)

    adapter.process_file()

    assert len(writer.contents) > 0
    first_item = json.loads(writer.contents[0])

    assert '_from' in first_item
    assert '_to' in first_item
    assert 'chr' in first_item
    assert 'negated' in first_item
    assert 'variant_1_base_pair' in first_item
    assert 'variant_2_base_pair' in first_item
    assert 'variant_1_rsid' in first_item
    assert 'variant_2_rsid' in first_item
    assert 'r2:long' in first_item
    assert 'd_prime:long' in first_item
    assert 'ancestry' in first_item
    assert 'label' in first_item
    assert 'name' in first_item
    assert 'inverse_name' in first_item
    assert 'source' in first_item
    assert 'source_url' in first_item

    assert first_item['chr'] == 'chr22'
    assert first_item['ancestry'] == 'SAS'
    assert first_item['label'] == 'linkage disequilibrum'
    assert first_item['name'] == 'correlated with'
    assert first_item['inverse_name'] == 'correlated with'
    assert first_item['source'] == 'TopLD'
    assert first_item['source_url'] == 'http://topld.genetics.unc.edu/'


def test_topld_adapter_process_annotations():
    writer = SpyWriter()
    adapter = TopLD(filepath='./samples/topld_sample.csv',
                    annotation_filepath='./samples/topld_info_annotation.csv',
                    chr='chr22',
                    ancestry='SAS',
                    writer=writer)

    adapter.process_annotations()

    assert len(adapter.ids) > 0
    first_key = next(iter(adapter.ids))
    first_value = adapter.ids[first_key]

    assert 'rsid' in first_value
    assert 'variant_id' in first_value
    assert first_value['variant_id'].startswith('variants/')
