import json
from unittest.mock import patch

import pytest

from adapters.CRISPR_variant_phenotype_adapter import CRISPRVariantPhenotype
from adapters.writer import SpyWriter

MOCK_VARIANT = {
    '_key': 'NC_000001.11:25253603:G:A',
    'name': 'NC_000001.11:25253603:G:A',
    'chr': 'chr1',
    'pos': 25253603,
    'ref': 'G',
    'alt': 'A',
    'variation_type': 'SNP',
    'spdi': 'NC_000001.11:25253603:G:A',
    'hgvs': 'NC_000001.11:g.25253604G>A',
    'organism': 'Homo sapiens',
    'rsid': [],
    'qual': '100',
    'annotations': {},
    'vrs_digest': 'test_digest',
    'ca_id': 'CA1234567890',
}


@pytest.fixture
def mock_file_fileset():
    with patch(
        'adapters.CRISPR_variant_phenotype_adapter.get_file_fileset_by_accession_in_arangodb'
    ) as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'method': 'CRISPR screen',
            'class': 'observed data',
            'crispr_modality': 'base editing',
            'simple_sample_summaries': ['Homo sapiens HepG2 cell line'],
            'samples': ['ontology_terms/EFO_0001187'],
            'treatments_term_ids': None,
        }
        yield mock_get_file_fileset


def _mock_load_variant(variant_id, **kwargs):
    if not variant_id.startswith('NC_'):
        return None, {'variant_id': variant_id, 'reason': 'unrecognized'}

    variant = dict(MOCK_VARIANT)
    variant['_key'] = variant_id
    variant['name'] = variant_id
    variant['spdi'] = variant_id
    parts = variant_id.split(':')
    variant['ref'] = parts[2]
    variant['alt'] = parts[3]
    variant['pos'] = int(parts[1])
    return variant, None


def test_unsupported_accession(mock_file_fileset):
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Unsupported file accession'):
        CRISPRVariantPhenotype(
            filepath='./samples/crispr_variant_phenotype_sherwood_prime.example.csv',
            label='variant',
            source_url='https://api.data.igvf.org/tabular-files/IGVFFI0000AAAA/',
            writer=writer,
        )


def test_dropped_sherwood_chr_pos_accessions(mock_file_fileset):
    writer = SpyWriter()
    for accession in ('IGVFFI7160EKDK', 'IGVFFI7659OTOX'):
        with pytest.raises(ValueError, match='Unsupported file accession'):
            CRISPRVariantPhenotype(
                filepath='./samples/crispr_variant_phenotype_sherwood_prime.example.csv',
                label='variant',
                source_url=f'https://api.data.igvf.org/tabular-files/{accession}/',
                writer=writer,
            )


def test_invalid_label(mock_file_fileset):
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label'):
        CRISPRVariantPhenotype(
            filepath='./samples/crispr_variant_phenotype_sherwood_prime.example.csv',
            label='invalid_label',
            source_url='https://api.data.igvf.org/tabular-files/IGVFFI2014OOZP/',
            writer=writer,
        )


@patch(
    'adapters.CRISPR_variant_phenotype_adapter.bulk_check_variants_in_arangodb',
    return_value=set(),
)
@patch(
    'adapters.CRISPR_variant_phenotype_adapter.load_variant',
    side_effect=_mock_load_variant,
)
def test_variant_sherwood_prime(mock_load, mock_bulk, mock_file_fileset):
    mock_file_fileset.return_value['crispr_modality'] = 'prime editing'
    writer = SpyWriter()
    adapter = CRISPRVariantPhenotype(
        filepath='./samples/crispr_variant_phenotype_sherwood_prime.example.csv',
        label='variant',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI2014OOZP/',
        writer=writer,
        validate=True,
    )
    adapter.process_file()

    assert len(writer.contents) == 2
    first = json.loads(writer.contents[0])
    assert first['files_filesets'] == 'files_filesets/IGVFFI2014OOZP'
    assert first['source'] == 'IGVF'
    assert first['spdi'].startswith('NC_')


