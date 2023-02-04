import { getSnpCorrelations, snpCorrelationFormat, snpCorrelationQueryFormat, snpCorrelations } from '../snpCorrelations'
import { z } from 'zod'
import { db } from '../../database'

describe('Snp Correlation Endpoint', () => {
  beforeEach(() => {
    jest.resetModules()
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  describe('OpenAPI', () => {
    const openApi = snpCorrelations._def.meta?.openapi

    test('implements OpenApi protocol', () => {
      expect(typeof openApi).toBe('object')
    })

    test('has correct URL', () => {
      expect(openApi?.method).toBe('GET')
      expect(openApi?.path).toBe('/snp-correlations/{rsid}')
    })
  })

  test('Receives as input a snpCorrelationQueryFormat object', () => {
    expect(snpCorrelations._def.inputs.length).toBe(1)
    expect(snpCorrelations._def.inputs[0]).toBe(snpCorrelationQueryFormat)
  })

  test('Outputs an array of snpCorrelations', () => {
    const outputFormat = Object(snpCorrelations._def.output)
    expect(outputFormat._def).toMatchObject(z.array(snpCorrelationFormat)._def)
  })

  test('Expects procedure to be a trpc query', () => {
    expect(snpCorrelations._def.query).toBeTruthy()
  })

  describe('getSnpCorrelations', () => {
    test('queries correct DB collection', async () => {
      const collectionName = 'snp_correlations'
      const mockCollectionDb = jest.spyOn(db, 'collection')
      await getSnpCorrelations('12345', 1)
      expect(mockCollectionDb).toHaveBeenCalledWith(collectionName)
    })

    test('queries all correlations', async () => {
      const snpCorr = {
        source: 'snps/10511349',
        target: 'snps/11450751',
        chr: 'chr22',
        ancestry: 'SAS',
        negated: 'True',
        snp_1_base_pair: 'AT:A',
        snp_2_base_pair: 'AT:A',
        r2: 0.248
      }

      class DB {
        public all (): any[] {
          return [snpCorr]
        }
      }

      const mockPromise = new Promise<any>((resolve) => {
        resolve(new DB())
      })
      const mockQueryDb = jest.spyOn(db, 'query').mockReturnValue(mockPromise)

      const collectionName = 'snp_correlations'
      const rsid = '12345'
      const queryPage = 1

      const snpCorrelations = await getSnpCorrelations(rsid, queryPage)

      const bindVars = { '@value0': collectionName, value1: 'snps/' + rsid, value2: queryPage, value3: 100 }

      expect(mockQueryDb).toHaveBeenCalledWith(expect.objectContaining({ bindVars }))
      expect(snpCorrelations).toMatchObject([snpCorr])

      mockQueryDb.mockRestore()
    })

    test('undefined or null page value defaults to page 0', async () => {
      const mockQueryDb = jest.spyOn(db, 'query')

      const collectionName = 'snp_correlations'
      const rsid = '12345'
      const queryPage = 0

      await getSnpCorrelations(rsid, undefined)

      const bindVars = { '@value0': collectionName, value1: 'snps/' + rsid, value2: queryPage, value3: 100 }

      expect(mockQueryDb).toHaveBeenCalledWith(expect.objectContaining({ bindVars }))

      await getSnpCorrelations(rsid, null)

      expect(mockQueryDb).toHaveBeenCalledWith(expect.objectContaining({ bindVars }))
    })
  })
})
