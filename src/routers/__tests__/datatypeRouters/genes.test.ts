import { genesRouters, geneSearch, nearestGeneSearch, findGenesByTextSearch } from '../../datatypeRouters/nodes/genes'
import { db } from '../../../database'
import { TRPCError } from '@trpc/server'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'

// Mock the database
jest.mock('../../../database', () => ({
  db: {
    query: jest.fn()
  }
}))

describe('genes routers', () => {
  test('router is defined and available', () => {
    expect('genes' in genesRouters)
  })

  describe('it implements general query', () => {
    let router: any
    let openApi: any

    beforeEach(() => {
      router = genesRouters.genes
      openApi = router._def.meta?.openapi
    })

    test('implements OpenApi protocol', () => {
      expect(typeof openApi).toBe('object')
    })

    test('accepts pagination', () => {
      let inputParsing = router._def.inputs[0].parse({ gene_type: 'miRNA' })
      expect(inputParsing.page).toEqual(0)

      inputParsing = router._def.inputs[0].parse({ gene_type: 'miRNA', page: 1 })
      expect(inputParsing.page).toEqual(1)
    })

    test('accepts gene query format', () => {
      const geneQuery = {
        organism: 'Homo sapiens',
        region: 'chr1:12345-54321',
        gene_type: 'miRNA',
        page: 0
      }

      const inputParsing = router._def.inputs[0].parse(geneQuery)
      expect(inputParsing).toEqual(geneQuery)
    })

    test('returns an array of genes in correct format', () => {
      const genes = [{
        _id: 'ENSG00000207644',
        gene_type: 'miRNA',
        chr: 'chr19',
        start: 53669156,
        end: 53669254,
        name: 'MIR512-2',
        source: 'GENCODE',
        version: 'v43',
        source_url: 'https://www.gencodegenes.org/human/'
      }]

      const outputParsing = router._def.output.parse(genes)
      expect(outputParsing).toEqual(genes)
    })

    test('has correct URL', () => {
      expect(openApi?.method).toBe('GET')
      expect(openApi?.path).toBe('/genes')
    })

    test('Expects procedure to be a trpc query', () => {
      expect(router._def.query).toBeTruthy()
    })
  })

  describe('geneSearch function', () => {
    const mockQuery = {
      all: jest.fn()
    }

    beforeEach(() => {
      jest.clearAllMocks()
      ;(db.query as jest.Mock).mockReturnValue(mockQuery)
    })

    test('handles human organism by default', async () => {
      mockQuery.all.mockResolvedValue([{ _id: 'test', name: 'test' }])

      const result = await geneSearch({ organism: 'Homo sapiens' })

      expect(db.query).toHaveBeenCalledWith(expect.stringContaining('genes'))
      expect(result).toEqual([{ _id: 'test', name: 'test' }])
    })

    test('handles mouse organism', async () => {
      mockQuery.all.mockResolvedValue([{ _id: 'test', name: 'test' }])

      const result = await geneSearch({ organism: 'Mus musculus' })

      expect(db.query).toHaveBeenCalledWith(expect.stringContaining('mm_genes'))
      expect(result).toEqual([{ _id: 'test', name: 'test' }])
    })

    test('converts gene_id to _key', async () => {
      mockQuery.all.mockResolvedValue([{ _id: 'test', name: 'test' }])

      await geneSearch({ gene_id: 'ENSG00000139618' })

      expect(db.query).toHaveBeenCalledWith(expect.stringContaining('_key'))
    })

    test('converts synonym to synonyms', async () => {
      mockQuery.all.mockResolvedValue([])

      await geneSearch({ synonym: 'BRCA1' })

      expect(db.query).toHaveBeenCalledWith(expect.stringContaining('synonyms'))
    })

    test('converts collection to collections', async () => {
      mockQuery.all.mockResolvedValue([])

      await geneSearch({ collection: 'test_collection' })

      expect(db.query).toHaveBeenCalledWith(expect.stringContaining('collections'))
    })

    test('converts study_set to study_sets', async () => {
      mockQuery.all.mockResolvedValue([])

      await geneSearch({ study_set: 'test_study' })

      expect(db.query).toHaveBeenCalledWith(expect.stringContaining('study_sets'))
    })

    test('handles entrez ID without prefix', async () => {
      mockQuery.all.mockResolvedValue([])

      await geneSearch({ entrez: '672' })

      expect(db.query).toHaveBeenCalledWith(expect.stringContaining('ENTREZ:672'))
    })

    test('handles entrez ID with prefix', async () => {
      mockQuery.all.mockResolvedValue([])

      await geneSearch({ entrez: 'ENTREZ:672' })

      expect(db.query).toHaveBeenCalledWith(expect.stringContaining('ENTREZ:672'))
    })

    test('handles hgnc_id without prefix', async () => {
      mockQuery.all.mockResolvedValue([])

      await geneSearch({ hgnc_id: '1100' })

      expect(db.query).toHaveBeenCalledWith(expect.stringContaining('HGNC:1100'))
    })

    test('handles hgnc_id with prefix', async () => {
      mockQuery.all.mockResolvedValue([])

      await geneSearch({ hgnc_id: 'HGNC:1100' })

      expect(db.query).toHaveBeenCalledWith(expect.stringContaining('HGNC:1100'))
    })

    test('handles limit parameter', async () => {
      mockQuery.all.mockResolvedValue([])

      await geneSearch({ limit: 100 })

      expect(db.query).toHaveBeenCalledWith(expect.stringContaining('LIMIT'))
    })

    test('caps limit at MAX_PAGE_SIZE', async () => {
      mockQuery.all.mockResolvedValue([])

      await geneSearch({ limit: 1000 })

      expect(db.query).toHaveBeenCalledWith(expect.stringContaining('LIMIT'))
    })

    test('returns empty array when no results', async () => {
      mockQuery.all.mockResolvedValue([])

      const result = await geneSearch({})

      expect(result).toEqual([])
    })

    test('calls findGenesByTextSearch when text search parameters are present', async () => {
      mockQuery.all.mockResolvedValue([])

      await geneSearch({ name: 'BRCA1' })

      expect(db.query).toHaveBeenCalledTimes(3) // Once for regular search, twice for text search (exact + levenshtein)
    })
  })

  describe('nearestGeneSearch function', () => {
    const mockQuery = {
      all: jest.fn()
    }

    beforeEach(() => {
      jest.clearAllMocks()
      ;(db.query as jest.Mock).mockReturnValue(mockQuery)
    })

    test('throws error for invalid region format', async () => {
      await expect(nearestGeneSearch({ region: 'invalid' })).rejects.toThrow(TRPCError)
    })

    test('returns genes in region when found', async () => {
      const mockGenes = [{ _id: 'test', name: 'test' }]
      mockQuery.all.mockResolvedValue(mockGenes)

      const result = await nearestGeneSearch({ region: 'chr1:12345-54321' })

      expect(result).toEqual(mockGenes)
    })

    test('returns nearest genes when no genes in region', async () => {
      mockQuery.all
        .mockResolvedValueOnce([]) // First call returns empty (no genes in region)
        .mockResolvedValueOnce([{ _id: 'nearest', name: 'nearest' }]) // Second call returns nearest genes

      const result = await nearestGeneSearch({ region: 'chr1:12345-54321' })

      expect(result).toEqual({ _id: 'nearest', name: 'nearest' })
    })

    test('returns empty array when no nearest genes found', async () => {
      mockQuery.all
        .mockResolvedValueOnce([]) // No genes in region
        .mockResolvedValueOnce([]) // No nearest genes

      const result = await nearestGeneSearch({ region: 'chr1:12345-54321' })

      expect(result).toEqual(undefined)
    })

    test('applies gene_type filter', async () => {
      mockQuery.all.mockResolvedValue([])

      await nearestGeneSearch({ region: 'chr1:12345-54321', gene_type: 'protein_coding' })

      expect(db.query).toHaveBeenCalledWith(expect.stringContaining("gene_type == 'protein_coding'"))
    })
  })

  describe('findGenesByTextSearch function', () => {
    const mockQuery = {
      all: jest.fn()
    }

    beforeEach(() => {
      jest.clearAllMocks()
      ;(db.query as jest.Mock).mockReturnValue(mockQuery)
    })

    test('searches by gene name', async () => {
      mockQuery.all.mockResolvedValue([{ _id: 'test', name: 'BRCA1' }])

      const schema = loadSchemaConfig()
      const result = await findGenesByTextSearch({ name: 'BRCA1' }, schema.gene)

      expect(db.query).toHaveBeenCalledWith(expect.stringContaining('TOKENS'))
      expect(result).toEqual([{ _id: 'test', name: 'BRCA1' }])
    })

    test('searches by synonym', async () => {
      mockQuery.all.mockResolvedValue([{ _id: 'test', name: 'BRCA1' }])

      const schema = loadSchemaConfig()
      const result = await findGenesByTextSearch({ synonym: 'BRCAI' }, schema.gene)

      expect(db.query).toHaveBeenCalledWith(expect.stringContaining('TOKENS'))
      expect(result).toEqual([{ _id: 'test', name: 'BRCA1' }])
    })

    test('falls back to Levenshtein search when exact search fails', async () => {
      mockQuery.all
        .mockResolvedValueOnce([]) // First search returns empty
        .mockResolvedValueOnce([{ _id: 'test', name: 'BRCA1' }]) // Levenshtein search returns result

      const schema = loadSchemaConfig()
      const result = await findGenesByTextSearch({ name: 'BRCA1' }, schema.gene)

      expect(db.query).toHaveBeenCalledTimes(2)
      expect(result).toEqual([{ _id: 'test', name: 'BRCA1' }])
    })

    test('handles limit parameter', async () => {
      mockQuery.all.mockResolvedValue([])

      const schema = loadSchemaConfig()
      await findGenesByTextSearch({ name: 'BRCA1', limit: 50 }, schema.gene)

      expect(db.query).toHaveBeenCalledWith(expect.stringContaining('LIMIT'))
    })

    test('caps limit at MAX_PAGE_SIZE', async () => {
      mockQuery.all.mockResolvedValue([])

      const schema = loadSchemaConfig()
      await findGenesByTextSearch({ name: 'BRCA1', limit: 1000 }, schema.gene)

      expect(db.query).toHaveBeenCalledWith(expect.stringContaining('LIMIT'))
    })
  })
})
