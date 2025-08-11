import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { geneFormat, geneSearch } from '../nodes/genes'
import { getDBReturnStatements, paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { commonHumanEdgeParamsFormat, commonPathwayQueryFormat, genesCommonQueryFormat } from '../params'
import { pathwayFormat, pathwaySearchPersistent } from '../nodes/pathways'

const MAX_PAGE_SIZE = 500

const genesPathwaysFormat = z.object({
  source: z.string().optional(),
  source_url: z.string().optional(),
  orgnism: z.string().optional(),
  gene: z.string().or(geneFormat).optional(),
  pathway: z.string().or(pathwayFormat).optional(),
  name: z.string()
})
const schema = loadSchemaConfig()

const genesPathwaysSchema = schema['gene to pathway association']
const geneSchema = schema.gene
const pathwaySchema = schema.pathway

function validateGeneInput (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['gene_id', 'hgnc_id', 'gene_name', 'alias'].includes(item))
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one gene property must be defined.'
    })
  }
}
function validatePathwayInput (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['pathway_id', 'pathway_name', 'name_aliases', 'disease_ontology_terms', 'go_biological_process'].includes(item))
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one pathway property must be defined.'
    })
  }
}

async function findPathwaysFromGeneSearch (input: paramsFormatType): Promise<any[]> {
  validateGeneInput(input)
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { gene_id, hgnc_id, gene_name: name, alias, organism } = input
  const geneInput: paramsFormatType = { gene_id, hgnc_id, name, alias, organism, page: 0 }
  delete input.hgnc_id
  delete input.gene_name
  delete input.alias
  delete input.organism
  const genes = await geneSearch(geneInput)
  const geneIDs = genes.map(gene => `${geneSchema.db_collection_name as string}/${gene._id as string}`)

  const verboseQueryPathway = `
    FOR otherRecord IN ${pathwaySchema.db_collection_name as string}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${getDBReturnStatements(pathwaySchema).replaceAll('record', 'otherRecord')}}
  `
  const verboseQueryGene = `
    FOR otherRecord IN ${geneSchema.db_collection_name as string}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
    RETURN {${getDBReturnStatements(geneSchema).replaceAll('record', 'otherRecord')}}
  `
  const query = `
    FOR record IN ${genesPathwaysSchema.db_collection_name as string}
      FILTER record._from IN ${JSON.stringify(geneIDs)}
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'gene': ${input.verbose === 'true' ? `(${verboseQueryGene})[0]` : 'record._from'},
        'pathway': ${input.verbose === 'true' ? `(${verboseQueryPathway})[0]` : 'record._to'},
        'name': record.name,
        ${getDBReturnStatements(genesPathwaysSchema)}
      }
  `
  return await (await db.query(query)).all()
}

async function findGenesFromPathways (input: paramsFormatType): Promise<any[]> {
  validatePathwayInput(input)
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { pathway_id: id, pathway_name: name, name_aliases, disease_ontology_terms, go_biological_process } = input
  const pathwayInput: paramsFormatType = { id, name, name_aliases, disease_ontology_terms, go_biological_process, organism: 'Homo sapiens', page: 0 }
  delete input.pathway_id
  delete input.pathway_name
  delete input.name_aliases
  delete input.disease_ontology_terms
  delete input.go_biological_process
  delete input.organism
  const pathways = await pathwaySearchPersistent(pathwayInput)
  const pathwayIDs = pathways.map(pathway => `${pathwaySchema.db_collection_name as string}/${pathway._id as string}`)
  const verboseQuery = `
    FOR otherRecord IN ${geneSchema.db_collection_name as string}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
    RETURN {${getDBReturnStatements(geneSchema).replaceAll('record', 'otherRecord')}}
  `

  const query = `
    FOR record IN ${genesPathwaysSchema.db_collection_name as string}
      FILTER record._to IN ${JSON.stringify(pathwayIDs)}
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'gene':  ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'record._from'},
        'pathway': record._to,
        'name': record.inverse_name, // endpoint is opposite to ArangoDB collection name
        ${getDBReturnStatements(genesPathwaysSchema)}
      }
  `
  return await (await db.query(query)).all()
}

const pathwaysFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/pathways', description: descriptions.genes_pathways } })
  .input(genesCommonQueryFormat.merge(commonHumanEdgeParamsFormat))
  .output(z.array(genesPathwaysFormat))
  .query(async ({ input }) => await findPathwaysFromGeneSearch(input))

const genesFromPathways = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/pathways/genes', description: descriptions.pathways_genes } })
  .input(commonPathwayQueryFormat.merge(commonHumanEdgeParamsFormat))
  .output(z.array(genesPathwaysFormat))
  .query(async ({ input }) => await findGenesFromPathways(input))

export const genesPathwaysRouters = {
  pathwaysFromGenes,
  genesFromPathways
}
