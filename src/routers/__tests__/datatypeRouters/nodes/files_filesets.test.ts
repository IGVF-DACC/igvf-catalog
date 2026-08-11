import { filesFilesetsRouters, filesFilesetsFormat } from '../../../datatypeRouters/nodes/files_filesets'
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
      lab: 'jesse-engreitz',
      preferred_assay_titles: ['HiC'],
      assay_term_ids: ['AT1'],
      method: 'MPRA',
      class: 'experiment',
      software: ['BEDTools'],
      samples: ['ontology_terms/S1'],
      sample_ids: ['SID1'],
      simple_sample_summaries: ['summary'],
      donors: ['donors/D1'],
      source: 'IGVF',
      source_url: 'https://data.igvf.org/signal-files/IGVFFI8400FXRX/',
      download_link: 'https://api.data.igvf.org/signal-files/IGVFFI8400FXRX/@@download/IGVFFI8400FXRX.bigWig',
      genome_browser_link: 'https://api.data.igvf.org/signal-files/IGVFFI8400FXRX/@@download/IGVFFI8400FXRX.bigWig'
    }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('lab == "jesse-engreitz"')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, file_set_id, lab, preferred_assay_titles, method, class, software, samples, donors, source, source_url, download_link, genome_browser_link')

    const input = {
      lab: 'jesse-engreitz',
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

describe('filesFilesetsFormat', () => {
  const baseRecord = {
    _id: '1',
    file_set_id: 'FS1',
    lab: 'jesse-engreitz',
    class: 'observed data',
    source: 'IGVF',
    download_link: 'https://api.data.igvf.org/signal-files/IGVFFI8400FXRX/@@download/IGVFFI8400FXRX.bigWig'
  }

  // Regression test: some real file_filesets records legitimately have method: null and/or
  // source_url: null (per the JSON schema's ["string", "null"] type), but the output format
  // previously declared these as required non-nullable strings, causing "Output validation
  // failed" whenever such a record was returned (e.g. /files-filesets?limit=500&page=2).
  it('accepts records with a null method', () => {
    expect(() => filesFilesetsFormat.parse({ ...baseRecord, method: null, source_url: 'https://example.com' })).not.toThrow()
  })

  it('accepts records with a null source_url', () => {
    expect(() => filesFilesetsFormat.parse({ ...baseRecord, method: 'MPRA', source_url: null })).not.toThrow()
  })

  it('accepts records with both method and source_url null', () => {
    expect(() => filesFilesetsFormat.parse({ ...baseRecord, method: null, source_url: null })).not.toThrow()
  })
})
