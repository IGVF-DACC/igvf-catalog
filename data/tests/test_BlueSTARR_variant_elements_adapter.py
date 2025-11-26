import json
import pytest
from adapters.BlueSTARR_variant_elements_adapter import BlueSTARRVariantElement
from adapters.writer import SpyWriter
from unittest.mock import patch, mock_open, MagicMock

# mock get_file_fileset_by_accession_in_arangodb so files_fileset data change will not affect the test


@pytest.fixture
def mock_file_fileset():
    """Fixture to mock get_file_fileset_by_accession_in_arangodb function."""
    with patch('adapters.BlueSTARR_variant_elements_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'method': 'BlueSTARR',
            'class': 'prediction',
            'samples': ['ontology_terms/EFO_0002067'],
            'simple_sample_summaries': ['K562']
        }
        yield mock_get_file_fileset


@patch('adapters.BlueSTARR_variant_elements_adapter.bulk_check_variants_in_arangodb', return_value=set())
def test_process_file_variant(mock_bulk_check, mock_file_fileset, mocker):
    # Create a complete mock variant that satisfies the schema requirements
    mock_variant = {
        '_key': 'NC_000005.10:1778862:T:G',
        'name': 'NC_000005.10:1778862:T:G',
        'chr': 'chr5',
        'pos': 1778862,
        'rsid': ['rs1234567890'],
        'ref': 'T',
        'alt': 'G',
        'qual': '60',
        'filter': None,
        'variation_type': 'SNP',
        'annotations': {},
        'spdi': 'NC_000005.10:1778862:T:G',
        'hgvs': 'NC_000005.10:g.1778863T>G',
        'vrs_digest': 'fake_vrs_digest',
        'ca_id': 'CA1234567890',
        'organism': 'Homo sapiens'
    }
    mocker.patch(
        'adapters.BlueSTARR_variant_elements_adapter.load_variant',
        return_value=(mock_variant, None)
    )

    # Create a temporary test file instead of mocking builtins.open
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as temp_file:
        temp_file.write(
            'chr5\t1778763\t1779094\t0.131\tNC_000005.10:1778862:T:G\n')
        temp_file_path = temp_file.name

    try:
        writer = SpyWriter()
        adapter = BlueSTARRVariantElement(
            filepath=temp_file_path, writer=writer, label='variant', validate=True)
        adapter.process_file()
        first_item = json.loads(writer.contents[0])
        assert len(writer.contents) > 0
        assert '_key' in first_item
        assert 'spdi' in first_item
        assert 'hgvs' in first_item
        assert 'variation_type' in first_item
        assert first_item['source'] == BlueSTARRVariantElement.SOURCE
        assert first_item['source_url'] == BlueSTARRVariantElement.SOURCE_URL
    finally:
        import os
        os.unlink(temp_file_path)


@patch('adapters.helpers.get_ref_seq_by_spdi', return_value='T')
@patch('adapters.BlueSTARR_variant_elements_adapter.bulk_check_variants_in_arangodb', return_value={'NC_000005.10:1778862:T:G'})
def test_process_file_variant_genomic_element(mock_bulk_check, mock_validate, mock_file_fileset, mocker):
    mocker.patch('adapters.BlueSTARR_variant_elements_adapter.build_variant_id',
                 return_value='fake_variant_id')

    # Create a temporary test file instead of mocking builtins.open
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as temp_file:
        temp_file.write(
            'chr5\t1778763\t1779094\t0.131\tNC_000005.10:1778862:T:G\n')
        temp_file_path = temp_file.name

    try:
        writer = SpyWriter()
        adapter = BlueSTARRVariantElement(
            filepath=temp_file_path, writer=writer, label='variant_genomic_element', validate=True)
        adapter.process_file()
        first_item = json.loads(writer.contents[0])
        assert len(writer.contents) > 0
        assert '_key' in first_item
        assert '_from' in first_item
        assert '_to' in first_item
        assert 'log2FC' in first_item
        assert 'label' in first_item
        assert first_item['source'] == BlueSTARRVariantElement.SOURCE
        assert first_item['source_url'] == BlueSTARRVariantElement.SOURCE_URL
    finally:
        import os
        os.unlink(temp_file_path)


def test_invalid_label_raises_error(mock_file_fileset):
    with pytest.raises(ValueError, match='Invalid label: invalid_label. Allowed values: variant, variant_genomic_element'):
        BlueSTARRVariantElement(
            filepath='./samples/bluestarr_variant_element.example.tsv', label='invalid_label')


@patch('adapters.BlueSTARR_variant_elements_adapter.bulk_check_variants_in_arangodb', return_value=set())
@patch('builtins.open', new_callable=mock_open, read_data='chr5\t1778763\t1779094\t0.131\tNC_000005.10:1778862:T:G\n')
def test_process_file_handles_empty_chunk(mock_file, mock_bulk_check, mock_file_fileset, mocker):
    mocker.patch(
        'adapters.BlueSTARR_variant_elements_adapter.load_variant',
        return_value=({'_key': 'NC_000005.10:1778862:T:G', 'spdi': 'NC_000005.10:1778862:T:G', 'hgvs': 'NC_000005.10:g.1778863T>G',
                      'variation_type': 'SNP'}, None)
    )
    writer = SpyWriter()
    adapter = BlueSTARRVariantElement(
        filepath='./samples/bluestarr_variant_element.example.tsv', writer=writer, label='variant')
    adapter.process_file()
    # Ensure no errors occur with a single chunk
    assert len(writer.contents) > 0


