import { goTermsAnnotations } from '../../../datatypeRouters/edges/go_terms_annotations'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

const goAnnotation = {
  gene_product_id: 'transcripts/ENST00000357654',
  gene_product_name: 'BRCA1-201',
  go_term_name: 'DNA repair',
  source: 'GO',
  gene_product_type: 'transcript',
  gene_product_symbol: 'BRCA1',
  qualifier: ['involved_in'],
  organism: 'Homo sapiens',
  evidence: 'IDA',
  go_id: 'GO_0006281',
  name: 'involved in',
  class: 'biological relationship',
  method: null,
  label: 'gene product go term annotation',
  files_filesets: 'files_filesets/IGVFFI0003XXXX'
}

describe('goTermsAnnotations.goTermsFromAnnotations', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns GO term annotations when the query matches a transcript', async () => {
    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(['transcripts/ENST00000357654']) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([goAnnotation]) } as any)

    const input = { query: 'ENST00000357654', page: 0 }
    const result = await goTermsAnnotations.goTermsFromAnnotations({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual([goAnnotation])
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('falls back to protein matches when no transcript matches the query', async () => {
    const proteinAnnotation = { ...goAnnotation, gene_product_id: 'proteins/ENSP00000493376', gene_product_type: 'protein' }

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([]) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(['proteins/ENSP00000493376']) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([proteinAnnotation]) } as any)

    const input = { query: 'ENSP00000493376', page: 0 }
    const result = await goTermsAnnotations.goTermsFromAnnotations({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual([proteinAnnotation])
    expect(dbModule.db.query).toHaveBeenCalledTimes(3)
  })

  it('returns an empty array when the query matches neither transcripts nor proteins', async () => {
    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([]) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([]) } as any)

    const input = { query: 'unknown-id', page: 0 }
    const result = await goTermsAnnotations.goTermsFromAnnotations({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual([])
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('rejects when the required query parameter is missing', async () => {
    const input = { page: 0 } as any
    await expect(
      goTermsAnnotations.goTermsFromAnnotations({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('goTermsAnnotations.annotationsFromGoTerms', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns gene products annotated with a GO term', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([goAnnotation])
    } as any)

    const input = { go_term_id: 'GO_0006281', page: 0 }
    const result = await goTermsAnnotations.annotationsFromGoTerms({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual([goAnnotation])
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('rejects when the required go_term_id parameter is missing', async () => {
    const input = { page: 0 } as any
    await expect(
      goTermsAnnotations.annotationsFromGoTerms({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})
