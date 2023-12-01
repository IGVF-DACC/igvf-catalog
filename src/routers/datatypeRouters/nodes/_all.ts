import { motifsRouters } from './motifs'
import { ontologyRouters } from './ontologies'
import { proteinsRouters } from './proteins'
import { regulatoryRegionRouters } from './regulatory_regions'
import { transcriptsRouters } from './transcripts'
import { variantsRouters } from './variants'
import { genesRouters } from './genes'
import { complexesRouters } from './complexes'
import { mmRegulatoryRegionRouters } from './mm_regulatory_regions'

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
  ...mmRegulatoryRegionRouters
}
