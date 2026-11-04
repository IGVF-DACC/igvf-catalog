import json
import math
from unittest.mock import patch

import pytest

from adapters.CRISPR_variant_phenotype_adapter import CRISPRVariantPhenotype
from adapters.ontology_term_validator import OntologyTermValidator
from adapters.writer import SpyWriter

PRIME_PATH = './tests/fixtures/IGVFFI2014OOZP_crispr_variant_phenotype_sherwood_prime.example.csv'
CRISPRI_PATH = './tests/fixtures/IGVFFI9726GFTC_crispr_variant_phenotype_sherwood_crispri.example.csv'
ABE_PATH = './tests/fixtures/IGVFFI1678CDBR_crispr_variant_phenotype_sherwood_abe.example.csv'

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
}


@pytest.fixture
def mock_file_fileset():
    with patch(
        'adapters.CRISPR_variant_phenotype_adapter.get_file_fileset_by_accession_in_arangodb'
    ) as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'method': 'CRISPR screen',
            'class': 'observed data',
            'perturbation': 'CRISPR prime editing',
            'simple_sample_summaries': ['Homo sapiens HepG2 cell line'],
            'samples': ['ontology_terms/EFO_0001187'],
            'treatments_term_ids': None,
        }
        yield mock_get_file_fileset


@pytest.fixture
def mock_ontology_term_validator():
    with patch('adapters.CRISPR_variant_phenotype_adapter.OntologyTermValidator') as MockValidator:
        MockValidator.normalize_term_key = staticmethod(
            OntologyTermValidator.normalize_term_key)
        mock_validator = MockValidator.return_value
        mock_validator.validate.return_value = True
        mock_validator.ensure.return_value = True
        yield mock_validator


def _mock_load_variant(variant_id, **kwargs):
    if variant_id.startswith('NC_') and len(variant_id.split(':')) == 4:
        _chr, pos, ref, alt = variant_id.split(':')
        spdi = variant_id
        pos = int(pos)
    elif len(variant_id.split('-')) == 4:
        _chrom, pos, ref, alt = variant_id.split('-')
        pos = int(pos) - 1
        spdi = f'NC_MOCK:{pos}:{ref}:{alt}'
    else:
        return None, {'variant_id': variant_id, 'reason': 'unrecognized'}

    variant = dict(MOCK_VARIANT)
    variant['_key'] = spdi
    variant['name'] = spdi
    variant['spdi'] = spdi
    variant['ref'] = ref
    variant['alt'] = alt
    variant['pos'] = pos
    return variant, None


def test_unsupported_accession(mock_file_fileset, tmp_path):
    sample = tmp_path / 'IGVFFI0000AAAA_unsupported.csv'
    sample.write_text('variant_id\n')
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Unsupported file accession'):
        CRISPRVariantPhenotype(
            filepath=str(sample),
            label='variant',
            writer=writer,
        )


def test_dropped_accessions(mock_file_fileset, tmp_path):
    writer = SpyWriter()
    for accession in ('IGVFFI7160EKDK', 'IGVFFI7659OTOX', 'IGVFFI7206JILF'):
        sample = tmp_path / f'{accession}_dropped.csv'
        sample.write_text('variant_id\n')
        with pytest.raises(ValueError, match='Unsupported file accession'):
            CRISPRVariantPhenotype(
                filepath=str(sample),
                label='variant',
                writer=writer,
            )


