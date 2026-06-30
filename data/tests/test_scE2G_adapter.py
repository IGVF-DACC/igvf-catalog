import gzip
import json
import pytest
from unittest.mock import MagicMock, patch

from adapters.scE2G_adapter import scE2G
from adapters.writer import SpyWriter

FILE_ACCESSION = 'IGVFFI5648GWQX'
SOURCE_URL = f'https://data.igvf.org/tabular-files/{FILE_ACCESSION}'
REGULATORY_ELEMENT_ID = (
    'promoter_chr1_169893055_169894554_GRCh38_IGVFFI5648GWQX'
)
GENE_ID = 'ENSG00000000457'
CELL_TYPE_TERM_ID = 'CL_0000336'
EDGE_KEY = f'{REGULATORY_ELEMENT_ID}_{GENE_ID}_{CELL_TYPE_TERM_ID}'

MOCK_FILE_FILESET = {
    'method': 'scE2G',
    'class': 'prediction',
    'simple_sample_summaries': ['adrenal medulla chromaffin cell'],
    'samples': ['ontology_terms/CL_0000336'],
}

SCE2G_HEADER = (
    'ElementChr\tElementStart\tElementEnd\tElementName\tElementClass\t'
    'GeneSymbol\tGeneEnsemblID\tGeneTSS\tCellType\tCellTypeOntologyTerm\t'
    'CellTypeOntologyTermName\tScore\tRNA_pseudobulkTPM\n'
)
SCE2G_ROW = (
    'chr1\t169893055\t169894554\tchr1:169893055-169894554\tpromoter\t'
    'SCYL3\tENSG00000000457\t169893959\tAdrenal medulla chromaffin cell\t'
    'CL:0000336\tAdrenal medulla chromaffin cell\t0.996889932534048\t'
    '22.8574991753656\n'
)
SCE2G_ROW_GENIC = (
    'chr1\t24321501\t24322805\tchr1:24321501-24322805\tgenic\tSTPG1\t'
    'ENSG00000001460\t24413772\tAdrenal medulla chromaffin cell\t'
    'CL:0000336\tAdrenal medulla chromaffin cell\t0.510427225480237\t'
    '13.2358832214525\n'
)

SCE2G_EXTENDED_HEADER = (
    'ElementChr\tElementStart\tElementEnd\tElementName\tElementClass\t'
    'GeneSymbol\tGeneEnsemblID\tGeneTSS\tCellType\tCellTypeOntologyTerm\t'
    'CellTypeOntologyTermName\tSampleOntologyTerm\tSampleOntologyTermName\t'
    'Qualifier\tScore\tRNA_pseudobulkTPM\n'
)
SCE2G_EXTENDED_ROW = (
    'chr1\t169893055\t169894554\tchr1:169893055-169894554\tpromoter\t'
    'SCYL3\tENSG00000000457\t169893959\tAdrenal medulla chromaffin cell\t'
    'CL:0000336\tAdrenal medulla chromaffin cell\tEFO:0002067\t'
    'K562\tCRISPRi\t0.996889932534048\t22.8574991753656\n'
)

SCE2G_ALTERNATE_HEADER = (
    'ElementChr\tElementStart\tElementEnd\tGeneSymbol\tGeneEnsemblID\t'
    'GeneTSS\tABC.Score\tARC.E2G.Score\tScore.ignoreTPM\tScore\t'
    'ElementName\tSampleSummaryShort\n'
)
SCE2G_ALTERNATE_ROW = (
    'chr1\t778173\t779428\tLINC01128\tENSG00000228794\t827590\t'
    '0.071691\t0.0851271937191741\t0.20658503871143\t0.20658503871143\t'
    'chr1:778173-779428\tK562-CRISPRi\n'
)
ALTERNATE_FILE_ACCESSION = 'IGVFFI0793NWFM'
ALTERNATE_REGULATORY_ELEMENT_ID = (
    'enhancer_chr1_778173_779428_GRCh38_IGVFFI0793NWFM'
)
ALTERNATE_GENE_ID = 'ENSG00000228794'
ALTERNATE_EDGE_KEY = (
    f'{ALTERNATE_REGULATORY_ELEMENT_ID}_{ALTERNATE_GENE_ID}_{CELL_TYPE_TERM_ID}'
)


