import { filesFilesetsRouters, filesFilesetsSearch } from '../../datatypeRouters/nodes/files_filesets'
import { db } from '../../../database'
import { appRouter } from '../../_app'

// Mock the database
jest.mock('../../../database', () => ({
  db: {
    query: jest.fn()
  }
}))

// Mock data constants
const mockFilesFileset = {
  _id: 'ENCSR000AAC',
  file_set_id: 'ENCFF000AAC',
  lab: 'roderic-guigo',
  preferred_assay_titles: ['HiC'],
  assay_term_ids: ['OBI:0000716'],
  method: 'candidate Cis-Regulatory Elements',
  class: 'prediction',
  software: ['EPIraction'],
  samples: ['ontology_terms/CL:0000066'],
  sample_ids: ['ENCBS000AAC'],
  simple_sample_summaries: ['HepG2'],
  donors: ['donors/ENCDO000AAC'],
  source: 'ENCODE'
}

describe('files_filesets router', () => {
  const mockQuery = { all: jest.fn() }

  beforeEach(() => {
    jest.clearAllMocks()
    ;(db.query as jest.Mock).mockReturnValue(mockQuery)
  })

  test('router structure', () => {
    const router = filesFilesetsRouters.filesFilesets
    const openApi = router._def.meta?.openapi

    // Basic router structure
    expect('filesFilesets' in filesFilesetsRouters).toBe(true)
    expect(router._def.query).toBeTruthy()
    expect(openApi?.method).toBe('GET')
    expect(openApi?.path).toBe('/files-filesets')
  })

  test('filesFilesetsSearch by ID functionality', async () => {
    mockQuery.all.mockResolvedValue([mockFilesFileset])

    // Test file_fileset_id
    const result = await filesFilesetsSearch({ file_fileset_id: 'ENCSR000AAC', page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining("FILTER record.file_fileset_id == 'ENCSR000AAC'"))
    expect(result).toEqual([mockFilesFileset])

    // Test fileset_id
    jest.clearAllMocks()
    mockQuery.all.mockResolvedValue([mockFilesFileset])
    await filesFilesetsSearch({ fileset_id: 'ENCFF000AAC', page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining("FILTER record.fileset_id == 'ENCFF000AAC'"))
  })

  test('filesFilesetsSearch by various parameters', async () => {
    mockQuery.all.mockResolvedValue([mockFilesFileset])

    // Test lab parameter
    await filesFilesetsSearch({ lab: 'roderic-guigo', page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining("FILTER record.lab == 'roderic-guigo'"))

    // Test preferred_assay_title parameter
    jest.clearAllMocks()
    await filesFilesetsSearch({ preferred_assay_title: 'HiC', page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining("FILTER record.preferred_assay_title == 'HiC'"))

    // Test method parameter
    jest.clearAllMocks()
    await filesFilesetsSearch({ method: 'candidate Cis-Regulatory Elements', page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining("FILTER record.method == 'candidate Cis-Regulatory Elements'"))

    // Test donor_id parameter (should be transformed to donors/)
    jest.clearAllMocks()
    await filesFilesetsSearch({ donors: 'ENCDO000AAC', page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining("FILTER 'donors/ENCDO000AAC' in record.donors"))

    // Test sample_term parameter (should be transformed to ontology_terms/)
    jest.clearAllMocks()
    await filesFilesetsSearch({ samples: 'CL:0000066', page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining("FILTER 'ontology_terms/CL:0000066' in record.samples"))

    // Test software parameter
    jest.clearAllMocks()
    await filesFilesetsSearch({ software: 'EPIraction', page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining("FILTER 'EPIraction' in record.software"))

    // Test source parameter
    jest.clearAllMocks()
    await filesFilesetsSearch({ source: 'ENCODE', page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining("FILTER record.source == 'ENCODE'"))

    // Test class parameter
    jest.clearAllMocks()
    await filesFilesetsSearch({ class: 'prediction', page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining("FILTER record.class == 'prediction'"))
  })

  test('filesFilesetsSearch parameter handling', async () => {
    // Test limit parameter
    mockQuery.all.mockResolvedValue([])
    await filesFilesetsSearch({ lab: 'roderic-guigo', limit: 10, page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 10'))

    // Test limit capping at MAX_PAGE_SIZE (500)
    jest.clearAllMocks()
    mockQuery.all.mockResolvedValue([])
    await filesFilesetsSearch({ lab: 'roderic-guigo', limit: 600, page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 500'))

    // Test page parameter
    jest.clearAllMocks()
    mockQuery.all.mockResolvedValue([])
    await filesFilesetsSearch({ lab: 'roderic-guigo', page: 2, limit: 10 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('LIMIT 20, 10'))

    // Test no filters case
    jest.clearAllMocks()
    mockQuery.all.mockResolvedValue([])
    await filesFilesetsSearch({ page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
  })

  test('filesFilesetsSearch with no parameters', async () => {
    mockQuery.all.mockResolvedValue([mockFilesFileset])
    const result = await filesFilesetsSearch({ page: 0 })
    expect(result).toEqual([mockFilesFileset])
    expect(db.query).not.toHaveBeenCalledWith(expect.stringContaining('FILTER'))
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('SORT record._key'))
  })

  test('tRPC router integration', async () => {
    mockQuery.all.mockResolvedValue([mockFilesFileset])
    const caller = appRouter.createCaller({ requestId: 'test-request-id' })
    const result = await caller.filesFilesets({ lab: 'roderic-guigo' })

    expect(db.query).toHaveBeenCalledWith(expect.stringContaining("FILTER record.lab == 'roderic-guigo'"))
    expect(result).toEqual([mockFilesFileset])
    expect(db.query).toHaveBeenCalledTimes(1)
  })
})
