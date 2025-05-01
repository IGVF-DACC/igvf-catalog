import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, verboseItems } from '../_helpers'
import { descriptions } from '../descriptions'

const MAX_PAGE_SIZE = 100

const schema = loadSchemaConfig()

const genesToTranscriptsSchema = schema['transcribed to']
const transcriptsToProteinsSchema = schema['translates to']
const proteinsProteinsSchema = schema['protein to protein interaction']
const geneGeneSchema = schema['gene to gene interaction']

const geneSchema = schema.gene
const proteinSchema = schema.protein
const variantSchema = schema['sequence variant']

const variantToGeneSchema = schema['variant to gene association']
const variantToProteinSchema = schema['allele specific binding']

const variantQueryFormat = z.object({
  variant_id: z.string(),
  page: z.number().default(0),
  limit: z.number().optional()
})

const queryFormat = z.object({
  query: z.string(),
  page: z.number().default(0),
  limit: z.number().optional()
})

const relatedGeneFormat = z.object({
  _id: z.string(),
  chr: z.string(),
  gene_id: z.string(),
  hgnc: z.string().nullish(),
  name: z.string(),
  organism: z.string()
})

const relatedProteinFormat = z.object({
  _id: z.string(),
  name: z.string()
})

const relatedQTLFormat = z.object({
  label: z.string(),
  source: z.string(),
  log10pvalue: z.number(),
  biological_context: z.string()
})

const relatedMotifFormat = z.object({
  motif: z.string().nullable(),
  source: z.string()
})

const geneProteinRelatedFormat = z.object({
  protein: relatedProteinFormat.nullish(),
  gene: relatedGeneFormat.nullish(),
  related: z.array(relatedProteinFormat.or(relatedGeneFormat)).nullish()
})

const sequenceVariantRelatedFormat = z.object({
  sequence_variant: z.object({
    _id: z.string(),
    chr: z.string(),
    pos: z.number(),
    rsid: z.array(z.string()).nullish(),
    ref: z.string(),
    alt: z.string(),
    spdi: z.string(),
    hgvs: z.string()
  }),
  related: z.array(z.object({
    gene: (relatedGeneFormat.nullish()).or(z.string()),
    protein: relatedProteinFormat.nullish(),
    sources: z.array(relatedQTLFormat).or(z.array(relatedMotifFormat))
  }))
})

async function geneIds (id: string): Promise<any[]> {
  const input: paramsFormatType = {}
  input.gene_name = id
  input.gene_id = id
  input.hgnc = `HGNC:${id}`
  input.alias = id
  input._key = id

  const query = `
    FOR record IN ${geneSchema.db_collection_name as string}
    FILTER ${getFilterStatements(geneSchema, input, 'or')}
    RETURN DISTINCT record._id
  `

  return await (await db.query(query)).all()
}

async function proteinIds (id: string): Promise<any[]> {
  const input: paramsFormatType = {}
  input.name = id
  input.dbxrefs = id
  input._key = id

  const query = `
    FOR record IN ${proteinSchema.db_collection_name as string}
    FILTER ${getFilterStatements(proteinSchema, input, 'or')}
    RETURN DISTINCT record._id
  `

  return await (await db.query(query)).all()
}

async function findVariantsFromGenesProteinsSearch (input: paramsFormatType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const searchQuery = input.query as string

  const genes = await geneIds(searchQuery)
  const variantsFromGenesQuery = `
    LET A = (
      FOR record in ${variantToGeneSchema.db_collection_name as string}
      FILTER record._to IN ['${genes.join('\',\'')}']
      SORT record._from
      COLLECT from = record._from, to = record._to INTO sources = {${getDBReturnStatements(variantToGeneSchema, true)}}
      RETURN {
        'sequence_variant': from,
        'related': { 'gene': to, 'sources': sources }
      })
  `

  const proteins = await proteinIds(searchQuery)
  const variantsFromProteinsQuery = `
    LET B = (
      FOR record in ${variantToProteinSchema.db_collection_name as string}
      FILTER record._to IN ['${proteins.join('\',\'')}']
      SORT record._from
      COLLECT from = record._from, to = record._to INTO sources = {${getDBReturnStatements(variantToProteinSchema, true)}}
      RETURN {
        'sequence_variant': from,
        'related': { 'protein': to, 'sources': sources }
      })
  `

  const query = `
    ${variantsFromGenesQuery}
    ${variantsFromProteinsQuery}

    FOR record in UNION(A, B)
    COLLECT source = record['sequence_variant'] INTO relatedObjs = record.related
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN {
      'related': relatedObjs,
      'sequence_variant': (
        FOR otherRecord in ${variantSchema.db_collection_name as string}
        FILTER otherRecord._id == source
        RETURN {${getDBReturnStatements(variantSchema, true).replaceAll('record', 'otherRecord')}}
      )[0]
    }
  `

  const objs = await (await db.query(query)).all()

  const variantsFromGenes = new Set<string>()
  const variantsFromProteins = new Set<string>()
  objs.forEach(obj => {
    obj.related.forEach((related: Record<string, any>) => {
      if (related.gene !== undefined) {
        variantsFromGenes.add(related.gene)
      }

      if (related.protein !== undefined) {
        variantsFromProteins.add(related.protein)
      }
    })
  })

  const verboseVariantsFromGenes = await verboseItems(Array.from(variantsFromGenes), geneSchema)
  const verboseVariantsFromProteins = await verboseItems(Array.from(variantsFromProteins), proteinSchema)
  const dictionary = Object.assign({}, verboseVariantsFromGenes, verboseVariantsFromProteins)
  objs.forEach(obj => {
    obj.related.forEach((related: Record<string, any>) => {
      if (related.gene !== undefined && dictionary[related.gene] !== undefined) {
        related.gene = dictionary[related.gene]
      }

      if (related.protein !== undefined && dictionary[related.protein] !== undefined) {
        related.protein = dictionary[related.protein]
      }
    })
  })

  return objs
}

