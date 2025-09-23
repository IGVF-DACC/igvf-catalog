import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { QUERY_LIMIT } from '../../../constants'
import { db } from '../../../database'
import { TRPCError } from '@trpc/server'
import { commonHumanEdgeParamsFormat } from '../params'
import { variantSimplifiedFormat } from '../nodes/variants'

const MAX_PAGE_SIZE = 100

const variantQueryFormat = z.object({
  variant_id: z.string().trim()
})

const geneQueryFormat = z.object({
  gene_id: z.string()
})

const codingVariantsPhenotypeAggregationFormat = z.object({
  method: z.string(),
  count: z.number()
})

const fromCodingVariantsQueryFormat = z.object({
  coding_variant_name: z.string().optional(),
  hgvsp: z.string().optional(),
  protein_name: z.string().optional(),
  gene_name: z.string().optional(),
  amino_acid_position: z.number().optional(),
  transcript_id: z.string().optional()
})

const scoreSummaryOutputFormat = z.object({
  dataType: z.string(),
  score: z.number().nullable(),
  portalLink: z.string().nullable()
})

const outputFormat = z.object({
  coding_variant: z.object({ _id: z.string(), aapos: z.number().nullish(), protein_name: z.string().nullish(), gene_name: z.string().nullish(), ref: z.string().nullish(), alt: z.string().nullish() }).nullish(),
  phenotype: z.object({ phenotype_id: z.string(), phenotype_name: z.string() }).nullish(),
  score: z.number().nullable(),
  method: z.string().nullish().optional(),
  source: z.string(),
  source_url: z.string(),
  variant: variantSimplifiedFormat.nullish()
})

const schema = loadSchemaConfig()
const codingVariantToPhenotypeSchema = schema['coding variant to phenotype']
const codingVariantSchema = schema['coding variant']
const ontologySchema = schema['ontology term']
const variantSchema = schema['sequence variant']
const geneSchema = schema.gene

function variantQueryValidation (input: paramsFormatType): void {
  const validKeys = ['coding_variant_name', 'hgvsp', 'protein_name', 'gene_name', 'amino_acid_position', 'transcript_id'] as const

  // Count how many keys are defined in input
  const definedKeysCount = validKeys.filter(key => key in input && input[key] !== undefined).length

  if (definedKeysCount < 1) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'None of the coding variant properties is defined.'
    })
  }
}

function phenotypeQueryValidation (input: paramsFormatType): void {
  const validKeys = ['phenotype_id', 'phenotype_name'] as const

  // Count how many keys are defined in input
  const definedKeysCount = validKeys.filter(key => key in input && input[key] !== undefined).length

  if (definedKeysCount < 1) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'None of the phenotype properties is defined.'
    })
  }
}

async function findCodingVariantsFromPhenotypesSearch (input: paramsFormatType): Promise<any[]> {
  phenotypeQueryValidation(input)
  delete input.organism
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let phenotypeQuery = ''
  let phenotypeIds = '[]'
  if (input.phenotype_id !== undefined) {
    phenotypeIds = `['ontology_terms/${input.phenotype_id as string}']`
  } else if (input.phenotype_name !== undefined) {
    phenotypeQuery = `
      FOR record IN ontology_terms
      FILTER record.name == "${input.phenotype_name as string}"
      RETURN record._id
    `
    const phenotypes = await (await db.query(phenotypeQuery)).all()
    if (phenotypes.length !== 0) {
      phenotypeIds = `${JSON.stringify(phenotypes)}`
    } else {
      phenotypeQuery = `
        FOR record IN ontology_terms_text_en_no_stem_inverted_search_alias
        SEARCH TOKENS("${input.phenotype_name as string}", "text_en_no_stem") ALL in record.name
        SORT BM25(record) DESC
        RETURN record._id
      `
      const phenotypes = await (await db.query(phenotypeQuery)).all()
      phenotypeIds = `${JSON.stringify(phenotypes)}`
    }
  }

  if (phenotypeIds.includes('ontology_terms/GO_0003674')) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'GO_0003674 / GO Molecular function is not supported at this time due to the very large number of matching edges. Please contact us if you need this data.'
    })
  }

  const query = `
    LET phenotypes = ${phenotypeIds}

    LET a = (
      FOR phenoEdges IN coding_variants_phenotypes
        FILTER phenoEdges._to IN phenotypes
        RETURN {
          'coding_variant': phenoEdges._from,
          'phenotype': phenoEdges._to,
          'score': phenoEdges.score,
          'source': phenoEdges.source,
          'source_url': phenoEdges.source_url,
          'coding_variant_to_variant': phenoEdges._from
        }
    )

    LET b = (
      FOR phenoEdges IN variants_phenotypes
        FILTER phenoEdges._to IN phenotypes
        FOR cpcv IN variants_phenotypes_coding_variants
          FILTER cpcv._from == phenoEdges._id
          RETURN {
            'coding_variant': cpcv._to,
            'phenotype': phenoEdges._to,
            'variant': phenoEdges._from,
            'score': phenoEdges.score,
            'source': phenoEdges.source,
            'source_url': phenoEdges.source_url
          }
    )

    LET combined = UNION(a, b)
    RETURN SLICE(combined, ${input.page as number * limit}, ${limit})
  `

  let objs = await ((await db.query(query)).all())
  objs = objs[0] || []

  await addVerboseInfoToReturn(objs)

  return objs
}

