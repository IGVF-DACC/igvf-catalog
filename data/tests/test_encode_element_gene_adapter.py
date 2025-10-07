import json
import pytest
from unittest.mock import patch, MagicMock
from adapters.encode_element_gene_adapter import EncodeElementGeneLink
from adapters.writer import SpyWriter


@patch('adapters.encode_element_gene_adapter.FileFileSet.query_fileset_files_props_encode')
def test_encode_element_gene_adapter_genomic_element_gene(mock_fileset_props):
    # Mock the fileset properties
    mock_fileset_props.return_value = [{
        'method': 'element gene regulatory interaction predictions using Distal regulation ENCODE-rE2G',
        'simple_sample_summaries': ['K562'],
        'treatments_term_ids': ['UniProtKB:P05112']
    }]

    # Mock GeneValidator
    with patch('adapters.encode_element_gene_adapter.GeneValidator') as mock_gene_validator:
        mock_validator_instance = MagicMock()
        mock_validator_instance.validate.return_value = True
        mock_gene_validator.return_value = mock_validator_instance

        writer = SpyWriter()

        # Create a small temporary test file
        import tempfile
        import gzip
        with tempfile.NamedTemporaryFile(suffix='.bed.gz', delete=False) as temp_file:
            with gzip.open(temp_file.name, 'wt') as f:
                f.write('#chr\tstart\tend\tname\tclass\tTargetGene\tTargetGeneEnsemblID\tTargetGeneTSS\tCellType\tScore\tDistanceToTSS\tH3K27ac\tOpen\tCofactor\tActivity\tHiC_contacts\tHiC_foldchange\n')
                f.write('chr1\t827140\t827667\te:chr1:827140-827667\tenhancer\tNOC2L\tENSG00000188976\t959156\tBlood.Myeloid.Erythroblast\t0.1094868\t131089\t29.0349\t15.5104\t8.8905\t60.5940863\t0.13094\t9.70500\n')
            temp_file_path = temp_file.name

        try:
            adapter = EncodeElementGeneLink(
                filepath=temp_file_path,
                label='genomic_element_gene',
                source='ENCODE-E2G-DNaseOnly',
                source_url='https://www.encodeproject.org/files/ENCFF712SUP/',
                biological_context='CL_0000765',
                writer=writer,
                validate=True
            )
            adapter.process_file()

            first_item = json.loads(writer.contents[0])
            assert len(writer.contents) > 0
            assert '_key' in first_item
            assert '_from' in first_item
            assert '_to' in first_item
            assert 'score' in first_item
            assert 'method' in first_item
            assert 'source' in first_item
            assert 'source_url' in first_item
            assert 'files_filesets' in first_item
            assert 'biological_context' in first_item
            assert 'simple_sample_summaries' in first_item
            assert 'treatments_term_ids' in first_item
            assert 'name' in first_item
            assert 'inverse_name' in first_item
            assert first_item['source'] == 'ENCODE'
            assert first_item['name'] == 'regulates'
            assert first_item['inverse_name'] == 'regulated by'
        finally:
            import os
            os.unlink(temp_file_path)


