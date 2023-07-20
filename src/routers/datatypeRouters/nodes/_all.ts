import { ontologyRouters } from './ontologies'
import { proteinsRouters } from './proteins'
import { regulatoryRegionRouters } from './regulatory_regions'
import { transcriptsRouters } from './transcripts'
import { variantsRouters } from './variants'
import { genesRouters } from './genes'

export const nodeRouters = {
  ...ontologyRouters,
  ...regulatoryRegionRouters,
  ...variantsRouters,
  ...transcriptsRouters,
  ...proteinsRouters,
  ...genesRouters
}
