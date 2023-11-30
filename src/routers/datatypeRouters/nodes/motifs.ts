import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'

const schema = loadSchemaConfig()

export const motifsQueryFormat = z.object({
  name: z.string().trim(),
  source: z.string().trim().optional(),
  page: z.number().default(0)
})

export const motifFormat = z.object({
  _id: z.string(),
  tf_name: z.string(),
  length: z.number(),
  pwm: z.array(z.array(z.string().optional())),
  source: z.string(),
  source_url: z.string()
})

const schemaObj = schema.motif
const router = new RouterFilterBy(schemaObj)

function preProcessInput (input: paramsFormatType): paramsFormatType {
  input.tf_name = (input.name as string).toUpperCase()
  delete input.name
  return input
}

const motifs = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/${router.apiName}`, description: descriptions.motifs } })
  .input(motifsQueryFormat)
  .output(z.array(motifFormat))
  .query(async ({ input }) => await router.getObjects(preProcessInput(input)))

export const motifsRouters = {
  motifs
}
