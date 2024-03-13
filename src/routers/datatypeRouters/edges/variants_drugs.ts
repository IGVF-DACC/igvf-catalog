import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { variantFormat, variantsQueryFormat } from '../nodes/variants'
import { drugFormat, drugsQueryFormat } from '../nodes/drugs'
import { paramsFormatType } from '../_helpers'
import { TRPCError } from '@trpc/server'
import { descriptions } from '../descriptions'

const schema = loadSchemaConfig()

const variantsToDrugsQueryFormat = z.object({
  pmid: z.string().trim().optional(),
  phenotype_categories: z.string().trim().optional(),
  verbose: z.enum(['true', 'false']).default('false')
})

const studyParametersDict = z.object({
  study_parameter_id: z.string(),
  study_type: z.string().optional(),
  study_cases: z.string().optional(),
  study_controls: z.string().optional(),
  'p-value': z.string().optional(),
  biogeographical_groups: z.string().optional()
})

const variantsToDrugsFormat = z.object({
  drug: z.string().or(z.array(drugFormat)).optional(),
  _from: z.string(),
  gene_symbol: z.array(z.string()).optional(),
  pmid: z.string().optional(),
  study_parameters: z.array(studyParametersDict).optional(),
  phenotype_categories: z.array(z.string()).optional(),
  source: z.string(),
  source_url: z.string()
}).transform(({ _from, ...rest }) => ({ 'sequence variant': _from, ...rest }))

const drugsToVariantsFormat = z.object({
  'sequence variant': z.string().or(variantFormat).optional(),
  _to: z.string(),
  gene_symbol: z.array(z.string()).optional(),
  pmid: z.string().optional(),
  study_parameters: z.array(studyParametersDict).optional(),
  phenotype_categories: z.array(z.string()).optional(),
  source: z.string(),
  source_url: z.string()
}).transform(({ _to, ...rest }) => ({ drug: _to, ...rest }))

const schemaObj = schema['variant to drug']
const router = new RouterEdges(schemaObj)

function edgeQuery (input: paramsFormatType): string {
  const query = []

  if (input.pmid !== undefined && input.pmid !== '') {
    query.push(`record.pmid == '${input.pmid}'`)
    delete input.pmid
  }

  if (input.phenotype_categories !== undefined && input.phenotype_categories !== '') {
    query.push(`'${input.phenotype_categories}' IN record.phenotype_categories`)
    delete input.phenotype_categories
  }

  if (Object.keys(input).filter(item => !['page', 'verbose'].includes(item)).length === 0) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one node property for variant / drug must be defined.'
    })
  }

  return query.join(' and ')
}

async function conditionalDrugSearch (input: paramsFormatType): Promise<any[]> {
  if (input.drug_id !== undefined) {
    input._id = `drugs/${input.drug_id}`
    delete input.drug_id
  }
  return await router.getSources(input, '_key', input.verbose === 'true', edgeQuery(input))
}

async function conditionalVariantSearch (input: paramsFormatType): Promise<any []> {
  // removed region query
  if (input.variant_id !== undefined) {
    input._id = `variants/${input.variant_id}`
    delete input.variant_id
  }

  return await router.getTargetsWithEdgeFilter(input, '_key', '', input.verbose === 'true', edgeQuery(input))
}

const drugsQuery = drugsQueryFormat.merge(
  variantsToDrugsQueryFormat
).merge(z.object({drug_name: z.string().trim().optional()})).omit({
  name: true
}).transform(({ drug_name, ...rest }) => ({ name: drug_name, ...rest }))

const variantsFromDrugs = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/drugs/variants', description: descriptions.drugs_variants } })
  .input(drugsQuery)
  .output(z.array(drugsToVariantsFormat))
  .query(async ({ input }) => await conditionalDrugSearch(input))

const drugsFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/drugs', description: descriptions.variants_drugs } })
  .input(variantsQueryFormat.omit({ region: true, funseq_description: true }).merge(variantsToDrugsQueryFormat))
  .output(z.array(variantsToDrugsFormat))
  .query(async ({ input }) => await conditionalVariantSearch(input))

export const variantsDrugsRouters = {
  variantsFromDrugs,
  drugsFromVariants
}
