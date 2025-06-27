import os

from adapters.gencode_adapter import Gencode
from adapters.gencode_gene_adapter import GencodeGene
from adapters.gencode_protein_adapter import GencodeProtein
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
from adapters.encode_mpra_adapter import EncodeMPRA
from adapters.mgi_human_mouse_ortholog_adapter import MGIHumanMouseOrthologAdapter
from adapters.gvatdb_asb_adapter import ASB_GVATDB
from adapters.AFGR_eqtl_adapter import AFGREQtl
from adapters.AFGR_sqtl_adapter import AFGRSQtl
from adapters.AFGR_caqtl_adapter import AFGRCAQtl
from adapters.dbSNFP_adapter import DbSNFP
from adapters.pQTL_adapter import pQTL
from adapters.biogrid_gene_gene_adapter import GeneGeneBiogrid
from adapters.encode_E2G_CRISPR_adapter import ENCODE2GCRISPR
from adapters.gersbach_E2G_perturb_seq_adapter import GersbachE2GPerturbseq
from adapters.mouse_genomes_project_adapter import MouseGenomesProjectAdapter
from adapters.clingen_variant_disease_adapter import ClinGen
from adapters.gencode_gene_structure_adapter import GencodeStructure
from adapters.VAMP_coding_variant_scores_adapter import VAMPAdapter
from adapters.SEM_motif_adapter import SEMMotif
from adapters.SEM_prediction_adapter import SEMPred
from adapters.BlueSTARR_variant_elements_adapter import BlueSTARRVariantElement
from adapters.file_fileset_adapter import FileFileSet

LABEL_TO_ADAPTER = {
    'gencode_genes': GencodeGene,
    'gencode_transcripts': Gencode,
    'transcribed_to': Gencode,
    'gencode_structure': GencodeStructure,
    'gencode_proteins': GencodeProtein,
    'eqtl': GtexEQtl,
    'eqtl_term': GtexEQtl,
    'AFGR_eqtl': AFGREQtl,
    'AFGR_eqtl_term': AFGREQtl,
    'topld': TopLD,
    'caqtl_ocr': CAQtl,
    'caqtl': CAQtl,
    'AFGR_caqtl_ocr': AFGRCAQtl,
    'AFGR_caqtl': AFGRCAQtl,
    'ccre': CCRE,
    'UniProtKB_sprot': UniprotProtein,
    'UniProtKB_trembl': UniprotProtein,
    'UniProtKB_Translates_To': Uniprot,
    'UniProtKB_Translation_Of': Uniprot,
    'favor': Favor,
    'pQTL': pQTL,
    'allele_specific_binding': ASB,
    'allele_specific_binding_cell': ASB,
    'allele_specific_binding_GVATdb': ASB_GVATDB,
    'gtex_splice_qtl': GtexSQtl,
    'gtex_splice_qtl_term': GtexSQtl,
    'AFGR_sqtl': AFGRSQtl,
    'AFGR_sqtl_term': AFGRSQtl,
    'encode_genomic_element': EncodeElementGeneLink,
    'encode_genomic_element_gene': EncodeElementGeneLink,
    'encode_genomic_element_gene_biosample': EncodeElementGeneLink,
    'encode_genomic_element_gene_treatment_CHEBI': EncodeElementGeneLink,
    'encode_genomic_element_gene_treatment_protein': EncodeElementGeneLink,
    'encode_donor': EncodeElementGeneLink,
    'encode_biosample': EncodeElementGeneLink,
    'encode_mpra_genomic_element': EncodeMPRA,
    'encode_mpra_genomic_element_biosample': EncodeMPRA,
    'encode_genomic_element_crispr': ENCODE2GCRISPR,
    'encode_genomic_element_gene_crispr': ENCODE2GCRISPR,
    'gersbach_genomic_element_gene_perturb_seq': GersbachE2GPerturbseq,
    'encode_element_gene_adapter': EncodeElementGeneLink,
    'file_fileset': FileFileSet,
    'encode_donor': FileFileSet,
    'encode_sample_term': FileFileSet,
    'igvf_donor': FileFileSet,
    'igvf_sample_term': FileFileSet,
    'gaf': GAF,
    'gaf_mouse': GAF,
    'gaf_isoform': GAF,
    'gaf_rna': GAF,
    'gwas_studies': GWAS,
    'gwas_var_phenotypes': GWAS,
    'gwas_var_phenotypes_studies': GWAS,
    'motif': Motif,
    'motif to protein': Motif,
    'coxpresdb': Coxpresdb,
    'pathway': ReactomePathway,
    'genes_pathways': Reactome,
    'parent_pathway_of': Reactome,
    'cellosaurus_terms': Cellosaurus,
    'cellosaurus_relationships': Cellosaurus,
    'drug': PharmGKB,
    'variant_drug': PharmGKB,
    'variant_drug_gene': PharmGKB,
    'disease_gene': Disease,
    'oncotree_terms': Oncotree,
    'oncotree_relationships': Oncotree,
    'gene_term': DepMap,
    'complex': EBIComplex,
    'complex_protein': EBIComplex,
    'complex_term': EBIComplex,
    'protein_protein': ProteinsInteraction,
    'gene_gene_biogrid': GeneGeneBiogrid,
    'mouse_gene_gene_biogrid': GeneGeneBiogrid,
    'genomic_element_mm_genomic_element': HumanMouseElementAdapter,
    'mm_orthologs': MGIHumanMouseOrthologAdapter,
    'coding_variants': DbSNFP,
    'variants_coding_variants': DbSNFP,
    'coding_variants_proteins': DbSNFP,
    'mouse_variant': MouseGenomesProjectAdapter,
    'variant_disease': ClinGen,
    'variant_disease_gene': ClinGen,
    'bluestarr_variant_elements': BlueSTARRVariantElement,
    'vamp_coding_variant_phenotype': VAMPAdapter,
    'ontology': Ontology,
    'SEM_motif': SEMMotif,
    'SEM_motif_protein': SEMMotif,
    'SEM_variant_protein': SEMPred,
}

in_docker = os.environ.get('IN_DOCKER') == 'TRUE'
