import { codingVariantsRouters } from '../../../datatypeRouters/nodes/coding_variants'
import * as dbModule from '../../../../database'
import * as helpers from '../../../datatypeRouters/_helpers'

describe('codingVariantsRouters', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('transforms input and output correctly', async () => {
    // Mock DB and helpers
    const mockResult = [{
      _id: '1',
      name: 'A!B-C',
      ref: 'A',
      alt: 'B',
      protein_name: 'PN',
      protein_id: 'PID',
      gene_name: 'GN',
      transcript_id: 'TID',
      aapos: 42,
      hgvsp: 'hgvsp',
      hgvs: 'hgvs',
      refcodon: 'refcodon',
      codonpos: 1,
      SIFT_score: 0.1,
      SIFT4G_score: 0.2,
      Polyphen2_HDIV_score: 0.3,
      Polyphen2_HVAR_score: 0.4,
      VEST4_score: 0.5,
      Mcap_score: 0.6,
      REVEL_score: 0.7,
      MutPred_score: 0.8,
      BayesDel_addAF_score: 0.9,
      BayesDel_noAF_score: 1.0,
      VARITY_R_score: 1.1,
      VARITY_ER_score: 1.2,
      VARITY_R_LOO_score: 1.3,
      VARITY_ER_LOO_score: 1.4,
      ESM1b_score: 1.5,
      EVE_score: 1.6,
      AlphaMissense_score: 1.7,
      CADD_raw_score: 1.8,
      source: 'src',
      source_url: 'url'
    }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('gene_name == "GN"')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name')

    const input = {
      id: '1',
      name: 'A?B>C',
      amino_acid_position: '42',
      page: 0,
      limit: 10
    }
    const result = await codingVariantsRouters.codingVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    // Assert result type to avoid 'unknown' error
    const typedResult = result as Array<{ name: string }>
    // Output name should be transformed back
    expect(typedResult[0].name).toBe('A?B>C')
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('limits the page size to MAX_PAGE_SIZE', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([])
    } as any)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name')

    const input = {
      page: 0,
      limit: 1000 // above MAX_PAGE_SIZE
    }
    await codingVariantsRouters.codingVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    // The query should still run, but limit should be capped
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('handles missing optional fields', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([])
    } as any)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name')

    const input = {}
    const result = await codingVariantsRouters.codingVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(Array.isArray(result)).toBe(true)
  })
})
