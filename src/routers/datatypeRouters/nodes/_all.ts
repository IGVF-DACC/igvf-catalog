import { ontologyRouters } from './ontologies'
import { proteinsRouters } from './proteins'
import { regulatoryRegionRouters } from './regulatory_regions'
import { transcriptsRouters } from './transcripts'
import { variantsRouters } from './variants'

export const nodeRouters = {
  ...ontologyRouters,
  ...regulatoryRegionRouters,
  ...variantsRouters,
  ...proteinsRouters,
  ...transcriptsRouters
}
