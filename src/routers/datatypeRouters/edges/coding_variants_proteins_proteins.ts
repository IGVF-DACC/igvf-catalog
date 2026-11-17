import { z } from 'zod/v4'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, withExpandedAssayTitles } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { commonHumanEdgeParamsFormat, proteinsCommonQueryFormat } from '../params'
import {
  codingVariantsFormat,
  pickCodingVariantFilters,
  ALT_AMINO_ACID_CODES
} from '../nodes/coding_variants'
import { proteinsProteinsFormat } from './proteins_proteins'
import { getSchema, getCollectionEnumValuesOrThrow } from '../schema'

const MAX_PAGE_SIZE = 100

const codingVariantsProteinsProteinsSchema = getSchema('data/schemas/edges/coding_variants_proteins_proteins.SemiQY2H.json')
const codingVariantsProteinsProteinsCollectionName = codingVariantsProteinsProteinsSchema.db_collection_name as string
const codingVariantSchema = getSchema('data/schemas/nodes/coding_variants.DbNSFP.json')
const codingVariantCollectionName = codingVariantSchema.db_collection_name as string
const proteinProteinSchema = getSchema('data/schemas/edges/proteins_proteins.ProteinsInteraction.json')
const proteinProteinCollectionName = proteinProteinSchema.db_collection_name as string
const proteinSchema = getSchema('data/schemas/nodes/proteins.GencodeProtein.json')
const proteinCollectionName = proteinSchema.db_collection_name as string

const methods = z.enum(getCollectionEnumValuesOrThrow('edges', 'coding_variants_proteins_proteins', 'method'))

// Only one hop deep: the PPI's own fields, with its two proteins left as bare id
// strings rather than recursively verbose-expanded - no precedent in this codebase for
// double expansion through an edge whose target is itself an edge, and it keeps response
// size bounded. Call /proteins/proteins separately for the PPI's own verbose protein data.
const proteinsProteinsEdgeFormat = proteinsProteinsFormat.omit({ protein_1: true, protein_2: true, preferred_assay_titles: true }).extend({
  protein_1: z.string(),
  protein_2: z.string()
})

export const codingVariantsProteinsProteinsFormat = z.object({
  _id: z.string(),
  coding_variant: z.string().or(codingVariantsFormat),
  proteins_proteins: z.string().or(proteinsProteinsEdgeFormat),
  consensus_score: z.number(),
  wt_consensus_score: z.number(),
  log2FC: z.number(),
  molecular_function: z.string(),
  method: z.string(),
  label: z.string(),
  class: z.string(),
  source: z.string(),
  source_url: z.string(),
  name: z.string(),
  inverse_name: z.string(),
  files_filesets: z.string(),
  preferred_assay_titles: z.array(z.string()).nullish()
})

const codingVariantsFromProteinsProteinsQueryFormat = z.object({
  coding_variant_name: z.string().trim().optional(),
  hgvsp: z.string().trim().optional(),
  protein_id: z.string().trim().optional(),
  uniprot_name: z.string().trim().optional(),
  gene_name: z.string().trim().optional(),
  amino_acid_position: z.string().trim().optional(),
  alt_amino_acid: z.enum(ALT_AMINO_ACID_CODES).optional(),
  transcript_id: z.string().trim().optional(),
  associated_protein_id: z.string().trim().optional(),
  associated_protein_name: z.string().trim().optional(),
  associated_uniprot_name: z.string().trim().optional(),
  method: methods.optional(),
  files_fileset: z.string().trim().optional(),
  consensus_score: z.string().trim().optional(),
  wt_consensus_score: z.string().trim().optional(),
  log2FC: z.string().trim().optional()
}).merge(commonHumanEdgeParamsFormat)
  // eslint-disable-next-line @typescript-eslint/naming-convention
  .transform(({ amino_acid_position, alt_amino_acid, coding_variant_name, uniprot_name, ...rest }) => ({
    ...rest,
    ...(amino_acid_position !== undefined ? { aapos: amino_acid_position } : {}),
    ...(alt_amino_acid !== undefined ? { alt: alt_amino_acid } : {}),
    ...(uniprot_name !== undefined ? { protein_name: uniprot_name } : {}),
    ...(coding_variant_name !== undefined ? { name: coding_variant_name.replaceAll('?', '!').replaceAll('>', '-') } : {})
  }))

const proteinsProteinsFromCodingVariantsQueryFormat = proteinsCommonQueryFormat.merge(z.object({
  associated_protein_id: z.string().trim().optional(),
  associated_protein_name: z.string().trim().optional(),
  associated_uniprot_name: z.string().trim().optional(),
  associated_uniprot_full_name: z.string().trim().optional(),
  method: methods.optional(),
  files_fileset: z.string().trim().optional(),
  consensus_score: z.string().trim().optional(),
  wt_consensus_score: z.string().trim().optional(),
  log2FC: z.string().trim().optional()
})).merge(commonHumanEdgeParamsFormat)

