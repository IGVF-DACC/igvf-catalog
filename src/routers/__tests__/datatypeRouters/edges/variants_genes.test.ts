import { variantsGenesRouters } from '../../../datatypeRouters/edges/variants_genes'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

const callProcedure = async (procedure: any, input: Record<string, unknown>): Promise<any> =>
  procedure({ input, ctx: {}, type: 'query', path: '', rawInput: input })

describe('variantsGenesRouters', () => {
  beforeEach(() => {
    jest.resetAllMocks()
  })

  describe('qtlSummaryEndpoint', () => {
    it('returns qtl summary records for a variant', async () => {
      const variantSearchResult = [{ _id: 'NC_000001.11:10000:T:A', chr: 'chr1', pos: 10000 }]
      const summaryResult = [{
        qtl_type: 'eQTL',
        neg_log10_pvalue: 5.2,
        chr: 'chr1',
        biological_context: 'liver',
        effect_size: 0.4,
        gene: { gene_name: 'GENE1', gene_id: 'ENSG00000187583', gene_start: 1000, gene_end: 5000 },
        name: 'modulates expression of',
        files_filesets: 'files_filesets/IGVFFI0332UGDD'
      }]

      jest.spyOn(dbModule.db, 'query')
        .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(variantSearchResult) } as any)
        .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(summaryResult) } as any)

      const input = { spdi: 'NC_000001.11:10000:T:A', page: 0 }
      const result = await callProcedure(variantsGenesRouters.qtlSummaryEndpoint, input)

      expect(result).toEqual(summaryResult)
      expect(dbModule.db.query).toHaveBeenCalledTimes(2)
    })

    it('throws NOT_FOUND when the variant does not exist', async () => {
      jest.spyOn(dbModule.db, 'query').mockResolvedValue({
        all: jest.fn().mockResolvedValue([])
      } as any)

      const input = { spdi: 'NC_000001.11:99999:T:A', page: 0 }
      await expect(callProcedure(variantsGenesRouters.qtlSummaryEndpoint, input)).rejects.toThrow(TRPCError)
    })
  })

  describe('genesFromVariants', () => {
    it('returns qtl records for a variant filtered by method', async () => {
      const mockResult = [{
        gene: 'genes/ENSG00000187583',
        sequence_variant: 'variants/NC_000001.11:10000:T:A',
        effect_size: 0.5,
        neg_log10_pvalue: 3.1,
        neg_log10_pvalue_adj: null,
        log2FC: null,
        posterior_inclusion_probability: null,
        coefficient_stddev: null,
        power: null,
        significant: true,
        standard_error: null,
        z_score: null,
        credible_set_min_r2: null,
        method: 'CRISPR screen',
        perturbation: null,
        source: 'IGVF',
        source_url: 'https://data.igvf.org/tabular-files/IGVFFI0524YUIL/',
        label: 'variant effect on gene expression',
        p_value: null,
        chr: null,
        biological_context: 'THP-1',
        biosample_term: 'ontology_terms/EFO_0002067',
        name: 'expression modulated by',
        class: null,
        files_filesets: 'files_filesets/IGVFFI0332UGDD'
      }]

      jest.spyOn(dbModule.db, 'query').mockResolvedValue({
        all: jest.fn().mockResolvedValue(mockResult)
      } as any)

      const input = { method: 'CRISPR screen', page: 0 }
      const result = await callProcedure(variantsGenesRouters.genesFromVariants, input)

      expect(result).toEqual(mockResult)
      expect(dbModule.db.query).toHaveBeenCalledTimes(1)
    })

    it('falls back to prefix match when the exact biological_context match is empty', async () => {
      const prefixResult = [{
        gene: 'genes/ENSG00000187583',
        sequence_variant: 'variants/NC_000001.11:10000:T:A',
        effect_size: null,
        neg_log10_pvalue: null,
        neg_log10_pvalue_adj: null,
        log2FC: null,
        posterior_inclusion_probability: null,
        coefficient_stddev: null,
        power: null,
        significant: null,
        standard_error: null,
        z_score: null,
        credible_set_min_r2: null,
        method: 'CRISPR screen',
        perturbation: null,
        source: 'IGVF',
        source_url: 'https://data.igvf.org/tabular-files/IGVFFI0524YUIL/',
        label: 'variant effect on gene expression',
        p_value: null,
        chr: null,
        biological_context: 'THP-1 cells',
        biosample_term: 'ontology_terms/EFO_0002067',
        name: 'expression modulated by',
        class: null,
        files_filesets: null
      }]

      jest.spyOn(dbModule.db, 'query')
        .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([]) } as any)
        .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(prefixResult) } as any)

      const input = { method: 'CRISPR screen', biological_context: 'THP-1', page: 0 }
      const result = await callProcedure(variantsGenesRouters.genesFromVariants, input)

      expect(result).toEqual(prefixResult)
      expect(dbModule.db.query).toHaveBeenCalledTimes(2)
    })

    it('throws BAD_REQUEST when neg_log10_pvalue is not a range query', async () => {
      const input = { method: 'CRISPR screen', neg_log10_pvalue: '5', page: 0 }
      await expect(callProcedure(variantsGenesRouters.genesFromVariants, input)).rejects.toThrow(TRPCError)
    })

    it('throws BAD_REQUEST when no variant-identifying property is provided', async () => {
      const input = {}
      await expect(callProcedure(variantsGenesRouters.genesFromVariants, input)).rejects.toThrow(TRPCError)
    })

    it('looks up preferred_assay_titles via files_filesets and expands TAP-seq to include Perturb-seq', async () => {
      const mockResult = [{
        gene: 'genes/ENSG00000187583',
        sequence_variant: 'variants/NC_000001.11:10000:T:A',
        effect_size: null,
        neg_log10_pvalue: null,
        neg_log10_pvalue_adj: null,
        log2FC: 0.5,
        posterior_inclusion_probability: null,
        coefficient_stddev: null,
        power: null,
        significant: true,
        standard_error: null,
        z_score: null,
        credible_set_min_r2: null,
        method: 'Perturb-seq',
        crispr_modality: null,
        source: 'IGVF',
        source_url: 'https://data.igvf.org/tabular-files/IGVFFI0524YUIL/',
        label: 'variant effect on gene expression',
        p_value: null,
        chr: null,
        biological_context: 'THP-1',
        biosample_term: 'ontology_terms/EFO_0002067',
        name: 'expression modulated by',
        class: null,
        files_filesets: 'files_filesets/IGVFFI0332UGDD',
        preferred_assay_titles: ['TAP-seq']
      }]

      const query = jest.spyOn(dbModule.db, 'query').mockResolvedValue({
        all: jest.fn().mockResolvedValue(mockResult)
      } as any)

      const input = { method: 'CRISPR screen', page: 0 }
      const result = await callProcedure(variantsGenesRouters.genesFromVariants, input)

      expect(query.mock.calls[0][0]).toContain('DOCUMENT(record.files_filesets).preferred_assay_titles')
      expect(result).toEqual([{ ...mockResult[0], preferred_assay_titles: ['TAP-seq', 'Perturb-seq'] }])
    })
  })

  describe('variantsFromGenes', () => {
    it('returns qtl records for a gene filtered by method', async () => {
      const mockResult = [{
        gene: 'genes/ENSG00000187583',
        sequence_variant: 'variants/NC_000001.11:10000:T:A',
        effect_size: 0.2,
        neg_log10_pvalue: null,
        neg_log10_pvalue_adj: null,
        log2FC: null,
        posterior_inclusion_probability: null,
        coefficient_stddev: null,
        power: null,
        significant: null,
        standard_error: null,
        z_score: null,
        credible_set_min_r2: null,
        method: 'CRISPR screen',
        perturbation: null,
        source: 'IGVF',
        source_url: 'https://data.igvf.org/tabular-files/IGVFFI0524YUIL/',
        label: 'variant effect on gene expression',
        p_value: null,
        chr: null,
        biological_context: 'THP-1',
        biosample_term: 'ontology_terms/EFO_0002067',
        name: 'modulates expression of',
        class: null,
        files_filesets: null
      }]

      jest.spyOn(dbModule.db, 'query').mockResolvedValue({
        all: jest.fn().mockResolvedValue(mockResult)
      } as any)

      const input = { method: 'CRISPR screen', page: 0 }
      const result = await callProcedure(variantsGenesRouters.variantsFromGenes, input)

      expect(result).toEqual(mockResult)
    })

    it('throws BAD_REQUEST when no gene-identifying property is provided', async () => {
      const input = {}
      await expect(callProcedure(variantsGenesRouters.variantsFromGenes, input)).rejects.toThrow(TRPCError)
    })
  })

  describe('nearestGenes', () => {
    it('returns coding-region genes for a valid region', async () => {
      const mockResult = [{
        _id: 'ENSG00000187583',
        chr: 'chr1',
        start: 900,
        end: 2000,
        gene_type: 'protein_coding',
        name: 'GENE1',
        source: 'GENCODE',
        version: 'v44',
        source_url: 'https://www.gencodegenes.org/'
      }]

      jest.spyOn(dbModule.db, 'query').mockResolvedValue({
        all: jest.fn().mockResolvedValue(mockResult)
      } as any)

      const input = { region: 'chr1:1000-2000' }
      const result = await callProcedure(variantsGenesRouters.nearestGenes, input)

      expect(result).toEqual(mockResult)
    })

    it('throws BAD_REQUEST for an invalid region format', async () => {
      const input = { region: 'not-a-region' }
      await expect(callProcedure(variantsGenesRouters.nearestGenes, input)).rejects.toThrow(TRPCError)
    })
  })
})

