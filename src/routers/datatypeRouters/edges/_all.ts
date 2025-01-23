import { genesGenesEdgeRouters } from './genes_genes'
import { genesTranscriptsRouters } from './genes_transcripts'
import { ontologyTermsEdgeRouters } from './ontology_terms_ontology_terms'
import { transcriptsProteinsRouters } from './transcripts_proteins'
import { variantsPhenotypesRouters } from './variants_phenotypes'
import { variantsVariantsRouters } from './variants_variants'
import { variantsGenesRouters } from './variants_genes'
import { diseasesGenesRouters } from './diseases_genes'
import { complexesProteinsRouters } from './complexes_proteins'
import { variantsProteinsRouters } from './variants_proteins'
import { motifsProteinsRouters } from './motifs_proteins'
import { genomicElementsGenesRouters } from './genomic_elements_genes'
import { variantsDrugsRouters } from './variants_drugs'
import { proteinsProteinsRouters } from './proteins_proteins'
import { genesProteinsVariants } from './genes_proteins_variants'
import { genomicElementsBiosamplesRouters } from './genomic_elements_biosamples'
import { goTermsAnnotations } from './go_terms_annotations'
import { variantsRegulatoryRegionsRouters } from './variants_regulatory_regions'
import { variantsDiseasesRouters } from './variants_diseases'
import { variantsCodingVariantsRouters } from './variants_coding_variants'
import { genesPathwaysRouters } from './genes_pathways'
import { pathwaysPathwaysRouters } from './pathways_pathways'

export const edgeRouters = {
  ...genesTranscriptsRouters,
  ...transcriptsProteinsRouters,
  ...variantsVariantsRouters,
  ...ontologyTermsEdgeRouters,
  ...variantsGenesRouters,
  ...genesGenesEdgeRouters,
  ...variantsPhenotypesRouters,
  ...diseasesGenesRouters,
  ...complexesProteinsRouters,
  ...variantsProteinsRouters,
  ...motifsProteinsRouters,
  ...genomicElementsGenesRouters,
  ...variantsDrugsRouters,
  ...proteinsProteinsRouters,
  ...genesProteinsVariants,
  ...genomicElementsBiosamplesRouters,
  ...goTermsAnnotations,
  ...variantsRegulatoryRegionsRouters,
  ...variantsDiseasesRouters,
  ...variantsCodingVariantsRouters,
  ...genesPathwaysRouters,
  ...pathwaysPathwaysRouters
}