function validateCodingVariantInput (input: paramsFormatType): void {
  const hasCodingVariantFilter = ['name', 'hgvsp', 'protein_id', 'protein_name', 'gene_name', 'aapos', 'alt', 'transcript_id'].some(key => input[key] !== undefined)
  if (!hasCodingVariantFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one coding variant parameter must be defined: coding_variant_name, hgvsp, protein_id, uniprot_name, gene_name, amino_acid_position, alt_amino_acid, or transcript_id.'
    })
  }
}

function validateProteinInput (input: paramsFormatType): void {
  const isInvalidProteinFilter = !['protein_id', 'protein_name', 'uniprot_name', 'uniprot_full_name'].some(key => input[key] !== undefined)
  const isInvalidAssociatedProteinFilter = !['associated_protein_id', 'associated_protein_name', 'associated_uniprot_name', 'associated_uniprot_full_name'].some(key => input[key] !== undefined)
  if (isInvalidProteinFilter && isInvalidAssociatedProteinFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one protein must be defined: protein_id, protein_name, uniprot_name, uniprot_full_name (or the associated_ equivalents).'
    })
  }
}

const verboseProteinsProteinsReturn = `{
  _id: ppi._id,
  protein_1: ppi._from,
  protein_2: ppi._to,
  detection_method: ppi.detection_method,
  detection_method_code: ppi.detection_method_code,
  interaction_type: ppi.interaction_type,
  interaction_type_code: ppi.interaction_type_code,
  confidence_value_biogrid: ppi.confidence_value_biogrid,
  confidence_value_intact: ppi.confidence_value_intact,
  label: ppi.label,
  class: ppi.class,
  method: ppi.method,
  source_url: ppi.source_url,
  source: ppi.source,
  organism: ppi.organism,
  pmids: ppi.pmids,
  name: ppi.name,
  files_filesets: ppi.files_filesets
}`

async function findProteinsProteinsFromCodingVariants (input: paramsFormatType): Promise<any[]> {
  validateCodingVariantInput(input)
  delete input.organism

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
  const page = input.page as number
  delete input.page
  const verbose = input.verbose === 'true'
  delete input.verbose

  if (input.files_fileset !== undefined) {
    input.files_filesets = `files_filesets/${input.files_fileset as string}`
    delete input.files_fileset
  }

  const associatedProteinInput: paramsFormatType = {
    _key: input.associated_protein_id,
    name: input.associated_protein_name,
    uniprot_names: input.associated_uniprot_name
  }
  delete input.associated_protein_id
  delete input.associated_protein_name
  delete input.associated_uniprot_name

  let associatedProtein = getFilterStatements(proteinSchema, associatedProteinInput).replaceAll('record', 'associatedProtein')
  if (associatedProteinInput._key !== undefined) {
    const associatedProteinId = decodeURIComponent(associatedProteinInput._key as string)
    associatedProtein = `associatedProtein._key == '${associatedProteinId}' OR associatedProtein.protein_id == '${associatedProteinId}' OR '${associatedProteinId}' IN associatedProtein.uniprot_ids`
  }

  const codingVariantInput = pickCodingVariantFilters(input)
  for (const key of Object.keys(codingVariantInput)) {
    // eslint-disable-next-line @typescript-eslint/no-dynamic-delete
    delete input[key]
  }
  const codingVariantFilters = getFilterStatements(codingVariantSchema, codingVariantInput).replaceAll('record', 'cv')
  const edgeFilters = getFilterStatements(codingVariantsProteinsProteinsSchema, input)

  const filters = [edgeFilters]
  if (associatedProtein !== '') {
    filters.push('(ppi._from == associatedProtein._id OR ppi._to == associatedProtein._id)')
  }
  const combinedFilter = filters.filter((filter) => filter !== '').join(' AND ')

  const query = `
    ${associatedProtein !== '' ? `FOR associatedProtein IN ${proteinCollectionName} FILTER ${associatedProtein}` : ''}

    FOR cv IN ${codingVariantCollectionName}
      FILTER ${codingVariantFilters}
      FOR record IN ${codingVariantsProteinsProteinsCollectionName}
        FILTER record._from == cv._id
        LET ppi = DOCUMENT(record._to)
        ${combinedFilter !== '' ? `FILTER ${combinedFilter}` : ''}
        SORT record._key
        LIMIT ${page * limit}, ${limit}
        RETURN {
          _id: record._id,
          coding_variant: ${verbose ? `{${getDBReturnStatements(codingVariantSchema).replaceAll('record', 'cv')}}` : 'record._from'},
          proteins_proteins: ${verbose ? verboseProteinsProteinsReturn : 'record._to'},
          ${getDBReturnStatements(codingVariantsProteinsProteinsSchema, false, '', ['_from', '_to'])},
          preferred_assay_titles: DOCUMENT(record.files_filesets).preferred_assay_titles
        }
  `
  return await (await db.query(query)).all()
}

