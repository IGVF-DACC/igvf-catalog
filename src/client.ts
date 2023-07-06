import { createTRPCProxyClient, httpBatchLink } from '@trpc/client'
import { igvfCatalogRouter } from './routers/_app'

async function main (): Promise<void> {
  const trpc = createTRPCProxyClient<igvfCatalogRouter>({
    links: [
      httpBatchLink({ url: 'http://localhost:2023/trpc' })
    ]
  })

  let terms = await trpc.ontologyTerm.query({
    term_name: 'brain'
  })

  console.log(terms)

  terms = await trpc.ontologyTerm.query({
    source: 'MONDO'
  })

  console.log(terms)

  const term = await trpc.ontologyTermID.query({
    id: 'GO_000001'
  })

  console.log(term)

  terms = await trpc.ontologyTermSearch.query({
    term: 'liver'
  })

  console.log(terms)

  terms = await trpc.ontologyGoTermBP.query({
    term_name: 'synthesis'
  })

  console.log(terms)

  terms = await trpc.ontologyGoTermCC.query({
    term_name: 'nucleous'
  })

  console.log(terms)

  terms = await trpc.ontologyGoTermMF.query({
    term_name: 'catabolic'
  })

  console.log(terms)

  let regions = await trpc.regulatoryRegions.query({
    region: 'chr1:1157520-1158189'
  })

  console.log(regions)

  regions = await trpc.regulatoryRegionsByCandidateCis.query({
    biological_activity: 'CA',
    type: 'candidate_cis_regulatory_element'
  })

  console.log(regions)
}

void main()
