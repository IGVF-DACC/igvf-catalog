import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { RouterFilterByID } from '../../genericRouters/routerFilterByID'

const schema = loadSchemaConfig()

const ontologyQueryFormat = z.object({
  term_id: z.string().optional(),
  term_name: z.string().optional()
})

const ontologyFormat = z.object({
  _id: z.string(),
  uri: z.string(),
  term_id: z.string(),
  term_name: z.string()
})

// CLO

let schemaObj = schema['clo cell']
let router = new RouterFilterBy(schemaObj)
let routerID = new RouterFilterByID(schemaObj)

export const cloOntology = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${router.apiName}`, description: router.apiSpecs.description } })
  .input(ontologyQueryFormat)
  .output(z.array(ontologyFormat))
  .query(async ({ input }) => await router.getObjects(input))

export const cloOntologyID = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${routerID.path}`, description: router.apiSpecs.description } })
  .input(z.object({ id: z.string() }))
  .output(ontologyFormat)
  .query(async ({ input }) => await routerID.getObjectById(input.id))

// UBERON

schemaObj = schema['uberon gross anatomical structure']
router = new RouterFilterBy(schemaObj)
routerID = new RouterFilterByID(schemaObj)

export const uberonOntology = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${router.apiName}`, description: router.apiSpecs.description } })
  .input(ontologyQueryFormat)
  .output(z.array(ontologyFormat))
  .query(async ({ input }) => await router.getObjects(input))

export const uberonOntologyID = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${routerID.path}`, description: router.apiSpecs.description } })
  .input(z.object({ id: z.string() }))
  .output(ontologyFormat)
  .query(async ({ input }) => await routerID.getObjectById(input.id))

// CL

schemaObj = schema['cl cell']
router = new RouterFilterBy(schemaObj)
routerID = new RouterFilterByID(schemaObj)

export const clOntology = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${router.apiName}`, description: router.apiSpecs.description } })
  .input(ontologyQueryFormat)
  .output(z.array(ontologyFormat))
  .query(async ({ input }) => await router.getObjects(input))

export const clOntologyID = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${routerID.path}`, description: router.apiSpecs.description } })
  .input(z.object({ id: z.string() }))
  .output(ontologyFormat)
  .query(async ({ input }) => await routerID.getObjectById(input.id))

// HPO

schemaObj = schema['hpo disease or phenotypic feature']
router = new RouterFilterBy(schemaObj)
routerID = new RouterFilterByID(schemaObj)

export const hpoOntology = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${router.apiName}`, description: router.apiSpecs.description } })
  .input(ontologyQueryFormat)
  .output(z.array(ontologyFormat))
  .query(async ({ input }) => await router.getObjects(input))

export const hpoOntologyID = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${routerID.path}`, description: router.apiSpecs.description } })
  .input(z.object({ id: z.string() }))
  .output(ontologyFormat)
  .query(async ({ input }) => await routerID.getObjectById(input.id))

// MONDO

schemaObj = schema['mondo disease or phenotypic feature']
router = new RouterFilterBy(schemaObj)
routerID = new RouterFilterByID(schemaObj)

export const mondoOntology = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${router.apiName}`, description: router.apiSpecs.description } })
  .input(ontologyQueryFormat)
  .output(z.array(ontologyFormat))
  .query(async ({ input }) => await router.getObjects(input))

export const mondoOntologyID = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${routerID.path}`, description: router.apiSpecs.description } })
  .input(z.object({ id: z.string() }))
  .output(ontologyFormat)
  .query(async ({ input }) => await routerID.getObjectById(input.id))

// GO - MOLECULAR ACTIVITY

schemaObj = schema['molecular activity']
router = new RouterFilterBy(schemaObj)
routerID = new RouterFilterByID(schemaObj)

export const goMLOntology = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${router.apiName}`, description: router.apiSpecs.description } })
  .input(ontologyQueryFormat)
  .output(z.array(ontologyFormat))
  .query(async ({ input }) => await router.getObjects(input))

export const goMLOntologyID = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${routerID.path}`, description: router.apiSpecs.description } })
  .input(z.object({ id: z.string() }))
  .output(ontologyFormat)
  .query(async ({ input }) => await routerID.getObjectById(input.id))

// GO - CELLULAR COMPONENT

schemaObj = schema['cellular component']
router = new RouterFilterBy(schemaObj)
routerID = new RouterFilterByID(schemaObj)

export const goCCOntology = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${router.apiName}`, description: router.apiSpecs.description } })
  .input(ontologyQueryFormat)
  .output(z.array(ontologyFormat))
  .query(async ({ input }) => await router.getObjects(input))

export const goCCOntologyID = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${routerID.path}`, description: router.apiSpecs.description } })
  .input(z.object({ id: z.string() }))
  .output(ontologyFormat)
  .query(async ({ input }) => await routerID.getObjectById(input.id))

// GO - BIOLOGICAL PROCESS

schemaObj = schema['biological process']
router = new RouterFilterBy(schemaObj)
routerID = new RouterFilterByID(schemaObj)

export const goBPOntology = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${router.apiName}`, description: router.apiSpecs.description } })
  .input(ontologyQueryFormat)
  .output(z.array(ontologyFormat))
  .query(async ({ input }) => await router.getObjects(input))

export const goBPOntologyID = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${routerID.path}`, description: router.apiSpecs.description } })
  .input(z.object({ id: z.string() }))
  .output(ontologyFormat)
  .query(async ({ input }) => await routerID.getObjectById(input.id))

// EFO

schemaObj = schema['experimental factor']
router = new RouterFilterBy(schemaObj)
routerID = new RouterFilterByID(schemaObj)

export const efoOntology = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${router.apiName}`, description: router.apiSpecs.description } })
  .input(ontologyQueryFormat)
  .output(z.array(ontologyFormat))
  .query(async ({ input }) => await router.getObjects(input))

export const efoOntologyID = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${routerID.path}`, description: router.apiSpecs.description } })
  .input(z.object({ id: z.string() }))
  .output(ontologyFormat)
  .query(async ({ input }) => await routerID.getObjectById(input.id))