async function findCodingVariantsFromProteinsProteins (input: paramsFormatType): Promise<any[]> {
  validateProteinInput(input)
  delete input.organism

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
  const page = input.page as number
  delete input.page
  const verbose = input.verbose === 'true'
  delete input.verbose

  if (input.files_fileset !== undefined) {
    input.files_filesets = `files_filesets/${input.files_fileset as string}`
    delete input.files_fileset
  }

  const proteinInput: paramsFormatType = {
    _key: input.protein_id,
    name: input.protein_name,
    uniprot_names: input.uniprot_name,
    uniprot_full_names: input.uniprot_full_name
  }
  delete input.protein_id
  delete input.protein_name
  delete input.uniprot_name
  delete input.uniprot_full_name

  const associatedProteinInput: paramsFormatType = {
    _key: input.associated_protein_id,
    name: input.associated_protein_name,
    uniprot_names: input.associated_uniprot_name,
    uniprot_full_names: input.associated_uniprot_full_name
  }
  delete input.associated_protein_id
  delete input.associated_protein_name
  delete input.associated_uniprot_name
  delete input.associated_uniprot_full_name

  let protein = getFilterStatements(proteinSchema, proteinInput).replaceAll('record', 'protein')
  if (proteinInput._key !== undefined) {
    const proteinId = decodeURIComponent(proteinInput._key as string)
    protein = `protein._key == '${proteinId}' OR protein.protein_id == '${proteinId}' OR '${proteinId}' IN protein.uniprot_ids`
  }

  let associatedProtein = getFilterStatements(proteinSchema, associatedProteinInput).replaceAll('record', 'associatedProtein')
  if (associatedProteinInput._key !== undefined) {
    const associatedProteinId = decodeURIComponent(associatedProteinInput._key as string)
    associatedProtein = `associatedProtein._key == '${associatedProteinId}' OR associatedProtein.protein_id == '${associatedProteinId}' OR '${associatedProteinId}' IN associatedProtein.uniprot_ids`
  }

  const ppiFilters: string[] = []
  if (protein !== '') ppiFilters.push('(ppi._from == protein._id OR ppi._to == protein._id)')
  if (associatedProtein !== '') ppiFilters.push('(ppi._from == associatedProtein._id OR ppi._to == associatedProtein._id)')

  const edgeFilters = getFilterStatements(codingVariantsProteinsProteinsSchema, input)

  const query = `
    ${protein !== '' ? `FOR protein IN ${proteinCollectionName} FILTER ${protein}` : ''}
    ${associatedProtein !== '' ? `FOR associatedProtein IN ${proteinCollectionName} FILTER ${associatedProtein}` : ''}

    FOR ppi IN ${proteinProteinCollectionName}
      FILTER ${ppiFilters.join(' AND ')}
      FOR record IN ${codingVariantsProteinsProteinsCollectionName}
        FILTER record._to == ppi._id ${edgeFilters !== '' ? `AND ${edgeFilters}` : ''}
        LET cv = DOCUMENT(record._from)
        SORT record._key
        LIMIT ${page * limit}, ${limit}
        RETURN {
          _id: record._id,
          coding_variant: ${verbose ? `{${getDBReturnStatements(codingVariantSchema).replaceAll('record', 'cv')}}` : 'record._from'},
          proteins_proteins: ${verbose ? verboseProteinsProteinsReturn : 'record._to'},
          ${getDBReturnStatements(codingVariantsProteinsProteinsSchema, false, '', ['_from', '_to'])},
          preferred_assay_titles: DOCUMENT(record.files_filesets).preferred_assay_titles
        }
  `
  return await (await db.query(query)).all()
}

const proteinsProteinsFromCodingVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/coding-variants/ppi', description: descriptions.coding_variants_proteins_proteins } })
  .input(codingVariantsFromProteinsProteinsQueryFormat)
  .output(z.array(codingVariantsProteinsProteinsFormat))
  .query(async ({ input }) => withExpandedAssayTitles(await findProteinsProteinsFromCodingVariants(input)))

const codingVariantsFromProteinsProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/ppi/coding-variants', description: descriptions.proteins_proteins_coding_variants } })
  .input(proteinsProteinsFromCodingVariantsQueryFormat)
  .output(z.array(codingVariantsProteinsProteinsFormat))
  .query(async ({ input }) => withExpandedAssayTitles(await findCodingVariantsFromProteinsProteins(input)))

export const codingVariantsProteinsProteinsRouters = {
  proteinsProteinsFromCodingVariants,
  codingVariantsFromProteinsProteins
}