@pytest.fixture
def mock_file_fileset():
    """Mock ArangoDB lookup so file_fileset data changes do not affect tests."""
    with patch(
        'adapters.scE2G_adapter.get_file_fileset_by_accession_in_arangodb'
    ) as mock_get_file_fileset:
        mock_get_file_fileset.return_value = MOCK_FILE_FILESET.copy()
        yield mock_get_file_fileset


@pytest.fixture
def sce2g_filepath(tmp_path):
    """Create a gzipped scE2G TSV test file and return its path."""
    def _create(
        rows=None,
        include_comments=True,
        include_blank_row=False,
        filename=f'{FILE_ACCESSION}.tsv.gz',
        header=SCE2G_HEADER,
    ):
        path = str(tmp_path / filename)
        rows = rows if rows is not None else [SCE2G_ROW]
        with gzip.open(path, 'wt') as out:
            if include_comments:
                out.write('# Source: scE2G\n')
                out.write('# Version: v1.2.0\n')
            out.write(header)
            for index, row in enumerate(rows):
                if include_blank_row and index == 1:
                    out.write('\n')
                out.write(row)
        return path

    return _create


def test_scE2G_adapter_initialization():
    writer = SpyWriter()
    filepath = f'/data/tabular-files/{FILE_ACCESSION}.tsv.gz'

    edge_adapter = scE2G(
        filepath=filepath,
        label='genomic_element_gene',
        writer=writer,
    )
    assert edge_adapter.filepath == filepath
    assert edge_adapter.label == 'genomic_element_gene'
    assert edge_adapter.writer == writer
    assert edge_adapter.file_accession == FILE_ACCESSION
    assert edge_adapter.source_url == SOURCE_URL
    assert edge_adapter.SOURCE == 'IGVF'
    assert hasattr(edge_adapter, 'gene_validator')

    node_adapter = scE2G(
        filepath=filepath,
        label='genomic_element',
        writer=writer,
    )
    assert node_adapter.label == 'genomic_element'
    assert not hasattr(node_adapter, 'gene_validator')


def test_scE2G_get_schema_type_and_collection_name():
    writer = SpyWriter()
    filepath = f'/data/tabular-files/{FILE_ACCESSION}.tsv.gz'

    edge_adapter = scE2G(
        filepath=filepath,
        label='genomic_element_gene',
        writer=writer,
    )
    assert edge_adapter._get_schema_type() == 'edges'
    assert edge_adapter._get_collection_name() == 'genomic_elements_genes'

    node_adapter = scE2G(
        filepath=filepath,
        label='genomic_element',
        writer=writer,
    )
    assert node_adapter._get_schema_type() == 'nodes'
    assert node_adapter._get_collection_name() == 'genomic_elements'


def test_scE2G_adapter_genomic_element_gene(mock_file_fileset, sce2g_filepath):
    writer = SpyWriter()
    with patch('adapters.scE2G_adapter.GeneValidator') as mock_gene_validator:
        mock_validator_instance = MagicMock()
        mock_validator_instance.validate.return_value = True
        mock_gene_validator.return_value = mock_validator_instance

        adapter = scE2G(
            filepath=sce2g_filepath(),
            label='genomic_element_gene',
            writer=writer,
            validate=True,
        )
        adapter.process_file()

        mock_validator_instance.log.assert_called_once()
        mock_file_fileset.assert_called_once_with(FILE_ACCESSION)

        parsed = [json.loads(item) for item in writer.contents if item.strip()]
        assert len(parsed) == 1
        first_item = parsed[0]
        assert first_item['_key'] == EDGE_KEY
        assert first_item['_from'] == f'genomic_elements/{REGULATORY_ELEMENT_ID}'
        assert first_item['_to'] == f'genes/{GENE_ID}'
        assert first_item['transcription_start_site'] == 169893959
        assert first_item['score'] == pytest.approx(0.996889932534048)
        assert first_item['rna_pseudobulk_tpm'] == pytest.approx(
            22.8574991753656)
        assert first_item['cell_type'] == 'adrenal medulla chromaffin cell'
        assert first_item['cell_type_term'] == 'ontology_terms/CL_0000336'
        assert first_item['files_filesets'] == f'files_filesets/{FILE_ACCESSION}'
        assert first_item['label'] == scE2G.COLLECTION_LABEL
        assert first_item['method'] == 'scE2G'
        assert first_item['class'] == 'prediction'
        assert first_item['source'] == 'IGVF'
        assert first_item['source_url'] == SOURCE_URL
        assert first_item['name'] == 'regulates'
        assert first_item['inverse_name'] == 'regulated by'