describe('variantsGenesRouters.genesVariantsScoreSummary', () => {
  beforeEach(() => {
    jest.resetAllMocks()
  })

  it('returns grouped min/max summaries for a known gene, restricted to CRISPR screen edges', async () => {
    const mockGroups = [
      {
        method: 'CRISPR screen',
        source: 'IGVF',
        files_filesets: 'files_filesets/IGVFFI0524YUIL',
        biosample_term: 'ontology_terms/EFO_0001253',
        biological_context: 'human THP-1 cell line',
        perturbation: 'prime editing',
        min: -0.727384492,
        max: -0.1,
        edge_count: 2,
        numeric_count: 2,
        missing_count: 0,
        invalid_count: 0,
        zero_count: 0
      }
    ]

    const query = jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(['genes/ENSG00000108179']) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([{ total_edge_count: 2, groups: mockGroups }]) } as any)

    const input = { gene_id: 'ENSG00000108179', score_field: 'effect_size' }
    const result = await callProcedure(variantsGenesRouters.genesVariantsScoreSummary, input)

    expect(result).toEqual({
      gene_id: 'ENSG00000108179',
      score_field: 'effect_size',
      total_edge_count: 2,
      groups: mockGroups
    })

    const aql = String(query.mock.calls[1][0])
    expect(aql).toContain("record.method == 'CRISPR screen'")
    expect(aql).toContain("record.label == 'variant effect on gene expression'")
  })

  it('throws NOT_FOUND for an unknown gene without running the aggregation query', async () => {
    const query = jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([]) } as any)

    const input = { gene_id: 'NOT_A_REAL_GENE', score_field: 'effect_size' }
    await expect(callProcedure(variantsGenesRouters.genesVariantsScoreSummary, input)).rejects.toThrow(TRPCError)
    expect(query).toHaveBeenCalledTimes(1)
  })

  it('returns an empty group list and zero total for a known gene with no matching edges', async () => {
    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(['genes/ENSG00000108179']) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([{ total_edge_count: 0, groups: [] }]) } as any)

    const input = { gene_id: 'ENSG00000108179', score_field: 'effect_size', files_fileset: 'NOTAREALFILESET' }
    const result = await callProcedure(variantsGenesRouters.genesVariantsScoreSummary, input)

    expect(result).toEqual({
      gene_id: 'ENSG00000108179',
      score_field: 'effect_size',
      total_edge_count: 0,
      groups: []
    })
  })

  it('maps perturbation to the stored perturbation field and filters biological_context exactly', async () => {
    const query = jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(['genes/ENSG00000108179']) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([{ total_edge_count: 0, groups: [] }]) } as any)

    const input = {
      gene_id: 'ENSG00000108179',
      score_field: 'effect_size',
      perturbation: 'CRISPR base editing',
      biological_context: 'human THP-1 cell line'
    }
    await callProcedure(variantsGenesRouters.genesVariantsScoreSummary, input)

    const [aql, bindVars] = query.mock.calls[1]
    const aqlText = String(aql)
    expect(aqlText).toContain("record.perturbation == 'CRISPR base editing'")
    expect(aqlText).toContain('record.biological_context == @biologicalContext')
    expect(bindVars).toMatchObject({ biologicalContext: 'human THP-1 cell line' })
  })

  it('defaults to page 0 and a limit of 25, capping a larger requested limit at 500', async () => {
    const query = jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(['genes/ENSG00000108179']) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([{ total_edge_count: 0, groups: [] }]) } as any)

    const input = { gene_id: 'ENSG00000108179', score_field: 'effect_size' }
    await callProcedure(variantsGenesRouters.genesVariantsScoreSummary, input)
    expect(query.mock.calls[1][1]).toMatchObject({ page: 0, limit: 25 })

    jest.resetAllMocks()
    const query2 = jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(['genes/ENSG00000108179']) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([{ total_edge_count: 0, groups: [] }]) } as any)

    const input2 = { gene_id: 'ENSG00000108179', score_field: 'effect_size', page: 2, limit: 99999 }
    await callProcedure(variantsGenesRouters.genesVariantsScoreSummary, input2)
    expect(query2.mock.calls[1][1]).toMatchObject({ page: 2, limit: 500 })
  })

  it('excludes groups with no numeric scores before pagination and counts only scored edges', async () => {
    const query = jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(['genes/ENSG00000108179']) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([{ total_edge_count: 0, groups: [] }]) } as any)

    const input = { gene_id: 'ENSG00000108179', score_field: 'effect_size' }
    await callProcedure(variantsGenesRouters.genesVariantsScoreSummary, input)

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
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(['genes/ENSG00000108179']) } as any)

    const input = { gene_id: 'ENSG00000108179', score_field: 'effect_size', ...overrides }
    await expect(callProcedure(variantsGenesRouters.genesVariantsScoreSummary, input)).rejects.toThrow(TRPCError)
    expect(query).not.toHaveBeenCalled()
  })

  it.each([
    [{ limit: -1 }],
    [{ limit: 0 }],
    [{ limit: 1.5 }]
  ])('throws BAD_REQUEST for an invalid limit %j instead of silently bypassing the page size cap', async (overrides) => {
    const query = jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(['genes/ENSG00000108179']) } as any)

    const input = { gene_id: 'ENSG00000108179', score_field: 'effect_size', ...overrides }
    await expect(callProcedure(variantsGenesRouters.genesVariantsScoreSummary, input)).rejects.toThrow(TRPCError)
    expect(query).not.toHaveBeenCalled()
  })
})
