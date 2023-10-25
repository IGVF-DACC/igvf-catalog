import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { ontologyFormat, ontologyQueryFormat } from '../nodes/ontologies'
import { paramsFormatType, preProcessRegionParam } from '../_helpers'

import { variantFormat, variantsQueryFormat } from '../nodes/variants'
import { proteinFormat, proteinsQueryFormat } from '../nodes/proteins'


const schema = loadSchemaConfig()

// primary: variants -> proteins
const schemaObj = schema['allele specific binding']

// secondary: variants -> (edge) proteins, (edge) -> terms
const secondarySchemaObj = schema['allele specific binding cell ontology']
const routerEdge = new RouterEdges(schemaObj, new RouterEdges(secondarySchemaObj))

//Todo: remove asb part from variants_genes.ts
//remove console.log(query)

const variantsAsbQueryFormat = z.object({
    verbose: z.enum(['true', 'false']).default('false'),
    page: z.number().default(0)

})

const asbFormat = z.object({
    'sequence variant': z.string().or(z.array(variantFormat)).optional(),
    'protein': z.string().or(z.array(proteinFormat)).optional(),
    //'ontology term': z.string().or(z.array(ontologyFormat)).optional(),
    biological_context: z.string().nullable(),
    motif_fc: z.string().nullable(),
    motif_pos: z.string().nullable(),
    motif_orient: z.string().nullable(),
    motif_conc: z.string().nullable(),
    motif: z.string().nullable(),
    source: z.string().nullable(),
})

const asbFormatValue = z.object({
    'ontology term': z.string().or(z.array(ontologyFormat)).optional(),
    es_mean_ref: z.string().nullable(),
    es_mean_alt: z.string().nullable(),
    fdrp_bh_ref: z.string().nullable(),
    fdrp_bh_alt: z.string().nullable(),
    biological_context: z.string().nullable(),
    source_url: z.string().nullable()
})

//copied from variants_phenotypes.ts, removed Filter
async function variantSearch (input: paramsFormatType): Promise<any[]> {
    let queryOptions = ''
    if (input.region !== undefined) {
      queryOptions = 'OPTIONS { indexHint: "region", forceIndexHint: true }'
    }

    if (input.funseq_description !== undefined) {
      input['annotations.funseq_description'] = input.funseq_description
      delete input.funseq_description
    }

    if (input.source !== undefined) {
      input[`annotations.freq.${input.source}.alt`] = `range:${input.min_alt_freq as string}-${input.max_alt_freq as string}`
      delete input.min_alt_freq
      delete input.max_alt_freq
      delete input.source
    }

    return await routerEdge.getSecondaryTargetsFromHyperEdge(preProcessRegionParam(input, 'pos'), input.page as number, '_key', queryOptions, '', input.verbose === 'true', 'hyperedge', 'source')
}

const proteinsFromVariantID = publicProcedure
    .meta({ openapi: { method: 'GET', path: '/variants/{variant_id}/proteins' } })
    .input(z.object({ variant_id: z.string() }).merge(variantsAsbQueryFormat))
    .output(z.array(asbFormat))
    .query(async ({ input }) => await routerEdge.getTargetsByID(input.variant_id, input.page, '_key', input.verbose === 'true'))

const proteinsFromVariants = publicProcedure
    .meta({ openapi: { method: 'GET', path: '/variants/proteins' } })
    .input(variantsQueryFormat.merge(variantsAsbQueryFormat))
    .output(z.array(asbFormat))
    .query(async ({ input}) => await routerEdge.getTargets(preProcessRegionParam(input, 'pos'), '_key', input.verbose === 'true'))

const variantsFromProteinID = publicProcedure
    .meta({ openapi: { method: 'GET', path: '/proteins/{protein_id}/variants' }})
    .input(z.object({ protein_id: z.string() }).merge(variantsAsbQueryFormat))
    .output(z.array(asbFormat))
    .query(async ({ input }) => await routerEdge.getSourcesByID(input.protein_id, input.page, '_key', input.verbose === 'true'))

const variantsFromProteins = publicProcedure
    .meta({ openapi: { method: 'GET', path: '/proteins/variants' }})
    .input(proteinsQueryFormat.merge(variantsAsbQueryFormat))
    .output(z.array(asbFormat))
    .query(async ({ input }) => await routerEdge.getSources(input, '_key', input.verbose === 'true'))

const termsFromProteinID = publicProcedure
    .meta({ openapi: { method: 'GET', path: '/proteins/{protein_id}/terms' } })
    .input(z.object({ protein_id: z.string() }).merge(variantsAsbQueryFormat))
    .output(z.array(asbFormatValue))
    .query(async ({ input }) => await routerEdge.getSecondaryTargetFromHyperEdgeByID(input.protein_id, input.page, '', '', input.verbose === 'true','hyperedge' ))

const termsFromVariantsID = publicProcedure
    .meta({ openapi: { method: 'GET', path: '/variants/{variant_id}/terms' } })
    .input(z.object({ variant_id: z.string() }).merge(variantsAsbQueryFormat))
    .output(z.array(asbFormatValue))
    .query(async ({ input }) => await routerEdge.getSecondaryTargetFromHyperEdgeByID(input.variant_id, input.page, '', '', input.verbose === 'true','hyperedge','source' ))


const termsFromVariants = publicProcedure
    .meta({ openapi: { method: 'GET', path: '/variants/terms' } })
    .input(variantsQueryFormat.omit({ funseq_description: true }).merge(variantsAsbQueryFormat))
    .output(z.array(asbFormatValue))
    .query(async ({ input }) => await variantSearch(input))

const termsFromProteins = publicProcedure
    .meta({ openapi: { method: 'GET', path: '/proteins/terms' } })
    .input(proteinsQueryFormat.merge(variantsAsbQueryFormat))
    .output(z.array(asbFormatValue))
    .query(async ({ input }) => await routerEdge.getSecondaryTargetsFromHyperEdge(input, input.page as number, '_key', '', '', input.verbose === 'true', 'hyperedge'))

const variantsFromTermID = publicProcedure
    .meta({ openapi: { method: 'GET', path: '/terms/{term_id}/variants' } })
    .input(z.object({ term_id: z.string() }).merge(variantsAsbQueryFormat))
    .output(z.array(asbFormat))
    .query(async ({ input }) => await routerEdge.getPrimaryTargetFromHyperEdgeByID(input.term_id, input.page, '_key', '', input.verbose === 'true'))
    // needs to add cell-specific values from variants_proteins_terms

const variantsFromTerms = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/terms/variants' } })
  .input(ontologyQueryFormat.omit({ source: true, subontology: true }).merge(variantsAsbQueryFormat))
  .output(z.array(asbFormat))
  .query(async ({ input }) => await routerEdge.getPrimaryTargetsFromHyperEdge(input, input.page, '_key', '', input.verbose === 'true'))

//might want to merge {id} endpoints
export const variantsProteinsRouters = {
    proteinsFromVariantID,
    proteinsFromVariants,
    variantsFromProteinID,
    variantsFromProteins,
    termsFromProteinID,
    termsFromProteins,
    termsFromVariantsID,
    termsFromVariants,
    variantsFromTermID,
    variantsFromTerms
}
//TODO: rename terms -> biosamples
