import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { RouterFilterByID } from '../../genericRouters/routerFilterByID'
import { RouterFuzzy } from '../../genericRouters/routerFuzzy'

const schema = loadSchemaConfig()

export const ontologyQueryFormat = z.object({
  term_id: z.string().optional(),
  term_name: z.string().optional(),
  source: z.string().optional(),
  subontology: z.string().optional(),
  page: z.number().default(0)
})

const subontologyQueryFormat = z.object({
  term_id: z.string().optional(),
  term_name: z.string().optional(),
  page: z.number().default(0)
})

const ontologySearchFormat = z.object({
  term: z.string(),
  page: z.number().default(0)
})

export const ontologyFormat = z.object({
  uri: z.string(),
  term_id: z.string(),
  term_name: z.string(),
  description: z.string().nullable(),
  source: z.string().optional(),
  subontology: z.string().optional()
})

const schemaObj = schema['ontology term']
const router = new RouterFilterBy(schemaObj)
const routerID = new RouterFilterByID(schemaObj)
const routerSearch = new RouterFuzzy(schemaObj)

export const ontologyTerm = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/${router.apiName}`, description: router.apiSpecs.description } })
  .input(ontologyQueryFormat)
  .output(z.array(ontologyFormat))
  .query(async ({ input }) => await router.getObjects(input))

export const ontologyTermID = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/${routerID.path}`, description: router.apiSpecs.description } })
  .input(z.object({ id: z.string() }))
  .output(ontologyFormat)
  .query(async ({ input }) => await routerID.getObjectById(input.id))

export const ontologyTermSearch = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/${routerSearch.path}`, description: router.apiSpecs.description } })
  .input(ontologySearchFormat)
  .output(z.array(ontologyFormat))
  .query(async ({ input }) => await routerSearch.getObjectsByFuzzyTextSearch(input.term, input.page ?? 0))

// aliases

export const ontologyGoTermMF = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/go-mf-terms', description: router.apiSpecs.description } })
  .input(subontologyQueryFormat)
  .output(z.array(ontologyFormat))
  .query(async ({ input }) => await router.getObjects({ ...input, ...{ source: 'GO', subontology: 'molecular_function' } }))

export const ontologyGoTermCC = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/go-cc-terms', description: router.apiSpecs.description } })
  .input(subontologyQueryFormat)
  .output(z.array(ontologyFormat))
  .query(async ({ input }) => await router.getObjects({ ...input, ...{ source: 'GO', subontology: 'cellular_component' } }))

export const ontologyGoTermBP = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/go-bp-terms', description: router.apiSpecs.description } })
  .input(subontologyQueryFormat)
  .output(z.array(ontologyFormat))
  .query(async ({ input }) => await router.getObjects({ ...input, ...{ source: 'GO', subontology: 'biological_process' } }))

export const ontologyRouters = {
  ontologyTerm,
  ontologyTermID,
  ontologyTermSearch,
  ontologyGoTermBP,
  ontologyGoTermCC,
  ontologyGoTermMF
}
