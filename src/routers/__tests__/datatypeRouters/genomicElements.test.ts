import { genomicRegionsRouters } from '../../datatypeRouters/nodes/genomic_elements'

describe('genomic element routers', () => {
  test('router is defined and available', () => {
    expect('genomicElements' in genomicRegionsRouters)
  })

  describe('it implements exact match', () => {
    let router: any
    let openApi: any

    beforeEach(() => {
      router = genomicRegionsRouters.genomicElements
      openApi = router._def.meta?.openapi
    })

    test('implements OpenApi protocol', () => {
      expect(typeof openApi).toBe('object')
    })

    test('accepts pagination', () => {
      let inputParsing = router._def.inputs[0].parse({ biological_activity: 'CA' })
      expect(inputParsing.page).toEqual(0)

      inputParsing = router._def.inputs[0].parse({ biological_activity: 'CA', page: 1 })
      expect(inputParsing.page).toEqual(1)
    })

    test('accepts genomic element query format', () => {
      const genomicElementQuery = {
        organism: 'Homo sapiens',
        region: 'chr1:12345-54321',
        source_annotation: 'enhancer',
        source: 'ENCODE_MPRA',
        page: 0
      }

      const inputParsing = router._def.inputs[0].parse(genomicElementQuery)
      expect(inputParsing).toEqual(genomicElementQuery)
    })

    test('returns an array of ontology term in correct format', () => {
      const genomicElements = [{
        chr: 'chr1',
        start: 1157527,
        end: 1158185,
        name: 'ABC123',
        source_annotation: 'enhancer',
        type: 'candidate_cis_regulatory_element',
        source: 'ENCODE_EpiRaction',
        source_url: 'https://www.encodeproject.org/annotations/ENCSR831INH/'
      }]

      const outputParsing = router._def.output.parse(genomicElements)
      expect(outputParsing).toEqual(genomicElements)
    })

    test('has correct URL', () => {
      expect(openApi?.method).toBe('GET')
      expect(openApi?.path).toBe('/genomic-elements')
    })

    test('Expects procedure to be a trpc query', () => {
      expect(router._def.query).toBeTruthy()
    })
  })
})
