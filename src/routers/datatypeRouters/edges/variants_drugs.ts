import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { variantFormat, variantIDSearch } from '../nodes/variants'
import { drugFormat } from '../nodes/drugs'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { TRPCError } from '@trpc/server'
import { descriptions } from '../descriptions'
import { commonDrugsQueryFormat, commonHumanEdgeParamsFormat, variantsCommonQueryFormat } from '../params'

const MAX_PAGE_SIZE = 100

const schema = loadSchemaConfig()
const variantToDrugSchemaObj = schema['variant to drug']
const drugSchemaObj = schema.drug
const humanVariantSchema = schema['sequence variant']

const phenotypeList = z.enum([
  'Dosage', 'Efficacy', 'Metabolism/PK', 'Other', 'PD', 'Toxicity'
])

const variantsDrugsQueryFormat = z.object({
  phenotype_categories: phenotypeList.optional(),
  pmid: z.string().trim().optional()
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
  drug: z.string().or(drugFormat).optional(),
  _from: z.string(),
  gene_symbol: z.array(z.string()).optional(),
  pmid: z.string().optional(),
  study_parameters: z.array(studyParametersDict).optional(),
  phenotype_categories: z.array(z.string()).optional(),
  source: z.string(),
  source_url: z.string(),
  name: z.string()
}).transform(({ _from, ...rest }) => ({ sequence_variant: _from, ...rest }))

const drugsToVariantsFormat = z.object({
  sequence_variant: z.string().or(variantFormat).optional(),
  _to: z.string(),
  gene_symbol: z.array(z.string()).optional(),
  pmid: z.string().optional(),
  study_parameters: z.array(studyParametersDict).optional(),
  phenotype_categories: z.array(z.string()).optional(),
  source: z.string(),
  source_url: z.string(),
  name: z.string()
}).transform(({ _to, ...rest }) => ({ drug: _to, ...rest }))

function validateInput (input: paramsFormatType): void {
  if (Object.keys(input).filter(item => !['limit', 'page', 'verbose', 'organism', 'pmid', 'phenotype_categories'].includes(item)).length === 0) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one node property for variant / drug must be defined.'
    })
  }
  if ((input.chr === undefined && input.position !== undefined) || (input.chr !== undefined && input.position === undefined)) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'Chromosome and position must be defined together.'
    })
  }
}

function getCustomFilters (input: paramsFormatType): string {
  const query = []

  if (input.pmid !== undefined && input.pmid !== '') {
    query.push(`record.pmid == '${input.pmid as string}'`)
    delete input.pmid
  }

  if (input.phenotype_categories !== undefined && input.phenotype_categories !== '') {
    query.push(`'${input.phenotype_categories as string}' IN record.phenotype_categories`)
    delete input.phenotype_categories
  }
  return query.join(' and ')
}

async function variantsFromDrugSearch (input: paramsFormatType): Promise<any[]> {
  validateInput(input)
  delete input.organism
  if (input.drug_id !== undefined) {
    input._id = `drugs/${input.drug_id as string}`
    delete input.drug_id
  }
  if (input.drug_name !== undefined) {
    input.name = input.drug_name
    delete input.drug_name
  }

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
  let customFilter = getCustomFilters(input)
  if (customFilter !== '') {
    customFilter = `and ${customFilter}`
  }

  const verbose = input.verbose === 'true'

  const variantVerboseQuery = `
    FOR otherRecord IN ${humanVariantSchema.db_collection_name as string}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
    RETURN {${getDBReturnStatements(humanVariantSchema).replaceAll('record', 'otherRecord')}}
  `

  const query = `
    LET drugs = (
      FOR record IN ${drugSchemaObj.db_collection_name as string}
      FILTER ${getFilterStatements(drugSchemaObj, input)}
      RETURN record._id
    )

    FOR record IN ${variantToDrugSchemaObj.db_collection_name as string}
      FILTER record._to IN drugs ${customFilter}
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        ${getDBReturnStatements(variantToDrugSchemaObj)},
        'sequence_variant': ${verbose ? `(${variantVerboseQuery})[0]` : 'record._from'},
        'name': record.inverse_name // endpoint is opposite to ArangoDB collection name
      }
  `
  return await (await db.query(query)).all()
}

async function drugsFromVariantSearch (input: paramsFormatType): Promise<any []> {
  validateInput(input)
  delete input.organism

  // eslint-disable-next-line @typescript-eslint/naming-convention
  const variantInput: paramsFormatType = (({ variant_id, spdi, hgvs, rsid, chr, position }) => ({ variant_id, spdi, hgvs, rsid, chr, position }))(input)
  delete input.variant_id
  delete input.spdi
  delete input.hgvs
  delete input.rsid
  delete input.chr
  delete input.position
  const variantIDs = await variantIDSearch(variantInput)

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let customFilter = getCustomFilters(input)
  if (customFilter !== '') {
    customFilter = `and ${customFilter}`
  }

  const verbose = input.verbose === 'true'

  const drugVerboseQuery = `
    FOR otherRecord IN ${drugSchemaObj.db_collection_name as string}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${getDBReturnStatements(drugSchemaObj).replaceAll('record', 'otherRecord')}}
  `
  const query = `

    FOR record IN ${variantToDrugSchemaObj.db_collection_name as string}
      FILTER record._from IN ['${variantIDs.join('\', \'')}'] ${customFilter}
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        ${getDBReturnStatements(variantToDrugSchemaObj)},
        'drug': ${verbose ? `(${drugVerboseQuery})[0]` : 'record._to'},
        'name': record.name
      }
  `
  return await (await db.query(query)).all()
}

const variantsFromDrugs = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/drugs/variants', description: descriptions.drugs_variants } })
  .input(commonDrugsQueryFormat.merge(variantsDrugsQueryFormat).merge(commonHumanEdgeParamsFormat))
  .output(z.array(drugsToVariantsFormat))
  .query(async ({ input }) => await variantsFromDrugSearch(input))

const drugsFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/drugs', description: descriptions.variants_drugs } })
  .input(variantsCommonQueryFormat.merge(variantsDrugsQueryFormat).merge(commonHumanEdgeParamsFormat))
  .output(z.array(variantsToDrugsFormat))
  .query(async ({ input }) => await drugsFromVariantSearch(input))

export const variantsDrugsRouters = {
  variantsFromDrugs,
  drugsFromVariants
}
