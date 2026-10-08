import { genesGenesEdgeRouters } from '../../../datatypeRouters/edges/genes_genes'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

describe('genesGenesEdgeRouters.genesGenes', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns COXPRESdb coexpression edges for a gene', async () => {
    const mockResult = [
      {
        _id: 'genes_genes/80185_2222_coxpresdb',
        name: 'coexpressed with',
        gene_1: 'genes/ENSG1',
        gene_2: 'genes/ENSG2',
        z_score: 3.2,
        associated_process: 'ontology_terms/GO_0010467',
        source: 'COXPRESdb',
        source_url: 'https://coxpresdb.jp/',
        method: 'COXPRESdb',
        class: 'observed data',
        label: 'co-expression',
        files_filesets: 'files_filesets/FILESET1'
      }
    ]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { gene_id: 'ENSG1', page: 0 }
    const result = await genesGenesEdgeRouters.genesGenes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('returns BioGRID genetic-interaction edges for a gene', async () => {
    const mockResult = [
      {
        _id: 'genes_genes/abcdef123456',
        name: 'interacts with',
        gene_1: 'genes/ENSG1',
        gene_2: 'genes/ENSG3',
        // BioGRID edges have no coexpression z-score field in the DB at all; AQL
        // returns null (not undefined) for a missing field.
        z_score: null,
        detection_method: 'genetic interference',
        detection_method_code: 'MI:0254',
        interaction_type: ['positive genetic interaction (sensu BioGRID)'],
        interaction_type_code: ['MI:2377'],
        confidence_value_biogrid: null,
        confidence_value_intact: null,
        pmids: ['12345'],
        label: 'genetic interference',
        method: 'positive genetic interaction (sensu BioGRID)',
        class: 'observed data',
        source: 'BioGRID',
        source_url: 'https://example.com/biogrid',
        files_filesets: 'files_filesets/FILESET2'
      }
    ]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { gene_id: 'ENSG1', page: 0 }
    const result = await genesGenesEdgeRouters.genesGenes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('throws BAD_REQUEST when no gene identifying property is provided', async () => {
    const input = { page: 0 } as any
    await expect(
      genesGenesEdgeRouters.genesGenes({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })

  it('throws BAD_REQUEST when z_score is not numeric and not a range operator', async () => {
    const input = { gene_id: 'ENSG1', z_score: 'abc', page: 0 }
    await expect(
      genesGenesEdgeRouters.genesGenes({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})