@patch('adapters.BlueSTARR_variant_elements_adapter.bulk_check_variants_in_arangodb', return_value={'NC_000005.10:1778862:T:G'})
@patch('builtins.open', new_callable=mock_open, read_data='chr5\t1778763\t1779094\t0.131\tNC_000005.10:1778862:T:G\n')
def test_process_file_skips_loaded_variants(mock_file, mock_bulk_check, mock_file_fileset, mocker):
    mocker.patch(
        'adapters.BlueSTARR_variant_elements_adapter.load_variant',
        return_value=({'_key': 'NC_000005.10:1778862:T:G', 'spdi': 'NC_000005.10:1778862:T:G', 'hgvs': 'NC_000005.10:g.1778863T>G',
                      'variation_type': 'SNP'}, None)
    )
    writer = SpyWriter()
    adapter = BlueSTARRVariantElement(
        filepath='./samples/bluestarr_variant_element.example.tsv', writer=writer, label='variant')
    adapter.process_file()
    # No unloaded variants should be processed
    assert len(writer.contents) == 0


@patch('adapters.BlueSTARR_variant_elements_adapter.bulk_check_variants_in_arangodb', return_value=set())
@patch('builtins.open', new_callable=mock_open, read_data='chr5\t1778763\t1779094\t0.131\tNC_000005.10:1778862:T:G\n')
def test_process_file_skips_variant_on_ref_mismatch(mock_file, mock_bulk_check, mock_file_fileset, mocker):
    mocker.patch(
        'adapters.BlueSTARR_variant_elements_adapter.load_variant',
        return_value=({}, {'variant_id': 'NC_000005.10:1778862:T:G',
                      'reason': 'Ref allele mismatch'})
    )
    writer = SpyWriter()
    adapter = BlueSTARRVariantElement(
        filepath='./samples/bluestarr_variant_element.example.tsv',
        writer=writer,
        label='variant'
    )
    adapter.process_file()
    # Since ref != 'T' from SPDI, variant should be skipped
    assert len(writer.contents) == 0


def test_validate_doc_invalid(mock_file_fileset):
    """Test that ValidationError is properly caught and converted to ValueError (covers lines 46-47)"""
    writer = SpyWriter()
    adapter = BlueSTARRVariantElement(
        filepath='./samples/bluestarr_variant_element.example.tsv', writer=writer, label='variant_genomic_element', validate=True)

    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }

    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)


def test_process_file_chunk_processing(mock_file_fileset):
    """Test chunk processing when data size equals chunk_size (covers lines 60-64)"""
    writer = SpyWriter()

    # Create a test file with exactly chunk_size (6500) rows
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as temp_file:
        # Write header
        temp_file.write('chr\tstart\tend\tlog2FC\tvariant_id\n')
        # Write exactly 6500 data rows
        for i in range(6500):
            temp_file.write(
                f'chr5\t1778763\t1779094\t0.131\tNC_000005.10:1778862:T:G\n')
        temp_file_path = temp_file.name

    try:
        with patch('adapters.BlueSTARR_variant_elements_adapter.bulk_check_variants_in_arangodb', return_value=set()):
            with patch('adapters.BlueSTARR_variant_elements_adapter.load_variant',
                       return_value=({'_key': 'NC_000005.10:1778862:T:G', 'spdi': 'NC_000005.10:1778862:T:G', 'hgvs': 'NC_000005.10:g.1778863T>G', 'variation_type': 'SNP'}, None)):
                adapter = BlueSTARRVariantElement(
                    filepath=temp_file_path, writer=writer, label='variant')
                adapter.process_file()

                # Should have processed all 6500 rows
                # Note: The exact number depends on how the chunk processing works
                assert len(writer.contents) >= 6500
    finally:
        import os
        os.unlink(temp_file_path)


def test_process_file_chunk_processing_variant_genomic_element(mock_file_fileset):
    """Test chunk processing for variant_genomic_element label (covers lines 62-63)"""
    writer = SpyWriter()

    # Create a test file with exactly chunk_size (6500) rows
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as temp_file:
        # Write header
        temp_file.write('chr\tstart\tend\tlog2FC\tvariant_id\n')
        # Write exactly 6500 data rows
        for i in range(6500):
            temp_file.write(
                f'chr5\t1778763\t1779094\t0.131\tNC_000005.10:1778862:T:G\n')
        temp_file_path = temp_file.name

    try:
        with patch('adapters.BlueSTARR_variant_elements_adapter.bulk_check_variants_in_arangodb', return_value={'NC_000005.10:1778862:T:G'}):
            with patch('adapters.BlueSTARR_variant_elements_adapter.build_variant_id', return_value='fake_variant_id'):
                with patch('adapters.BlueSTARR_variant_elements_adapter.build_regulatory_region_id', return_value='fake_element_id'):
                    with patch('adapters.BlueSTARR_variant_elements_adapter.split_spdi', return_value=('5', 1778862, 'T', 'G')):
                        adapter = BlueSTARRVariantElement(
                            filepath=temp_file_path, writer=writer, label='variant_genomic_element')
                        adapter.process_file()

                        # Should have processed all 6500 rows
                        # Note: The exact number depends on how the chunk processing works
                        assert len(writer.contents) >= 6500
    finally:
        import os
        os.unlink(temp_file_path)
