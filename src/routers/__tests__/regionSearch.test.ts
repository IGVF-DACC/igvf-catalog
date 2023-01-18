import { getRegions, regionFormat, regionQueryFormat, regions } from '../regionSearch'
import { z } from 'zod'
import { db } from '../../database'

describe('Region Search Endpoint', () => {
  beforeEach(() => {
    jest.resetModules()
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  describe('OpenAPI', () => {
    const openApi = regions._def.meta?.openapi

    test('implements OpenApi protocol', () => {
      expect(typeof openApi).toBe('object')
    })

    test('has correct URL', () => {
      expect(openApi?.method).toBe('GET')
      expect(openApi?.path).toBe('/regions/{chr}')
    })
  })

  test('Receives as input a regionQueryFormat object', () => {
    expect(regions._def.inputs.length).toBe(1)
    expect(regions._def.inputs[0]).toBe(regionQueryFormat)
  })

  test('Outputs an array of regions', () => {
    const outputFormat = Object(regions._def.output)
    expect(outputFormat._def).toMatchObject(z.array(regionFormat)._def)
  })

  test('Expects procedure to be a trpc query', () => {
    expect(regions._def.query).toBeTruthy()
  })

  describe('getRegions', () => {
    test('queries correct DB collection', async () => {
      const collectionName = 'regulome_chr22'
      const mockCollectionDb = jest.spyOn(db, 'collection')
      await getRegions(69754000, 69754090, '22')
      expect(mockCollectionDb).toHaveBeenCalledWith(collectionName)
    })

    test('queries all regions', async () => {
      const region = {
        _key: '123',
        _id: '321',
        coordinates: {
          gte: 69754001,
          lt: 69754089
        },
        strand: '+',
        value: '1',
        uuid: '12345'
      }

      class DB {
        public all (): any[] {
          return [region]
        }
      }

      const mockPromise = new Promise<any>((resolve) => {
        resolve(new DB())
      })
      const mockQueryDb = jest.spyOn(db, 'query').mockReturnValue(mockPromise)

      const chr = '22'
      const collectionName = 'regulome_chr' + chr
      const gte = 69754000
      const lt = 69754090

      const regions = await getRegions(gte, lt, '22')

      const bindVars = { '@value0': collectionName, value1: gte, value2: lt }

      expect(mockQueryDb).toHaveBeenCalledWith(expect.objectContaining({ bindVars }))
      expect(regions).toMatchObject([region])

      mockQueryDb.mockRestore()
    })
  })
})
