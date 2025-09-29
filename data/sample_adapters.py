from adapters.gencode_adapter import Gencode
from adapters.gencode_gene_adapter import GencodeGene
from adapters.topld_adapter import TopLD
from adapters.encode_caqtl_adapter import CAQtl
from adapters.ccre_adapter import CCRE
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
from adapters.encode_mpra_adapter import EncodeMPRA
from adapters.mgi_human_mouse_ortholog_adapter import MGIHumanMouseOrthologAdapter
from adapters.gvatdb_asb_adapter import ASB_GVATDB
from adapters.AFGR_eqtl_adapter import AFGREQtl
from adapters.AFGR_sqtl_adapter import AFGRSQtl
from adapters.AFGR_caqtl_adapter import AFGRCAQtl
from adapters.dbNSFP_adapter import DbNSFP
from adapters.pQTL_adapter import pQTL
from adapters.biogrid_gene_gene_adapter import GeneGeneBiogrid
from adapters.encode_E2G_CRISPR_adapter import ENCODE2GCRISPR
from adapters.mouse_genomes_project_adapter import MouseGenomesProjectAdapter
from adapters.clingen_variant_disease_adapter import ClinGen
from adapters.gencode_gene_structure_adapter import GencodeStructure
from adapters.VAMP_coding_variant_scores_adapter import VAMPAdapter
from adapters.SEM_motif_adapter import SEMMotif
from adapters.SEM_prediction_adapter import SEMPred
from adapters.BlueSTARR_variant_elements_adapter import BlueSTARRVariantElement
from adapters.file_fileset_adapter import FileFileSet

