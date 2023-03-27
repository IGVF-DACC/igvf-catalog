import { createTRPCProxyClient, httpBatchLink } from "@trpc/client";
import { igvfCatalogRouter } from "./routers/_app";

async function main(): Promise<void> {
  const trpc = createTRPCProxyClient<igvfCatalogRouter>({
    links: [httpBatchLink({ url: "http://localhost:2023/trpc" })],
  });

  const variantCorrelations = await trpc.variantCorrelations.query({
    rsid: "10511349",
    page: 1,
    ancestry: "SAS",
  });

  console.log(variantCorrelations);
}

void main();
