import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { getDBReturnStatements, paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { commonHumanEdgeParamsFormat, commonPathwayQueryFormat } from '../params'
import { pathwayFormat, pathwaySearchPersistent } from '../nodes/pathways'

const MAX_PAGE_SIZE = 500

const genesPathwaysFormat = z.object({
  source: z.string().optional(),
  source_url: z.string().optional(),
  orgnism: z.string().optional(),
  parent_pathway: z.string().or(pathwayFormat).optional(),
  child_pathway: z.string().or(pathwayFormat).optional()
})
const schema = loadSchemaConfig()

const pathwaysPathwaysSchema = schema['parent pathway of']
const pathwaySchema = schema.pathway

function validatePathwayInput (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['pathway_id', 'pathway_name', 'name_aliases', 'disease_ontology_terms', 'go_biological_process'].includes(item))
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one pathway property must be defined.'
    })
  }
}

async function findGenesFromPathways (input: paramsFormatType): Promise<any[]> {
  validatePathwayInput(input)
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
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
  const verboseQueryForParent = `
    FOR otherRecord IN ${pathwaySchema.db_collection_name as string}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
    RETURN {${getDBReturnStatements(pathwaySchema).replaceAll('record', 'otherRecord')}}
  `
  const verboseQueryForChild = `
    FOR otherRecord IN ${pathwaySchema.db_collection_name as string}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${getDBReturnStatements(pathwaySchema).replaceAll('record', 'otherRecord')}}
  `

  const query = `
    FOR record IN ${pathwaysPathwaysSchema.db_collection_name as string}
      FILTER record._to IN ${JSON.stringify(pathwayIDs)} or record._from IN ${JSON.stringify(pathwayIDs)}
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'parent_pathway':  ${input.verbose === 'true' ? `(${verboseQueryForParent})[0]` : 'record._from'},
        'child_pathway': ${input.verbose === 'true' ? `(${verboseQueryForChild})[0]` : 'record._to'},
        ${getDBReturnStatements(pathwaysPathwaysSchema)}
      }
  `
  return await (await db.query(query)).all()
}

const pathwaysFromPathways = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/pathways/pathways', description: descriptions.pathways_pathways } })
  .input(commonPathwayQueryFormat.merge(commonHumanEdgeParamsFormat))
  .output(z.array(genesPathwaysFormat))
  .query(async ({ input }) => await findGenesFromPathways(input))

export const pathwaysPathwaysRouters = {
  pathwaysFromPathways
}
