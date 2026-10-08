import { proteinsProteinsRouters } from '../../../datatypeRouters/edges/proteins_proteins'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

const callProcedure = async (procedure: any, input: Record<string, unknown>): Promise<any> =>
  procedure({ input, ctx: {}, type: 'query', path: '', rawInput: input })

const buildInteractionRecord = (overrides: Record<string, unknown> = {}): Record<string, unknown> => ({
  _id: 'proteins_proteins/ENSP00000340898_ENSP00000341289',
  protein_1: 'proteins/ENSP00000340898',
  protein_2: 'proteins/ENSP00000341289',
  detection_method: 'coimmunoprecipitation',
  detection_method_code: 'MI:0019',
  interaction_type: ['physical association'],
  interaction_type_code: ['MI:0915'],
  confidence_value_biogrid: null,
  confidence_value_intact: 0.56,
  label: 'coimmunoprecipitation',
  class: 'observed data',
  method: 'direct interaction',
  source_url: 'https://data.igvf.org/reference-files/IGVFFI4317VDGK',
  source: 'IntAct',
  organism: 'Homo sapiens',
  pmids: ['http://pubmed.ncbi.nlm.nih.gov/23836931'],
  name: 'physically interacts with',
  files_filesets: 'files_filesets/IGVFFI4317VDGK',
  ...overrides
})

describe('proteinsProteinsRouters.proteinsProteins', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns interactions for a protein filtered by associated protein and source', async () => {
    const mockResult = [buildInteractionRecord()]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = {
      protein_id: 'ENSP00000340898',
      associated_protein_id: 'ENSP00000341289',
      source: 'IntAct',
      detection_method: 'coimmunoprecipitation',
      interaction_type: 'physical association',
      pmid: '23836931',
      page: 0
    }
    const result = await callProcedure(proteinsProteinsRouters.proteinsProteins, input)

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('returns verbose protein_1/protein_2 objects when verbose=true', async () => {
    const mockResult = [buildInteractionRecord({
      protein_1: [{
        _id: 'proteins/ENSP00000340898',
        name: 'GENE1',
        uniprot_names: ['GENE1_HUMAN'],
        uniprot_full_names: ['Gene 1 protein'],
        uniprot_ids: ['P12345'],
        MANE_Select: true,
        organism: 'Homo sapiens',
        source: 'UniProt',
        source_url: 'https://www.uniprot.org/'
      }],
      protein_2: [{
        _id: 'proteins/ENSP00000341289',
        name: 'GENE2',
        uniprot_names: ['GENE2_HUMAN'],
        uniprot_full_names: ['Gene 2 protein'],
        uniprot_ids: ['P54321'],
        MANE_Select: false,
        organism: 'Homo sapiens',
        source: 'UniProt',
        source_url: 'https://www.uniprot.org/'
      }]
    })]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { protein_id: 'ENSP00000340898', verbose: 'true', page: 0 }
    const result = await callProcedure(proteinsProteinsRouters.proteinsProteins, input)

    expect(result).toEqual(mockResult)
  })

  it('returns interactions filtered by files_fileset', async () => {
    const mockResult = [buildInteractionRecord()]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { protein_id: 'ENSP00000340898', files_fileset: 'IGVFFI4317VDGK', page: 0 }
    const result = await callProcedure(proteinsProteinsRouters.proteinsProteins, input)

    expect(result).toEqual(mockResult)
  })

  it('throws BAD_REQUEST when neither a protein nor an associated protein filter is provided', async () => {
    const input = { organism: 'Homo sapiens', page: 0 }
    await expect(callProcedure(proteinsProteinsRouters.proteinsProteins, input)).rejects.toThrow(TRPCError)
  })
})
