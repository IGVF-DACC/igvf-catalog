import { codingVariantsRouters, queryCodingVariants } from '../../datatypeRouters/nodes/coding_variants'
import { db } from '../../../database'
import { appRouter } from '../../_app'

// Mock the database
jest.mock('../../../database', () => ({
  db: {
    query: jest.fn()
  }
}))

// Mock data constants
const mockCodingVariant = {
  _id: 'SAMD11_ENST00000420190_p.Ala3Gly_c.8C-G',
  name: 'SAMD11_ENST00000420190_p.Ala3Gly_c.8C>G',
  ref: 'M',
  alt: 'L',
  aapos: 1,
  gene_name: 'OR4F5',
  protein_name: 'A0A2U3U0J3_HUMAN',
  protein_id: 'ENSP00000493376',
  hgvsp: 'p.Met1?',
  hgvs: 'c.1A>C',
  refcodon: 'ATG',
  codonpos: 1,
  transcript_id: 'ENST00000641515',
  SIFT_score: null,
  SIFT4G_score: null,
  Polyphen2_HDIV_score: null,
  Polyphen2_HVAR_score: null,
  VEST4_score: null,
  Mcap_score: null,
  REVEL_score: null,
  MutPred_score: null,
  BayesDel_addAF_score: null,
  BayesDel_noAF_score: null,
  VARITY_R_score: null,
  VARITY_ER_score: null,
  VARITY_R_LOO_score: null,
  VARITY_ER_LOO_score: null,
  ESM1b_score: null,
  EVE_score: null,
  AlphaMissense_score: null,
  CADD_raw_score: 2.0917,
  source: 'dbSNFP 5.1a',
  source_url: 'http://database.liulab.science/dbNSFP'
}

describe('coding variants router', () => {
  const mockQuery = { all: jest.fn() }

  beforeEach(() => {
    jest.clearAllMocks()
    ;(db.query as jest.Mock).mockReturnValue(mockQuery)
  })

  test('router structure', () => {
    const router = codingVariantsRouters.codingVariants
    const openApi = router._def.meta?.openapi

    // Basic router structure
    expect('codingVariants' in codingVariantsRouters).toBe(true)
    expect(router._def.query).toBeTruthy()
    expect(openApi?.method).toBe('GET')
    expect(openApi?.path).toBe('/coding-variants')
  })

  test('queryCodingVariants by valid input', async () => {
    mockQuery.all.mockResolvedValue([mockCodingVariant])

    // Test regular ID
    const result = await queryCodingVariants({ id: 'SAMD11_ENST00000420190_p.Ala3Gly_c.8C-G' })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining("FILTER record._key == 'SAMD11_ENST00000420190_p.Ala3Gly_c.8C-G'"))
    expect(result).toEqual([mockCodingVariant])
  })

  test('queryCodingVariants parameter handling', async () => {
    // Test limit parameter
    mockQuery.all.mockResolvedValue([])
    await queryCodingVariants({ name: 'SAMD11_ENST00000420190_p.Ala3Gly_c.8C>G', limit: 10, page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 10'))

    // Test limit capping (MAX_PAGE_SIZE is 25)
    jest.clearAllMocks()
    mockQuery.all.mockResolvedValue([])
    await queryCodingVariants({ name: 'SAMD11_ENST00000420190_p.Ala3Gly_c.8C>G', limit: 50, page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))

    // Test pagination
    jest.clearAllMocks()
    mockQuery.all.mockResolvedValue([])
    await queryCodingVariants({ name: 'SAMD11_ENST00000420190_p.Ala3Gly_c.8C>G', page: 1 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('LIMIT 25, 25'))
  })

  test('queryCodingVariants with no filters', async () => {
    mockQuery.all.mockResolvedValue([mockCodingVariant])

    // Test with empty input (no filters)
    const result = await queryCodingVariants({})
    expect(result).toEqual([mockCodingVariant])
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('FOR record IN'))
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('SORT record.gene_name, record.aapos'))
    expect(db.query).not.toHaveBeenCalledWith(expect.stringContaining('FILTER'))
  })

  test('queryCodingVariants with only pagination parameters', async () => {
    mockQuery.all.mockResolvedValue([mockCodingVariant])

    // Test with only pagination parameters (which are ignored by getFilterStatements)
    const result = await queryCodingVariants({ page: 0, limit: 10 })
    expect(result).toEqual([mockCodingVariant])
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('FOR record IN'))
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('SORT record.gene_name, record.aapos'))
    expect(db.query).not.toHaveBeenCalledWith(expect.stringContaining('FILTER'))
  })

  test('tRPC router integration', async () => {
    mockQuery.all.mockResolvedValue([mockCodingVariant])
    const caller = appRouter.createCaller({ requestId: 'test-request-id' })
    const result = await caller.codingVariants({ name: 'SAMD11_ENST00000420190_p.Ala3Gly_c.8C>G' })

    expect(db.query).toHaveBeenCalledWith(expect.stringContaining("FILTER record.name == 'SAMD11_ENST00000420190_p.Ala3Gly_c.8C-G'"))
    expect(result).toEqual([mockCodingVariant])
    expect(db.query).toHaveBeenCalledTimes(1)
  })
})
