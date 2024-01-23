import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { paramsFormatType } from '../_helpers'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'

const schema = loadSchemaConfig()

const geneSchema = schema.gene
const proteinSchema = schema.protein

const genesVariantsSchema = schema['variant to gene association']
const proteinsVariantsSchema = schema['allele specific binding']
const genesProteinsRouter = new RouterEdges(genesVariantsSchema, new RouterEdges(proteinsVariantsSchema))

const variantQueryFormat = z.object({
  variant_id: z.string(),
  page: z.number().default(0)
})

const queryFormat = z.object({
  id: z.string(),
  page: z.number().default(0)
})

async function geneIds (id: string): Promise<any[]> {
  const input: paramsFormatType = {}
  input.gene_name = id
  input.gene_id = id
  input.hgnc = `HGNC:${id}`
  input.alias = id
  input._key = id

  const geneIds = await (new RouterFilterBy(geneSchema)).getObjectIDs(input, '', false)
  return geneIds
}

async function proteinIds (id: string): Promise<any[]> {
  const input: paramsFormatType = {}
  input.name = id
  input.dbxrefs = id
  input._key = id

  const proteinIds = await (new RouterFilterBy(proteinSchema)).getObjectIDs(input, '', false)
  return proteinIds
}

async function geneProteinSearch (input: paramsFormatType): Promise<any[]> {
  const id = input.id as string
  const page = input.page as number

  const elementIds = (await geneIds(id)).concat(await proteinIds(id))
  return await genesProteinsRouter.getSourceSetByUnion(elementIds, page)
}

async function variantSearch (input: paramsFormatType): Promise<any[]> {
  const id = `variants/${input.variant_id as string}`
  const page = input.page as number

  return await genesProteinsRouter.getTargetSetByUnion(id, page)
}

async function geneProteinGeneProtein (input: paramsFormatType): Promise<any[]> {
  const id = input.id as string
  const page = input.page as number

  // genes <-> proteins
  // primary: genes_transcripts
  const schemaObj = schema['transcribed to']
  // secondary: transcripts_proteins
  const secondarySchemaObj = schema['translates to']
  const geneProteinsRouterEdge = new RouterEdges(schemaObj, new RouterEdges(secondarySchemaObj))

  let response

  // assuming an ID will match either a gene or a protein
  const genes = await geneIds(id)
  if (genes.length !== 0) {
    response = await geneProteinsRouterEdge.getSelfAndTransversalTargetEdges(genes, page, 'genes_genes', 'proteins_proteins')
    if (response[0].related.length === 0 && response[1].related.length === 0) {
      return []
    }

    return response
  }

  const proteins = await proteinIds(id)
  if (proteins.length > 0) {
    response = await geneProteinsRouterEdge.getSelfAndTransversalSourceEdges(proteins, page, 'genes_genes', 'proteins_proteins')
    if (response[0].related.length === 0 && response[1].related.length === 0) {
      return []
    }

    return response
  }

  return []
}

const variantsFromGeneProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes-proteins/variants' } })
  .input(queryFormat)
  .output(z.any())
  .query(async ({ input }) => await geneProteinSearch(input))

const genesProteinsFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/genes-proteins' } })
  .input(variantQueryFormat)
  .output(z.any())
  .query(async ({ input }) => await variantSearch(input))

const genesProteinsGenesProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes-proteins/genes-proteins' } })
  .input(queryFormat)
  .output(z.any())
  .query(async ({ input }) => await geneProteinGeneProtein(input))

export const genesProteinsVariants = {
  variantsFromGeneProteins,
  genesProteinsFromVariants,
  genesProteinsGenesProteins
}