async function findPhenotypesFromCodingVariantSearch (input: paramsFormatType): Promise<any[]> {
  variantQueryValidation(input)
  delete input.organism

  if (input.amino_acid_position !== undefined) {
    input.aapos = input.amino_acid_position
    delete input.amino_acid_position
  }
  if (input.coding_variant_name !== undefined) {
    // all name properties are copies of the _key property
    input._key = input.coding_variant_name as string
    delete input.coding_variant_name
  }

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let codingVariantFilters = getFilterStatements(codingVariantSchema, input)

  if (codingVariantFilters !== '') {
    codingVariantFilters = `FILTER ${codingVariantFilters}`
  }

  const query = `
    LET coding_variants = (
      FOR record IN coding_variants
      ${codingVariantFilters}
      RETURN record._id
    )

    LET a = (
      FOR phenoEdges IN coding_variants_phenotypes
      FILTER phenoEdges._from IN coding_variants
      RETURN {
        'coding_variant': phenoEdges._from,
        'coding_variant_to_variant': phenoEdges._from,
        'phenotype': phenoEdges._to,
        'source': phenoEdges.source,
        'method': phenoEdges.method,
        'score': phenoEdges.pathogenicity_score OR phenoEdges.esm_1v_score OR phenoEdges.score,
        'source_url': phenoEdges.source_url
      }
    )

    LET b = (
      FOR cpcv IN variants_phenotypes_coding_variants
      FILTER cpcv._to IN coding_variants
      FOR phenoEdges IN variants_phenotypes
        FILTER phenoEdges._id == cpcv._from
        RETURN {
          'coding_variant': cpcv._to, //gene_name, protein_name, aa_position, aa_ref
          'variant': phenoEdges._from,
          'score': phenoEdges.score,
          'method': phenoEdges.method,
          'phenotype': phenoEdges._to,
          'source': phenoEdges.source,
          'source_url': phenoEdges.source_url
        }
    )

    LET combined = UNION(a, b)
    RETURN SLICE(combined, ${input.page as number * limit}, ${limit})
  `

  let objs = await ((await db.query(query)).all())
  objs = objs[0] || []

  await addVerboseInfoToReturn(objs)

  return objs
}

async function addVerboseInfoToReturn (objs: any[]): Promise<void> {
  // Resolving coding_variants -> variant via variants_coding_variants edge
  const codingVariantsToVariantIds = objs.map(obj => obj.coding_variant_to_variant).filter(id => id !== undefined)
  if (codingVariantsToVariantIds.length > 0) {
    const codingVariantQuery = `
      FOR record IN variants_coding_variants
      FILTER record._to IN ${JSON.stringify(codingVariantsToVariantIds)}
      RETURN { variant_id: record._from, cv_id: record._to }
    `
    const codingVariants = await ((await db.query(codingVariantQuery)).all())
    for (const obj of objs) {
      obj.coding_variant_to_variant = codingVariants.find(cv => cv.cv_id === obj.coding_variant_to_variant).variant_id || null
      obj.variant = obj.variant || obj.coding_variant_to_variant
      delete obj.coding_variant_to_variant
    }
  }

  const phenotypeIds = objs.map(obj => obj.phenotype).filter(id => id !== undefined)
  const variantIds = objs.map(obj => obj.variant).filter(id => id !== undefined)
  const codingVariantIds = objs.map(obj => obj.coding_variant).filter(id => id !== undefined)

  if (phenotypeIds.length > 0) {
    const phenotypeQuery = `
      FOR record IN ${ontologySchema.db_collection_name as string}
      FILTER record._id IN ${JSON.stringify(phenotypeIds)}
      RETURN { phenotype_id: record._key, phenotype_name: record.name }
    `
    const phenotypes = await ((await db.query(phenotypeQuery)).all())
    for (const obj of objs) {
      obj.phenotype = phenotypes.find(p => (`ontology_terms/${p.phenotype_id as string}`) === obj.phenotype) || null
    }
  }

  if (variantIds.length > 0) {
    const variantQuery = `
      FOR record IN ${variantSchema.db_collection_name as string}
      FILTER record._id IN ${JSON.stringify(variantIds)}
      RETURN { ${getDBReturnStatements(variantSchema, true)} }
    `
    const variants = await ((await db.query(variantQuery)).all())
    for (const obj of objs) {
      obj.variant = variants.find(v => (`variants/${v._id as string}`) === obj.variant) || null
    }
  }

  if (codingVariantIds.length > 0) {
    const codingVariantQuery = `
      FOR record IN ${codingVariantSchema.db_collection_name as string}
      FILTER record._id IN ${JSON.stringify(codingVariantIds)}
      RETURN { _id: record._key, aapos: record.aapos, protein_name: record.protein_name, gene_name: record.gene_name, ref: record.ref, alt: record.alt }
    `
    const codingVariants = await ((await db.query(codingVariantQuery)).all())
    for (const obj of objs) {
      obj.coding_variant = codingVariants.find(cv => (`coding_variants/${cv._id as string}`) === obj.coding_variant) || null
    }
  }
}