def test_scE2G_adapter_genomic_element(mock_file_fileset, sce2g_filepath):
    writer = SpyWriter()
    adapter = scE2G(
        filepath=sce2g_filepath(),
        label='genomic_element',
        writer=writer,
        validate=True,
    )
    adapter.process_file()

    parsed = [json.loads(item) for item in writer.contents if item.strip()]
    assert len(parsed) == 1
    first_item = parsed[0]
    assert first_item['_key'] == REGULATORY_ELEMENT_ID
    assert first_item['name'] == REGULATORY_ELEMENT_ID
    assert first_item['chr'] == 'chr1'
    assert first_item['start'] == 169893055
    assert first_item['end'] == 169894554
    assert first_item['source_annotation'] == 'promoter'
    assert first_item['type'] == 'accessible dna elements'
    assert first_item['method'] == 'scE2G'
    assert first_item['source'] == 'IGVF'
    assert first_item['source_url'] == SOURCE_URL
    assert first_item['files_filesets'] == f'files_filesets/{FILE_ACCESSION}'


def test_scE2G_adapter_process_without_validation(
    mock_file_fileset, sce2g_filepath
):
    writer = SpyWriter()
    with patch('adapters.scE2G_adapter.GeneValidator') as mock_gene_validator:
        mock_validator_instance = MagicMock()
        mock_validator_instance.validate.return_value = True
        mock_gene_validator.return_value = mock_validator_instance

        adapter = scE2G(
            filepath=sce2g_filepath(),
            label='genomic_element_gene',
            writer=writer,
            validate=False,
        )
        adapter.process_file()

        parsed = [json.loads(item) for item in writer.contents if item.strip()]
        assert len(parsed) == 1
        mock_validator_instance.log.assert_called_once()


def test_scE2G_adapter_skips_comment_and_blank_rows(
    mock_file_fileset, sce2g_filepath
):
    writer = SpyWriter()
    filepath = sce2g_filepath(
        rows=[SCE2G_ROW, SCE2G_ROW_GENIC],
        include_blank_row=True,
    )

    with patch('adapters.scE2G_adapter.GeneValidator') as mock_gene_validator:
        mock_validator_instance = MagicMock()
        mock_validator_instance.validate.return_value = True
        mock_gene_validator.return_value = mock_validator_instance

        adapter = scE2G(
            filepath=filepath,
            label='genomic_element_gene',
            writer=writer,
            validate=True,
        )
        adapter.process_file()

        parsed = [json.loads(item) for item in writer.contents if item.strip()]
        assert len(parsed) == 2
        assert parsed[0]['_key'] == EDGE_KEY
        assert parsed[0]['_to'] == 'genes/ENSG00000000457'
        assert parsed[1]['_key'] == (
            'genic_chr1_24321501_24322805_GRCh38_IGVFFI5648GWQX'
            '_ENSG00000001460_CL_0000336'
        )
        assert parsed[1]['_to'] == 'genes/ENSG00000001460'


def test_scE2G_adapter_skips_invalid_gene_id(
    mock_file_fileset, sce2g_filepath, caplog
):
    writer = SpyWriter()
    with patch('adapters.scE2G_adapter.GeneValidator') as mock_gene_validator:
        mock_validator_instance = MagicMock()
        mock_validator_instance.validate.return_value = False
        mock_gene_validator.return_value = mock_validator_instance

        adapter = scE2G(
            filepath=sce2g_filepath(),
            label='genomic_element_gene',
            writer=writer,
            validate=True,
        )
        with caplog.at_level('WARNING'):
            adapter.process_file()

        assert len(writer.contents) == 0
        assert 'Skipping row: gene "ENSG00000000457" is not a valid gene.' in caplog.text
        mock_validator_instance.log.assert_called_once()