async function variantSearch (input: paramsFormatType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const id = `variants/${input.variant_id as string}`

  const genesFromVariantQuery = `
  LET A = (
    FOR record in ${variantToGeneSchema.db_collection_name as string}
    FILTER record._from == '${id}'
    SORT record._to
    COLLECT from = record._from, to = record._to INTO sources = {${getDBReturnStatements(variantToGeneSchema, true)}}
    RETURN {
      'sequence_variant': from,
      'related': { 'gene': to, 'sources': sources }
    })`

  const proteinsFromVariantQuery = `
  LET B = (
    FOR record in ${variantToProteinSchema.db_collection_name as string}
    FILTER record._from == '${id}'
    SORT record._to
    COLLECT from = record._from, to = record._to INTO sources = {${getDBReturnStatements(variantToProteinSchema, true)}}
    RETURN {
      'sequence_variant': from,
      'related': { 'protein': to, 'sources': sources }
    })`

  const query = `
    ${genesFromVariantQuery}
    ${proteinsFromVariantQuery}

    FOR record in UNION(A, B)
    COLLECT source = record['sequence_variant'] INTO relatedObjs = record.related
    RETURN {
      'sequence_variant': (
        FOR otherRecord in ${variantSchema.db_collection_name as string}
        FILTER otherRecord._id == source
        RETURN {${getDBReturnStatements(variantSchema, true).replaceAll('record', 'otherRecord')}}
      )[0],
      'related': (
        FOR ro in relatedObjs
        LIMIT ${input.page as number * limit}, ${limit}
        RETURN ro
      )
    }
  `

  const objs = await (await db.query(query)).all()

  const genesFromVariant = new Set<string>()
  const proteinsFromVariant = new Set<string>()
  objs.forEach(obj => {
    obj.related.forEach((related: Record<string, any>) => {
      if (related.gene !== undefined) {
        genesFromVariant.add(related.gene)
      }

      if (related.protein !== undefined) {
        proteinsFromVariant.add(related.protein)
      }
    })
  })

  const genesFromVariantVerbose = await verboseItems(Array.from(genesFromVariant), geneSchema)
  const proteinsFromVariantVerbose = await verboseItems(Array.from(proteinsFromVariant), proteinSchema)
  const dictionary = Object.assign({}, genesFromVariantVerbose, proteinsFromVariantVerbose)
  objs.forEach(obj => {
    obj.related.forEach((related: Record<string, any>) => {
      if (related.gene !== undefined && dictionary[related.gene] !== undefined) {
        related.gene = dictionary[related.gene]
      }

      if (related.protein !== undefined && dictionary[related.protein] !== undefined) {
        related.protein = dictionary[related.protein]
      }
    })
  })

  return objs
}

async function genesProteinsFromGenes (genes: string[], page: number, limit: number): Promise<any[]> {
  const query = `
    LET ids = ['${Array.from(genes).join('\',\'')}']

    // genes -> transcripts
    LET Transcripts = (
      FOR record IN ${genesToTranscriptsSchema.db_collection_name as string}
      FILTER record._from IN ids
      RETURN record._to
    )

    // transcripts -> proteins
    LET Proteins = (
      FOR record IN ${transcriptsToProteinsSchema.db_collection_name as string}
      FILTER record._from IN Transcripts

      LET relatedIds = (
        FOR relatedRecord IN ${proteinsProteinsSchema.db_collection_name as string}
        FILTER relatedRecord._from == record._to OR relatedRecord._to == record._to
        SORT relatedRecord._key
        LIMIT ${page * limit}, ${limit}
        RETURN DISTINCT(relatedRecord._to == record._to ? relatedRecord._from : relatedRecord._to)
      )
      RETURN DISTINCT {
        'protein': (
          FOR otherRecord in ${proteinSchema.db_collection_name as string}
          FILTER otherRecord._id == record._to
          RETURN {${getDBReturnStatements(proteinSchema, true).replaceAll('record', 'otherRecord')}}
        )[0],

        // protein <-> protein
        'related': (
          FOR otherRecord in ${proteinSchema.db_collection_name as string}
          FILTER otherRecord._id IN relatedIds
          RETURN {${getDBReturnStatements(proteinSchema, true).replaceAll('record', 'otherRecord')}}
        )
      }
    )

    LET Genes = (
      FOR record IN ${geneSchema.db_collection_name as string}
      FILTER record._id IN ids

      // genes <-> genes
      LET relatedIds = (
        FOR relatedRecord IN ${geneGeneSchema.db_collection_name as string}
        FILTER relatedRecord._from == record._id or relatedRecord._to == record._id
        SORT relatedRecord._key
        LIMIT ${page * limit}, ${limit}
        RETURN DISTINCT(relatedRecord._to == record._id ? relatedRecord._from : relatedRecord._to)
      )

      RETURN {
        'gene': {${getDBReturnStatements(geneSchema, true)}},
        'related': (
          FOR otherRecord IN ${geneSchema.db_collection_name as string}
          FILTER otherRecord._id IN relatedIds
          RETURN {${getDBReturnStatements(geneSchema, true).replaceAll('record', 'otherRecord')}}
        )
      }
    )

    FOR record IN UNION(Proteins, Genes)
    RETURN record
  `

  let response = await ((await db.query(query)).all())
  if (response[0].related.length === 0 && response[1].related.length === 0) {
    response = []
  }
  return response
}

