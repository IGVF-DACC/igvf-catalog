import { variantsPhenotypesRouters } from '../../../datatypeRouters/edges/variants_phenotypes'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

const callProcedure = async (procedure: any, input: Record<string, unknown>): Promise<any> =>
  procedure({ input, ctx: {}, type: 'query', path: '', rawInput: input })

describe('variantsPhenotypesRouters', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('phenotypesFromVariants', () => {
    it('returns GWAS phenotype associations for a variant filtered by method', async () => {
      const mockResult = [{
        variant: 'variants/NC_000001.11:10000:T:A',
        phenotype_id: 'ontology_terms/EFO_0004339',
        name: 'associated with',
        source: 'OpenTargets',
        source_url: 'https://genetics.opentargets.org',
        class: 'observed data',
        method: 'GWAS',
        label: 'GWAS',
        study: 'studies/GCST90002357',
        version: 'October 2022 (22.10)',
        lead_chrom: '1',
        lead_pos: 10000,
        lead_ref: 'A',
        lead_alt: 'G',
        direction: '+',
        beta: 0.01,
        beta_ci_lower: 0.005,
        beta_ci_upper: 0.015,
        p_value: 0.001,
        neg_log10_pvalue: 3,
        oddsr_ci_lower: null,
        oddsr_ci_upper: null,
        phenotype_term: 'body height'
      }]

      jest.spyOn(dbModule.db, 'query').mockResolvedValue({
        all: jest.fn().mockResolvedValue(mockResult)
      } as any)

      const input = { method: 'GWAS', page: 0 }
      const result = await callProcedure(variantsPhenotypesRouters.phenotypesFromVariants, input)

      expect(result).toEqual(mockResult)
      expect(dbModule.db.query).toHaveBeenCalledTimes(1)
    })

    it('returns CRISPR screen phenotype associations for a variant', async () => {
      const mockResult = [{
        variant: 'variants/NC_000001.11:25253603:G:A',
        phenotype_id: 'ontology_terms/NTR_0001118',
        name: 'associated with',
        source: 'IGVF',
        source_url: 'https://data.igvf.org/tabular-files/IGVFFI2014OOZP/',
        class: 'observed data',
        method: 'CRISPR screen',
        label: 'variant effect on phenotype',
        crispr_modality: 'prime editing',
        biological_context: 'human HCT116 cell line',
        biosample_term: 'ontology_terms/EFO_0002824',
        files_filesets: 'files_filesets/IGVFFI2014OOZP',
        effect_size: 0.3,
        z_score: 1.2,
        significant: true,
        num_guides: 4,
        edit_rate_mean: 0.6,
        effect_size_ci95_lower: 0.1,
        effect_size_ci95_upper: 0.5,
        p_value_adj: 0.01,
        neg_log10_pvalue_adj: 2,
        phenotype_term: 'cell migration'
      }]

      jest.spyOn(dbModule.db, 'query').mockResolvedValue({
        all: jest.fn().mockResolvedValue(mockResult)
      } as any)

      const input = { method: 'CRISPR screen', page: 0 }
      const result = await callProcedure(variantsPhenotypesRouters.phenotypesFromVariants, input)

      expect(result).toEqual(mockResult)
    })

    it('throws BAD_REQUEST when no variant-identifying property, method, or files_fileset is provided', async () => {
      const input = {}
      await expect(callProcedure(variantsPhenotypesRouters.phenotypesFromVariants, input)).rejects.toThrow(TRPCError)
    })

    it('throws BAD_REQUEST when neg_log10_pvalue is not numeric and not a range query', async () => {
      const input = { method: 'GWAS', neg_log10_pvalue: 'not-a-number', page: 0 }
      await expect(callProcedure(variantsPhenotypesRouters.phenotypesFromVariants, input)).rejects.toThrow(TRPCError)
    })

    // Known real-world data issue: some GWAS-sourced variants_phenotypes edges reference a
    // variant (_from) that no longer exists in the variants collection. In verbose mode the
    // router expands _from via DOCUMENT(record._from) with no null-check, so ArangoDB returns
    // a variant object whose fields are all null. That fails the variant zod schema during
    // output validation, which trpc surfaces as a 500 (INTERNAL_SERVER_ERROR). This test
    // documents that CURRENT behavior; it is intentionally not fixed here (a data-layer fix,
    // not an API-layer null-check, is the agreed remediation).
    it('surfaces an INTERNAL_SERVER_ERROR when a GWAS edge references a dangling variant in verbose mode', async () => {
      const mockResult = [{
        variant: { _id: null, chr: null, pos: null, alt: null, ref: null, rsid: null, spdi: null, hgvs: null, ca_id: null },
        phenotype_id: 'ontology_terms/EFO_0004339',
        name: 'associated with',
        source: 'OpenTargets',
        source_url: 'https://genetics.opentargets.org',
        class: 'observed data',
        method: 'GWAS',
        label: 'GWAS',
        study: 'studies/GCST90002357',
        version: 'October 2022 (22.10)',
        lead_chrom: '1',
        lead_pos: 10000,
        lead_ref: 'A',
        lead_alt: 'G',
        direction: '+',
        beta: 0.01,
        beta_ci_lower: 0.005,
        beta_ci_upper: 0.015,
        p_value: 0.001,
        neg_log10_pvalue: 3,
        oddsr_ci_lower: null,
        oddsr_ci_upper: null,
        phenotype_term: 'body height'
      }]

      jest.spyOn(dbModule.db, 'query').mockResolvedValue({
        all: jest.fn().mockResolvedValue(mockResult)
      } as any)

      const input = { method: 'GWAS', verbose: 'true', page: 0 }
      const call = callProcedure(variantsPhenotypesRouters.phenotypesFromVariants, input)

      await expect(call).rejects.toThrow(TRPCError)
      await expect(call.catch((error: TRPCError) => error.code)).resolves.toBe('INTERNAL_SERVER_ERROR')
    })
  })

  describe('variantsFromPhenotypes', () => {
    it('returns variants for a phenotype_id without an extra ontology lookup', async () => {
      const mockResult = [{
        rsid: ['rs123'],
        phenotype_id: 'ontology_terms/EFO_0004339',
        phenotype_term: 'body height',
        study: 'studies/GCST90002357',
        neg_log10_pvalue: 3,
        p_value: 0.001,
        beta: 0.01,
        beta_ci_lower: 0.005,
        beta_ci_upper: 0.015,
        oddsr_ci_lower: null,
        oddsr_ci_upper: null,
        lead_chrom: '1',
        lead_pos: 10000,
        lead_ref: 'A',
        lead_alt: 'G',
        direction: '+',
        source: 'OpenTargets',
        source_url: 'https://genetics.opentargets.org',
        class: 'observed data',
        method: 'GWAS',
        label: 'GWAS',
        version: 'October 2022 (22.10)',
        name: 'associated with',
        variant: 'variants/NC_000001.11:10000:T:A',
        files_filesets: null
      }]

      jest.spyOn(dbModule.db, 'query').mockResolvedValue({
        all: jest.fn().mockResolvedValue(mockResult)
      } as any)

      const input = { phenotype_id: 'EFO_0004339', page: 0 }
      const result = await callProcedure(variantsPhenotypesRouters.variantsFromPhenotypes, input)

      expect(result).toEqual(mockResult)
      expect(dbModule.db.query).toHaveBeenCalledTimes(1)
    })

    it('resolves phenotype_name to ontology term ids before querying variants', async () => {
      const phenotypeIds = ['ontology_terms/EFO_0004339']
      const mockResult = [{
        rsid: null,
        phenotype_id: 'ontology_terms/EFO_0004339',
        phenotype_term: 'body height',
        study: 'studies/GCST90002357',
        neg_log10_pvalue: 3,
        p_value: 0.001,
        beta: 0.01,
        beta_ci_lower: 0.005,
        beta_ci_upper: 0.015,
        oddsr_ci_lower: null,
        oddsr_ci_upper: null,
        lead_chrom: '1',
        lead_pos: 10000,
        lead_ref: 'A',
        lead_alt: 'G',
        direction: '+',
        source: 'OpenTargets',
        source_url: 'https://genetics.opentargets.org',
        class: 'observed data',
        method: 'GWAS',
        label: 'GWAS',
        version: 'October 2022 (22.10)',
        name: 'associated with',
        variant: 'variants/NC_000001.11:10000:T:A',
        files_filesets: null
      }]

      jest.spyOn(dbModule.db, 'query')
        .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(phenotypeIds) } as any)
        .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(mockResult) } as any)

      const input = { phenotype_name: 'body height', page: 0 }
      const result = await callProcedure(variantsPhenotypesRouters.variantsFromPhenotypes, input)

      expect(result).toEqual(mockResult)
      expect(dbModule.db.query).toHaveBeenCalledTimes(2)
    })

    it('throws BAD_REQUEST when no phenotype-identifying property, method, or files_fileset is provided', async () => {
      const input = {}
      await expect(callProcedure(variantsPhenotypesRouters.variantsFromPhenotypes, input)).rejects.toThrow(TRPCError)
    })

    it('throws BAD_REQUEST when neg_log10_pvalue is not numeric and not a range query', async () => {
      const input = { phenotype_id: 'EFO_0004339', neg_log10_pvalue: 'nope', page: 0 }
      await expect(callProcedure(variantsPhenotypesRouters.variantsFromPhenotypes, input)).rejects.toThrow(TRPCError)
    })
  })
})
