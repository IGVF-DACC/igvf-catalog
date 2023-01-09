import { createTRPCProxyClient, httpBatchLink } from '@trpc/client'
import { igvfCatalogRouter } from './server'

async function main (): Promise<void> {
  const trpc = createTRPCProxyClient<igvfCatalogRouter>({
    links: [
      httpBatchLink({ url: 'http://localhost:2023' })
    ]
  })

  const regions = await trpc.regions.query({
    gte: 69754011,
    lt: 69754090,
    chr: '1'
  })

  console.log(regions)
}

void main()
