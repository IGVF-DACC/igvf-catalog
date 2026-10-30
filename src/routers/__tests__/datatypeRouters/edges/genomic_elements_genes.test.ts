import { genomicElementsGenesRouters } from '../../../datatypeRouters/edges/genomic_elements_genes'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

describe('genomicElementsGenesRouters.genomicElementsFromGenes', () => {
  beforeEach(() => {
    jest.resetAllMocks()
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
        perturbation: null,
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

  it('looks up preferred_assay_titles via files_filesets and expands TAP-seq to include Perturb-seq', async () => {
    const geneRecords = [{ _id: 'ENSG00000116198', name: 'CALML6', chr: 'chr1', start: 1850597, end: 1858437 }]
    const mockResult = [
      {
        name: 'regulates',
        label: 'perturbation effect on gene expression',
        method: 'Perturb-seq',
        class: 'observed data',
        source: 'IGVF',
        source_url: 'https://data.igvf.org/tabular-files/IGVFFI0001XXXX/',
        biological_context: 'K562',
        biosample_term: 'ontology_terms/EFO_0002067',
        cell_annotation: null,
        cell_annotation_term: null,
        files_filesets: 'files_filesets/IGVFFI0001XXXX',
        preferred_assay_titles: ['TAP-seq'],
        perturbation: null,
        score: null,
        transcription_start_site: null,
        rna_pseudobulk_tpm: null,
        log2FC: -0.42,
        log2FC_ci95_lower: null,
        log2FC_ci95_upper: null,
        effect_size: null,
        effect_size_ci_95: null,
        z_score: null,
        t_score: null,
        idr: null,
        pct_1: null,
        pct_2: null,
        num_guides: null,
        num_cells: null,
        fold_change: null,
        background_corrected_fold_change: null,
        cpm_perturb: null,
        cpm_bg: null,
        gamma_approximation_ln_p_value: null,
        hypergeometric_ln_p_value: null,
        empirical_p_value: null,
        p_value: 0.001,
        p_value_adj: 0.004023984,
        neg_log10_pvalue: null,
        neg_log10_pvalue_adj: null,
        significant: true,
        genomic_element: 'genomic_elements/CRISPR_chr1_3774714_3775214_GRCh38_IGVFFI0001XXXX',
        gene: 'genes/ENSG00000116198'
      }
    ]

    const query = jest.spyOn(dbModule.db, 'query')
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

    const aql = String(query.mock.calls[1][0])
    expect(aql).toContain('DOCUMENT(record.files_filesets).preferred_assay_titles')
    expect(result).toEqual([{ ...mockResult[0], preferred_assay_titles: ['TAP-seq', 'Perturb-seq'] }])
  })
})

describe('genomicElementsGenesRouters.genesFromGenomicElements', () => {
  beforeEach(() => {
    jest.resetAllMocks()
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
        perturbation: 'CRISPR interference',
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
        perturbation: null,
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
    jest.resetAllMocks()
  })

  it('returns the gene regulatory network for a response gene', async () => {
    const mockResult = [
      {
        response_gene: 'CALML6',
        genomic_element: { chr: 'chr1', start: 1850597, end: 1858437, regulator_gene: 'SAMD11' },
        perturbation: 'CRISPR interference',
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

  it('looks up preferred_assay_titles via files_filesets and expands TAP-seq to include Perturb-seq', async () => {
    const mockResult = [
      {
        response_gene: 'CALML6',
        genomic_element: { chr: 'chr1', start: 1850597, end: 1858437, regulator_gene: 'SAMD11' },
        perturbation: null,
        class: 'observed data',
        method: 'Perturb-seq',
        source: 'IGVF',
        biological_context: 'K562',
        files_filesets: 'files_filesets/IGVFFI0001XXXX',
        preferred_assay_titles: ['TAP-seq'],
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

    const query = jest.spyOn(dbModule.db, 'query').mockResolvedValue({
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

    const aql = String(query.mock.calls[0][0])
    expect(aql).toContain('DOCUMENT(record.files_filesets).preferred_assay_titles')
    expect(result).toEqual([{ ...mockResult[0], preferred_assay_titles: ['TAP-seq', 'Perturb-seq'] }])
  })
})

describe('mouse element-gene routing', () => {
  beforeEach(() => jest.resetAllMocks())

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

describe('GRN organism routing', () => {
  beforeEach(() => jest.resetAllMocks())

  it.each([
    { regulator_gene_id: 'ENSMUSG00000032440' },
    { response_gene_id: 'ENSMUSG00000026043' },
    { regulator_gene_id: 'ENSMUSG00000032440', response_gene_id: 'ENSMUSG00000026043' }
  ])('routes mouse GRN queries and self-effects: %j', async (genes) => {
    const query = jest.spyOn(dbModule.db, 'query')
      .mockResolvedValue({ all: jest.fn().mockResolvedValue([]) } as any)
    const input = { ...genes, organism: 'Mus musculus', neg_log10_pvalue: 'gte:2', page: 1, limit: 10 }
    await genomicElementsGenesRouters.grn({ input, ctx: {}, type: 'query', path: '', rawInput: input })
    const aql = String(query.mock.calls[0][0])
    expect(aql).toContain('IN mm_genes')
    expect(aql).toContain('in mm_genomic_elements_mm_genes')
    expect(aql).toContain('FOR se IN mm_genomic_elements_mm_genes')
    expect(aql).toContain('ge.promoter_of')
    expect(aql).toContain('LIMIT 10, 10')
    expect(aql).not.toMatch(/\b(?:IN|in) (?:genes|genomic_elements|genomic_elements_genes)\b/)
    if ('regulator_gene_id' in genes) expect(aql).toMatch(/(?:IN|in) mm_genomic_elements\s/)
  })

  it('defaults to human collections', async () => {
    const query = jest.spyOn(dbModule.db, 'query')
      .mockResolvedValue({ all: jest.fn().mockResolvedValue([]) } as any)
    const input = { regulator_gene_id: 'ENSG00000123685' }
    await genomicElementsGenesRouters.grn({ input, ctx: {}, type: 'query', path: '', rawInput: input })
    expect(String(query.mock.calls[0][0])).toContain('FOR gene IN genes')
    expect(String(query.mock.calls[0][0])).toContain('FOR se IN genomic_elements_genes')
  })
})

describe('genomicElementsGenesRouters.genesGenomicElementsScoreSummary', () => {
  beforeEach(() => {
    jest.resetAllMocks()
  })

  it('returns grouped min/max summaries for a known gene', async () => {
    const mockGroups = [
      {
        method: 'ENCODE-rE2G',
        source: 'ENCODE',
        files_filesets: 'files_filesets/ENCFF003BKC',
        biosample_term: 'ontology_terms/UBERON_0002626',
        biological_context: 'head of caudate nucleus',
        cell_annotation: null,
        cell_annotation_term: null,
        perturbation: null,
        min: 0.20425818,
        max: 0.99998393,
        edge_count: 5,
        numeric_count: 5,
        missing_count: 0,
        invalid_count: 0,
        zero_count: 0
      }
    ]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(['genes/ENSG00000000003']) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([{ total_edge_count: 5, groups: mockGroups }]) } as any)

    const input = { gene_id: 'ENSG00000000003', score_field: 'score' }
    const result = await genomicElementsGenesRouters.genesGenomicElementsScoreSummary({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual({
      gene_id: 'ENSG00000000003',
      score_field: 'score',
      total_edge_count: 5,
      groups: mockGroups
    })
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('defaults to page 0 and a limit of 25, capping a larger requested limit at 500', async () => {
    const query = jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(['genes/ENSG00000000003']) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([{ total_edge_count: 0, groups: [] }]) } as any)

    const input = { gene_id: 'ENSG00000000003', score_field: 'score' }
    await genomicElementsGenesRouters.genesGenomicElementsScoreSummary({
      input, ctx: {}, type: 'query', path: '', rawInput: input
    })
    expect(query.mock.calls[1][1]).toMatchObject({ page: 0, limit: 25 })

    jest.resetAllMocks()
    const query2 = jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(['genes/ENSG00000000003']) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([{ total_edge_count: 0, groups: [] }]) } as any)

    const input2 = { gene_id: 'ENSG00000000003', score_field: 'score', page: 2, limit: 99999 }
    await genomicElementsGenesRouters.genesGenomicElementsScoreSummary({
      input: input2, ctx: {}, type: 'query', path: '', rawInput: input2
    })
    expect(query2.mock.calls[1][1]).toMatchObject({ page: 2, limit: 500 })
  })

  it('throws NOT_FOUND for an unknown gene without ever running the aggregation query', async () => {
    const query = jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([]) } as any)

    const input = { gene_id: 'NOT_A_REAL_GENE', score_field: 'score' }
    await expect(
      genomicElementsGenesRouters.genesGenomicElementsScoreSummary({
        input, ctx: {}, type: 'query', path: '', rawInput: input
      })
    ).rejects.toThrow(TRPCError)
    expect(query).toHaveBeenCalledTimes(1)
  })

  it('returns an empty group list for a known gene with no matching edges', async () => {
    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(['genes/ENSG00000000003']) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([{ total_edge_count: 0, groups: [] }]) } as any)

    const input = { gene_id: 'ENSG00000000003', score_field: 'idr', files_fileset: 'NOTAREALFILESET' }
    const result = await genomicElementsGenesRouters.genesGenomicElementsScoreSummary({
      input, ctx: {}, type: 'query', path: '', rawInput: input
    })

    expect(result).toEqual({
      gene_id: 'ENSG00000000003',
      score_field: 'idr',
      total_edge_count: 0,
      groups: []
    })
  })

  it('filters biological_context as an exact match, not a fuzzy search', async () => {
    const query = jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(['genes/ENSG00000000003']) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([{ total_edge_count: 0, groups: [] }]) } as any)

    const input = { gene_id: 'ENSG00000000003', score_field: 'score', biological_context: 'HCASMC-hTERT' }
    await genomicElementsGenesRouters.genesGenomicElementsScoreSummary({
      input, ctx: {}, type: 'query', path: '', rawInput: input
    })

    const [aql, bindVars] = query.mock.calls[1]
    expect(String(aql)).toContain('record.biological_context == @biologicalContext')
    expect(bindVars).toMatchObject({ biologicalContext: 'HCASMC-hTERT' })
  })

  it('excludes groups with no numeric scores before pagination and counts only scored edges', async () => {
    const query = jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(['genes/ENSG00000000003']) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([{ total_edge_count: 0, groups: [] }]) } as any)

    const input = { gene_id: 'ENSG00000000003', score_field: 'score' }
    await genomicElementsGenesRouters.genesGenomicElementsScoreSummary({
      input, ctx: {}, type: 'query', path: '', rawInput: input
    })

    const aql = String(query.mock.calls[1][0])
    expect(aql).toContain('FILTER g.numeric_count > 0')
    expect(aql).toContain('total_edge_count: SUM(scoredGroups[*].numeric_count)')
    expect(aql).toContain('groups: SLICE(scoredGroups, @page * @limit, @limit)')
  })

  it.each([
    [{ page: -1 }],
    [{ page: 1.5 }]
  ])('throws BAD_REQUEST for an invalid page %j', async (overrides) => {
    const query = jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(['genes/ENSG00000000003']) } as any)

    const input = { gene_id: 'ENSG00000000003', score_field: 'score', ...overrides }
    await expect(
      genomicElementsGenesRouters.genesGenomicElementsScoreSummary({
        input, ctx: {}, type: 'query', path: '', rawInput: input
      })
    ).rejects.toThrow(TRPCError)
    expect(query).not.toHaveBeenCalled()
  })

  it.each([
    [{ limit: -1 }],
    [{ limit: 0 }],
    [{ limit: 1.5 }]
  ])('throws BAD_REQUEST for an invalid limit %j instead of silently bypassing the page size cap', async (overrides) => {
    const query = jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(['genes/ENSG00000000003']) } as any)

    const input = { gene_id: 'ENSG00000000003', score_field: 'score', ...overrides }
    await expect(
      genomicElementsGenesRouters.genesGenomicElementsScoreSummary({
        input, ctx: {}, type: 'query', path: '', rawInput: input
      })
    ).rejects.toThrow(TRPCError)
    expect(query).not.toHaveBeenCalled()
  })
})

