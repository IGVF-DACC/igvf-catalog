import { genesPathwaysRouters } from '../../../datatypeRouters/edges/genes_pathways'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

describe('genesPathwaysRouters.pathwaysFromGenes', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns pathways for a gene', async () => {
    const geneSearchResult = [
      { _id: 'ENSG1', chr: 'chr1', start: 100, end: 200, gene_type: 'protein_coding', name: 'GENE1', source: 'GENCODE', version: '44', source_url: 'http://x' }
    ]
    const mockResult = [
      {
        gene: 'genes/ENSG1',
        pathway: 'pathways/R-HSA-123',
        name: 'participates in',
        source: 'Reactome',
        source_url: 'https://reactome.org',
        organism: 'Homo sapiens',
        class: 'biological relationship',
        method: null,
        label: null,
        files_filesets: 'files_filesets/FILESET1'
      }
    ]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(geneSearchResult) } as any) // geneSearch
      .mockResolvedValue({ all: jest.fn().mockResolvedValue(mockResult) } as any) // main query

    const input = { gene_id: 'ENSG1', page: 0 }
    const result = await genesPathwaysRouters.pathwaysFromGenes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('throws BAD_REQUEST when no gene identifying property is provided', async () => {
    const input = { page: 0 } as any
    await expect(
      genesPathwaysRouters.pathwaysFromGenes({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('genesPathwaysRouters.genesFromPathways', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns genes for a pathway', async () => {
    const pathwaySearchResult = [
      {
        _id: 'R-HSA-123',
        name: 'Pathway1',
        organism: 'Homo sapiens',
        source: 'Reactome',
        source_url: 'https://reactome.org',
        id_version: '1',
        is_in_disease: false,
        name_aliases: [],
        is_top_level_pathway: false,
        disease_ontology_terms: null,
        biological_process: null,
        class: 'biological relationship',
        method: null,
        label: null,
        files_filesets: 'files_filesets/FILESET1'
      }
    ]
    const mockResult = [
      {
        gene: 'genes/ENSG1',
        pathway: 'pathways/R-HSA-123',
        name: 'has participant',
        source: 'Reactome',
        source_url: 'https://reactome.org',
        organism: 'Homo sapiens',
        class: 'biological relationship',
        method: null,
        label: null,
        files_filesets: 'files_filesets/FILESET1'
      }
    ]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(pathwaySearchResult) } as any) // pathwaySearchPersistent
      .mockResolvedValue({ all: jest.fn().mockResolvedValue(mockResult) } as any) // main query

    const input = { pathway_id: 'R-HSA-123', page: 0 }
    const result = await genesPathwaysRouters.genesFromPathways({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('throws BAD_REQUEST when no pathway identifying property is provided', async () => {
    const input = { page: 0 } as any
    await expect(
      genesPathwaysRouters.genesFromPathways({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})
