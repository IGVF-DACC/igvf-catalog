import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, verboseItems } from '../_helpers'
import { descriptions } from '../descriptions'
import { getSchema } from '../schema'

const MAX_PAGE_SIZE = 100

const genesToTranscriptsSchema = getSchema('data/schemas/edges/genes_transcripts.Gencode.json')
const genesToTranscriptsCollectionName = (genesToTranscriptsSchema.accessible_via as Record<string, any>).name as string
const transcriptsToProteinsCollectionName = 'transcripts_proteins'
const proteinsProteinsCollectionName = 'proteins_proteins'
const geneGeneCollectionName = 'genes_genes'

const geneSchema = getSchema('data/schemas/nodes/genes.GencodeGene.json')
const geneCollectionName = (geneSchema.accessible_via as Record<string, any>).name as string
const proteinSchema = getSchema('data/schemas/nodes/proteins.GencodeProtein.json')
const proteinCollectionName = (proteinSchema.accessible_via as Record<string, any>).name as string
const variantSchema = getSchema('data/schemas/nodes/variants.Favor.json')
const variantCollectionName = (variantSchema.accessible_via as Record<string, any>).name as string

const variantToGeneSchema = getSchema('data/schemas/edges/variants_genes.AFGRSQtl.json')
const variantToGeneCollectionName = (variantToGeneSchema.accessible_via as Record<string, any>).name as string
const variantToProteinSchema = getSchema('data/schemas/edges/variants_proteins.ASB.json')
const variantToProteinCollectionName = (variantToProteinSchema.accessible_via as Record<string, any>).name as string

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
  names: z.array(z.string())
})

const relatedQTLFormat = z.object({
  label: z.string(),
  source: z.string(),
  log10pvalue: z.number().nullish(),
  biological_context: z.string(),
  name: z.string()
})

