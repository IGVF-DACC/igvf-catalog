import { motifsRouters } from './motifs'
import { ontologyRouters } from './ontologies'
import { proteinsRouters } from './proteins'
import { genomicRegionsRouters } from './genomic_elements'
import { transcriptsRouters } from './transcripts'
import { variantsRouters } from './variants'
import { genesRouters } from './genes'
import { complexesRouters } from './complexes'
import { studiesRouters } from './studies'
import { drugsRouters } from './drugs'
import { codingVariantsRouters } from './coding_variants'
import { genesStructureRouters } from './genes_structure'
import { pathwaysRouters } from './pathways'

export const nodeRouters = {
  ...ontologyRouters,
  ...genomicRegionsRouters,
  ...variantsRouters,
  ...transcriptsRouters,
  ...proteinsRouters,
  ...genesRouters,
  ...motifsRouters,
  ...proteinsRouters,
  ...complexesRouters,
  ...drugsRouters,
  ...studiesRouters,
  ...codingVariantsRouters,
  ...genesStructureRouters,
  ...pathwaysRouters
}
