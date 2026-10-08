import { genomicElementsPhenotypesRouters } from '../../../datatypeRouters/edges/genomic_elements_phenotypes'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

const callProcedure = async (procedure: any, input: Record<string, unknown>): Promise<any> =>
  procedure({ input, ctx: {}, type: 'query', path: '', rawInput: input })

const buildEdgeRecord = (overrides: Record<string, unknown> = {}): Record<string, unknown> => ({
  name: 'associated with',
  label: 'regulatory element effect on phenotype',
  method: 'CRISPR screen',
  class: 'observed data',
  source: 'IGVF',
  source_url: 'https://data.igvf.org/tabular-files/IGVFFI5135QZCS/',
  biological_context: 'human HFF-1 cell line',
  biosample_term: 'ontology_terms/CLO_0003730',
  files_filesets: 'files_filesets/IGVFFI5135QZCS',
  crispr_modality: 'interference',
  z_score: 1.5,
  p_value: 0.01,
  neg_log10_pvalue: 2,
  significant: true,
  num_guides: 6,
  num_guides_hit: 4,
  num_guides_nonhit: 2,
  fraction_guides_hit: 0.66,
  phenotype_name: 'cell migration',
  genomic_element: 'genomic_elements/CRISPR_chr1_101174581_101175330_GRCh38_IGVFFI5135QZCS',
  phenotype: 'ontology_terms/GO_0016477',
  ...overrides
})

describe('genomicElementsPhenotypesRouters', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('phenotypesFromGenomicElements', () => {
    it('returns phenotype associations for genomic elements filtered by method', async () => {
      const mockResult = [buildEdgeRecord()]

      jest.spyOn(dbModule.db, 'query').mockResolvedValue({
        all: jest.fn().mockResolvedValue(mockResult)
      } as any)

      const input = { method: 'CRISPR screen', page: 0 }
      const result = await callProcedure(genomicElementsPhenotypesRouters.phenotypesFromGenomicElements, input)

      expect(result).toEqual(mockResult)
      expect(dbModule.db.query).toHaveBeenCalledTimes(1)
    })

    it('resolves a region to genomic element ids before querying edges', async () => {
      const elementIDs = ['genomic_elements/CRISPR_chr1_101174581_101175330_GRCh38_IGVFFI5135QZCS']
      const mockResult = [buildEdgeRecord()]

      jest.spyOn(dbModule.db, 'query')
        .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(elementIDs) } as any)
        .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(mockResult) } as any)

      const input = { region: 'chr1:101174000-101176000', page: 0 }
      const result = await callProcedure(genomicElementsPhenotypesRouters.phenotypesFromGenomicElements, input)

      expect(result).toEqual(mockResult)
      expect(dbModule.db.query).toHaveBeenCalledTimes(2)
    })

    it('resolves phenotype_name to ontology term ids before querying edges', async () => {
      const phenotypeIds = ['ontology_terms/GO_0016477']
      const mockResult = [buildEdgeRecord()]

      jest.spyOn(dbModule.db, 'query')
        .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(phenotypeIds) } as any)
        .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(mockResult) } as any)

      const input = { phenotype_name: 'cell migration', page: 0 }
      const result = await callProcedure(genomicElementsPhenotypesRouters.phenotypesFromGenomicElements, input)

      expect(result).toEqual(mockResult)
      expect(dbModule.db.query).toHaveBeenCalledTimes(2)
    })

    it('returns verbose genomic element and phenotype objects', async () => {
      const mockResult = [buildEdgeRecord({
        genomic_element: {
          _id: 'genomic_elements/CRISPR_chr1_101174581_101175330_GRCh38_IGVFFI5135QZCS',
          type: 'CRISPR element',
          chr: 'chr1',
          start: 101174581,
          end: 101175330,
          name: 'CRISPR_chr1_101174581_101175330_GRCh38_IGVFFI5135QZCS'
        },
        phenotype: {
          phenotype_id: 'ontology_terms/GO_0016477',
          phenotype_name: 'cell migration'
        }
      })]

      jest.spyOn(dbModule.db, 'query').mockResolvedValue({
        all: jest.fn().mockResolvedValue(mockResult)
      } as any)

      const input = { method: 'CRISPR screen', verbose: 'true', page: 0 }
      const result = await callProcedure(genomicElementsPhenotypesRouters.phenotypesFromGenomicElements, input)

      expect(result).toEqual(mockResult)
    })

    it('throws BAD_REQUEST when none of region, files_fileset, phenotype_id, phenotype_name or method are provided', async () => {
      const input = {}
      await expect(callProcedure(genomicElementsPhenotypesRouters.phenotypesFromGenomicElements, input)).rejects.toThrow(TRPCError)
    })
  })

  describe('genomicElementsFromPhenotypes', () => {
    it('returns genomic elements associated with a phenotype_id', async () => {
      const mockResult = [buildEdgeRecord()]

      jest.spyOn(dbModule.db, 'query').mockResolvedValue({
        all: jest.fn().mockResolvedValue(mockResult)
      } as any)

      const input = { phenotype_id: 'GO_0016477', page: 0 }
      const result = await callProcedure(genomicElementsPhenotypesRouters.genomicElementsFromPhenotypes, input)

      expect(result).toEqual(mockResult)
      expect(dbModule.db.query).toHaveBeenCalledTimes(1)
    })

    it('throws BAD_REQUEST when none of phenotype_id, phenotype_name, files_fileset or method are provided', async () => {
      const input = {}
      await expect(callProcedure(genomicElementsPhenotypesRouters.genomicElementsFromPhenotypes, input)).rejects.toThrow(TRPCError)
    })
  })
})
