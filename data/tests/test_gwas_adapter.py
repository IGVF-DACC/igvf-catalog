import json
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


def test_variants_phenotypes_collection(gwas_files, spy_writer):
    gwas = GWAS(gwas_files['variants_to_ontology'], gwas_files['variants_to_genes'],
                gwas_collection='variants_phenotypes', writer=spy_writer)
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


def test_get_tagged_variants(gwas_files):
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
