import { complexesProteinsRouters } from '../../../datatypeRouters/edges/complexes_proteins'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

const callProcedure = async (procedure: any, input: Record<string, unknown>): Promise<any> =>
  procedure({ input, ctx: {}, type: 'query', path: '', rawInput: input })

const buildComplexProteinRecord = (overrides: Record<string, unknown> = {}): Record<string, unknown> => ({
  protein: 'proteins/ENSP00000372925',
  complex: 'complexes/CPX-2428',
  name: 'contains',
  stoichiometry: 1,
  chain_id: null,
  isoform_id: null,
  number_of_paralogs: null,
  linked_features: null,
  class: 'biological relationship',
  method: null,
  label: null,
  files_filesets: null,
  source: 'EBI',
  source_url: 'https://www.ebi.ac.uk/complexportal/',
  ...overrides
})

describe('complexesProteinsRouters', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('proteinsFromComplexes', () => {
    it('returns proteins for a complex looked up by complex_id', async () => {
      const mockResult = [buildComplexProteinRecord()]

      jest.spyOn(dbModule.db, 'query').mockResolvedValue({
        all: jest.fn().mockResolvedValue(mockResult)
      } as any)

      const input = { complex_id: 'CPX-2428', page: 0 }
      const result = await callProcedure(complexesProteinsRouters.proteinsFromComplexes, input)

      expect(result).toEqual(mockResult)
      expect(dbModule.db.query).toHaveBeenCalledTimes(1)
    })

    it('resolves complex_name via complexSearch before querying proteins', async () => {
      const complexSearchResult = [{ _id: 'CPX-2428', name: 'BRCA1-BARD1 complex' }]
      const mockResult = [buildComplexProteinRecord()]

      jest.spyOn(dbModule.db, 'query')
        .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(complexSearchResult) } as any)
        .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(mockResult) } as any)

      const input = { complex_name: 'BRCA1-BARD1 complex', page: 0 }
      const result = await callProcedure(complexesProteinsRouters.proteinsFromComplexes, input)

      expect(result).toEqual(mockResult)
      expect(dbModule.db.query).toHaveBeenCalledTimes(2)
    })

    it('returns verbose protein and complex objects when verbose=true', async () => {
      const mockResult = [buildComplexProteinRecord({
        protein: {
          _id: 'proteins/ENSP00000372925',
          name: 'BRCA1',
          uniprot_names: ['BRCA1_HUMAN'],
          uniprot_full_names: ['Breast cancer type 1 susceptibility protein'],
          uniprot_ids: ['P38398'],
          dbxrefs: [{ name: 'HGNC', id: 'HGNC:1100' }],
          MANE_Select: true,
          organism: 'Homo sapiens',
          source: 'UniProt',
          source_url: 'https://www.uniprot.org/'
        },
        complex: {
          _id: 'complexes/CPX-2428',
          name: 'BRCA1-BARD1 complex',
          alias: null,
          molecules: null,
          evidence_code: null,
          experimental_evidence: null,
          description: 'A complex of BRCA1 and BARD1',
          complex_assembly: null,
          complex_source: null,
          reactome_xref: null,
          class: 'biological relationship',
          method: null,
          label: null,
          files_filesets: null,
          source: 'EBI',
          source_url: 'https://www.ebi.ac.uk/complexportal/'
        }
      })]

      jest.spyOn(dbModule.db, 'query').mockResolvedValue({
        all: jest.fn().mockResolvedValue(mockResult)
      } as any)

      const input = { complex_id: 'CPX-2428', verbose: 'true', page: 0 }
      const result = await callProcedure(complexesProteinsRouters.proteinsFromComplexes, input)

      expect(result).toEqual(mockResult)
    })

    it('throws BAD_REQUEST when no complex_id, name or description is provided', async () => {
      const input = {}
      await expect(callProcedure(complexesProteinsRouters.proteinsFromComplexes, input)).rejects.toThrow(TRPCError)
    })
  })

  describe('complexesFromProteins', () => {
    it('returns complexes for a protein looked up by protein_id', async () => {
      const mockResult = [buildComplexProteinRecord({ name: 'belongs to' })]

      jest.spyOn(dbModule.db, 'query').mockResolvedValue({
        all: jest.fn().mockResolvedValue(mockResult)
      } as any)

      const input = { protein_id: 'ENSP00000372925', page: 0 }
      const result = await callProcedure(complexesProteinsRouters.complexesFromProteins, input)

      expect(result).toEqual(mockResult)
      expect(dbModule.db.query).toHaveBeenCalledTimes(1)
    })

    it('returns complexes for a protein looked up by protein_name', async () => {
      const mockResult = [buildComplexProteinRecord({ name: 'belongs to' })]

      jest.spyOn(dbModule.db, 'query').mockResolvedValue({
        all: jest.fn().mockResolvedValue(mockResult)
      } as any)

      const input = { protein_name: 'BRCA1', page: 0 }
      const result = await callProcedure(complexesProteinsRouters.complexesFromProteins, input)

      expect(result).toEqual(mockResult)
      expect(dbModule.db.query).toHaveBeenCalledTimes(1)
    })

    it('throws BAD_REQUEST when no protein_id, name or uniprot identifiers are provided', async () => {
      const input = {}
      await expect(callProcedure(complexesProteinsRouters.complexesFromProteins, input)).rejects.toThrow(TRPCError)
    })
  })
})
