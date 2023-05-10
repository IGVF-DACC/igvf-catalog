import { createTRPCProxyClient, httpBatchLink } from '@trpc/client'
import { igvfCatalogRouter } from './routers/_app'

async function main (): Promise<void> {
  const trpc = createTRPCProxyClient<igvfCatalogRouter>({
    links: [
      httpBatchLink({ url: 'http://localhost:2023/trpc' })
    ]
  })

  const proteins = await trpc.proteins.query({
    name: 'COQ8A_HUMAN'
  })

  console.log(proteins)

  const protein = await trpc.proteinID.query({
    id: 'Q8NI60'
  })

  console.log(protein)
}

void main()