@patch('adapters.encode_element_gene_adapter.FileFileSet.query_fileset_files_props_encode')
def test_encode_element_gene_adapter_genomic_element(mock_fileset_props):
    # Mock the fileset properties
    mock_fileset_props.return_value = [{
        'method': 'element gene regulatory interaction predictions using Distal regulation ENCODE-rE2G',
        'simple_sample_summaries': ['K562'],
        'treatments_term_ids': ['UniProtKB:P05112']
    }]

    writer = SpyWriter()

    # Create a small temporary test file
    import tempfile
    import gzip
    with tempfile.NamedTemporaryFile(suffix='.bed.gz', delete=False) as temp_file:
        with gzip.open(temp_file.name, 'wt') as f:
            f.write('#chr\tstart\tend\tname\tclass\tTargetGene\tTargetGeneEnsemblID\tTargetGeneTSS\tCellType\tScore\tDistanceToTSS\tH3K27ac\tOpen\tCofactor\tActivity\tHiC_contacts\tHiC_foldchange\n')
            f.write('chr1\t827140\t827667\te:chr1:827140-827667\tenhancer\tNOC2L\tENSG00000188976\t959156\tBlood.Myeloid.Erythroblast\t0.1094868\t131089\t29.0349\t15.5104\t8.8905\t60.5940863\t0.13094\t9.70500\n')
        temp_file_path = temp_file.name

    try:
        adapter = EncodeElementGeneLink(
            filepath=temp_file_path,
            label='genomic_element',
            source='ENCODE-E2G-DNaseOnly',
            source_url='https://www.encodeproject.org/files/ENCFF712SUP/',
            biological_context='CL_0000765',
            writer=writer,
            validate=True
        )
        adapter.process_file()

        first_item = json.loads(writer.contents[0])
        assert len(writer.contents) > 0
        assert '_key' in first_item
        assert 'name' in first_item
        assert 'chr' in first_item
        assert 'start' in first_item
        assert 'end' in first_item
        assert 'method' in first_item
        assert 'type' in first_item
        assert 'source_annotation' in first_item
        assert 'source' in first_item
        assert 'source_url' in first_item
        assert 'files_filesets' in first_item
        assert 'simple_sample_summaries' in first_item
        assert 'treatments_term_ids' in first_item
        assert first_item['type'] == 'accessible dna elements'
        assert first_item['source'] == 'ENCODE'
    finally:
        import os
        os.unlink(temp_file_path)


def test_encode_element_gene_adapter_initialization():
    writer = SpyWriter()
    for label in EncodeElementGeneLink.ALLOWED_LABELS:
        adapter = EncodeElementGeneLink(
            filepath='./samples/epiraction_ENCFF712SUP.bed.gz',
            label=label,
            source='ENCODE-E2G-DNaseOnly',
            source_url='https://www.encodeproject.org/files/ENCFF712SUP/',
            biological_context='CL_0000765',
            writer=writer
        )
        assert adapter.filepath == './samples/epiraction_ENCFF712SUP.bed.gz'
        assert adapter.label == label
        assert adapter.dataset == label
        assert adapter.dry_run == True
        assert adapter.writer == writer
        assert adapter.source == 'ENCODE-E2G-DNaseOnly'
        assert adapter.source_url == 'https://www.encodeproject.org/files/ENCFF712SUP/'
        assert adapter.biological_context == 'CL_0000765'

        if label == 'genomic_element':
            assert adapter.type == 'node'
        else:
            assert adapter.type == 'edge'


def test_encode_element_gene_adapter_validate_doc_invalid():
    writer = SpyWriter()
    adapter = EncodeElementGeneLink(
        filepath='./samples/epiraction_ENCFF712SUP.bed.gz',
        label='genomic_element_gene',
        source='ENCODE-E2G-DNaseOnly',
        source_url='https://www.encodeproject.org/files/ENCFF712SUP/',
        biological_context='CL_0000765',
        writer=writer,
        validate=True
    )

    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }

    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)


def test_encode_element_gene_adapter_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label. Allowed values: genomic_element_gene,genomic_element'):
        EncodeElementGeneLink(
            filepath='./samples/epiraction_ENCFF712SUP.bed.gz',
            label='invalid_label',
            source='ENCODE-E2G-DNaseOnly',
            source_url='https://www.encodeproject.org/files/ENCFF712SUP/',
            biological_context='CL_0000765',
            writer=writer,
            validate=True
        )


def test_encode_element_gene_adapter_invalid_source():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid source. Allowed values: ENCODE-E2G-DNaseOnly,ENCODE-E2G-Full'):
        EncodeElementGeneLink(
            filepath='./samples/epiraction_ENCFF712SUP.bed.gz',
            label='genomic_element_gene',
            source='INVALID_SOURCE',
            source_url='https://www.encodeproject.org/files/ENCFF712SUP/',
            biological_context='CL_0000765',
            writer=writer,
            validate=True
        )


