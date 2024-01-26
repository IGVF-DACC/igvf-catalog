import os

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
from adapters.encode_element_gene_adapter import EncodeElementGeneLink
from adapters.gaf_adapter import GAF
from adapters.gwas_adapter import GWAS
from adapters.motif_adapter import Motif
from adapters.coxpresdb_adapter import Coxpresdb
from adapters.reactome_pathway_adapter import ReactomePathway
from adapters.reactome_adapter import Reactome
from adapters.cellosaurus_ontology_adapter import Cellosaurus
from adapters.pharmgkb_drug_adapter import PharmGKB
from adapters.orphanet_disease_adapter import Disease
from adapters.oncotree_adapter import Oncotree
from adapters.depmap_adapter import DepMap
from adapters.ebi_complex_adapter import EBIComplex
from adapters.proteins_interaction_adapter import ProteinsInteraction
from adapters.human_mouse_element_adapter import HumanMouseElementAdapter

ADAPTERS = {
    'gencode_genes': GencodeGene(filepath='./samples/gencode_sample.gtf', gene_alias_file_path='./samples/Homo_sapiens.gene_info.gz'),
    'gencode_transcripts': Gencode(filepath='./samples/gencode_sample.gtf', label='gencode_transcript'),
    'transcribed_to': Gencode(filepath='./samples/gencode_sample.gtf', label='transcribed_to'),
    'transcribed_from': Gencode(filepath='./samples/gencode_sample.gtf', label='transcribed_from'),
    'eqtl': GtexEQtl(filepath='./samples/GTEx_eQTL', label='GTEx_eqtl'),
    'eqtl_term': GtexEQtl(filepath='./samples/GTEx_eQTL', label='GTEx_eqtl_term'),
    'topld': TopLD('chr22', './samples/topld_sample.csv', './samples/topld_info_annotation.csv', ancestry='SAS'),
    'caqtl_ocr': CAQtl(filepath='./samples/caqtl-sample.bed', source='PMID:34017130', label='regulatory_region'),
    'caqtl': CAQtl(filepath='./samples/caqtl-sample.bed', source='PMID:34017130', label='encode_caqtl'),
    'ccre': CCRE(filepath='./samples/ccre_example.bed.gz'),
    'UniProtKB_sprot': UniprotProtein(filepath='./samples/uniprot_sprot_human_sample.dat.gz', source='UniProtKB/Swiss-Prot'),
    'UniProtKB_trembl': UniprotProtein(filepath='./samples/uniprot_trembl_human_sample.dat.gz', source='UniProtKB/TrEMBL'),
    'UniProtKB_Translates_To': Uniprot(filepath='./samples/uniprot_sprot_human_sample.dat.gz', label='UniProtKB_Translates_To', source='UniProtKB/Swiss-Prot'),
    'UniProtKB_Translation_Of': Uniprot(filepath='./samples/uniprot_sprot_human_sample.dat.gz', label='UniProtKB_Translation_Of', source='UniProtKB/Swiss-Prot'),
    'favor': Favor(filepath='./samples/favor_sample.vcf'),
    'favor_xy': Favor(filepath='./samples/favor_xy_sample.vcf', chr_x_y='X'),
    'allele_specific_binding': ASB(filepath='./samples/allele_specific_binding', label='asb'),
    'allele_specific_binding_cell': ASB(filepath='./samples/allele_specific_binding', label='asb_cell_ontology'),
    'gtex_splice_qtl': GtexSQtl('./samples/GTEx_sQTL', label='GTEx_splice_QTL'),
    'gtex_splice_qtl_term': GtexSQtl('./samples/GTEx_sQTL', label='GTEx_splice_QTL_term'),
    'encode_regulatory_region': EncodeElementGeneLink('./samples/epiraction_ENCFF712SUP.bed.gz', 'regulatory_region', 'ENCODE_EpiRaction', 'https://www.encodeproject.org/files/ENCFF712SUP/', 'CL_0000765'),
    'encode_regulatory_region_gene': EncodeElementGeneLink('./samples/epiraction_ENCFF712SUP.bed.gz', 'regulatory_region_gene', 'ENCODE_EpiRaction', 'https://www.encodeproject.org/files/ENCFF712SUP/', 'CL_0000765'),
    'encode_regulatory_region_gene_biosample': EncodeElementGeneLink('./samples/E2G_ENCFF617FJH.bed.gz', 'regulatory_region_gene_biosample', 'ENCODE-E2G-DNaseOnly', 'https://www.encodeproject.org/files/ENCFF617FJH/', 'EFO_0001203'),
    'encode_regulatory_region_gene_treatment_CHEBI': EncodeElementGeneLink('./samples/E2G_ENCFF617FJH.bed.gz', 'regulatory_region_gene_biosample_treatment_CHEBI', 'ENCODE-E2G-DNaseOnly', 'https://www.encodeproject.org/files/ENCFF617FJH/', 'EFO_0001203'),
    'encode_regulatory_region_gene_treatment_protein': EncodeElementGeneLink('./samples/E2G_ENCFF728HSS.bed.gz', 'regulatory_region_gene_biosample_treatment_protein', 'ENCODE-E2G-DNaseOnly', 'https://www.encodeproject.org/files/ENCFF728HSS/', 'NTR_0000502'),
    'encode_donor': EncodeElementGeneLink('./samples/E2G_ENCFF617FJH.bed.gz', 'donor', 'ENCODE-E2G-DNaseOnly', 'https://www.encodeproject.org/files/ENCFF617FJH/', 'EFO_0001203'),
    'encode_regulatory_region_gene_donor': EncodeElementGeneLink('./samples/E2G_ENCFF617FJH.bed.gz', 'regulatory_region_gene_biosample_donor', 'ENCODE-E2G-DNaseOnly', 'https://www.encodeproject.org/files/ENCFF617FJH/', 'EFO_0001203'),
    'gaf': GAF(filepath='./samples/goa_human_sample.gaf.gz'),
    'gaf_isoform': GAF(filepath='./samples/goa_human_isoform.gaf.gz', gaf_type='human_isoform'),
    'gaf_rna': GAF(filepath='./samples/goa_human_rna.gaf.gz', gaf_type='rna'),
    'gwas_studies': GWAS(variants_to_ontology='./samples/gwas_v2d_igvf_sample.tsv', variants_to_genes='./samples/gwas_v2g_igvf_sample.tsv'),
    'gwas_var_studies': GWAS(variants_to_ontology='./samples/gwas_v2d_igvf_sample.tsv', variants_to_genes='./samples/gwas_v2g_igvf_sample.tsv', gwas_collection='studies_variants'),
    'gwas_var_studies_phenotypes': GWAS(variants_to_ontology='./samples/gwas_v2d_igvf_sample.tsv', variants_to_genes='./samples/gwas_v2g_igvf_sample.tsv', gwas_collection='studies_variants_phenotypes'),
    'motif': Motif(filepath='./samples/motifs', label='motif'),
    'motif to protein': Motif(filepath='./samples/motifs', label='motif_protein_link'),
    'coxpresdb': Coxpresdb('./samples/coxpresdb/1'),
    'pathway': ReactomePathway('./samples/reactome/ReactomePathways.txt'),
    'genes_pathways': Reactome('./samples/reactome/Ensembl2Reactome_All_Levels_sample.txt', 'genes_pathways'),
    'parent_pathway_of': Reactome('./samples/reactome/ReactomePathwaysRelation.txt', 'parent_pathway_of'),
    'child_pathway_of': Reactome('./samples/reactome/ReactomePathwaysRelation.txt', 'child_pathway_of'),
    'cellosaurus_terms': Cellosaurus('./samples/cellosaurus_example.obo.txt', type='node'),
    'cellosaurus_relationships': Cellosaurus('./samples/cellosaurus_example.obo.txt', type='edge'),
    'drug': PharmGKB('./samples/pharmGKB', label='drug'),
    'variant_drug': PharmGKB('./samples/pharmGKB', label='variant_drug'),
    'variant_drug_gene': PharmGKB('./samples/pharmGKB', label='variant_drug_gene'),
    'disease_gene': Disease('./samples/orphanet_example.xml'),
    'oncotree_terms': Oncotree(type='node'),
    'oncotree_relationships': Oncotree(type='edge'),
    'gene_term': DepMap('./samples/DepMap/CRISPRGeneDependency_transposed_example.csv', type='edge', label='gene_term'),
    'complex': EBIComplex('./samples/EBI_complex_example.tsv', label='complex'),
    'complex_protein': EBIComplex('./samples/EBI_complex_example.tsv', label='complex_protein'),
    'complex_term': EBIComplex('./samples/EBI_complex_example.tsv', label='complex_term'),
    'protein_protein': ProteinsInteraction('./samples/merged_PPI.UniProt.collapsed.example.tsv', label='protein_protein'),
    'regulatory_region_mm_regulatory_region': HumanMouseElementAdapter('./samples/element_mapping_example.txt.gz', label='regulatory_region_mm_regulatory_region')
}

in_docker = os.environ.get('IN_DOCKER') == 'TRUE'

if not in_docker:
    for ontology in Ontology.ONTOLOGIES.keys():
        ADAPTERS[ontology] = Ontology(ontology=ontology)
