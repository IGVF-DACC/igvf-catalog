import { qtlsRouters } from '../../../datatypeRouters/edges/qtls'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

describe('qtlsRouters.qtls', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns QTLs for a gene search (no method filter)', async () => {
    const geneSearchResult = [{
      _id: 'ENSG00000012048',
      name: 'BRCA1',
      chr: 'chr17',
      start: 43044295,
      end: 43125483,
      gene_type: 'protein_coding',
      source: 'GENCODE',
      version: '44',
      source_url: 'https://www.gencodegenes.org'
    }]
    const qtlResult = [{
      variant: { chr: 'chr17', pos: 43044300, spdi: 'NC_000017.11:43044300:A:G', rsid: ['rs123'], ca_id: 'CA123' },
      gene: { name: 'BRCA1', id: 'ENSG00000012048' },
      protein_complex: null,
      genomic_element: null,
      source: 'EBI',
      method: 'eQTL',
      regulatory_type: null,
      gene_consequence: null,
      biological_context: 'liver',
      neg_log10_pvalue: 5.2,
      effect_size: 0.3,
      posterior_inclusion_probability: 0.9,
      intron_chr: null,
      intron_start: null,
      intron_end: null,
      study: { id: 'STUDY1', pmid: '12345678' },
      files_filesets: 'files_filesets/IGVFFI0001XXXX'
    }]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(geneSearchResult) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(qtlResult) } as any)

    const input = { gene_id: 'ENSG00000012048' }
    const result = await qtlsRouters.qtls({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(qtlResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('returns QTLs for a variant search (rsid)', async () => {
    const variantIdResult = ['variants/NC_000017.11:43044300:A:G']
    const qtlResult = [{
      variant: { chr: 'chr17', pos: 43044300, spdi: 'NC_000017.11:43044300:A:G', rsid: ['rs123'], ca_id: 'CA123' },
      gene: { name: 'BRCA1', id: 'ENSG00000012048' },
      protein_complex: null,
      genomic_element: null,
      source: 'EBI',
      method: 'eQTL',
      biological_context: 'liver',
      neg_log10_pvalue: 5.2,
      effect_size: 0.3,
      study: { id: 'STUDY1', pmid: '12345678' },
      files_filesets: 'files_filesets/IGVFFI0001XXXX'
    }]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(variantIdResult) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(qtlResult) } as any)

    const input = { rsid: 'rs123' }
    const result = await qtlsRouters.qtls({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(qtlResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('returns pQTLs for a gene search filtered by method and source', async () => {
    const geneSearchResult = [{ _id: 'ENSG00000012048', name: 'BRCA1' }]
    const qtlResult = [{
      variant: { chr: 'chr17', pos: 43044300, spdi: 'NC_000017.11:43044300:A:G', rsid: null, ca_id: null },
      gene: { name: 'BRCA1', id: 'ENSG00000012048' },
      protein_complex: { name: 'Some Complex', id: 'COMPLEX1' },
      genomic_element: null,
      source: 'UKB',
      method: 'pQTL',
      regulatory_type: 'cis',
      gene_consequence: 'missense',
      files_filesets: 'files_filesets/IGVFFI0002XXXX'
    }]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(geneSearchResult) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(qtlResult) } as any)

    const input = { gene_id: 'ENSG00000012048', method: 'pQTL', source: 'UKB' }
    const result = await qtlsRouters.qtls({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(qtlResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('throws BAD_REQUEST when no gene, variant or region property is defined', async () => {
    const input = {}
    await expect(
      qtlsRouters.qtls({ input, ctx: {}, type: 'query', path: '', rawInput: input })
    ).rejects.toThrow(TRPCError)
  })

  it('throws BAD_REQUEST when both gene and variant inputs are defined', async () => {
    const input = { gene_id: 'ENSG00000012048', variant_id: 'NC_000017.11:43044300:A:G' }
    await expect(
      qtlsRouters.qtls({ input, ctx: {}, type: 'query', path: '', rawInput: input })
    ).rejects.toThrow(TRPCError)
  })

  it('throws BAD_REQUEST when both gene and region inputs are defined', async () => {
    const input = { gene_id: 'ENSG00000012048', region: 'chr17:43044000-43045000' }
    await expect(
      qtlsRouters.qtls({ input, ctx: {}, type: 'query', path: '', rawInput: input })
    ).rejects.toThrow(TRPCError)
  })

  it('throws BAD_REQUEST when both variant and region inputs are defined', async () => {
    const input = { variant_id: 'NC_000017.11:43044300:A:G', region: 'chr17:43044000-43045000' }
    await expect(
      qtlsRouters.qtls({ input, ctx: {}, type: 'query', path: '', rawInput: input })
    ).rejects.toThrow(TRPCError)
  })

  it('throws BAD_REQUEST for an invalid region format', async () => {
    const input = { region: 'not-a-region' }
    await expect(
      qtlsRouters.qtls({ input, ctx: {}, type: 'query', path: '', rawInput: input })
    ).rejects.toThrow(TRPCError)
  })

  it('throws BAD_REQUEST when the region span exceeds 10kb', async () => {
    const input = { region: 'chr17:43000000-43020000' }
    await expect(
      qtlsRouters.qtls({ input, ctx: {}, type: 'query', path: '', rawInput: input })
    ).rejects.toThrow(TRPCError)
  })
})
