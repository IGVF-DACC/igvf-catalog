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

  const proteins = await trpc.proteins.query({
    name: 'BTBD3_HUMAN'
  })

  console.log(proteins)

  const protein = await trpc.proteinID.query({
    id: 'Q9Y2F9'
  })

  console.log(protein)

  const transcripts = await trpc.transcripts.query({
    region: 'chr20:9537369-9839076',
    transcript_type: 'protein_coding'
  })

  console.log(transcripts)

  const transcript = await trpc.transcriptID.query({
    id: 'ENST00000353224'
  })

  console.log(transcript)

  const genes = await trpc.genes.query({
    gene_type: 'protein_coding',
    region: 'chr19:53431983-53461862'
  })

  console.log(genes)

  const gene = await trpc.geneID.query({
    id: 'ENSG00000160336'
  })

  console.log(gene)
}

void main()