@patch('adapters.encode_element_gene_adapter.FileFileSet.query_fileset_files_props_encode')
def test_encode_element_gene_adapter_skips_na_gene_id(mock_fileset_props):
    # Mock the fileset properties
    mock_fileset_props.return_value = [{
        'method': 'element gene regulatory interaction predictions using Distal regulation ENCODE-rE2G',
        'simple_sample_summaries': ['K562'],
        'treatments_term_ids': ['UniProtKB:P05112']
    }]

    # Mock GeneValidator
    with patch('adapters.encode_element_gene_adapter.GeneValidator') as mock_gene_validator:
        mock_validator_instance = MagicMock()
        mock_validator_instance.validate.return_value = True
        mock_gene_validator.return_value = mock_validator_instance

        writer = SpyWriter()

        # Create a small temporary test file with NA gene ID
        import tempfile
        import gzip
        with tempfile.NamedTemporaryFile(suffix='.bed.gz', delete=False) as temp_file:
            with gzip.open(temp_file.name, 'wt') as f:
                f.write('#chr\tstart\tend\tname\tclass\tTargetGene\tTargetGeneEnsemblID\tTargetGeneTSS\tCellType\tScore\tDistanceToTSS\tH3K27ac\tOpen\tCofactor\tActivity\tHiC_contacts\tHiC_foldchange\n')
                f.write('chr1\t827140\t827667\te:chr1:827140-827667\tenhancer\tNA\tNA\t959156\tBlood.Myeloid.Erythroblast\t0.1094868\t131089\t29.0349\t15.5104\t8.8905\t60.5940863\t0.13094\t9.70500\n')
            temp_file_path = temp_file.name

        try:
            adapter = EncodeElementGeneLink(
                filepath=temp_file_path,
                label='genomic_element_gene',
                source='ENCODE-E2G-DNaseOnly',
                source_url='https://www.encodeproject.org/files/ENCFF712SUP/',
                biological_context='CL_0000765',
                writer=writer,
                validate=True
            )
            adapter.process_file()

            # Should skip the row with NA gene ID
            assert len(writer.contents) == 0
        finally:
            import os
            os.unlink(temp_file_path)


@patch('adapters.encode_element_gene_adapter.FileFileSet.query_fileset_files_props_encode')
def test_encode_element_gene_adapter_skips_invalid_gene_id(mock_fileset_props):
    # Mock the fileset properties
    mock_fileset_props.return_value = [{
        'method': 'element gene regulatory interaction predictions using Distal regulation ENCODE-rE2G',
        'simple_sample_summaries': ['K562'],
        'treatments_term_ids': ['UniProtKB:P05112']
    }]

    # Mock GeneValidator to return False for invalid gene ID
    with patch('adapters.encode_element_gene_adapter.GeneValidator') as mock_gene_validator:
        mock_validator_instance = MagicMock()
        mock_validator_instance.validate.return_value = False
        mock_gene_validator.return_value = mock_validator_instance

        writer = SpyWriter()

        # Create a small temporary test file with invalid gene ID
        import tempfile
        import gzip
        with tempfile.NamedTemporaryFile(suffix='.bed.gz', delete=False) as temp_file:
            with gzip.open(temp_file.name, 'wt') as f:
                f.write('#chr\tstart\tend\tname\tclass\tTargetGene\tTargetGeneEnsemblID\tTargetGeneTSS\tCellType\tScore\tDistanceToTSS\tH3K27ac\tOpen\tCofactor\tActivity\tHiC_contacts\tHiC_foldchange\n')
                f.write('chr1\t827140\t827667\te:chr1:827140-827667\tenhancer\tINVALID_GENE\tINVALID_GENE\t959156\tBlood.Myeloid.Erythroblast\t0.1094868\t131089\t29.0349\t15.5104\t8.8905\t60.5940863\t0.13094\t9.70500\n')
            temp_file_path = temp_file.name

        try:
            adapter = EncodeElementGeneLink(
                filepath=temp_file_path,
                label='genomic_element_gene',
                source='ENCODE-E2G-DNaseOnly',
                source_url='https://www.encodeproject.org/files/ENCFF712SUP/',
                biological_context='CL_0000765',
                writer=writer,
                validate=True
            )
            adapter.process_file()

            # Should skip the row with invalid gene ID
            assert len(writer.contents) == 0
        finally:
            import os
            os.unlink(temp_file_path)
