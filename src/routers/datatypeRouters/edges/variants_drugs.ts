import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { variantFormat, variantsQueryFormat } from '../nodes/variants'
import { drugFormat, drugsQueryFormat } from '../nodes/drugs'
import { paramsFormatType, preProcessRegionParam } from '../_helpers'
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
  'sequence variant': z.string().or(z.array(variantFormat)).optional(),
  drug: z.string().or(z.array(drugFormat)).optional(),
  _from: z.string(),
  _to: z.string(),
  gene_symbol: z.array(z.string()).optional(),
  pmid: z.string().optional(),
  study_parameters: z.array(studyParametersDict).optional(),
  phenotype_categories: z.array(z.string()).optional(),
  source: z.string(),
  source_url: z.string()
})
// maybe should rename '_from' or '_to' in final output

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
  if (input.variant_id !== undefined) {
    input._id = `variants/${input.variant_id}`
    delete input.variant_id
  }

  if (input.funseq_description !== undefined) {
    input['annotations.funseq_description'] = input.funseq_description
    delete input.funseq_description
  }
  return await router.getTargetsWithEdgeFilter(preProcessRegionParam(input, 'pos'), '_key', input.verbose === 'true', edgeQuery(input))
}
const variantsFromDrugs = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/drugs/variants', description: descriptions.drugs_variants } })
  .input(drugsQueryFormat.merge(variantsToDrugsQueryFormat))
  .output(z.array(variantsToDrugsFormat.omit({ _from: true })))
  .query(async ({ input }) => await conditionalDrugSearch(input))

const drugsFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/drugs', description: descriptions.variants_drugs } })
  .input(variantsQueryFormat.merge(variantsToDrugsQueryFormat))
  .output(z.array(variantsToDrugsFormat.omit({ _to: true })))
  .query(async ({ input }) => await conditionalVariantSearch(input))

export const variantsDrugsRouters = {
  variantsFromDrugs,
  drugsFromVariants
}
