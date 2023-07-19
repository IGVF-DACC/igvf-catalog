import { variantsRouters } from '../../datatypeRouters/nodes/variants'

describe('variant routers', () => {
  test('router is defined and available', () => {
    expect('variants' in variantsRouters)
  })

  describe('it implements general query', () => {
    let router: any
    let openApi: any

    beforeEach(() => {
      router = variantsRouters.variants
      openApi = router._def.meta?.openapi
    })

    test('implements OpenApi protocol', () => {
      expect(typeof openApi).toBe('object')
    })

    test('accepts pagination', () => {
      let inputParsing = router._def.inputs[0].parse({ funseq_description: 'noncoding' })
      expect(inputParsing.page).toEqual(0)

      inputParsing = router._def.inputs[0].parse({ funseq_description: 'noncoding', page: 1 })
      expect(inputParsing.page).toEqual(1)
    })

    test('accepts variant query format', () => {
      const variantQuery = {
        region: 'chr1:12345-54321',
        rsid: 'rs12345',
        funseq_description: 'noncoding',
        page: 0
      }

      const inputParsing = router._def.inputs[0].parse(variantQuery)
      expect(inputParsing).toEqual(variantQuery)
    })

    test('returns an array of variants in correct format', () => {
      const variants = [{
        _id: '28f79153e8c2730893ecf970877ae724f63a5c2a80061cd7098729baddb9e415',
        chr: 'chr1',
        pos: 1157527,
        rsid: ['rs1639548796'],
        ref: 'C',
        alt: 'T',
        qual: '.',
        filter: null,
        annotations: {
          freq: {
            gnomad: {
              ref: 0.5,
              alt: 0.5
            }
          },
          funseq_description: 'noncoding'
        },
        source: 'FAVOR',
        source_url: 'https://favor.genohub.org/'
      }]

      const outputParsing = router._def.output.parse(variants)
      expect(outputParsing).toEqual(variants)
    })

    test('has correct URL', () => {
      expect(openApi?.method).toBe('GET')
      expect(openApi?.path).toBe('/variants')
    })

    test('Expects procedure to be a trpc query', () => {
      expect(router._def.query).toBeTruthy()
    })
  })

  describe('it implements exact match by ID', () => {
    let router: any
    let openApi: any

    beforeEach(() => {
      router = variantsRouters.variantID
      openApi = router._def.meta?.openapi
    })

    test('implements OpenApi protocol', () => {
      expect(typeof openApi).toBe('object')
    })

    test('accepts variants by ID format', () => {
      const variantsByIDQuery = {
        id: '28f79153e8c2730893ecf970877ae724f63a5c2a80061cd7098729baddb9e415'
      }

      const inputParsing = router._def.inputs[0].parse(variantsByIDQuery)
      expect(inputParsing).toEqual(variantsByIDQuery)
    })

    test('outputs a single variant in correct format', () => {
      const variant = {
        _id: '28f79153e8c2730893ecf970877ae724f63a5c2a80061cd7098729baddb9e415',
        chr: 'chr1',
        pos: 1157527,
        rsid: ['rs1639548796'],
        ref: 'C',
        alt: 'T',
        qual: '.',
        filter: null,
        annotations: {
          freq: {
            gnomad: {
              ref: 0.5,
              alt: 0.5
            }
          },
          funseq_description: 'noncoding'
        },
        source: 'FAVOR',
        source_url: 'https://favor.genohub.org/'
      }

      const inputParsing = router._def.output.parse(variant)
      expect(inputParsing).toEqual(variant)
    })

    test('has correct URL', () => {
      expect(openApi?.method).toBe('GET')
      expect(openApi?.path).toBe('/variants/{id}')
    })

    test('Expects procedure to be a trpc query', () => {
      expect(router._def.query).toBeTruthy()
    })
  })

  describe('it implements frequency queries', () => {
    let router: any
    let openApi: any

    beforeEach(() => {
      router = variantsRouters.variantByFrequencySource
      openApi = router._def.meta?.openapi
    })

    test('implements OpenApi protocol', () => {
      expect(typeof openApi).toBe('object')
    })

    test('accepts pagination', () => {
      let inputParsing = router._def.inputs[0].parse({ source: 'gnomad', region: 'chr12:123-321' })
      expect(inputParsing.page).toEqual(0)

      inputParsing = router._def.inputs[0].parse({ source: 'gnomad', region: 'chr12:123-321', page: 1 })
      expect(inputParsing.page).toEqual(1)
    })

    test('accepts variant query format', () => {
      const variantFreqQuery = {
        source: '1000genomes',
        region: 'chr1:12345-54321',
        funseq_description: 'noncoding',
        min_alt_freq: 0.8,
        max_alt_freq: 1,
        page: 0
      }

      const inputParsing = router._def.inputs[0].parse(variantFreqQuery)
      expect(inputParsing).toEqual(variantFreqQuery)
    })

    test('returns an array of variants in correct format', () => {
      const variants = [{
        _id: '28f79153e8c2730893ecf970877ae724f63a5c2a80061cd7098729baddb9e415',
        chr: 'chr1',
        pos: 1157527,
        rsid: ['rs1639548796'],
        ref: 'C',
        alt: 'T',
        qual: '.',
        filter: null,
        annotations: {
          freq: {
            gnomad: {
              ref: 0.5,
              alt: 0.5
            }
          },
          funseq_description: 'noncoding'
        },
        source: 'FAVOR',
        source_url: 'https://favor.genohub.org/'
      }]

      const outputParsing = router._def.output.parse(variants)
      expect(outputParsing).toEqual(variants)
    })

    test('has correct URL', () => {
      expect(openApi?.method).toBe('GET')
      expect(openApi?.path).toBe('/variants/freq/{source}')
    })

    test('Expects procedure to be a trpc query', () => {
      expect(router._def.query).toBeTruthy()
    })
  })
})