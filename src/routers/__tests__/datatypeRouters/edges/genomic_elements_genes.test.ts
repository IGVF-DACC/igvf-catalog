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
    jest.clearAllMocks()
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

describe('GRN organism routing', () => {
  beforeEach(() => jest.clearAllMocks())

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

describe('MORF gene regulatory network', () => {
  beforeEach(() => {
    jest.clearAllMocks()
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

  it('preserves each MORF transcript and nullable efficiency in the response', async () => {
    const records = ['ENST00000450518', 'ENST00000392662'].map(transcript => ({
      response_gene: 'TOX',
      regulator_gene: 'ACTL6A',
      genomic_element: null,
      transcript: `transcripts/${transcript}`,
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
    const input = { response_gene_name: 'TOX' }
    expect(await genomicElementsGenesRouters.grn({ input, ctx: {}, type: 'query', path: '', rawInput: input })).toEqual(records)
  })

  it('does not join human MORF data for mouse requests', async () => {
    const input = { regulator_gene_id: 'ENSMUSG00000027018', organism: 'Mus musculus' }
    await genomicElementsGenesRouters.grn({ input, ctx: {}, type: 'query', path: '', rawInput: input })
    expect(String((dbModule.db.query as jest.Mock).mock.calls[0][0])).not.toContain('genes_transcripts_genes')
  })
})
