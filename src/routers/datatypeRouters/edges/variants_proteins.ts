import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { ontologyFormat } from '../nodes/ontologies'
import { paramsFormatType, preProcessRegionParam } from '../_helpers'
import { variantSimplifiedFormat, variantsQueryFormat } from '../nodes/variants'
import { proteinFormat, proteinsQueryFormat } from '../nodes/proteins'
import { descriptions } from '../descriptions'

const schema = loadSchemaConfig()

// primary: variants -> proteins (generic context)
const schemaObj = schema['allele specific binding']

// secondary: variants -> (edge) proteins, (edge) -> biosample terms (cell-type specific context)
const secondarySchemaObj = schema['allele specific binding cell ontology']
const routerEdge = new RouterEdges(schemaObj, new RouterEdges(secondarySchemaObj))

const AsbQueryFormat = z.object({
  verbose: z.enum(['true', 'false']).default('false'),
  page: z.number().default(0)

})

const AsbFormat = z.object({
  'sequence variant': z.string().or(z.array(variantSimplifiedFormat)).optional(),
  protein: z.string().or(z.array(proteinFormat.omit({ dbxrefs: true }))).optional(),
  'ontology term': z.string().or(z.array(ontologyFormat)).optional(),
  biological_context: z.string().nullable(),
  es_mean_ref: z.string().nullable(),
  es_mean_alt: z.string().nullable(),
  fdrp_bh_ref: z.string().nullable(),
  fdrp_bh_alt: z.string().nullable(),
  motif_fc: z.string().nullable(),
  motif_pos: z.string().nullable(),
  motif_orient: z.string().nullable(),
  motif_conc: z.string().nullable(),
  motif: z.string().nullable(),
  source: z.string().nullable(),
  source_url: z.string().nullable()
})

async function secondaryProteinSearch (input: paramsFormatType): Promise<any[]> {
  if (input.protein_id !== undefined) {
    input._id = `proteins/${input.protein_id as string}`
    delete input.protein_id
  }

  return await routerEdge.getSecondaryTargetsAndEdgeObjectsByTargets(input, input.page as number, '_key', '', '', input.verbose === 'true', 'hyperedge')
}

async function secondaryVariantSearch (input: paramsFormatType): Promise<any[]> {
  let queryOptions = ''
  if (input.region !== undefined) {
    queryOptions = 'OPTIONS { indexHint: "region", forceIndexHint: true }'
  }

  if (input.variant_id !== undefined) {
    input._id = `variants/${input.variant_id as string}`
    delete input.variant_id
  }

  if (input.funseq_description !== undefined) {
    input['annotations.funseq_description'] = input.funseq_description
    delete input.funseq_description
  }

  return await routerEdge.getSecondaryTargetsAndEdgeObjectsBySource(preProcessRegionParam(input, 'pos'), input.page as number, '_key', queryOptions, '', input.verbose === 'true', 'hyperedge')
}

// Only keep cell-type scpecific queries for ASB endpoints here
// /variants/proteins, /proteins/variants -> returns cell-type specific values from hyperedges & generic values from primary edges (motif-relevant values)
const variantsFromProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/variants', description: descriptions.proteins_variants } })
  .input(proteinsQueryFormat.merge(AsbQueryFormat))
  .output(z.array(AsbFormat))
  .query(async ({ input }) => await secondaryProteinSearch(input))

const proteinsFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/proteins', description: descriptions.variants_proteins } })
  .input(variantsQueryFormat.merge(AsbQueryFormat))
  .output(z.array(AsbFormat))
  .query(async ({ input }) => await secondaryVariantSearch(input))

export const variantsProteinsRouters = {
  proteinsFromVariants,
  variantsFromProteins
}
