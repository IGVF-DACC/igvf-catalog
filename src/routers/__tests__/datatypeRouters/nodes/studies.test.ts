import { studiesRouters } from '../../../datatypeRouters/nodes/studies'
import * as dbModule from '../../../../database'
import * as helpers from '../../../datatypeRouters/_helpers'

jest.mock('../../../../database')
jest.mock('../../../datatypeRouters/_helpers')

describe('studiesRouters.studies', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns studies by study_id', async () => {
    const mockResult = [{
      _id: 'S1',
      name: 'StudyA',
      pmid: 'PMID:12345',
      source: 'GWAS Catalog',
      ancestry_initial: null,
      ancestry_replication: null,
      n_cases: null,
      n_initial: null,
      n_replication: null,
      pub_author: null,
      pub_date: null,
      pub_journal: null,
      pub_title: null,
      has_sumstats: null,
      num_assoc_loci: null,
      study_source: null,
      trait_reported: null,
      trait_efos: null,
      trait_category: null,
      study_type: null,
      version: null
    }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('_key == "S1"')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name, pmid, source')

    const input = { study_id: 'S1', page: 0 }
    const result = await studiesRouters.studies({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    // Should convert study_id to _key
    expect(dbModule.db.query).toHaveBeenCalled()
    expect(result).toEqual(mockResult)
  })

  it('returns studies by pmid', async () => {
    const mockResult = [{
      _id: 'S2',
      name: 'StudyB',
      pmid: 'PMID:67890',
      source: 'GWAS Catalog',
      ancestry_initial: null,
      ancestry_replication: null,
      n_cases: null,
      n_initial: null,
      n_replication: null,
      pub_author: null,
      pub_date: null,
      pub_journal: null,
      pub_title: null,
      has_sumstats: null,
      num_assoc_loci: null,
      study_source: null,
      trait_reported: null,
      trait_efos: null,
      trait_category: null,
      study_type: null,
      version: null
    }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('pmid == "PMID:67890"')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name, pmid, source')

    const input = { pmid: '67890', page: 0 }
    const result = await studiesRouters.studies({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    // Should convert pmid to 'PMID:67890'
    expect(dbModule.db.query).toHaveBeenCalled()
    expect(result).toEqual(mockResult)
  })

  it('returns studies with no id or pmid', async () => {
    const mockResult = [{
      _id: 'S3',
      name: 'StudyC',
      pmid: 'PMID:67890',
      source: 'GWAS Catalog',
      ancestry_initial: null,
      ancestry_replication: null,
      n_cases: null,
      n_initial: null,
      n_replication: null,
      pub_author: null,
      pub_date: null,
      pub_journal: null,
      pub_title: null,
      has_sumstats: null,
      num_assoc_loci: null,
      study_source: null,
      trait_reported: null,
      trait_efos: null,
      trait_category: null,
      study_type: null,
      version: null
    }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name, source')

    const input = { page: 0 }
    const result = await studiesRouters.studies({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(dbModule.db.query).toHaveBeenCalled()
    expect(result).toEqual(mockResult)
  })
})
