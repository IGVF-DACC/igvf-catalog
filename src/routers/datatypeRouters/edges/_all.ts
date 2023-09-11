import { genesTranscriptsRouters } from './genes_transcripts'
import { ontologyTermsEdgeRouters } from './ontology_terms_ontology_terms'
import { transcriptsProteinsRouters } from './transcripts_proteins'
import { variantsVariantsRouters } from './variants_variants'

export const edgeRouters = {
  ...genesTranscriptsRouters,
  ...transcriptsProteinsRouters,
  ...variantsVariantsRouters,
  ...ontologyTermsEdgeRouters
}
