import { createTRPCProxyClient, httpBatchLink } from '@trpc/client'
import { igvfCatalogRouter } from './routers/_app'

async function main (): Promise<void> {
  const trpc = createTRPCProxyClient<igvfCatalogRouter>({
    links: [
      httpBatchLink({ url: 'http://localhost:2023/trpc' })
    ]
  })

  const regions = await trpc.regions.query({
    gte: 69754011,
    lt: 69754099,
    chr: '1'
  })

  console.log(regions)

  const variantCorrelations = await trpc.variantCorrelations.query({
    chr: '22',
    r: 0.8,
    page: 1
  })

  console.log(variantCorrelations)
}

void main()
