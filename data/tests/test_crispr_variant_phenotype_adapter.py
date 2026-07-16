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
    if variant_id.startswith('NC_'):
        spdi = variant_id
    elif '-' in variant_id:
        # gnomad-style from chr_pos_hg38_ref_alt conversion
        chrom, pos, ref, alt = variant_id.split('-')
        # convert 1-based gnomad pos to 0-based SPDI pos
        spdi = f'NC_000001.11:{int(pos) - 1}:{ref}:{alt}'
        if chrom == 'chr19' or chrom == '19':
            spdi = f'NC_000019.10:{int(pos) - 1}:{ref}:{alt}'
    else:
        return None, {'variant_id': variant_id, 'reason': 'unrecognized'}

    variant = dict(MOCK_VARIANT)
    variant['_key'] = spdi
    variant['name'] = spdi
    variant['spdi'] = spdi
    variant['ref'] = spdi.split(':')[2]
    variant['alt'] = spdi.split(':')[3]
    variant['pos'] = int(spdi.split(':')[1])
    return variant, None


def test_parse_chr_pos_hg38_ref_alt():
    chrom, pos, ref, alt = CRISPRVariantPhenotype._parse_chr_pos_hg38_ref_alt(
        '1_25253604_hg38_G_A'
    )
    assert chrom == 'chr1'
    assert pos == 25253604
    assert ref == 'G'
    assert alt == 'A'

    chrom, pos, ref, alt = CRISPRVariantPhenotype._parse_chr_pos_hg38_ref_alt(
        '19_11091518_hg38_GC_G'
    )
    assert chrom == 'chr19'
    assert pos == 11091518
    assert ref == 'GC'
    assert alt == 'G'


def test_parse_chr_pos_hg38_ref_alt_invalid():
    with pytest.raises(ValueError, match='Unrecognized variant id'):
        CRISPRVariantPhenotype._parse_chr_pos_hg38_ref_alt('not_a_variant')


def test_unsupported_accession(mock_file_fileset):
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Unsupported file accession'):
        CRISPRVariantPhenotype(
            filepath='./samples/crispr_variant_phenotype_sherwood_base.example.csv',
            label='variant',
            source_url='https://api.data.igvf.org/tabular-files/IGVFFI0000AAAA/',
            writer=writer,
        )


def test_invalid_label(mock_file_fileset):
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label'):
        CRISPRVariantPhenotype(
            filepath='./samples/crispr_variant_phenotype_sherwood_base.example.csv',
            label='invalid_label',
            source_url='https://api.data.igvf.org/tabular-files/IGVFFI7160EKDK/',
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
def test_variant_sherwood_base(mock_load, mock_bulk, mock_file_fileset):
    writer = SpyWriter()
    adapter = CRISPRVariantPhenotype(
        filepath='./samples/crispr_variant_phenotype_sherwood_base.example.csv',
        label='variant',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI7160EKDK/',
        writer=writer,
        validate=True,
    )
    adapter.process_file()

    # PosControl row skipped; 2 Variant rows
    assert len(writer.contents) == 2
    first = json.loads(writer.contents[0])
    assert first['files_filesets'] == 'files_filesets/IGVFFI7160EKDK'
    assert first['source'] == 'IGVF'
    assert first['spdi'].startswith('NC_')


@patch(
    'adapters.CRISPR_variant_phenotype_adapter.bulk_check_variants_in_arangodb',
    return_value={'NC_000001.11:25253603:G:A', 'NC_000001.11:25341834:C:T'},
)
@patch(
    'adapters.CRISPR_variant_phenotype_adapter.load_variant',
    side_effect=_mock_load_variant,
)
def test_variant_phenotype_sherwood_base(mock_load, mock_bulk, mock_file_fileset):
    writer = SpyWriter()
    adapter = CRISPRVariantPhenotype(
        filepath='./samples/crispr_variant_phenotype_sherwood_base.example.csv',
        label='variant_phenotype',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI7160EKDK/',
        writer=writer,
        validate=True,
    )
    adapter.process_file()

    assert len(writer.contents) == 2
    first = json.loads(writer.contents[0])
    assert first['_to'] == 'ontology_terms/NTR_0001118'
    assert first['effect_size'] == pytest.approx(0.04365311)
    assert first['z_score'] == pytest.approx(0.276691)
    assert first['fdr'] == pytest.approx(0.866342209)
    assert first['significant'] is False
    assert first['edit_rate_mean'] == pytest.approx(0.601411259)
    assert first['crispr_modality'] == 'base editing'
    assert first['label'] == 'variant effect on phenotype'
    assert first['method'] == 'CRISPR screen'
    assert first['biosample_term'] == 'ontology_terms/EFO_0001187'


@patch(
    'adapters.CRISPR_variant_phenotype_adapter.bulk_check_variants_in_arangodb',
    return_value={'NC_000019.10:11091517:GC:G', 'NC_000001.11:26921330:G:A'},
)
@patch(
    'adapters.CRISPR_variant_phenotype_adapter.load_variant',
    side_effect=_mock_load_variant,
)
def test_variant_phenotype_sherwood_interference(mock_load, mock_bulk, mock_file_fileset):
    mock_file_fileset.return_value['crispr_modality'] = 'interference'
    writer = SpyWriter()
    adapter = CRISPRVariantPhenotype(
        filepath='./samples/crispr_variant_phenotype_sherwood_interference.example.csv',
        label='variant_phenotype',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI7659OTOX/',
        writer=writer,
        validate=True,
    )
    adapter.process_file()

    assert len(writer.contents) == 2
    first = json.loads(writer.contents[0])
    assert first['_to'] == 'ontology_terms/NTR_0001118'
    assert first['num_guides'] == 5
    assert first['ci_lower'] == pytest.approx(-0.195688948)
    assert first['ci_upper'] == pytest.approx(-0.099777892)
    assert first['significant'] is True  # CI excludes 0
    assert first['crispr_modality'] == 'interference'


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
        filepath='./samples/crispr_variant_phenotype_sherwood_base.example.csv',
        label='ontology_term',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI7160EKDK/',
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
