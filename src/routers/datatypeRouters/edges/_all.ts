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
  ...motifsProteinsRouters
}
