import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { RouterFilterByID } from '../../genericRouters/routerFilterByID'

const schema = loadSchemaConfig()
const schemaObj = schema.transcript

const transcriptQueryFormat = z.object({
  chr: z.string().optional(),
  gene_name: z.string().optional(),
  transcript_name: z.string().optional(),
  transcript_type: z.string().optional()
})

const transcriptFormat = z.object({
  _id: z.string(),
  chr: z.string(),
  start: z.string(),
  end: z.string(),
  gene_name: z.string(),
  transcript_id: z.string(),
  transcript_name: z.string(),
  transcript_type: z.string(),
  source: z.string(),
  source_url: z.string(),
  version: z.string()
})

const router = new RouterFilterBy(schemaObj)
const routerID = new RouterFilterByID(schemaObj)

export const transcripts = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${router.apiName}`, description: router.apiSpecs.description } })
  .input(transcriptQueryFormat)
  .output(z.array(transcriptFormat))
  .query(async ({ input }) => await router.getObjects(input))

export const transcriptID = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${routerID.path}`, description: router.apiSpecs.description } })
  .input(z.object({ id: z.string() }))
  .output(transcriptFormat)
  .query(async ({ input }) => await routerID.getObjectById(input.id))