def test_invalid_label(mock_file_fileset):
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label'):
        CRISPRVariantPhenotype(
            filepath=PRIME_PATH,
            label='invalid_label',
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
    mock_file_fileset.return_value['perturbation'] = 'CRISPR prime editing'
    writer = SpyWriter()
    adapter = CRISPRVariantPhenotype(
        filepath=PRIME_PATH,
        label='variant',
        writer=writer,
        validate=True,
    )
    adapter.process_file()

    assert len(writer.contents) == 2
    first = json.loads(writer.contents[0])
    assert first['files_filesets'] == 'files_filesets/IGVFFI2014OOZP'
    assert first['source'] == 'IGVF'
    assert first['source_url'] == 'https://data.igvf.org/tabular-files/IGVFFI2014OOZP/'
    assert first['spdi'].startswith('NC_')


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
def test_variant_phenotype_sherwood_prime(mock_load, mock_bulk, mock_file_fileset, mock_ontology_term_validator):
    mock_file_fileset.return_value['perturbation'] = 'CRISPR prime editing'
    writer = SpyWriter()
    adapter = CRISPRVariantPhenotype(
        filepath=PRIME_PATH,
        label='variant_phenotype',
        writer=writer,
        validate=True,
    )
    adapter.process_file()

    assert len(writer.contents) == 2
    first = json.loads(writer.contents[0])
    assert first['perturbation'] == 'CRISPR prime editing'
    assert first['significant'] is True
    assert first['num_guides'] == 1
    assert first['p_value_adj'] is None
    assert first['neg_log10_pvalue_adj'] is None
    assert first['_key'] == (
        'NC_000019.10:11105541:CAGC:GCTG_NTR_0001118_IGVFFI2014OOZP'
    )


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
        filepath=PRIME_PATH,
        label='ontology_term',
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
    assert term['class'] == 'observed data'
    assert term['method'] == 'CRISPR screen'
    # NTR phenotype terms are shared vocabulary, not tied to a single dataset. See DSERV-1466.
    assert term['files_filesets'] is None
    mock_get.assert_called_once()


def test_to_loadable_variant_id_converts_hg38_ids():
    assert CRISPRVariantPhenotype._to_loadable_variant_id(
        '19_11091518_hg38_GC_G'
    ) == '19-11091518-GC-G'
    assert CRISPRVariantPhenotype._to_loadable_variant_id(
        '1_25253604_hg38_G_A'
    ) == '1-25253604-G-A'
    assert CRISPRVariantPhenotype._to_loadable_variant_id(
        'NC_000019.10:11105541:CAGC:GCTG'
    ) == 'NC_000019.10:11105541:CAGC:GCTG'


@patch(
    'adapters.CRISPR_variant_phenotype_adapter.bulk_check_variants_in_arangodb',
    return_value=set(),
)
@patch(
    'adapters.CRISPR_variant_phenotype_adapter.load_variant',
    side_effect=_mock_load_variant,
)
def test_variant_sherwood_crispri(mock_load, mock_bulk, mock_file_fileset):
    mock_file_fileset.return_value['perturbation'] = 'CRISPR interference'
    writer = SpyWriter()
    adapter = CRISPRVariantPhenotype(
        filepath=CRISPRI_PATH,
        label='variant',
        writer=writer,
        validate=True,
    )
    adapter.process_file()

    assert len(writer.contents) == 2
    first = json.loads(writer.contents[0])
    assert first['files_filesets'] == 'files_filesets/IGVFFI9726GFTC'
    assert first['source'] == 'IGVF'
    assert first['spdi'] == 'NC_MOCK:11091517:GC:G'
    mock_load.assert_any_call('19-11091518-GC-G')
    loaded_ids = [call.args[0] for call in mock_load.call_args_list]
    assert 'LDLR' not in loaded_ids


@patch(
    'adapters.CRISPR_variant_phenotype_adapter.bulk_check_variants_in_arangodb',
    return_value={
        'NC_MOCK:11091517:GC:G',
        'NC_MOCK:26915517:G:A',
    },
)
@patch(
    'adapters.CRISPR_variant_phenotype_adapter.load_variant',
    side_effect=_mock_load_variant,
)
def test_variant_phenotype_sherwood_crispri(mock_load, mock_bulk, mock_file_fileset, mock_ontology_term_validator):
    mock_file_fileset.return_value['perturbation'] = 'CRISPR interference'
    writer = SpyWriter()
    adapter = CRISPRVariantPhenotype(
        filepath=CRISPRI_PATH,
        label='variant_phenotype',
        writer=writer,
        validate=True,
    )
    adapter.process_file()

    assert len(writer.contents) == 2
    docs = [json.loads(line) for line in writer.contents]
    by_key = {doc['_key']: doc for doc in docs}
    sig = by_key['NC_MOCK:11091517:GC:G_NTR_0001118_IGVFFI9726GFTC']
    nonsig = by_key['NC_MOCK:26915517:G:A_NTR_0001118_IGVFFI9726GFTC']
    assert sig['perturbation'] == 'CRISPR interference'
    assert sig['significant'] is True
    assert sig['num_guides'] == 5
    assert sig['effect_size'] == pytest.approx(-0.14773342)
    assert sig['p_value_adj'] is None
    assert sig['neg_log10_pvalue_adj'] is None
    assert nonsig['significant'] is False


@patch(
    'adapters.CRISPR_variant_phenotype_adapter.bulk_check_variants_in_arangodb',
    return_value=set(),
)
@patch(
    'adapters.CRISPR_variant_phenotype_adapter.load_variant',
    side_effect=_mock_load_variant,
)
def test_variant_sherwood_abe(mock_load, mock_bulk, mock_file_fileset):
    mock_file_fileset.return_value['perturbation'] = 'CRISPR base editing'
    writer = SpyWriter()
    adapter = CRISPRVariantPhenotype(
        filepath=ABE_PATH,
        label='variant',
        writer=writer,
        validate=True,
    )
    adapter.process_file()

    assert len(writer.contents) == 2
    first = json.loads(writer.contents[0])
    assert first['files_filesets'] == 'files_filesets/IGVFFI1678CDBR'
    mock_load.assert_any_call('1-25395599-A-G')
    loaded_ids = [call.args[0] for call in mock_load.call_args_list]
    assert 'ABCA1_1_donorT' not in loaded_ids


@patch(
    'adapters.CRISPR_variant_phenotype_adapter.bulk_check_variants_in_arangodb',
    return_value={
        'NC_MOCK:25395598:A:G',
        'NC_MOCK:25253603:G:A',
    },
)
@patch(
    'adapters.CRISPR_variant_phenotype_adapter.load_variant',
    side_effect=_mock_load_variant,
)
def test_variant_phenotype_sherwood_abe(mock_load, mock_bulk, mock_file_fileset, mock_ontology_term_validator):
    mock_file_fileset.return_value['perturbation'] = 'CRISPR base editing'
    writer = SpyWriter()
    adapter = CRISPRVariantPhenotype(
        filepath=ABE_PATH,
        label='variant_phenotype',
        writer=writer,
        validate=True,
    )
    adapter.process_file()

    assert len(writer.contents) == 2
    docs = [json.loads(line) for line in writer.contents]
    by_key = {doc['_key']: doc for doc in docs}
    sig = by_key['NC_MOCK:25395598:A:G_NTR_0001118_IGVFFI1678CDBR']
    nonsig = by_key['NC_MOCK:25253603:G:A_NTR_0001118_IGVFFI1678CDBR']
    assert sig['perturbation'] == 'CRISPR base editing'
    assert sig['significant'] is True
    assert sig['num_guides'] is None
    assert sig['edit_rate_mean'] == pytest.approx(0.515483206)
    assert sig['effect_size'] == pytest.approx(1.2640903)
    assert sig['z_score'] == pytest.approx(3.0179524)
    assert sig['effect_size_ci95_lower'] == pytest.approx(
        1.2640903 - 1.96 * 0.41885692
    )
    assert sig['effect_size_ci95_upper'] == pytest.approx(
        1.2640903 + 1.96 * 0.41885692
    )
    assert sig['p_value_adj'] == pytest.approx(0.038130911)
    assert sig['neg_log10_pvalue_adj'] == pytest.approx(1.418722818)
    assert nonsig['significant'] is False
    assert nonsig['p_value_adj'] == pytest.approx(0.866342209)


@patch('adapters.CRISPR_variant_phenotype_adapter.bulk_check_variants_in_arangodb', return_value=set())
@patch('adapters.CRISPR_variant_phenotype_adapter.load_variant', side_effect=_mock_load_variant)
def test_embedded_id_preserves_hg38_coordinates(
    mock_load, mock_bulk, mock_file_fileset, tmp_path, monkeypatch
):
    writer = SpyWriter()
    adapter = CRISPRVariantPhenotype(
        filepath=CRISPRI_PATH,
        label='variant',
        writer=writer,
    )
    monkeypatch.chdir(tmp_path)
    embedded = '19_11116804_hg38_A_19:11227480:A:C'
    adapter._process_chunk([
        {'target_id': embedded},
        {'target_id': '19_11091518_hg38_GC_G'},
    ])

    assert [call.args[0] for call in mock_load.call_args_list] == [
        '19-11116804-A-C', '19-11091518-GC-G',
    ]
    assert len(writer.contents) == 2
    assert not (tmp_path / 'skipped_variants.jsonl').exists()


def test_trailing_indel_coordinates():
    assert CRISPRVariantPhenotype._to_loadable_variant_id(
        '12_124877799_hg38_CAG_12:125362345:CAG:C'
    ) == '12-124877799-CAG-C'


@pytest.mark.parametrize('suffix', ['19:11227480:A', '19:bad:A:C', '19:0:A:C'])
def test_invalid_trailing_coordinates(suffix):
    with pytest.raises(ValueError, match='Invalid trailing'):
        CRISPRVariantPhenotype._to_loadable_variant_id(
            f'19_11116804_hg38_A_{suffix}'
        )


CHRX_MAGECK_ROWS = '''variant,num,neg|score,neg|p-value,neg|fdr,neg|rank,neg|goodsgrna,neg|lfc,pos|score,pos|p-value,pos|fdr,pos|rank,pos|goodsgrna,pos|lfc
NC_000023.11:56802295:T:C,5,1.0602e-12,2.219e-06,0.001238,1,4,-1.6533,0.94703,0.85192,1.0,1675,0,-1.6533
NC_000023.11:134660265:A:G,5,1.0,1.0,1.0,2127,0,1.4633,9.1505e-12,2.219e-06,9e-05,2,5,1.4633
NC_000023.11:110639463:G:A,5,0.010587,0.082632,0.646847,272,2,0.073106,0.21022,0.20397,0.601873,755,2,0.073106
NC_000023.11:57377840:T:C,6,2.6262e-08,2.219e-06,0.001238,2,6,-1.4426,1.0,1.0,1.0,2127,0,-1.4426
NC_000023.11:48791984:G:A,6,2.3724e-06,1.9971e-05,0.00495,8,5,-0.98956,0.80078,0.73248,1.0,1388,1,-0.98956
nt0,1,0.61809,0.7305,1.0,1313,0,0.21985,0.38191,0.2695,0.710712,931,1,0.21985
GATA1,5,0.21098,0.57584,1.0,864,3,-0.46243,0.90123,0.79537,1.0,1538,1,-0.46243
'''

CHRX_VARIANT_LIST_ROWS = '''element_id,genome_ref,chromosome,element_start,element_end,ref_allele,alt_allele,type,rsid
NC_000023.11:56802295:T:C,GRCh38,NC_000023.11,56802295,56802295,T,C,variant-concordant,rs1317882
NC_000023.11:134660265:A:G,GRCh38,NC_000023.11,134660265,134660265,A,G,variant-concordant,rs59156614
NC_000023.11:110639463:G:A,GRCh38,NC_000023.11,110639463,110639463,G,A,variant-concordant,rs5942662
NC_000023.11:57377840:T:C,GRCh38,NC_000023.11,57377840,57377840,T,C,variant-nonconcordant,rs5914997
NC_000023.11:48791984:G:A,GRCh38,NC_000023.11,48791984,48791984,G,A,clinvar,
'''

CHRX_CONCORDANT = {
    'NC_000023.11:56802295:T:C',
    'NC_000023.11:134660265:A:G',
    'NC_000023.11:110639463:G:A',
}


@pytest.fixture
def chrx_inputs(tmp_path):
    (tmp_path / 'IGVFFI4039BVDA.csv').write_text(CHRX_MAGECK_ROWS)
    (tmp_path / 'IGVFFI7806CLOH.csv').write_text(CHRX_VARIANT_LIST_ROWS)
    return tmp_path / 'IGVFFI4039BVDA.csv'


@patch('adapters.CRISPR_variant_phenotype_adapter.bulk_check_variants_in_arangodb', return_value=set())
@patch('adapters.CRISPR_variant_phenotype_adapter.load_variant', side_effect=_mock_load_variant)
def test_variant_chrx_loads_only_concordant(mock_load, mock_bulk, mock_file_fileset, chrx_inputs):
    mock_file_fileset.return_value['perturbation'] = 'CRISPR base editing'
    writer = SpyWriter()
    adapter = CRISPRVariantPhenotype(
        filepath=str(chrx_inputs),
        label='variant',
        writer=writer,
        validate=True,
    )
    adapter.process_file()

    loaded_ids = {call.args[0] for call in mock_load.call_args_list}
    assert loaded_ids == CHRX_CONCORDANT
    docs = [json.loads(line) for line in writer.contents]
    assert {doc['spdi'] for doc in docs} == CHRX_CONCORDANT
    assert all(doc['files_filesets'] ==
               'files_filesets/IGVFFI4039BVDA' for doc in docs)


@patch('adapters.CRISPR_variant_phenotype_adapter.bulk_check_variants_in_arangodb', return_value=CHRX_CONCORDANT)
@patch('adapters.CRISPR_variant_phenotype_adapter.load_variant', side_effect=_mock_load_variant)
def test_variant_phenotype_chrx_mageck(mock_load, mock_bulk, mock_file_fileset, mock_ontology_term_validator, chrx_inputs):
    mock_file_fileset.return_value['perturbation'] = 'CRISPR base editing'
    mock_file_fileset.return_value['simple_sample_summaries'] = [
        'human HUDEP-2 cell line from donor(s) IGVFDO0965QSBA']
    writer = SpyWriter()
    adapter = CRISPRVariantPhenotype(
        filepath=str(chrx_inputs),
        label='variant_phenotype',
        writer=writer,
        validate=True,
    )
    adapter.process_file()

    mock_ontology_term_validator.ensure.assert_called_once_with('GO_0008283')
    docs = {json.loads(line)['_key']: json.loads(line)
            for line in writer.contents}
    assert len(docs) == 3

    depleted = docs['NC_000023.11:56802295:T:C_GO_0008283_IGVFFI4039BVDA']
    assert depleted['_to'] == 'ontology_terms/GO_0008283'
    assert depleted['effect_size'] == pytest.approx(-1.6533)
    assert depleted['p_value'] == pytest.approx(2.219e-06)
    assert depleted['p_value_adj'] == pytest.approx(0.001238)
    assert depleted['neg_log10_pvalue_adj'] == pytest.approx(
        -math.log10(0.001238))
    assert depleted['significant'] is True
    assert depleted['num_guides'] == 5
    assert depleted['z_score'] is None
    assert depleted['effect_size_ci95_lower'] is None
    assert depleted['effect_size_ci95_upper'] is None
    assert depleted['edit_rate_mean'] is None
    assert depleted['perturbation'] == 'CRISPR base editing'

    enriched = docs['NC_000023.11:134660265:A:G_GO_0008283_IGVFFI4039BVDA']
    assert enriched['effect_size'] == pytest.approx(1.4633)
    assert enriched['p_value'] == pytest.approx(2.219e-06)
    assert enriched['p_value_adj'] == pytest.approx(9e-05)
    assert enriched['significant'] is True

    # Positive fold change uses the pos| test even though neg| has the smaller p.
    nonsig = docs['NC_000023.11:110639463:G:A_GO_0008283_IGVFFI4039BVDA']
    assert nonsig['p_value'] == pytest.approx(0.20397)
    assert nonsig['p_value_adj'] == pytest.approx(0.601873)
    assert nonsig['significant'] is False


def test_chrx_missing_variant_list(mock_file_fileset, tmp_path):
    sample = tmp_path / 'IGVFFI4039BVDA.csv'
    sample.write_text(CHRX_MAGECK_ROWS)
    with pytest.raises(FileNotFoundError, match='IGVFFI7806CLOH'):
        CRISPRVariantPhenotype(
            filepath=str(sample),
            label='variant',
            writer=SpyWriter(),
        )


def test_chrx_ontology_term_skips_variant_list(mock_file_fileset, tmp_path):
    sample = tmp_path / 'IGVFFI4039BVDA.csv'
    sample.write_text(CHRX_MAGECK_ROWS)
    writer = SpyWriter()
    adapter = CRISPRVariantPhenotype(
        filepath=str(sample),
        label='ontology_term',
        writer=writer,
    )
    adapter.process_file()
    assert writer.contents == []
