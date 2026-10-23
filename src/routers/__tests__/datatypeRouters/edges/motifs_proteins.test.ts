import { motifsProteinsRouters } from '../../../datatypeRouters/edges/motifs_proteins'
import * as dbModule from '../../../../database'

jest.mock('../../../../database')

describe('motifsProteinsRouters.motifsFromProteins', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns motifs bound to a protein looked up by protein_id', async () => {
    const combinedResult = [
      {
        motif: 'TFDP1_HUMAN_HOCOMOCOv11',
        protein: 'proteins/ENSP00000281043',
        source: 'HOCOMOCOv11',
        name: 'binding modulated by',
        class: 'observed data',
        method: 'HOCOMOCO',
        files_filesets: 'files_filesets/IGVFFI5943XCOS'
      }
    ]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([combinedResult])
    } as any)

    const input = { protein_id: 'ENSP00000281043', page: 0 }
    const result = await motifsProteinsRouters.motifsFromProteins({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(combinedResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('returns motifs bound to a protein looked up by protein_name', async () => {
    const combinedResult = [
      {
        motif: 'TFDP1_HUMAN_HOCOMOCOv11',
        complex: 'complexes/EBI-123456',
        source: 'HOCOMOCOv11',
        name: 'binding modulated by',
        class: 'observed data',
        method: 'HOCOMOCO',
        files_filesets: 'files_filesets/IGVFFI5943XCOS'
      }
    ]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([combinedResult])
    } as any)

    const input = { protein_name: 'TFDP1', page: 0 }
    const result = await motifsProteinsRouters.motifsFromProteins({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(combinedResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('looks up preferred_assay_titles via files_filesets and expands TAP-seq groupings', async () => {
    const combinedResult = [
      {
        motif: 'TFDP1_HUMAN_HOCOMOCOv11',
        protein: 'proteins/ENSP00000281043',
        source: 'HOCOMOCOv11',
        name: 'binding modulated by',
        class: 'observed data',
        method: 'Perturb-seq',
        files_filesets: 'files_filesets/IGVFFI5943XCOS',
        preferred_assay_titles: ['TAP-seq']
      }
    ]

    const query = jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([combinedResult])
    } as any)

    const input = { protein_id: 'ENSP00000281043', page: 0 }
    const result = await motifsProteinsRouters.motifsFromProteins({
      input, ctx: {}, type: 'query', path: '', rawInput: input
    })

    expect(query.mock.calls[0][0]).toContain('DOCUMENT(record.files_filesets).preferred_assay_titles')
    expect(result).toEqual([{ ...combinedResult[0], preferred_assay_titles: ['TAP-seq', 'Perturb-seq'] }])
  })
})

describe('motifsProteinsRouters.proteinsFromMotifs', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns proteins/complexes bound by a motif looked up by tf_name', async () => {
    const combinedResult = [
      {
        motif: 'TFDP1_HUMAN_HOCOMOCOv11',
        source: 'HOCOMOCOv11',
        protein: 'proteins/ENSP00000281043',
        name: 'modulates binding of',
        class: 'observed data',
        method: 'HOCOMOCO',
        files_filesets: 'files_filesets/IGVFFI5943XCOS'
      }
    ]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([combinedResult])
    } as any)

    const input = { tf_name: 'TFDP1', page: 0 }
    const result = await motifsProteinsRouters.proteinsFromMotifs({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(combinedResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('returns an empty array when no motifs/proteins match', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([[]])
    } as any)

    const input = { tf_name: 'UNKNOWN_TF', page: 0 }
    const result = await motifsProteinsRouters.proteinsFromMotifs({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual([])
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })
})
