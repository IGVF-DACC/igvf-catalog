import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { variantFormat, variantsQueryFormat } from '../nodes/variants'
import { ontologyFormat, ontologyQueryFormat } from '../nodes/ontologies'
import { paramsFormatType, preProcessRegionParam } from '../_helpers'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { descriptions } from '../descriptions'

const variantPhenotypeFormat = z.object({
  'sequence variant': z.string().or(z.array(variantFormat)).optional(),
  'ontology term': z.string().or(z.array(ontologyFormat)).optional(),
  p_val: z.number().nullable(),
  p_val_exponent: z.number().nullable(),
  p_val_mantissa: z.number().nullable(),
  beta: z.number().nullable(),
  beta_ci_lower: z.number().nullable(),
  beta_ci_upper: z.number().nullable(),
  oddsr_ci_lower: z.number().nullable(),
  oddsr_ci_upper: z.number().nullable(),
  lead_chrom: z.string().nullable(),
  lead_pos: z.string().nullable(),
  lead_ref: z.string().nullable(),
  lead_alt: z.string().nullable(),
  direction: z.string().nullable(),
  source: z.string().default('OpenTargets'),
  version: z.string().default('October 2022 (22.10)'),
  _from: z.string().nullable().optional()
}).transform(({ _from, ...rest }) => ({
  study_id: _from?.replace('studies/', ''),
  ...rest
}))

const schema = loadSchemaConfig()

const schemaObj = schema['study to variant']
const secondarySchemaObj = schema['study to variant to phenotype']

const studyObj = schema.study

const routerEdge = new RouterEdges(schemaObj, new RouterEdges(secondarySchemaObj))
const studyRouter = new RouterFilterBy(studyObj)

async function studySearchFilters (input: paramsFormatType): Promise<string> {
  const studyFilters = []

  const queryFilter: Record<string, string> = {}
  if (input.pmid !== undefined) {
    queryFilter.pmid = `PMID:${input.pmid as string}`
    delete input.pmid

    let studies = await studyRouter.getObjects(queryFilter)

    if (studies.length > 0) {
      studies = studies.map((s) => `studies/${s._id as string}`)
      studyFilters.push(`record._from IN ['${studies.join('\',\'')}']`)
    }
  }

  if (input.p_value !== undefined) {
    studyFilters.push(`${routerEdge.getFilterStatements({ p_val: input.p_value })}`)
    delete input.p_value
  }

  return studyFilters.join(' and ')
}

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

  const studiesFilter = await studySearchFilters(input)
  return await routerEdge.getSecondaryTargetsFromHyperEdge(preProcessRegionParam(input, 'pos'), input.page as number, '_key', queryOptions, studiesFilter, input.verbose === 'true')
}

const variantsFromPhenotypeID = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/phenotypes/{phenotype_id}/variants', description: descriptions.phenotypes_id_variants } })
  .input(z.object({ phenotype_id: z.string(), pmid: z.string().optional(), p_value: z.string().optional(), page: z.number().default(0), verbose: z.enum(['true', 'false']).default('false') }))
  .output(z.array(variantPhenotypeFormat))
  .query(async ({ input }) => await routerEdge.getPrimaryTargetFromHyperEdgeByID(input.phenotype_id, input.page, '_key', await studySearchFilters(input), input.verbose === 'true'))

const variantsFromPhenotypes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/phenotypes/variants', description: descriptions.phenotypes_variants } })
  .input(ontologyQueryFormat.omit({ source: true, subontology: true }).merge(z.object({ pmid: z.string().optional(), p_value: z.string().optional(), verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(variantPhenotypeFormat))
  .query(async ({ input }) => await routerEdge.getPrimaryTargetsFromHyperEdge(input, input.page, '_key', await studySearchFilters(input), input.verbose === 'true'))

const phenotypesFromVariantID = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/{variant_id}/phenotypes', description: descriptions.variants_id_phenotypes } })
  .input(z.object({ variant_id: z.string(), pmid: z.string().optional(), p_value: z.string().optional(), page: z.number().default(0), verbose: z.enum(['true', 'false']).default('false') }))
  .output(z.array(variantPhenotypeFormat))
  .query(async ({ input }) => await routerEdge.getSecondaryTargetFromHyperEdgeByID(input.variant_id, input.page, '_key', await studySearchFilters(input), input.verbose === 'true'))

const phenotypesFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/phenotypes', description: descriptions.variants_phenotypes } })
  .input(variantsQueryFormat.omit({ funseq_description: true }).merge(z.object({ pmid: z.string().optional(), p_value: z.string().optional(), verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(variantPhenotypeFormat))
  .query(async ({ input }) => await variantSearch(input))

export const variantsPhenotypesRouters = {
  variantsFromPhenotypeID,
  variantsFromPhenotypes,
  phenotypesFromVariantID,
  phenotypesFromVariants
}