def test_scE2G_adapter_genomic_element_gene_extended_header(
    mock_file_fileset, sce2g_filepath
):
    writer = SpyWriter()
    with patch('adapters.scE2G_adapter.GeneValidator') as mock_gene_validator:
        mock_validator_instance = MagicMock()
        mock_validator_instance.validate.return_value = True
        mock_gene_validator.return_value = mock_validator_instance

        adapter = scE2G(
            filepath=sce2g_filepath(
                rows=[SCE2G_EXTENDED_ROW],
                header=SCE2G_EXTENDED_HEADER,
            ),
            label='genomic_element_gene',
            writer=writer,
            validate=True,
        )
        adapter.process_file()

        parsed = [json.loads(item) for item in writer.contents if item.strip()]
        assert len(parsed) == 1
        first_item = parsed[0]
        assert first_item['_key'] == EDGE_KEY
        assert first_item['score'] == pytest.approx(0.996889932534048)
        assert first_item['rna_pseudobulk_tpm'] == pytest.approx(
            22.8574991753656)


def test_scE2G_adapter_genomic_element_gene_alternate_header(
    mock_file_fileset, sce2g_filepath
):
    writer = SpyWriter()
    with patch('adapters.scE2G_adapter.GeneValidator') as mock_gene_validator:
        mock_validator_instance = MagicMock()
        mock_validator_instance.validate.return_value = True
        mock_gene_validator.return_value = mock_validator_instance

        adapter = scE2G(
            filepath=sce2g_filepath(
                rows=[SCE2G_ALTERNATE_ROW],
                filename=f'{ALTERNATE_FILE_ACCESSION}.tsv.gz',
                header=SCE2G_ALTERNATE_HEADER,
            ),
            label='genomic_element_gene',
            writer=writer,
            validate=True,
        )
        adapter.process_file()

        parsed = [json.loads(item) for item in writer.contents if item.strip()]
        assert len(parsed) == 1
        first_item = parsed[0]
        assert first_item['_key'] == ALTERNATE_EDGE_KEY
        assert first_item['_from'] == (
            f'genomic_elements/{ALTERNATE_REGULATORY_ELEMENT_ID}'
        )
        assert first_item['_to'] == f'genes/{ALTERNATE_GENE_ID}'
        assert first_item['score'] == pytest.approx(0.20658503871143)
        assert first_item['rna_pseudobulk_tpm'] is None
        assert first_item['cell_type'] == 'adrenal medulla chromaffin cell'


def test_scE2G_adapter_genomic_element_alternate_header(
    mock_file_fileset, sce2g_filepath
):
    writer = SpyWriter()
    adapter = scE2G(
        filepath=sce2g_filepath(
            rows=[SCE2G_ALTERNATE_ROW],
            filename=f'{ALTERNATE_FILE_ACCESSION}.tsv.gz',
            header=SCE2G_ALTERNATE_HEADER,
        ),
        label='genomic_element',
        writer=writer,
        validate=True,
    )
    adapter.process_file()

    parsed = [json.loads(item) for item in writer.contents if item.strip()]
    assert len(parsed) == 1
    first_item = parsed[0]
    assert first_item['_key'] == ALTERNATE_REGULATORY_ELEMENT_ID
    assert first_item['source_annotation'] == 'enhancer'


def test_scE2G_adapter_invalid_label():
    writer = SpyWriter()
    with pytest.raises(
        ValueError,
        match='Invalid label: invalid_label. Allowed values: genomic_element_gene, genomic_element',
    ):
        scE2G(
            filepath=f'/data/tabular-files/{FILE_ACCESSION}.tsv.gz',
            label='invalid_label',
            writer=writer,
            validate=True,
        )


def test_scE2G_adapter_validate_doc_invalid(sce2g_filepath):
    writer = SpyWriter()
    adapter = scE2G(
        filepath=sce2g_filepath(),
        label='genomic_element_gene',
        writer=writer,
        validate=True,
    )
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123,
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
