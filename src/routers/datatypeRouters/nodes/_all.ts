import { ontologyRouters } from './ontologies'
import { regulatoryRegionRouters } from './regulatory_regions'

export const nodeRouters = {
  ...ontologyRouters,
  ...regulatoryRegionRouters
}
