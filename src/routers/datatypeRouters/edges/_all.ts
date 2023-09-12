import { genesGenesEdgeRouters } from './genes_genes'
import { genesTranscriptsRouters } from './genes_transcripts'
import { ontologyTermsEdgeRouters } from './ontology_terms_ontology_terms'
import { transcriptsProteinsRouters } from './transcripts_proteins'
import { variantsVariantsRouters } from './variants_variants'
import { variantsGenesRouters } from './variants_genes'

export const edgeRouters = {
  ...genesTranscriptsRouters,
  ...transcriptsProteinsRouters,
  ...variantsVariantsRouters,
  ...ontologyTermsEdgeRouters,
  ...variantsGenesRouters,
  ...genesGenesEdgeRouters
}
