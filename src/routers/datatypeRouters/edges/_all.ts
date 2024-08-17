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
import { regulatoryRegionsGenesRouters } from './regulatory_regions_genes'
import { variantsDrugsRouters } from './variants_drugs'
import { proteinsProteinsRouters } from './proteins_proteins'
import { genesProteinsVariants } from './genes_proteins_variants'
import { regulatoryRegionsBiosamplesRouters } from './regulatory_regions_biosamples'
import { goTermsAnnotations } from './go_terms_annotations'
import { variantsRegulatoryRegionsRouters } from './variants_regulatory_regions'
import { variantsDiseasesRouters } from './variants_diseases'
import { variantsCodingVariantsRouters } from './variants_coding_variants'
import { genesRegulatoryRegionsRouters } from './genes_regulatory_regions'

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
  ...regulatoryRegionsGenesRouters,
  ...variantsDrugsRouters,
  ...proteinsProteinsRouters,
  ...genesProteinsVariants,
  ...regulatoryRegionsBiosamplesRouters,
  ...goTermsAnnotations,
  ...variantsRegulatoryRegionsRouters,
  ...variantsDiseasesRouters,
  ...variantsCodingVariantsRouters,
  ...genesRegulatoryRegionsRouters
}
