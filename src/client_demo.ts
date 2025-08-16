import { createTRPCProxyClient, httpBatchLink } from '@trpc/client'
import { igvfCatalogRouter } from './routers/_app'

async function main (): Promise<void> {
  const trpc = createTRPCProxyClient<igvfCatalogRouter>({
    links: [
      httpBatchLink({ url: 'http://localhost:2023/trpc' })
    ]
  })

  let terms = await trpc.ontologyTerm.query({
    name: 'brain'
  })

  console.log('Find terms named brain:', terms)

  terms = await trpc.ontologyTerm.query({
    source: 'MONDO',
    limit: 2
  })

  console.log('Find terms from source MONDO:', terms)

  const regions = await trpc.genomicElements.query({
    region: 'chr1:1157520-1158189',
    limit: 2
  })

  console.log('Find genomic elements in region chr1:1157520-1158189:', regions)

  let variants = await trpc.variants.query({
    region: 'chr20:9564576-9564579',
    rsid: 'rs2045642915',
    GENCODE_category: 'noncoding',
    limit: 2
  })

  console.log('Find variants in region chr20:9564576-9564579, rsid = rs2045642915, GENCODE_category = noncoding:', variants)

  const variant = await trpc.variants.query({
    variant_id: 'NC_000001.11:10000:T:C'
  })

  console.log('Find variant by variant_id:', variant)

  variants = await trpc.variantByFrequencySource.query({
    source: 'bravo_af',
    region: 'chr3:186741137-186742238',
    GENCODE_category: 'noncoding',
    minimum_af: 0,
    maximum_af: 1,
    limit: 2
  })

  console.log('Find variants by frequency source bravo_af:', variants)

  const proteins = await trpc.proteins.query({
    name: 'BTBD3_HUMAN'
  })

  console.log('Find proteins named BTBD3_HUMAN:', proteins)

  const protein = await trpc.proteins.query({
    protein_id: 'ENSP00000493376'
  })

  console.log('Find protein by protein_id:', protein)

  const transcripts = await trpc.transcripts.query({
    region: 'chr20:9537369-9839076',
    transcript_type: 'protein_coding'
  })

  console.log('Find transcripts in region chr20:9537369-9839076, transcript_type = protein_coding:', transcripts)

  const transcript = await trpc.transcripts.query({
    transcript_id: 'ENST00000353224'
  })

  console.log('Find transcript by transcript_id:', transcript)

  const genes = await trpc.genes.query({
    gene_type: 'protein_coding',
    region: 'chr19:53431983-53461862'
  })

  console.log('Find genes by gene_type = protein_coding, region = chr19:53431983-53461862:', genes)

  const gene = await trpc.genes.query({
    gene_id: 'ENSG00000160336'
  })

  console.log('Find gene by gene_id:', gene)
}

void main()