describe('MORF gene regulatory network', () => {
  beforeEach(() => {
    jest.resetAllMocks()
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({ all: jest.fn().mockResolvedValue([]) } as any)
  })

  it.each([
    { regulator_gene_id: 'ENSG00000275700' },
    { response_gene_id: 'ENSG00000198846' },
    { regulator_gene_name: 'AATF', response_gene_name: 'TOX' }
  ])('joins MORF genes and transcripts for %j', async (genes) => {
    const input = { ...genes, method: 'MORF screen', perturbation: 'ORF overexpression', files_fileset: 'IGVFFI6734IWRB', significant: 'true', neg_log10_pvalue_adj: 'gte:2', page: 1, limit: 10 }
    await genomicElementsGenesRouters.grn({ input, ctx: {}, type: 'query', path: '', rawInput: input })
    const aql = String((dbModule.db.query as jest.Mock).mock.calls[0][0])
    const morf = aql.slice(aql.indexOf('LET morf ='))
    expect(morf).toContain('FOR record IN genes_transcripts_genes')
    expect(morf).toContain('DOCUMENT(record._from)')
    expect(morf).toContain('DOCUMENT(relationship._from)')
    expect(morf).toContain('transcript: relationship._to')
    expect(morf).toContain("record.method IN ['MORF screen']")
    expect(morf).toContain("record.perturbation == 'ORF overexpression'")
    expect(morf).toContain("record.files_filesets == 'files_filesets/IGVFFI6734IWRB'")
    expect(morf).toContain("'preferred_assay_titles': DOCUMENT(record.files_filesets).preferred_assay_titles")
    expect(morf).toContain('record.significant == true')
    expect(morf).toContain("record['neg_log10_pvalue_adj'] >= 2")
    if ('regulator_gene_id' in genes) expect(morf).toContain("regulator_gene._key == 'ENSG00000275700'")
    if ('response_gene_id' in genes) expect(morf).toContain("response_gene._key == 'ENSG00000198846'")
    if ('regulator_gene_name' in genes) {
      expect(morf).toContain("regulator_gene.name == 'AATF'")
      expect(morf).toContain("response_gene.name == 'TOX'")
    }
    const efficiency = morf.slice(morf.indexOf('LET perturbationEfficiencyEdge'), morf.indexOf('RETURN {'))
    expect(efficiency).toContain("se.morf_id == 'TOX_1'")
    expect(efficiency).toContain('se.files_filesets == record.files_filesets')
    expect(efficiency).toContain('se._to == record._to')
    expect(efficiency).not.toContain('se.significant')
    expect(efficiency).not.toContain('se._from == record._from')
    expect(aql).toContain('FOR result IN UNION(crispr, morf)')
    expect(aql.match(/LIMIT 10, 10/g)).toHaveLength(1)
    expect(aql.indexOf('LIMIT 10, 10')).toBeGreaterThan(aql.indexOf('UNION(crispr, morf)'))
  })

  it.each(['false', 'true'])('preserves MORF transcripts and nullable efficiency with verbose=%s', async (verbose) => {
    const records = ['ENST00000450518', 'ENST00000392662'].map(transcript => ({
      response_gene: 'TOX',
      regulator_gene: 'ACTL6A',
      genomic_element: null,
      transcript: verbose === 'true' ? { _id: `transcripts/${transcript}`, name: 'ACTL6A-201' } : `transcripts/${transcript}`,
      perturbation: 'ORF overexpression',
      method: 'MORF screen',
      class: 'observed data',
      source: 'IGVF',
      biological_context: 'T cell',
      files_filesets: 'files_filesets/IGVFFI6734IWRB',
      log2FC: 0.5,
      neg_log10_pvalue: 3,
      neg_log10_pvalue_adj: 2,
      significant: true,
      perturbation_efficiency_log2FC: null,
      perturbation_efficiency_neg_log10_pvalue: null,
      perturbation_efficiency_neg_log10_pvalue_adj: null,
      perturbation_efficiency_significant: null
    }))
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({ all: jest.fn().mockResolvedValue(records) } as any)
    const input = { response_gene_name: 'TOX', verbose }
    expect(await genomicElementsGenesRouters.grn({ input, ctx: {}, type: 'query', path: '', rawInput: input })).toEqual(records)
    const aql = String((dbModule.db.query as jest.Mock).mock.calls[0][0])
    if (verbose === 'true') {
      expect(aql).toContain('DOCUMENT(relationship._to)')
      expect(aql).toContain("transcript['name']")
    } else {
      expect(aql).not.toContain('DOCUMENT(relationship._to)')
    }
  })

  it('includes and expands preferred_assay_titles for MORF screen results', async () => {
    const records = [{
      response_gene: 'TOX',
      regulator_gene: 'ACTL6A',
      genomic_element: null,
      transcript: 'transcripts/ENST00000450518',
      perturbation: 'ORF overexpression',
      method: 'MORF screen',
      class: 'observed data',
      source: 'IGVF',
      biological_context: 'T cell',
      files_filesets: 'files_filesets/IGVFFI6734IWRB',
      preferred_assay_titles: ['TAP-seq'],
      log2FC: 0.5,
      neg_log10_pvalue: 3,
      neg_log10_pvalue_adj: 2,
      significant: true,
      perturbation_efficiency_log2FC: null,
      perturbation_efficiency_neg_log10_pvalue: null,
      perturbation_efficiency_neg_log10_pvalue_adj: null,
      perturbation_efficiency_significant: null
    }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({ all: jest.fn().mockResolvedValue(records) } as any)
    const input = { response_gene_name: 'TOX' }
    const result = await genomicElementsGenesRouters.grn({ input, ctx: {}, type: 'query', path: '', rawInput: input })
    expect(result).toEqual([{ ...records[0], preferred_assay_titles: ['TAP-seq', 'Perturb-seq'] }])
  })

  it('does not join human MORF data for mouse requests', async () => {
    const input = { regulator_gene_id: 'ENSMUSG00000027018', organism: 'Mus musculus' }
    await genomicElementsGenesRouters.grn({ input, ctx: {}, type: 'query', path: '', rawInput: input })
    expect(String((dbModule.db.query as jest.Mock).mock.calls[0][0])).not.toContain('genes_transcripts_genes')
  })
})

describe('GRN directional screen statistics', () => {
  it.each([
    { response_gene_id: 'ENSG00000179776' },
    { regulator_gene_id: 'ENSG00000179776' },
    { regulator_gene_id: 'ENSG00000179776', response_gene_id: 'ENSG00000179776' }
  ])('maps negative-selection statistics before filtering: %j', async (genes) => {
    const query = jest.spyOn(dbModule.db, 'query')
      .mockResolvedValue({ all: jest.fn().mockResolvedValue([]) } as any)
    const input = { ...genes, significant: 'true', neg_log10_pvalue_adj: 'gte:2', page: 0, limit: 10 }
    await genomicElementsGenesRouters.grn({ input, ctx: {}, type: 'query', path: '', rawInput: input })
    const aql = String(query.mock.calls[query.mock.calls.length - 1][0])
    expect(aql).toContain('log2FC: rawRecord.negative_selection_log2FC')
    expect(aql).toContain('p_value: rawRecord.negative_selection_p_value')
    expect(aql).toContain('p_value_adj: rawRecord.negative_selection_p_value_adj')
    expect(aql).toContain('significant: rawRecord.negative_selection_significant')
    expect(aql).toContain('log2FC: se.negative_selection_log2FC')
    expect(aql.indexOf('LET record =')).toBeLessThan(aql.indexOf('FILTER record.significant == true'))
    const edgeFilter = aql.indexOf('FILTER rawRecord.')
    expect(edgeFilter).toBeGreaterThan(-1)
    expect(edgeFilter).toBeLessThan(aql.indexOf('LET record ='))
    expect(aql).toContain('rawRecord.method IN')
    expect(aql).not.toContain('positive_selection')
  })
})
