import { router } from '../trpc'

import { motifsRouters } from './datatypeRouters/nodes/motifs'
import { ontologyRouters } from './datatypeRouters/nodes/ontologies'
import { proteinsRouters } from './datatypeRouters/nodes/proteins'
import { regulatoryRegionRouters } from './datatypeRouters/nodes/regulatory_regions'
import { transcriptsRouters } from './datatypeRouters/nodes/transcripts'
import { variantsRouters } from './datatypeRouters/nodes/variants'
import { genesRouters } from './datatypeRouters/nodes/genes'

import { genesGenesEdgeRouters } from './datatypeRouters/edges/genes_genes'
import { genesTranscriptsRouters } from './datatypeRouters/edges/genes_transcripts'
import { ontologyTermsEdgeRouters } from './datatypeRouters/edges/ontology_terms_ontology_terms'
import { transcriptsProteinsRouters } from './datatypeRouters/edges/transcripts_proteins'
import { variantsPhenotypesRouters } from './datatypeRouters/edges/variants_phenotypes'
import { variantsVariantsRouters } from './datatypeRouters/edges/variants_variants'
import { variantsGenesRouters } from './datatypeRouters/edges/variants_genes'
import { diseasesGenesRouters } from './datatypeRouters/edges/diseases_genes'

import { autocompleteRouters } from './datatypeRouters/autocomplete'

// Edge endpoints must preceed node endpoints to avoid naming conflicts
export const appRouter = router({
  ...regulatoryRegionRouters,
  ...genesRouters,
  ...transcriptsRouters,
  ...proteinsRouters,
  ...genesTranscriptsRouters,
  ...transcriptsProteinsRouters,
  ...genesGenesEdgeRouters,
  ...variantsRouters,
  ...variantsVariantsRouters,
  ...variantsGenesRouters,
  ...motifsRouters,
  ...variantsPhenotypesRouters,
  ...diseasesGenesRouters,
  ...ontologyRouters,
  ...ontologyTermsEdgeRouters,
  ...autocompleteRouters
})

export type igvfCatalogRouter = typeof appRouter
