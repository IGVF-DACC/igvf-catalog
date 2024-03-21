import { motifsRouters } from './motifs'
import { ontologyRouters } from './ontologies'
import { proteinsRouters } from './proteins'
import { regulatoryRegionRouters } from './regulatory_regions'
import { transcriptsRouters } from './transcripts'
import { variantsRouters } from './variants'
import { genesRouters } from './genes'
import { complexesRouters } from './complexes'
import { studiesRouters } from './studies'
import { drugsRouters } from './drugs'
import { codingVariantsRouters } from './coding_variants'

export const nodeRouters = {
  ...ontologyRouters,
  ...regulatoryRegionRouters,
  ...variantsRouters,
  ...transcriptsRouters,
  ...proteinsRouters,
  ...genesRouters,
  ...motifsRouters,
  ...proteinsRouters,
  ...complexesRouters,
  ...drugsRouters,
  ...studiesRouters,
  ...codingVariantsRouters
}