@patch(
    'adapters.CRISPR_variant_phenotype_adapter.bulk_check_variants_in_arangodb',
    return_value={
        'NC_000001.11:11845793:A:G',
        'NC_000001.11:11845916:A:G',
    },
)
@patch(
    'adapters.CRISPR_variant_phenotype_adapter.load_variant',
    side_effect=_mock_load_variant,
)
def test_variant_phenotype_lettre(mock_load, mock_bulk, mock_file_fileset):
    writer = SpyWriter()
    adapter = CRISPRVariantPhenotype(
        filepath='./samples/crispr_variant_phenotype_lettre.example.csv',
        label='variant_phenotype',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI7206JILF/',
        writer=writer,
        validate=True,
    )
    adapter.process_file()

    # splicesite skipped; one SPDI once + one SPDI twice (different guide counts)
    assert len(writer.contents) == 3
    items = [json.loads(line) for line in writer.contents]
    assert all(item['_to'] == 'ontology_terms/GO_0008283' for item in items)
    keys = {item['_key'] for item in items}
    assert 'NC_000001.11:11845916:A:G_GO_0008283_IGVFFI7206JILF_5' in keys
    assert 'NC_000001.11:11845916:A:G_GO_0008283_IGVFFI7206JILF_2' in keys


@patch(
    'adapters.CRISPR_variant_phenotype_adapter.bulk_check_variants_in_arangodb',
    return_value={
        'NC_000019.10:11105541:CAGC:GCTG',
        'NC_000019.10:11105382:CTGC:ATGG',
    },
)
@patch(
    'adapters.CRISPR_variant_phenotype_adapter.load_variant',
    side_effect=_mock_load_variant,
)
def test_variant_phenotype_sherwood_prime(mock_load, mock_bulk, mock_file_fileset):
    mock_file_fileset.return_value['crispr_modality'] = 'prime editing'
    writer = SpyWriter()
    adapter = CRISPRVariantPhenotype(
        filepath='./samples/crispr_variant_phenotype_sherwood_prime.example.csv',
        label='variant_phenotype',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI2014OOZP/',
        writer=writer,
        validate=True,
    )
    adapter.process_file()

    assert len(writer.contents) == 2
    first = json.loads(writer.contents[0])
    assert first['crispr_modality'] == 'prime editing'
    assert first['significant'] is True
    assert first['num_guides'] == 1


@patch('adapters.CRISPR_variant_phenotype_adapter.requests.get')
def test_ontology_term_ntr(mock_get, mock_file_fileset):
    mock_get.return_value.status_code = 200
    mock_get.return_value.raise_for_status = lambda: None
    mock_get.return_value.json.return_value = {
        '@graph': [{
            '@id': '/phenotype-terms/NTR_0001118/',
            'term_id': 'NTR:0001118',
            'term_name': 'LDL-C uptake',
            'synonyms': [],
        }]
    }

    writer = SpyWriter()
    adapter = CRISPRVariantPhenotype(
        filepath='./samples/crispr_variant_phenotype_sherwood_prime.example.csv',
        label='ontology_term',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI2014OOZP/',
        writer=writer,
        validate=True,
    )
    adapter.process_file()

    assert len(writer.contents) == 1
    term = json.loads(writer.contents[0])
    assert term['_key'] == 'NTR_0001118'
    assert term['name'] == 'LDL-C uptake'
    assert term['term_id'] == 'NTR_0001118'
    assert term['source'] == 'IGVF'
    assert term['synonyms'] is None


def test_ontology_term_skips_go(mock_file_fileset):
    writer = SpyWriter()
    adapter = CRISPRVariantPhenotype(
        filepath='./samples/crispr_variant_phenotype_lettre.example.csv',
        label='ontology_term',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI7206JILF/',
        writer=writer,
        validate=True,
    )
    adapter.process_file()
    assert writer.contents == []
