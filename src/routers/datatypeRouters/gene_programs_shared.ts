import { z } from 'zod/v4'
import { TRPCError } from '@trpc/server'

export const programContextFormat = z.object({
  source: z.string(),
  source_url: z.string().nullish(),
  files_filesets: z.string(),
  class: z.string(),
  method: z.string().nullable(),
  label: z.string(),
  biosample_term: z.string().nullish(),
  biological_context: z.string().nullish(),
  treatments_term_ids: z.array(z.string()).nullish(),
  perturbation: z.string().nullish()
})

export const programContextQuery = z.object({
  files_fileset: z.string().trim().min(1).optional(),
  biosample_term: z.string().trim().min(1).optional(),
  biological_context: z.string().trim().min(1).optional(),
  treatment_term_id: z.string().trim().min(1).optional()
})

export const programPagination = z.object({
  page: z.number().int().nonnegative().default(0),
  limit: z.number().int().positive().max(100).default(25)
})

// Validate before constructing range filters, including operators and extra colons.
export const programNumericFilter = z.string().trim().refine(value => {
  const parts = value.split(':')
  return parts.length <= 2 && (parts.length === 1 || ['gt', 'gte', 'lt', 'lte'].includes(parts[0])) &&
    parts[parts.length - 1].trim() !== '' && Number.isFinite(Number(parts[parts.length - 1]))
}, 'Use a finite number or gt:, gte:, lt:, lte: followed by a finite number.')

export function documentId (collection: string, value: string): string {
  if (value.includes('/')) {
    if (!value.startsWith(`${collection}/`) || value.split('/').length !== 2 || value.endsWith('/')) {
      throw new TRPCError({ code: 'BAD_REQUEST', message: `Expected a ${collection} key or document ID.` })
    }
    return value
  }
  return `${collection}/${value}`
}

export function contextFilters (input: Record<string, any>): Record<string, string> {
  const filters: Record<string, string> = {}
  if (input.files_fileset !== undefined) filters.files_filesets = documentId('files_filesets', input.files_fileset)
  if (input.biosample_term !== undefined) filters.biosample_term = documentId('ontology_terms', input.biosample_term.replace(':', '_'))
  if (input.biological_context !== undefined) filters.biological_context = input.biological_context
  if (input.treatment_term_id !== undefined) filters.treatments_term_ids = input.treatment_term_id
  return filters
}
