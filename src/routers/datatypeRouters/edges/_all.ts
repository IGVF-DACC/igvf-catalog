import { genesTranscriptsRouters } from './genes_transcripts'
import { transcriptsProteinsRouters } from './transcripts_proteins'
import { variantsVariantsRouters } from './variants_variants'

export const edgeRouters = {
  ...genesTranscriptsRouters,
  ...transcriptsProteinsRouters,
  ...variantsVariantsRouters
}
