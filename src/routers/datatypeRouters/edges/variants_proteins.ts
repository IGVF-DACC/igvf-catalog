import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { ontologyFormat } from '../nodes/ontologies'
import { variantFormat, variantsQueryFormat } from '../nodes/variants'
import { proteinFormat, proteinsQueryFormat } from '../nodes/proteins'


const schema = loadSchemaConfig()

// primary: variants -> proteins
const schemaObj = schema['allele specific binding']

// secondary: variants -> (edge) proteins, (edge) -> terms
const secondarySchemaObj = schema['allele specific binding cell ontology']
const routerEdge = new RouterEdges(schemaObj, new RouterEdges(secondarySchemaObj))

//Todo: remove asb part from variants_genes.ts

const variantsAsbQueryFormat = z.object({
    verbose: z.enum(['true', 'false']).default('false'),
    page: z.number().default(0)

})

const asbFormat = z.object({
    //sequence variant
    //_from
    //protein
    'ontology term': z.string().or(z.array(ontologyFormat)).optional(),
    biological_context: z.string().nullable(),
    motif_fc: z.string().nullable(),
    motif_pos: z.string().nullable(),
    motif_orient: z.string().nullable(),
    motif_conc: z.string().nullable(),
    motif: z.string().nullable(),
    source: z.string().nullable(),
})

const asbFormatValue = z.object({

    es_mean_ref: z.number().nullable(),
    es_mean_alt: z.number().nullable(),
    fdrp_bh_ref: z.number().nullable(),
    fdrp_bh_alt: z.number().nullable(),
    biological_context: z.string().nullable(),
    source_url: z.string().nullable()
})

//given a biological context or ontology term

//proteinsFromVariants
//given a genome region -> genetic variants -> proteins

//variantsFromProteins
//given a protein name/id

// exampleID: 6a8aca69286bb09fcf2eea0a48be0790a61a421a44ae2433d20315e46021583d
const proteinsFromVariantID = publicProcedure
    .meta({ openapi: { method: 'GET', path: '/variants/{variant_id}/proteins' } })
    .input(z.object({ variant_id: z.string() }).merge(variantsAsbQueryFormat))
    .output(z.array(asbFormat))
    .query(async ({ input }) => await routerEdge.getTargetsByID(input.variant_id, input.page, '_key', input.verbose === 'true'))

const variantsFromProteinID = publicProcedure
    .meta({ openapi: { method: 'GET', path: '/proteins/{protein_id}/variants' }})
    .input(z.object({ protein_id: z.string() }).merge(variantsAsbQueryFormat))
    .output(z.array(asbFormat))
    .query(async ({ input }) => await routerEdge.getSourcesByID(input.protein_id, input.page, '_key', input.verbose === 'true'))

const termsFromVariantID = publicProcedure
    .meta({ openapi: { method: 'GET', path: '/proteins/{protein_id}/terms' } })
    .input(z.object({ protein_id: z.string() }).merge(variantsAsbQueryFormat))
    .output(z.array(asbFormatValue))
    .query(async ({ input }) => await routerEdge.getSecondaryTargetFromHyperEdgeByID(input.protein_id, input.page, '', '', input.verbose === 'true','hyperedge' ))

export const variantsProteinsRouters = {
    proteinsFromVariantID,
    variantsFromProteinID,
    termsFromVariantID
}
