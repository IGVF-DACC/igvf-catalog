import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { RouterFilterByID } from '../../genericRouters/routerFilterByID'

const schema = loadSchemaConfig()
const schemaObj = schema.gene

const geneQueryFormat = z.object({
  chr: z.string().optional(),
  gene_name: z.string().optional(),
  gene_type: z.string().optional()
})

const geneFormat = z.object({
  _id: z.string(),
  chr: z.string(),
  start: z.string(),
  end: z.string(),
  gene_id: z.string(),
  gene_name: z.string(),
  gene_type: z.string(),
  source: z.string(),
  source_url: z.string(),
  version: z.string()
})

const router = new RouterFilterBy(schemaObj)
const routerID = new RouterFilterByID(schemaObj)

export const genes = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${router.apiName}`, description: router.apiSpecs.description } })
  .input(geneQueryFormat)
  .output(z.array(geneFormat))
  .query(async ({ input }) => await router.getObjects(input))

export const geneID = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${routerID.path}`, description: router.apiSpecs.description } })
  .input(z.object({ id: z.string() }))
  .output(geneFormat)
  .query(async ({ input }) => await routerID.getObjectById(input.id))
