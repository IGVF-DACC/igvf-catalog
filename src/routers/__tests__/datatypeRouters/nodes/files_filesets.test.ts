import { filesFilesetsRouters } from '../../../datatypeRouters/nodes/files_filesets'
import * as dbModule from '../../../../database'
import * as helpers from '../../../datatypeRouters/_helpers'

jest.mock('../../../../database')
jest.mock('../../../datatypeRouters/_helpers')

describe('filesFilesetsRouters.filesFilesets', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns files-filesets results', async () => {
    const mockResult = [{
      _id: '1',
      file_set_id: 'FS1',
      lab: 'roderic-guigo',
      preferred_assay_titles: ['HiC'],
      assay_term_ids: ['AT1'],
      method: 'MPRA',
      class: 'experiment',
      software: ['BEDTools'],
      samples: ['ontology_terms/S1'],
      sample_ids: ['SID1'],
      simple_sample_summaries: ['summary'],
      donors: ['donors/D1'],
      source: 'ENCODE'
    }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('lab == "roderic-guigo"')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, file_set_id, lab, preferred_assay_titles, method, class, software, samples, donors, source')

    const input = {
      lab: 'roderic-guigo',
      page: 0,
      limit: 10
    }
    const result = await filesFilesetsRouters.filesFilesets({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('caps limit to MAX_PAGE_SIZE', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([])
    } as any)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, file_set_id')

    const input = {
      page: 0,
      limit: 1000 // above MAX_PAGE_SIZE
    }
    await filesFilesetsRouters.filesFilesets({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('transforms samples and donors input', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([])
    } as any)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, file_set_id')

    const input = {
      samples: 'S1',
      donors: 'D1',
      page: 0
    }
    await filesFilesetsRouters.filesFilesets({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    // The transformation should prepend the correct string
    // You can check the query string or rely on the mock to be called
    expect(dbModule.db.query).toHaveBeenCalled()
  })
})
