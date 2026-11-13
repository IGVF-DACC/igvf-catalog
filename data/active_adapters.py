import os

from adapters.gencode_adapter import Gencode
from adapters.gencode_gene_adapter import GencodeGene
from adapters.gencode_protein_adapter import GencodeProtein
from adapters.topld_adapter import TopLD
from adapters.encode_caqtl_adapter import CAQtl
from adapters.ccre_adapter import CCRE
from adapters.ontologies_adapter import Ontology
from adapters.favor_adapter import Favor
from adapters.adastra_asb_adapter import ASB
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
from adapters.mpra_adapter import MPRAAdapter
from adapters.mgi_human_mouse_ortholog_adapter import MGIHumanMouseOrthologAdapter
from adapters.gvatdb_asb_adapter import ASB_GVATDB
from adapters.AFGR_eqtl_adapter import AFGREQtl
from adapters.AFGR_sqtl_adapter import AFGRSQtl
from adapters.AFGR_caqtl_adapter import AFGRCAQtl
from adapters.dbNSFP_adapter import DbNSFP
from adapters.pQTL_adapter import pQTL
from adapters.biogrid_gene_gene_adapter import GeneGeneBiogrid
from adapters.CRISPR_element_gene_ENCODE_adapter import CRISPRElementGeneENCODE
from adapters.CRISPR_element_gene_IGVF_adapter import CRISPRElementGeneIGVF
from adapters.CRISPR_element_element_adapter import CRISPRElementElement
from adapters.CRISPR_element_phenotype_adapter import CRISPRElementPhenotype
from adapters.CRISPR_variant_phenotype_adapter import CRISPRVariantPhenotype
from adapters.mouse_genomes_project_adapter import MouseGenomesProjectAdapter
from adapters.clingen_variant_disease_adapter import ClinGen
from adapters.gencode_gene_structure_adapter import GencodeStructure
from adapters.VAMP_coding_variant_scores_adapter import VAMPAdapter
from adapters.SEM_motif_adapter import SEMMotif
from adapters.SEM_prediction_adapter import SEMPred
from adapters.BlueSTARR_variants_biosamples_adapter import BlueSTARRVariantBiosample
from adapters.CRISPR_variant_gene_adapter import CRISPRVariantGene
from adapters.MORF_gene_transcript_gene_adapter import MORFGeneTranscriptGene
from adapters.ColocBoost_variants_biosamples_adapter import ColocBoostVariantBiosample
from adapters.overexpression_ATAC_adapter import OverexpressionATAC
from adapters.STARR_seq_adapter import STARRseqVariantBiosample
from adapters.file_fileset_adapter import FileFileSet
from adapters.eqtl_catalog_adapter import EQTLCatalog
from adapters.SGE_variant_phenotype_adapter import SGE
from adapters.cV2F_variant_phenotype_adapter import cV2F
from adapters.Mutpred2_coding_variants_adapter import Mutpred2CodingVariantsScores
from adapters.ESM_coding_variants_adapter import ESM1vCodingVariantsScores
from adapters.gencc_diseases_genes_adapter import GenccDiseasesGenes
from adapters.scE2G_adapter import scE2G
from adapters.DUAL_IPA_coding_variant_scores_adapter import DUALIPAAdapter
from adapters.variant_painting_coding_variant_scores_adapter import VariantPaintingAdapter
from adapters.gene_programs_adapter import GenePrograms

ADAPTERS = [
    AFGRCAQtl,
    AFGREQtl,
    AFGRSQtl,
    ASB,
    ASB_GVATDB,
    BlueSTARRVariantBiosample,
    CAQtl,
    CCRE,
    CRISPRElementElement,
    CRISPRElementGeneENCODE,
    CRISPRElementGeneIGVF,
    CRISPRElementPhenotype,
    CRISPRVariantGene,
    CRISPRVariantPhenotype,
    Cellosaurus,
    ClinGen,
    ColocBoostVariantBiosample,
    Coxpresdb,
    cV2F,
    DbNSFP,
    DepMap,
    Disease,
    DUALIPAAdapter,
    EBIComplex,
    EncodeElementGeneLink,
    EQTLCatalog,
    ESM1vCodingVariantsScores,
    Favor,
    FileFileSet,
    GAF,
    GenccDiseasesGenes,
    Gencode,
    GencodeGene,
    GencodeProtein,
    GencodeStructure,
    GeneGeneBiogrid,
    GenePrograms,
    GWAS,
    HumanMouseElementAdapter,
    MGIHumanMouseOrthologAdapter,
    MORFGeneTranscriptGene,
    Motif,
    MouseGenomesProjectAdapter,
    MPRAAdapter,
    Mutpred2CodingVariantsScores,
    Oncotree,
    Ontology,
    OverexpressionATAC,
    PharmGKB,
    pQTL,
    ProteinsInteraction,
    Reactome,
    ReactomePathway,
    scE2G,
    SEMMotif,
    SEMPred,
    SGE,
    STARRseqVariantBiosample,
    TopLD,
    VAMPAdapter,
    VariantPaintingAdapter,
]

KEY_TO_ADAPTER = {adapter.__name__: adapter for adapter in ADAPTERS}

in_docker = os.environ.get('IN_DOCKER') == 'TRUE'