async function genesProteinsFromProteins (proteins: string[], page: number, limit: number): Promise<any[]> {
  const query = `
    LET ids = ['${Array.from(proteins).join('\',\'')}']

    // transcripts -> proteins
    LET Transcripts = (
      FOR record IN ${transcriptsToProteinsSchema.db_collection_name as string}
      FILTER record._to IN ids
      RETURN record._from
    )

    // genes -> transcripts
    LET GeneIDs = (
      FOR record IN ${genesToTranscriptsSchema.db_collection_name as string}
      FILTER record._to IN Transcripts
      RETURN DISTINCT record._from
    )

    LET Genes = (
      FOR record in ${geneSchema.db_collection_name as string}
      FILTER record._id IN GeneIDs

      // genes <-> genes
      LET relatedIds = (
        FOR relatedRecord IN ${geneGeneSchema.db_collection_name as string}
        FILTER relatedRecord._from == record._id OR relatedRecord._to == record._id
        SORT relatedRecord._key
        LIMIT ${page * limit}, ${limit}
        RETURN DISTINCT(relatedRecord._to == record._id ? relatedRecord._from : relatedRecord._id)
      )

      RETURN {
        'gene': {${getDBReturnStatements(geneSchema, true)}},
        'related': (
          FOR otherRecord in ${geneSchema.db_collection_name as string}
          FILTER otherRecord._id IN relatedIds
          RETURN {${getDBReturnStatements(geneSchema, true).replaceAll('record', 'otherRecord')}}
        )
      }
    )

    LET Proteins = (
      FOR record IN ${proteinSchema.db_collection_name as string}
      FILTER record._id IN ids

      // proteins <-> proteins
      LET relatedIds = (
        FOR relatedRecord IN ${proteinsProteinsSchema.db_collection_name as string}
        FILTER relatedRecord._from == record._id or relatedRecord._to == record._id
        SORT relatedRecord._key
        LIMIT ${page * limit}, ${limit}
        RETURN DISTINCT(relatedRecord._to == record._id ? relatedRecord._from : record._id)
      )

      RETURN {
        'protein': {${getDBReturnStatements(proteinSchema, true)}},
        'related': (
          FOR otherRecord IN proteins
          FILTER otherRecord._id IN relatedIds
          RETURN {${getDBReturnStatements(proteinSchema, true).replaceAll('record', 'otherRecord')}}
        )
      }
    )

    FOR record IN UNION(Proteins, Genes)
    RETURN record
  `

  let response = await ((await db.query(query)).all())
  if (response[0].related.length === 0 && response[1].related.length === 0) {
    response = []
  }
  return response
}

async function geneProteinGeneProtein (input: paramsFormatType): Promise<any[]> {
  const query = input.query as string

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const genes = await geneIds(query)
  if (genes.length !== 0) {
    return await genesProteinsFromGenes(genes, input.page as number, limit)
  }

  const proteins = await proteinIds(query)
  if (proteins.length > 0) {
    return await genesProteinsFromProteins(proteins, input.page as number, limit)
  }

  return []
}

const variantsFromGeneProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes-proteins/variants', description: descriptions.genes_proteins_variants } })
  .input(queryFormat)
  .output(z.array(sequenceVariantRelatedFormat))
  .query(async ({ input }) => await findVariantsFromGenesProteinsSearch(input))

const genesProteinsFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/genes-proteins', description: descriptions.variants_genes_proteins } })
  .input(variantQueryFormat)
  .output(z.array(sequenceVariantRelatedFormat))
  .query(async ({ input }) => await variantSearch(input))

const genesProteinsGenesProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes-proteins/genes-proteins', description: descriptions.genes_proteins_genes_proteins } })
  .input(queryFormat)
  .output(z.array(geneProteinRelatedFormat))
  .query(async ({ input }) => await geneProteinGeneProtein(input))

export const genesProteinsVariants = {
  variantsFromGeneProteins,
  genesProteinsFromVariants,
  genesProteinsGenesProteins
}