const relatedMotifFormat = z.object({
  motif: z.string().nullable(),
  source: z.string(),
  name: z.string()
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
    gene: (relatedGeneFormat.nullish()).or(z.string().nullish()),
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
    FOR record IN ${geneCollectionName}
    FILTER ${getFilterStatements(geneSchema, input, 'or')}
    RETURN DISTINCT record._id
  `

  return await (await db.query(query)).all()
}

async function proteinIds (id: string): Promise<any[]> {
  const input: paramsFormatType = {}
  input._key = id
  input.protein_id = id
  input.uniprot_ids = id

  input.names = id
  input.full_names = id

  const query = `
    FOR record IN ${proteinCollectionName}
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
      FOR record in ${variantToGeneCollectionName}
      FILTER record._to IN ['${genes.join('\',\'')}']
      SORT record._from
      // endpoint is opposite to ArangoDB collection name
      COLLECT from = record._from, to = record._to INTO sources = { 'name': record.inverse_name, ${getDBReturnStatements(variantToGeneSchema, true)}}
      RETURN {
        'sequence_variant': from,
        'related': { 'gene': to, 'sources': sources }
      })
  `

  const proteins = await proteinIds(searchQuery)
  const variantsFromProteinsQuery = `
    LET B = (
      FOR record in ${variantToProteinCollectionName}
      FILTER record._to IN ['${proteins.join('\',\'')}']
      SORT record._from
      // endpoint is opposite to ArangoDB collection name
      COLLECT from = record._from, to = record._to INTO sources = { 'name': record.inverse_name, ${getDBReturnStatements(variantToProteinSchema, true)}}
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
        FOR otherRecord in ${variantCollectionName}
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

        // temporary fix until DSERV-1010 is resolved
        for (const idx in related.sources) {
          if (Array.isArray(related.sources[idx].biological_context)) {
            related.sources[idx].biological_context = related.sources[idx].biological_context[0] ?? null
          }
        }
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
    FOR record in ${variantToGeneCollectionName}
    FILTER record._from == '${id}'
    SORT record._to
    COLLECT from = record._from, to = record._to INTO sources = {'name': record.name, ${getDBReturnStatements(variantToGeneSchema, true)}}
    RETURN {
      'sequence_variant': from,
      'related': { 'gene': to, 'sources': sources }
    })`

  const proteinsFromVariantQuery = `
  LET B = (
    FOR record in ${variantToProteinCollectionName}
    FILTER record._from == '${id}' and STARTS_WITH(record._to, 'proteins/')
    SORT record._to
    COLLECT from = record._from, to = record._to INTO sources = {'name': record.name, ${getDBReturnStatements(variantToProteinSchema, true)}}
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
        FOR otherRecord in ${variantCollectionName}
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
      FOR record IN ${genesToTranscriptsCollectionName}
      FILTER record._from IN ids
      RETURN record._to
    )

    // transcripts -> proteins
    LET Proteins = (
      FOR record IN ${transcriptsToProteinsCollectionName}
      FILTER record._from IN Transcripts

      LET relatedIds = (
        FOR relatedRecord IN ${proteinsProteinsCollectionName}
        FILTER relatedRecord._from == record._to OR relatedRecord._to == record._to
        SORT relatedRecord._key
        LIMIT ${page * limit}, ${limit}
        RETURN DISTINCT(relatedRecord._to == record._to ? relatedRecord._from : relatedRecord._to)
      )
      RETURN DISTINCT {
        'protein': (
          FOR otherRecord in ${proteinCollectionName}
          FILTER otherRecord._id == record._to
          RETURN {${getDBReturnStatements(proteinSchema, true).replaceAll('record', 'otherRecord')}}
        )[0],

        // protein <-> protein
        'related': (
          FOR otherRecord in ${proteinCollectionName}
          FILTER otherRecord._id IN relatedIds
          RETURN {${getDBReturnStatements(proteinSchema, true).replaceAll('record', 'otherRecord')}}
        )
      }
    )

    LET Genes = (
      FOR record IN ${geneCollectionName}
      FILTER record._id IN ids

      // genes <-> genes
      LET relatedIds = (
        FOR relatedRecord IN ${geneGeneCollectionName}
        FILTER relatedRecord._from == record._id or relatedRecord._to == record._id
        SORT relatedRecord._key
        LIMIT ${page * limit}, ${limit}
        RETURN DISTINCT(relatedRecord._to == record._id ? relatedRecord._from : relatedRecord._to)
      )

      RETURN {
        'gene': {${getDBReturnStatements(geneSchema, true)}},
        'related': (
          FOR otherRecord IN ${geneCollectionName}
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
      FOR record IN ${transcriptsToProteinsCollectionName}
      FILTER record._to IN ids
      RETURN record._from
    )

    // genes -> transcripts
    LET GeneIDs = (
      FOR record IN ${genesToTranscriptsCollectionName}
      FILTER record._to IN Transcripts
      RETURN DISTINCT record._from
    )

    LET Genes = (
      FOR record in ${geneCollectionName}
      FILTER record._id IN GeneIDs

      // genes <-> genes
      LET relatedIds = (
        FOR relatedRecord IN ${geneGeneCollectionName}
        FILTER relatedRecord._from == record._id OR relatedRecord._to == record._id
        SORT relatedRecord._key
        LIMIT ${page * limit}, ${limit}
        RETURN DISTINCT(relatedRecord._to == record._id ? relatedRecord._from : relatedRecord._id)
      )

      RETURN {
        'gene': {${getDBReturnStatements(geneSchema, true)}},
        'related': (
          FOR otherRecord in ${geneCollectionName}
          FILTER otherRecord._id IN relatedIds
          RETURN {${getDBReturnStatements(geneSchema, true).replaceAll('record', 'otherRecord')}}
        )
      }
    )

    LET Proteins = (
      FOR record IN ${proteinCollectionName}
      FILTER record._id IN ids

      // proteins <-> proteins
      LET relatedIds = (
        FOR relatedRecord IN ${proteinsProteinsCollectionName}
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
