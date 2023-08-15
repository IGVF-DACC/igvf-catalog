import os
import argparse

from adapters.gencode_adapter import Gencode
from adapters.gencode_gene_adapter import GencodeGene
from adapters.topld_adapter import TopLD
from adapters.gtex_eqtl_adapter import GtexEQtl
from adapters.encode_caqtl_adapter import CAQtl
from adapters.ccre_adapter import CCRE
from adapters.ontologies_adapter import Ontology
from adapters.uniprot_adapter import Uniprot
from adapters.uniprot_protein_adapter import UniprotProtein
from adapters.favor_adapter import Favor
from adapters.adastra_asb_adapter import ASB
from adapters.gtex_sqtl_adapter import GtexSQtl
from adapters.encode_enhancer_gene_adapter import EncodeEnhancerGeneLink
from adapters.gaf_adapter import GAF
from adapters.gwas_adapter import GWAS
from adapters.motif_adapter import Motif
from adapters.coxpresdb_adapter import Coxpresdb
from adapters.reactome_pathway_adapter import ReactomePathway
from adapters.reactome_adapter import Reactome
from adapters.cellosaurus_ontology_adapter import Cellosaurus
from adapters.pharmgkb_drug_adapter import PharmGKB
from adapters.orphanet_disease_adapter import Disease

from db.arango_db import ArangoDB


ADAPTERS = {
    'gencode_genes': GencodeGene(filepath='./samples/gencode_sample.gtf', gene_alias_file_path='./samples/Homo_sapiens.gene_info.gz'),
    'gencode_transcripts': Gencode(filepath='./samples/gencode_sample.gtf', type='transcript', label='gencode_transcript'),
    'transcribed_to': Gencode(filepath='./samples/gencode_sample.gtf', type='transcribed to', label='transcribed_to'),
    'transcribed_from': Gencode(filepath='./samples/gencode_sample.gtf', type='transcribed from', label='transcribed_from'),
    'eqtl': GtexEQtl(filepath='./samples/qtl_sample.txt', biological_context='brain_amigdala'),
    'topld': TopLD('chr22', './samples/topld_sample.csv', './samples/topld_info_annotation.csv', ancestry='SAS'),
    'caqtl_ocr': CAQtl(filepath='./samples/caqtl-sample.bed', source='PMID:34017130', label='regulatory_region'),
    'caqtl': CAQtl(filepath='./samples/caqtl-sample.bed', source='PMID:34017130', label='encode_caqtl'),
    'ccre': CCRE(filepath='./samples/ccre_example.bed.gz'),
    'ontology_terms': Ontology(type='node'),
    'ontology_relationships': Ontology(type='edge'),
    'UniProtKB_sprot': UniprotProtein(filepath='./samples/uniprot_sprot_human_sample.dat.gz', source='UniProtKB/Swiss-Prot'),
    'UniProtKB_trembl': UniprotProtein(filepath='./samples/uniprot_trembl_human_sample.dat.gz', source='UniProtKB/TrEMBL'),
    'UniProtKB_Translates_To': Uniprot(filepath='./samples/uniprot_sprot_human_sample.dat.gz', type='translates to', label='UniProtKB_Translates_To'),
    'UniProtKB_Translation_Of': Uniprot(filepath='./samples/uniprot_sprot_human_sample.dat.gz', type='translation of', label='UniProtKB_Translation_Of'),
    'favor': Favor(filepath='./samples/favor_sample.vcf'),
    'favor_xy': Favor(filepath='./samples/favor_xy_sample.vcf', chr_x_y='X'),
    'allele_specific_binding': ASB(filepath='./samples/allele_specific_binding', label='asb'),
    'allele_specific_binding_cell': ASB(filepath='./samples/allele_specific_binding', label='asb_cell_ontology'),
    'gtex_splice_qtl': GtexSQtl('./samples/Kidney_Cortex.v8.sqtl_signifpairs.txt.gz', 'Kidney_Cortex'),
    'encode_EpiRaction_regulatory_region': EncodeEnhancerGeneLink('./samples/epiraction_ENCFF712SUP.bed.gz', 'regulatory_region', 'ENCODE_EpiRaction', 'https://www.encodeproject.org/annotations/ENCSR831INH/', 'CL_0000765'),
    'encode_EpiRaction_element_gene': EncodeEnhancerGeneLink('./samples/epiraction_ENCFF712SUP.bed.gz', 'element_gene', 'ENCODE_EpiRaction', 'https://www.encodeproject.org/annotations/ENCSR831INH/', 'CL_0000765'),
    'encode_EpiRaction_element_gene_tissue': EncodeEnhancerGeneLink('./samples/epiraction_ENCFF712SUP.bed.gz', 'biological_context', 'ENCODE_EpiRaction', 'https://www.encodeproject.org/annotations/ENCSR831INH/', 'CL_0000065'),
    'gaf': GAF(filepath='./samples/goa_human_sample.gaf.gz'),
    'gaf_isoform': GAF(filepath='./samples/goa_human_isoform.gaf.gz', gaf_type='human_isoform'),
    'gaf_rna': GAF(filepath='./samples/goa_human_rna.gaf.gz', gaf_type='rna'),
    'gwas_studies': GWAS(variants_to_ontology='../../../Downloads/v2d_igvf.tsv', variants_to_genes='../../../Downloads/v2g_igvf.tsv'),
    'gwas_var_studies': GWAS(variants_to_ontology='../../../Downloads/v2d_igvf.tsv', variants_to_genes='../../../Downloads/v2g_igvf.tsv', gwas_collection='studies_variants'),
    'gwas_var_studies_phenotypes': GWAS(variants_to_ontology='../../../Downloads/v2d_igvf.tsv', variants_to_genes='../../../Downloads/v2g_igvf.tsv', gwas_collection='studies_variants_phenotypes'),
    'motif': Motif(filepath='./samples/motifs', label='motif'),
    'motif to protein': Motif(filepath='./samples/motifs', label='motif_protein_link'),
    'coxpresdb': Coxpresdb('./samples/coxpresdb/1'),
    'pathway': ReactomePathway('./samples/reactome/ReactomePathways.txt'),
    'genes_pathways': Reactome('./samples/reactome/Ensembl2Reactome_All_Levels_sample.txt', 'genes_pathways'),
    'parent_pathway_of': Reactome('./samples/reactome/ReactomePathwaysRelation.txt', 'parent_pathway_of'),
    'child_pathway_of': Reactome('./samples/reactome/ReactomePathwaysRelation.txt', 'child_pathway_of'),
    'cellosaurus_terms': Cellosaurus('./samples/cellosaurus_example.obo.txt', type='node'),
    'cellosaurus_relationships': Cellosaurus('./samples/cellosaurus_example.obo.txt', type='edge'),
    'drug': PharmGKB('./samples/pharmGKB', type='node'),
    'variant_drug': PharmGKB('./samples/pharmGKB', type='edge'),
    'disease_gene': Disease('./samples/orphanet_example.xml'),
}