ADAPTERS = {
    'gencode_genes': GencodeGene(filepath='./samples/gencode_sample.gtf', gene_alias_file_path='./samples/Homo_sapiens.gene_info.gz'),
    'gencode_transcripts': Gencode(filepath='./samples/gencode_sample.gtf', label='gencode_transcript'),
    'transcribed_to': Gencode(filepath='./samples/gencode_sample.gtf', label='transcribed_to'),
    'gencode_gene_structures': GencodeStructure(filepath='./samples/gencode_sample.gtf', label='gene_structure'),
    'transcript_contains_gene_structure': GencodeStructure(filepath='./samples/gencode_sample.gtf', label='transcript_contains_gene_structure'),
    'AFGR_eqtl': AFGREQtl(filepath='./samples/AFGR/sorted.dist.hwe.af.AFR_META.eQTL.example.txt.gz', label='AFGR_eqtl'),
    'AFGR_eqtl_term': AFGREQtl(filepath='./samples/AFGR/sorted.dist.hwe.af.AFR_META.eQTL.example.txt.gz', label='AFGR_eqtl_term'),
    'topld': TopLD(filepath='./samples/topld_sample.csv', annotation_filepath='./samples/topld_info_annotation.csv', chr='chr22', ancestry='SAS'),
    'caqtl_ocr': CAQtl(filepath='./samples/caqtl-sample.bed', source='PMID:34017130', label='genomic_element'),
    'caqtl': CAQtl(filepath='./samples/caqtl-sample.bed', source='PMID:34017130', label='encode_caqtl'),
    'AFGR_caqtl_ocr': AFGRCAQtl(filepath='./samples/AFGR/sorted.dist.hwe.af.AFR.caQTL.example.txt.gz', label='genomic_element'),
    'AFGR_caqtl': AFGRCAQtl(filepath='./samples/AFGR/sorted.dist.hwe.af.AFR.caQTL.example.txt.gz', label='AFGR_caqtl'),
    'ccre': CCRE(filepath='./samples/ccre_example.bed.gz'),
    'favor': Favor(filepath='./samples/favor_sample.vcf', ca_ids_path='./samples/dummy_caids.pickle'),
    'pQTL': pQTL(filepath='./samples/pQTL_UKB_example.csv', label='pqtl'),
    'allele_specific_binding': ASB(filepath='./samples/allele_specific_binding', label='asb'),
    'allele_specific_binding_cell': ASB(filepath='./samples/allele_specific_binding', label='asb_cell_ontology'),
    'allele_specific_binding_GVATdb': ASB_GVATDB(filepath='./samples/GVATdb_sample.csv', label='asb'),
    'AFGR_sqtl': AFGRSQtl(filepath='./samples/AFGR/sorted.all.AFR.Meta.sQTL.example.txt.gz', label='AFGR_sqtl'),
    'AFGR_sqtl_term': AFGRSQtl(filepath='./samples/AFGR/sorted.all.AFR.Meta.sQTL.example.txt.gz', label='AFGR_sqtl_term'),
    'encode_genomic_element': EncodeElementGeneLink(filepath='./samples/epiraction_ENCFF712SUP.bed.gz', label='genomic_element', source='ENCODE_EpiRaction', source_url='https://www.encodeproject.org/files/ENCFF712SUP/', biological_context='CL_0000765'),
    'encode_genomic_element_gene': EncodeElementGeneLink(filepath='./samples/epiraction_ENCFF712SUP.bed.gz', label='genomic_element_gene', source='ENCODE_EpiRaction', source_url='https://www.encodeproject.org/files/ENCFF712SUP/', biological_context='CL_0000765'),
    'encode_donor': EncodeElementGeneLink(filepath='./samples/E2G_ENCFF617FJH.bed.gz', label='donor', source='ENCODE-E2G-DNaseOnly', source_url='https://www.encodeproject.org/files/ENCFF617FJH/', biological_context='EFO_0001203'),
    'encode_biosample': EncodeElementGeneLink(filepath='./samples/E2G_ENCFF728HSS.bed.gz', label='ontology_term', source='ENCODE-E2G-DNaseOnly', source_url='https://www.encodeproject.org/files/ENCFF728HSS/', biological_context='NTR_0000502'),
    'encode_mpra_genomic_element': EncodeMPRA(filepath='./samples/MPRA_ENCFF802FUV_example.bed.gz', label='genomic_element', source_url='https://www.encodeproject.org/files/ENCFF802FUV/', biological_context='EFO_0002067'),
    'encode_mpra_genomic_element_biosample': EncodeMPRA(filepath='./samples/MPRA_ENCFF802FUV_example.bed.gz', label='genomic_element_biosample', source_url='https://www.encodeproject.org/files/ENCFF802FUV/', biological_context='EFO_0002067'),
    'encode_genomic_element_crispr': ENCODE2GCRISPR(filepath='./samples/ENCODE_E2G_CRISPR_example.tsv', label='genomic_element'),
    'encode_genomic_element_gene_crispr': ENCODE2GCRISPR(filepath='./samples/ENCODE_E2G_CRISPR_example.tsv', label='genomic_element_gene'),
    'encode_file_fileset': FileFileSet(accession='ENCFF923FSV', label='encode_file_fileset'),
    'igvf_file_fileset': FileFileSet(accession='IGVFFI1663LKVQ', label='igvf_file_fileset'),
    'gaf': GAF(filepath='./samples/goa_human_sample.gaf.gz'),
    'gaf_mouse': GAF(filepath='./samples/mgi_sample.gaf.gz', gaf_type='mouse'),
    'gaf_isoform': GAF(filepath='./samples/goa_human_isoform.gaf.gz', gaf_type='human_isoform'),
    'gaf_rna': GAF(filepath='./samples/goa_human_rna.gaf.gz', gaf_type='rna'),
    'gwas_studies': GWAS(variants_to_ontology='./samples/gwas_v2d_igvf_sample.tsv', variants_to_genes='./samples/gwas_v2g_igvf_sample.tsv'),
    'gwas_var_phenotypes': GWAS(variants_to_ontology='./samples/gwas_v2d_igvf_sample.tsv', variants_to_genes='./samples/gwas_v2g_igvf_sample.tsv', gwas_collection='variants_phenotypes'),
    'gwas_var_phenotypes_studies': GWAS(variants_to_ontology='./samples/gwas_v2d_igvf_sample.tsv', variants_to_genes='./samples/gwas_v2g_igvf_sample.tsv', gwas_collection='variants_phenotypes_studies'),
    'motif': Motif(filepath='./samples/motifs', label='motif'),
    'motif to protein': Motif(filepath='./samples/motifs', label='motif_protein_link'),
    'coxpresdb': Coxpresdb(filepath='./samples/coxpresdb/1'),
    'pathway': ReactomePathway(filepath='./samples/reactome/ReactomePathways.txt'),
    'genes_pathways': Reactome(filepath='./samples/reactome/Ensembl2Reactome_All_Levels_sample.txt', label='genes_pathways'),
    'parent_pathway_of': Reactome(filepath='./samples/reactome/ReactomePathwaysRelation.txt', label='parent_pathway_of'),
    'cellosaurus_terms': Cellosaurus(filepath='./samples/cellosaurus_example.obo.txt', type='node'),
    'cellosaurus_relationships': Cellosaurus(filepath='./samples/cellosaurus_example.obo.txt', type='edge'),
    'drug': PharmGKB(filepath='./samples/pharmGKB', label='drug'),
    'variant_drug': PharmGKB(filepath='./samples/pharmGKB', label='variant_drug'),
    'variant_drug_gene': PharmGKB(filepath='./samples/pharmGKB', label='variant_drug_gene'),
    'disease_gene': Disease(filepath='./samples/orphanet_example.xml'),
    'oncotree_terms': Oncotree(type='node'),
    'oncotree_relationships': Oncotree(type='edge'),
    'gene_term': DepMap(filepath='./samples/DepMap/CRISPRGeneDependency_transposed_example.csv', type='edge', label='gene_term'),
    'complex': EBIComplex(filepath='./samples/EBI_complex_example.tsv', label='complex'),
    'complex_protein': EBIComplex(filepath='./samples/EBI_complex_example.tsv', label='complex_protein'),
    'complex_term': EBIComplex(filepath='./samples/EBI_complex_example.tsv', label='complex_term'),
    'protein_protein': ProteinsInteraction(filepath='./samples/merged_PPI.UniProt.example.csv', label='protein_protein'),
    'gene_gene_biogrid': GeneGeneBiogrid(filepath='./samples/merged_PPI.UniProt.example.csv', label='gene_gene_biogrid'),
    'mouse_gene_gene_biogrid': GeneGeneBiogrid(filepath='./samples/merged_PPI_mouse.UniProt.example.csv', label='mouse_gene_gene_biogrid'),
    'genomic_element_mm_genomic_element': HumanMouseElementAdapter(filepath='./samples/element_mapping_example.txt.gz', label='genomic_element_mm_genomic_element'),
    'mm_orthologs': MGIHumanMouseOrthologAdapter(filepath='./samples/HOM_MouseHumanSequence_sample.rpt'),
    'coding_variants': DbNSFP(filepath='./samples/dbNSFP4.5a_variant.chrY_sample'),
    'variants_coding_variants': DbNSFP(filepath='./samples/dbNSFP4.5a_variant.chrY_sample', collection='variants_coding_variants'),
    'coding_variants_proteins': DbNSFP(filepath='./samples/dbNSFP4.5a_variant.chrY_sample', collection='coding_variants_proteins'),
    'mouse_variant': MouseGenomesProjectAdapter(filepath='./samples/mouse_variants/mouse_variant_snps_rsid_sample.vcf'),
    'variant_disease': ClinGen('./samples/clinGen_variant_pathogenicity_example.csv', label='variant_disease'),
    'variant_disease_gene': ClinGen('./samples/clinGen_variant_pathogenicity_example.csv', label='variant_disease_gene'),
    'bluestarr_variant_elements': BlueSTARRVariantElement('./samples/variant_phenotype_V2F.example.tsv', label='variant_genomic_element'),
    'vamp_coding_variant_phenotype': VAMPAdapter('./samples/vamp_coding_variants.example.csv', label='vamp_coding_variants_phenotypes'),
    'SEM_motif': SEMMotif('./samples/SEM/', label='motif'),
    'SEM_motif_protein': SEMMotif('./samples/SEM/', label='motif_protein_link'),
    'SEM_variant_protein': SEMPred('./samples/SEM/', label='sem_predicted_asb')
}