async function countCodingVariantsFromGene (input: paramsFormatType): Promise<any[]> {
  if (input.gene_id === undefined) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'gene_id is required'
    })
  }

  const query = `
    LET gene_name = DOCUMENT('${geneSchema.db_collection_name as string}/${input.gene_id as string}').name

    LET codingVariants = (
      FOR record IN ${codingVariantSchema.db_collection_name as string}
      FILTER record.gene_name == gene_name
      RETURN DISTINCT record._id
    )

    LET sge = (
      FOR v IN variants_phenotypes_coding_variants
        FILTER v._to IN codingVariants
        COLLECT fileset_id = v.files_filesets WITH COUNT INTO count
        RETURN { method: 'SGE', count: count }
    )

    LET others = (
      FOR phenoEdges IN ${codingVariantToPhenotypeSchema.db_collection_name as string}
        FILTER phenoEdges._from IN codingVariants
        COLLECT src = phenoEdges.method WITH COUNT INTO count
        RETURN { method: src, count: count }
    )

    RETURN UNION(sge, others)
  `

  const objs = await ((await db.query(query)).all())
  return objs[0] || []
}

async function phenotypeScoresFromVariant (input: paramsFormatType): Promise<any[]> {
  if (input.variant_id === undefined) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'variant_id is required'
    })
  }

  let query = `
    FOR record IN ${variantSchema.db_collection_name as string}
    FILTER record._key == '${input.variant_id as string}'
    RETURN record._id
  `

  const variant = await ((await db.query(query)).all())
  if (variant.length === 0) {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: `Variant with id ${input.variant_id as string} not found`
    })
  }

  query = `
    LET codingVariants = (
      FOR record IN variants_coding_variants
      FILTER record._from == 'variants/${input.variant_id as string}'
      RETURN record._to
    )

    LET sge = (
      FOR v IN variants_phenotypes_coding_variants
        FILTER v._to IN codingVariants
        FOR p IN variants_phenotypes
          FILTER p._id == v._from
          RETURN {
            dataType: p.method,
            score: p.score,
            portalLink: p.source_url
          }
    )

    LET others = (FOR p IN ${codingVariantToPhenotypeSchema.db_collection_name as string}
      FILTER p._from IN codingVariants
      RETURN {
        dataType: p.method,
        score: p.pathogenicity_score OR p.esm_1v_score OR p.score,
        portalLink: p.source_url
      }
    )

    RETURN UNION(sge, others)
  `

  const objs = await ((await db.query(query)).all())
  return objs[0] || []
}

const codingVariantsFromPhenotypes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/phenotypes/coding-variants', description: descriptions.phenotypes_coding_variants } })
  .input((z.object({ phenotype_id: z.string().trim().optional(), phenotype_name: z.string().trim().optional() }).merge(commonHumanEdgeParamsFormat).omit({ verbose: true, organism: true })))
  .output(z.array(outputFormat))
  .query(async ({ input }) => await findCodingVariantsFromPhenotypesSearch(input))

const phenotypesFromCodingVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/coding-variants/phenotypes', description: descriptions.coding_variants_phenotypes } })
  .input(fromCodingVariantsQueryFormat.merge(commonHumanEdgeParamsFormat).omit({ verbose: true, organism: true }))
  .output(z.array(outputFormat))
  .query(async ({ input }) => await findPhenotypesFromCodingVariantSearch(input))

const codingVariantsCountFromGene = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/coding-variants/phenotypes-count', description: descriptions.coding_variants_phenotypes_count } })
  .input(geneQueryFormat)
  .output(z.array(codingVariantsPhenotypeAggregationFormat))
  .query(async ({ input }) => await countCodingVariantsFromGene(input))

const codingVariantsSummary = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/phenotypes/score-summary', description: descriptions.variants_phenotypes_summary } })
  .input(variantQueryFormat)
  .output(z.array(scoreSummaryOutputFormat))
  .query(async ({ input }) => await phenotypeScoresFromVariant(input))

export const codingVariantsPhenotypesRouters = {
  codingVariantsFromPhenotypes,
  phenotypesFromCodingVariants,
  codingVariantsCountFromGene,
  codingVariantsSummary
}