parser = argparse.ArgumentParser(
    prog='IGVF Catalog Sample Data Loader',
    description='Loads sample data into a local ArangoDB instance'
)

parser.add_argument('--dry-run', action='store_true',
                    help='Dry Run / Print ArangoDB Statements')
parser.add_argument('-a', '--adapter', nargs='*',
                    help='Loads the sampe adata for an adapter', choices=ADAPTERS.keys())
parser.add_argument('-i', '--create-indexes', action='store_true',
                    help='Creates ArangoDB indexes for a given adapter')

args = parser.parse_args()
dry_run = args.dry_run
create_indexes = args.create_indexes
adapters = args.adapter or ADAPTERS.keys()

if not dry_run:
    ArangoDB().setup_dev()

import_cmds = []

for a in adapters:
    adapter = ADAPTERS[a]

    if create_indexes:
        adapter.create_indexes()
        adapter.create_aliases()
    else:
        adapter.write_file()

        if getattr(adapter, 'SKIP_BIOCYPHER', None):
            exit(0)

        import_cmds.append(adapter.arangodb())

        if adapter.has_indexes():
            print(
                '{} needs indexes. After data loading, please run: python3 dev_setup.py -i -a {}'.format(a, a))

import_cmds = sum(import_cmds, [])  # [[cmd1], [cmd2]] => [cmd1, cmd2]

for cmd in import_cmds:
    if dry_run:
        print(cmd)
    else:
        os.system(cmd)
