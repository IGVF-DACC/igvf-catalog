import { genomicElementsGenesRouters } from '../../../datatypeRouters/edges/genomic_elements_genes'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

describe('genomicElementsGenesRouters.genomicElementsFromGenes', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns genomic elements for a gene, resolving the gene through geneSearch first', async () => {
    const geneRecords = [{ _id: 'ENSG00000116198', name: 'CALML6', chr: 'chr1', start: 1850597, end: 1858437 }]
    const mockResult = [
      {
        name: 'regulates',
        label: 'regulatory element effect on gene expression',
        method: 'CRISPR screen',
        class: 'observed data',
        source: 'ENCODE',
        source_url: 'https://www.encodeproject.org/files/ENCFF968BZL/',
        biological_context: 'K562',
        biosample_term: 'ontology_terms/EFO_0002067',
        cell_annotation: null,
        cell_annotation_term: null,
        files_filesets: 'files_filesets/ENCFF968BZL',
        crispr_modality: null,
        score: null,
        transcription_start_site: null,
        rna_pseudobulk_tpm: null,
        log2FC: -0.42,
        effect_size: -0.293431866,
        z_score: null,
        t_score: null,
        idr: null,
        p_value: 0.001,
        p_value_adj: 0.004023984,
        neg_log10_pvalue: null,
        neg_log10_pvalue_adj: null,
        significant: true,
        genomic_element: 'genomic_elements/CRISPR_chr1_3774714_3775214_GRCh38_ENCFF968BZL',
        gene: 'genes/ENSG00000116198'
      }
    ]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(geneRecords) } as any)
      .mockResolvedValue({ all: jest.fn().mockResolvedValue(mockResult) } as any)

    const input = { gene_id: 'ENSG00000116198', page: 0 }
    const result = await genomicElementsGenesRouters.genomicElementsFromGenes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('throws BAD_REQUEST when no gene/method/files_fileset filter is defined', async () => {
    const input = { page: 0 } as any
    await expect(
      genomicElementsGenesRouters.genomicElementsFromGenes({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('genomicElementsGenesRouters.genesFromGenomicElements', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns genes for a genomic element filtered by method', async () => {
    const mockResult = [
      {
        name: 'modulates expression of',
        label: 'regulatory element effect on gene expression',
        method: 'Perturb-seq',
        class: 'observed data',
        source: 'IGVF',
        source_url: 'https://api.data.igvf.org/tabular-files/IGVFFI3069QCRA/',
        biological_context: 'K562',
        biosample_term: 'ontology_terms/EFO_0002067',
        cell_annotation: null,
        cell_annotation_term: null,
        files_filesets: 'files_filesets/IGVFFI3069QCRA',
        crispr_modality: 'interference',
        score: null,
        transcription_start_site: null,
        rna_pseudobulk_tpm: null,
        log2FC: 0.15,
        effect_size: null,
        z_score: null,
        t_score: null,
        idr: null,
        p_value: null,
        p_value_adj: null,
        neg_log10_pvalue: 3.2,
        neg_log10_pvalue_adj: 2.1,
        significant: true,
        genomic_element: 'genomic_elements/CRISPR_chr1_212699339_212700840_GRCh38_IGVFFI3069QCRA',
        gene: 'genes/ENSG00000123685'
      }
    ]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { method: 'Perturb-seq', page: 0 }
    const result = await genomicElementsGenesRouters.genesFromGenomicElements({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('resolves the genomic element region first, then queries genes (two sequential db calls)', async () => {
    const elementIDs = ['genomic_elements/CRISPR_chr1_3774714_3775214_GRCh38_ENCFF968BZL']
    const mockResult = [
      {
        name: 'regulates',
        label: 'regulatory element effect on gene expression',
        method: 'CRISPR screen',
        class: 'observed data',
        source: 'ENCODE',
        source_url: 'https://www.encodeproject.org/files/ENCFF968BZL/',
        biological_context: 'K562',
        biosample_term: 'ontology_terms/EFO_0002067',
        cell_annotation: null,
        cell_annotation_term: null,
        files_filesets: 'files_filesets/ENCFF968BZL',
        crispr_modality: null,
        score: null,
        transcription_start_site: null,
        rna_pseudobulk_tpm: null,
        log2FC: null,
        effect_size: -0.293431866,
        z_score: null,
        t_score: null,
        idr: null,
        p_value: null,
        p_value_adj: null,
        neg_log10_pvalue: null,
        neg_log10_pvalue_adj: null,
        significant: true,
        genomic_element: 'genomic_elements/CRISPR_chr1_3774714_3775214_GRCh38_ENCFF968BZL',
        gene: 'genes/ENSG00000116198'
      }
    ]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(elementIDs) } as any)
      .mockResolvedValue({ all: jest.fn().mockResolvedValue(mockResult) } as any)

    const input = { region: 'chr1:3774714-3775214', page: 0 }
    const result = await genomicElementsGenesRouters.genesFromGenomicElements({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('throws BAD_REQUEST when no region/method/files_fileset filter is defined', async () => {
    const input = { page: 0 } as any
    await expect(
      genomicElementsGenesRouters.genesFromGenomicElements({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('genomicElementsGenesRouters.grn', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns the gene regulatory network for a response gene', async () => {
    const mockResult = [
      {
        response_gene: 'CALML6',
        genomic_element: { chr: 'chr1', start: 1850597, end: 1858437, regulator_gene: 'SAMD11' },
        crispr_modality: 'interference',
        class: 'observed data',
        method: 'CRISPR screen',
        source: 'IGVF',
        biological_context: 'K562',
        files_filesets: 'files_filesets/IGVFFI3069QCRA',
        log2FC: 0.5,
        neg_log10_pvalue: 2.5,
        neg_log10_pvalue_adj: 1.5,
        significant: true,
        perturbation_efficiency_log2FC: -1.2,
        perturbation_efficiency_neg_log10_pvalue: 4.1,
        perturbation_efficiency_neg_log10_pvalue_adj: 3.0,
        perturbation_efficiency_significant: true
      }
    ]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { response_gene_id: 'ENSG00000116198', page: 0 }
    const result = await genomicElementsGenesRouters.grn({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('throws BAD_REQUEST when neither regulator nor response gene filters are defined', async () => {
    const input = { page: 0 } as any
    await expect(
      genomicElementsGenesRouters.grn({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('mouse element-gene routing', () => {
  beforeEach(() => jest.clearAllMocks())

  it.each(['genomicElementsFromGenes', 'genesFromGenomicElements'] as const)(
    '%s keeps exact and fallback queries in mouse collections', async (endpoint) => {
      const query = jest.spyOn(dbModule.db, 'query')
        .mockResolvedValue({ all: jest.fn().mockResolvedValue([]) } as any)
      const input = {
        organism: 'Mus musculus',
        method: 'Perturb-seq',
        biological_context: 'aortic smooth muscle cell',
        verbose: 'true',
        page: 0
      }
      await genomicElementsGenesRouters[endpoint]({ input, ctx: {}, type: 'query', path: '', rawInput: input })
      expect(query).toHaveBeenCalledTimes(4)
      query.mock.calls.forEach(([aql], index) => {
        const text = String(aql)
        expect(text).toContain(index === 0
          ? 'FOR record IN mm_genomic_elements_mm_genes'
          : 'FOR record IN mm_genomic_elements_mm_genes_text_en_no_stem_inverted_search_alias')
        expect(text).toContain('FOR gene IN mm_genes')
        expect(text).toContain('FOR element IN mm_genomic_elements')
        expect(text).not.toMatch(/FOR (?:record|gene|element) IN (?:genes|genomic_elements)\b/)
      })
    }
  )

  it('resolves mouse genes and binds mouse document IDs', async () => {
    const query = jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([{ _id: 'ENSMUSG00000026043' }]) } as any)
      .mockResolvedValue({ all: jest.fn().mockResolvedValue([]) } as any)
    const input = { organism: 'Mus musculus', gene_id: 'ENSMUSG00000026043', page: 0 }
    await genomicElementsGenesRouters.genomicElementsFromGenes({ input, ctx: {}, type: 'query', path: '', rawInput: input })
    expect(String(query.mock.calls[0][0])).toContain('mm_genes')
    expect(query.mock.calls[1][1]).toEqual({ geneIDs: ['mm_genes/ENSMUSG00000026043'] })
  })

  it('resolves regions against mouse elements', async () => {
    const query = jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(['mm_genomic_elements/test']) } as any)
      .mockResolvedValue({ all: jest.fn().mockResolvedValue([]) } as any)
    const input = { organism: 'Mus musculus', region: 'chr9:116004181-116004247', page: 0 }
    await genomicElementsGenesRouters.genesFromGenomicElements({ input, ctx: {}, type: 'query', path: '', rawInput: input })
    expect(String(query.mock.calls[0][0])).toContain('FOR record IN mm_genomic_elements')
    expect(query.mock.calls[1][1]).toEqual({ elementIDs: ['mm_genomic_elements/test'] })
  })
})
