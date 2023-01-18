import { getSnpCorrelations, snpCorrelationFormat, snpCorrelationQueryFormat, snpCorrelations } from '../routers/snpCorrelations'
import { z } from 'zod'
import { db } from '../database'

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
      expect(openApi?.path).toBe('/snp-correlations/{chr}')
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
      const collectionName = 'topld'
      const mockCollectionDb = jest.spyOn(db, 'collection')
      await getSnpCorrelations('22', 0.8, 1)
      expect(mockCollectionDb).toHaveBeenCalledWith(collectionName)
    })

    test('queries all correlations', async () => {
      const snpCorr = {
        _key: '123',
        _id: '321',
        _from: '432',
        _to: '234',
        _rev: 'abc',
        Uniq_ID_1: 'snp1',
        Uniq_ID_2: 'snp2',
        R2: 0.8,
        Dprime: 1,
        '+/-corr': 1,
        chrom: 22
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

      const collectionName = 'topld'
      const chr = '22'
      const queryPage = 1
      const r = 0.8

      const snpCorrelations = await getSnpCorrelations(chr, r, queryPage)

      const bindVars = { '@value0': collectionName, value1: r, value2: parseInt(chr), value3: queryPage, value4: 100 }

      expect(mockQueryDb).toHaveBeenCalledWith(expect.objectContaining({ bindVars }))
      expect(snpCorrelations).toMatchObject([snpCorr])
      mockQueryDb.mockRestore()
    })

    test('undefined or null page value defaults to page 0', async () => {
      const mockQueryDb = jest.spyOn(db, 'query')

      const collectionName = 'topld'
      const chr = '22'
      const queryPage = 0
      const r = 0.8

      await getSnpCorrelations(chr, r, undefined)

      const bindVars = { '@value0': collectionName, value1: r, value2: parseInt(chr), value3: queryPage, value4: 100 }

      expect(mockQueryDb).toHaveBeenCalledWith(expect.objectContaining({ bindVars }))

      await getSnpCorrelations(chr, r, null)

      expect(mockQueryDb).toHaveBeenCalledWith(expect.objectContaining({ bindVars }))
    })
  })
})
