import { genesTranscriptsRouters } from './genes_transcripts'
import { transcriptsProteinsRouters } from './transcripts_proteins'

export const edgeRouters = {
  ...genesTranscriptsRouters,
  ...transcriptsProteinsRouters
}
