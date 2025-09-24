import json
from this import d
import pytest
from adapters.gwas_adapter import GWAS
from adapters.writer import SpyWriter


@pytest.fixture
def gwas_files():
    return {
        'variants_to_ontology': './samples/gwas_v2d_igvf_sample.tsv',
        'variants_to_genes': './samples/gwas_v2g_igvf_sample.tsv'
    }


@pytest.fixture
def spy_writer():
    return SpyWriter()


def test_variants_phenotypes_collection(gwas_files, spy_writer, mocker):
    mocker.patch('adapters.gwas_adapter.build_variant_id',
                 return_value='fake_variant_id')
    gwas = GWAS(gwas_files['variants_to_ontology'], gwas_files['variants_to_genes'],
                gwas_collection='variants_phenotypes', writer=spy_writer, validate=True)
    gwas.process_file()

    assert len(spy_writer.contents) > 0
    for item in spy_writer.contents:
        if item.startswith('{'):
            data = json.loads(item)
            assert '_from' in data
            assert '_to' in data
            assert '_key' in data
            assert 'source' in data
            assert 'name' in data


def test_get_tagged_variants(gwas_files, mocker):
    mocker.patch('adapters.gwas_adapter.build_variant_id',
                 return_value='fake_variant_id')
    gwas = GWAS(gwas_files['variants_to_ontology'], gwas_files['variants_to_genes'],
                gwas_collection='variants_phenotypes_studies')
    tagged_variants = gwas.get_tagged_variants()

    assert len(tagged_variants) > 0
    for key, variants in tagged_variants.items():
        assert isinstance(variants, list)
        for variant in variants:
            assert 'tag_chrom' in variant
            assert 'tag_pos' in variant
            assert 'tag_ref' in variant
            assert 'tag_alt' in variant


def test_get_genes_from_variant_to_genes_file(gwas_files):
    gwas = GWAS(gwas_files['variants_to_ontology'], gwas_files['variants_to_genes'],
                gwas_collection='variants_phenotypes_studies')
    genes = gwas.get_genes_from_variant_to_genes_file()

    assert len(genes) > 0
    for variant_id, gene_data in genes.items():
        assert isinstance(gene_data, dict)
        for gene_id, gene_info in gene_data.items():
            assert gene_id.startswith('genes/')
            assert isinstance(gene_info, list)
            for info in gene_info:
                assert 'feature' in info
                assert 'type_id' in info
                assert 'source_id' in info


def test_load_ontology_name_mapping(gwas_files):
    gwas = GWAS(gwas_files['variants_to_ontology'], gwas_files['variants_to_genes'],
                gwas_collection='variants_phenotypes_studies')
    gwas.load_ontology_name_mapping()

    assert hasattr(gwas, 'ontology_name_mapping')
    assert len(gwas.ontology_name_mapping) > 0
    for ontology_id, ontology_name in gwas.ontology_name_mapping.items():
        assert isinstance(ontology_id, str)
        assert isinstance(ontology_name, str)


def test_gwas_studies(gwas_files, spy_writer, mocker):
    mocker.patch('adapters.gwas_adapter.build_variant_id',
                 return_value='fake_variant_id')
    gwas = GWAS(gwas_files['variants_to_ontology'], gwas_files['variants_to_genes'],
                gwas_collection='studies', writer=spy_writer, validate=True)
    gwas.process_file()

    assert len(spy_writer.contents) > 0
    for item in spy_writer.contents:
        if item.startswith('{'):
            data = json.loads(item)
            assert '_key' in data
            assert 'name' in data
            assert 'ancestry_initial' in data
            assert 'ancestry_replication' in data
            assert 'n_cases' in data
            assert 'n_initial' in data
            assert 'n_replication' in data
            assert 'pmid' in data
            assert 'pub_author' in data
            assert 'pub_date' in data


def test_gwas_invalid_collection(gwas_files, spy_writer):
    with pytest.raises(ValueError):
        GWAS(gwas_files['variants_to_ontology'], gwas_files['variants_to_genes'],
             gwas_collection='invalid_collection', writer=spy_writer, validate=True)

# test gwas_collection == 'variants_phenotypes_studies' for adapter


def test_gwas_variants_phenotypes_studies(gwas_files, spy_writer, mocker):
    mocker.patch('adapters.gwas_adapter.build_variant_id',
                 return_value='fake_variant_id')
    gwas = GWAS(gwas_files['variants_to_ontology'], gwas_files['variants_to_genes'],
                gwas_collection='variants_phenotypes_studies', writer=spy_writer, validate=True)
    gwas.process_file()

    assert len(spy_writer.contents) > 0
    for item in spy_writer.contents:
        if item.startswith('{'):
            data = json.loads(item)
            assert '_key' in data
            assert 'lead_chrom' in data


def test_gwas_invalid_doc(gwas_files, spy_writer, mocker):
    mocker.patch('adapters.gwas_adapter.build_variant_id',
                 return_value='fake_variant_id')
    gwas = GWAS(gwas_files['variants_to_ontology'], gwas_files['variants_to_genes'],
                gwas_collection='variants_phenotypes_studies', writer=spy_writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        gwas.validate_doc(invalid_doc)
