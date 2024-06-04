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

    test('accepts human variant query format', () => {
      const variantQuery = {
        region: 'chr1:12345-54321',
        rsid: 'rs12345',
        GENCODE_category: 'noncoding',
        organism: 'Homo sapiens',
        page: 0
      }

      const inputParsing = router._def.inputs[0].parse(variantQuery)
      expect(inputParsing).toEqual(variantQuery)
    })

    test('accepts mouse variant query format', () => {
      const variantQuery = {
        region: 'chr1:12345-54321',
        organism: 'Mus musculus',
        mouse_strain: '129S1_SvImJ',
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
          GENCODE_category: 'noncoding'
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
      let inputParsing = router._def.inputs[0].parse({ source: 'bravo_af', region: 'chr12:123-321' })
      expect(inputParsing.page).toEqual(0)

      inputParsing = router._def.inputs[0].parse({ source: 'bravo_af', region: 'chr12:123-321', page: 1 })
      expect(inputParsing.page).toEqual(1)
    })

    test('accepts variant query format', () => {
      const variantFreqQuery = {
        source: 'bravo_af',
        region: 'chr1:12345-54321',
        GENCODE_category: 'noncoding',
        minimum_af: 0.8,
        maximum_af: 1,
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
          GENCODE_category: 'noncoding'
        },
        source: 'FAVOR',
        source_url: 'https://favor.genohub.org/'
      }]

      const outputParsing = router._def.output.parse(variants)
      expect(outputParsing).toEqual(variants)
    })

    test('has correct URL', () => {
      expect(openApi?.method).toBe('GET')
      expect(openApi?.path).toBe('/variants/freq')
    })

    test('Expects procedure to be a trpc query', () => {
      expect(router._def.query).toBeTruthy()
    })
  })
})
