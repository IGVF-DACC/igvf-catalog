import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { paramsFormatType } from '../_helpers'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { descriptions } from '../descriptions'

const schema = loadSchemaConfig()

const geneSchema = schema.gene
const proteinSchema = schema.protein

const goTermsProteinsSchema = schema.gaf
const genesProteinsGoRouter = new RouterEdges(goTermsProteinsSchema)

const goTermQueryFormat = z.object({
  go_term_id: z.string(),
  page: z.number().default(0)
})

const queryFormat = z.object({
  query: z.string(),
  page: z.number().default(0)
})

async function geneIds (id: string): Promise<any[]> {
  const input: paramsFormatType = {}
  input.gene_name = id
  input.gene_id = id
  input.hgnc = `HGNC:${id}`
  input.alias = id
  input._key = id

  return await (new RouterFilterBy(geneSchema)).getObjectIDs(input, '', false)
}

async function proteinIds (id: string): Promise<any[]> {
  const input: paramsFormatType = {}
  input.name = id
  input.dbxrefs = id
  input._key = id

  return await (new RouterFilterBy(proteinSchema)).getObjectIDs(input, '', false)
}

async function goTermsSearch (input: paramsFormatType): Promise<any[]> {
  const query = input.query as string
  const page = input.page as number

  let response

  // assuming an ID will match either a gene or a protein
  const genes = await geneIds(query)
  if (genes.length !== 0) {
    response = await genesProteinsGoRouter.getSourceAndEdgeSet(genes[0], page)

    return response
  }

  const proteins = await proteinIds(query)
  console.log(proteins)
  if (proteins.length > 0) {
    response = await genesProteinsGoRouter.getSourceAndEdgeSet(proteins[0], page)

    return response
  }

  return []
}

async function geneProteinSearch (input: paramsFormatType): Promise<any[]> {
  const id = `ontology_terms/${input.go_term_id as string}`
  const page = input.page as number

  return await genesProteinsGoRouter.getTargetAndEdgeSet(id, page)
}

const goTermsFromGenesProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes-proteins/go-terms', description: descriptions.genes_proteins_go_terms } })
  .input(queryFormat)
  .output(z.any())
  .query(async ({ input }) => await goTermsSearch(input))

const genesProteinsFromGoTerms = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/go-terms/genes-proteins', description: descriptions.go_terms_genes_proteins } })
  .input(goTermQueryFormat)
  .output(z.any())
  .query(async ({ input }) => await geneProteinSearch(input))

export const goTermsProteins = {
  goTermsFromGenesProteins,
  genesProteinsFromGoTerms
}
