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
    biochemical_activity: 'CA',
    type: 'candidate_cis_regulatory_element'
  })

  console.log(regions)

  let variants = await trpc.variants.query({
    region: 'chr20:9564576-9564579',
    rsid: 'rs2045642915',
    funseq_description: 'noncoding'
  })

  console.log(variants)

  const variant = await trpc.variantID.query({
    id: '0ddf235d8539cc856bde1a7030995c11dc3166221a21708961017fb1b68e3bdb'
  })

  console.log(variant)

  variants = await trpc.variantByFrequencySource.query({
    source: 'dbgap_popfreq',
    region: 'chr20:9564576-9564579',
    funseq_description: 'noncoding',
    min_alt_freq: 0,
    max_alt_freq: 1
  })

  console.log(variants)

  const transcripts = await trpc.transcripts.query({
    region: 'chr20:9537369-9839076',
    transcript_type: 'protein_coding'
  })

  console.log(transcripts)

  const transcript = await trpc.transcriptID.query({
    id: 'ENST00000353224'
  })

  console.log(transcript)
}

void main()
