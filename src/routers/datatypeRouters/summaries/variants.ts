import { z } from 'zod'
import { db } from '../../../database'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { nearestGeneSearch } from '../edges/variants_genes'

const schema = loadSchemaConfig()
const variantSchema = schema['sequence variant']

const variantsSummaryQueryFormat = z.object({
  variant_id: z.string()
})

const variantsSummaryFormat = z.object({
  summary: z.object({
    rsid: z.array(z.string()).nullish(),
    varinfo: z.string().nullish(),
    spdi: z.string().nullish(),
    hgvs: z.string().nullish(),
    ref: z.string().nullish(),
    alt: z.string().nullish()
  }),
  nearest_genes: z.object({
    nearestCodingGene: z.object({
      gene_name: z.string().nullish(),
      id: z.string(),
      start: z.number(),
      end: z.number(),
      distance: z.number()
    }),
    nearestGene: z.object({
      gene_name: z.string().nullish(),
      id: z.string(),
      start: z.number(),
      end: z.number(),
      distance: z.number()
  })}),
  cadd_scores: z.object({
    raw: z.number().nullish(),
    phread: z.number().nullish()
  }).nullish()
})

function distanceGeneVariant(gene_start: number, gene_end: number, variant_pos: number): number {
  return Math.min(Math.abs(variant_pos - gene_start), Math.abs(variant_pos - gene_end))
}

async function nearestGenes(variant: any): Promise<any> {
  let nearestGene, distNearestGene, nearestCodingGene, distCodingGene

  const nearestGenes = await nearestGeneSearch({ region: `${variant.chr}:${variant['pos:long']}-${variant['pos:long']}`})

  if (variant.annotations.funseq_description === 'coding') {
    nearestGene = nearestGenes[0]
    distNearestGene = distanceGeneVariant(nearestGene.start, nearestGene.end, variant['pos:long'])

    for (let index = 1; index < nearestGenes.length; index++){
      let newDistance = distanceGeneVariant(nearestGenes[index].start, nearestGenes[index].end, variant['pos:long'])
      if (newDistance < distNearestGene) {
        distNearestGene = newDistance
        nearestGene = nearestGenes[index]
      }
    }

    // nearestGene and nearestCodingGene are the same for coding variants
    nearestCodingGene = nearestGene
    distCodingGene = distNearestGene
  } else {
    const nearestCodingGenes = await nearestGeneSearch({ gene_type: 'protein_coding', region: `${variant.chr}:${variant['pos:long']}-${variant['pos:long']}`})

    nearestGene = nearestGenes[0]
    distNearestGene = distanceGeneVariant(nearestGenes[0].start, nearestGenes[0].end, variant['pos:long'])
    if (nearestGenes.length > 1) {
      const distGene1 = distanceGeneVariant(nearestGenes[1].start, nearestGenes[1].end, variant['pos:long'])
      if (distGene1 < distNearestGene) {
        nearestGene = nearestGenes[1]
        distNearestGene = distGene1
      }
    }

    nearestCodingGene = nearestCodingGenes[0]
    distCodingGene = distanceGeneVariant(nearestCodingGenes[0].start, nearestCodingGenes[0].end, variant['pos:long'])
    if (nearestCodingGenes.length > 1) {
      const distGene1 = distanceGeneVariant(nearestCodingGenes[1].start, nearestCodingGenes[1].end, variant['pos:long'])
      if (distGene1 < distCodingGene) {
        nearestCodingGene = nearestCodingGenes[1]
        distCodingGene = distGene1
      }
    }
  }

  return {
    nearestCodingGene: {
      gene_name: nearestCodingGene.name,
      id: nearestCodingGene._id,
      start: nearestCodingGene.start,
      end: nearestCodingGene.end,
      distance: distCodingGene
    },
    nearestGene: {
      gene_name: nearestGene.name,
      id: nearestGene._id,
      start: nearestGene.start,
      end: nearestGene.end,
      distance: distNearestGene
    }
  }
}

async function variantSummarySearch(variant_id: string): Promise<any> {
  const query = `
    FOR record in ${variantSchema.db_collection_name}
    FILTER record._key == '${variant_id}'
    RETURN record
  `

  const variant = (await (await db.query(query)).all())[0]

  if (variant === undefined) {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: `Variant ${variant_id as string} not found.`
    })
  }

  return {
    summary: {
      rsid: variant.rsid,
      varinfo: variant.annotations.varinfo,
      spdi: variant.spdi,
      hgvs: variant.hgvs,
      ref: variant.ref,
      alt: variant.alt,
      pos: variant['pos:long']
    },
    nearest_genes: await nearestGenes(variant),
    cadd_scores: {
      raw: variant.annotations.cadd_rawscore,
      phread: variant.annotations.cadd_phred
    }
  }
}

const variantSummary = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/summary', description: descriptions.variants_summary } })
  .input(variantsSummaryQueryFormat)
  .output(variantsSummaryFormat)
  .query(async ({ input }) => await variantSummarySearch(input.variant_id))

export const variantSummaryRouters = {
  variantSummary
}
