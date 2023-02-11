import { eqtls, eqtlsQueryFormat, eqtlsFormat, getQtls } from '../eqtls'
import { z } from 'zod'
import { db } from '../../database'
import { TRPCError } from '@trpc/server'

describe('QTL Endpoint', () => {
  beforeEach(() => {
    jest.resetModules()
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  describe('OpenAPI', () => {
    const openApi = eqtls._def.meta?.openapi

    test('implements OpenApi protocol', () => {
      expect(typeof openApi).toBe('object')
    })

    test('has correct URL', () => {
      expect(openApi?.method).toBe('GET')
      expect(openApi?.path).toBe('/eqtls')
    })
  })

  test('Receives as input a eqtlsQueryFormat object', () => {
    expect(eqtls._def.inputs.length).toBe(1)
    expect(eqtls._def.inputs[0]).toBe(eqtlsQueryFormat)
  })

  test('Outputs an array of eqtls', () => {
    const outputFormat = Object(eqtls._def.output)
    expect(outputFormat._def).toMatchObject(z.array(eqtlsFormat)._def)
  })

  test('Expects procedure to be a trpc query', () => {
    expect(eqtls._def.query).toBeTruthy()
  })

  describe('getQtls', () => {
    test('queries correct DB collection and return eqtls', async () => {
      class DB {
        public all (): any[] {
          return ['eqtl']
        }
      }

      const mockPromise = new Promise<any>((resolve) => {
        resolve(new DB())
      })
      const mockQuery = jest.spyOn(db, 'query').mockReturnValue(mockPromise)

      const eqtls = await getQtls('gene_12345', 'brain', 0.5, 0.1, 1)
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('IN variant_gene_links'))
      expect(eqtls).toEqual(['eqtl'])
    })

    test('returns 400 if neither gene id nor biological context are provided', async () => {
      try {
        await getQtls(null, null, 0.5, 0.1, 1)
      } catch (e) {
        const message = (e as TRPCError).message
        expect(message).toBe('Either a gene ID or a biological context must be provided.')
        return
      }
      fail('Either gene ID or biological context must be provided.')
    })

    test('filters by gene ID, biological context, pvalue, and beta', async () => {
      class DB {
        public all (): any[] {
          return ['eqtl']
        }
      }

      const mockPromise = new Promise<any>((resolve) => {
        resolve(new DB())
      })
      const mockQuery = jest.spyOn(db, 'query').mockReturnValue(mockPromise)

      await getQtls('gene_12345', 'brain', 0.5, 0.1, 1)
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("link._to == 'genes/gene_12345'"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("link.biological_context == 'brain'"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("link['p-value:long'] <= 0.5"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("link['beta:long'] <= 0.1"))
    })

    test('paginates with default page size of 25 and deafults to page 0', async () => {
      class DB {
        public all (): any[] {
          return ['eqtl']
        }
      }

      const mockPromise = new Promise<any>((resolve) => {
        resolve(new DB())
      })
      const mockQuery = jest.spyOn(db, 'query').mockReturnValue(mockPromise)

      await getQtls('gene_12345', 'brain', 0.5, 0.1, 3)
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 3, 25'))

      await getQtls('gene_12345', 'brain', 0.5, 0.1, null)
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
    })
  })
})
