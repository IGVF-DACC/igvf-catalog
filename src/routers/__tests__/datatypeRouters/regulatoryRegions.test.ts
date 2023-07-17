import { regulatoryRegionRouters } from '../../datatypeRouters/nodes/regulatory_regions'

describe('regulatory region routers', () => {
  test('router is defined and available', () => {
    expect('regulatoryRegions' in regulatoryRegionRouters)
  })

  describe('it implements exact match', () => {
    let router: any
    let openApi: any

    beforeEach(() => {
      router = regulatoryRegionRouters.regulatoryRegions
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

    test('accepts regulatory region query format', () => {
      const regulatoryRegionQuery = {
        region: 'chr1:12345-54321',
        biochemical_activity: 'CA',
        source: 'Encode',
        page: 0
      }

      const inputParsing = router._def.inputs[0].parse(regulatoryRegionQuery)
      expect(inputParsing).toEqual(regulatoryRegionQuery)
    })

    test('returns an array of ontology term in correct format', () => {
      const regulatoryRegions = [{
        chr: 'chr1',
        start: 1157527,
        end: 1158185,
        biochemical_activity: 'ENH',
        biochemical_activity_description: 'Enhancer',
        type: 'candidate_cis_regulatory_element',
        source: 'ENCODE_EpiRaction',
        source_url: 'https://www.encodeproject.org/annotations/ENCSR831INH/'
      }]

      const outputParsing = router._def.output.parse(regulatoryRegions)
      expect(outputParsing).toEqual(regulatoryRegions)
    })

    test('has correct URL', () => {
      expect(openApi?.method).toBe('GET')
      expect(openApi?.path).toBe('/regulatory_regions')
    })

    test('Expects procedure to be a trpc query', () => {
      expect(router._def.query).toBeTruthy()
    })
  })

  describe('it implements exact match with defined type', () => {
    let router: any
    let openApi: any

    beforeEach(() => {
      router = regulatoryRegionRouters.regulatoryRegionsByCandidateCis
      openApi = router._def.meta?.openapi
    })

    test('implements OpenApi protocol', () => {
      expect(typeof openApi).toBe('object')
    })

    test('accepts regulatory region query format', () => {
      const regulatoryRegionByTypeQuery = {
        type: 'candidate_cis_regulatory_element',
        region: 'chr1:12345-54321',
        biochemical_activity: 'CA',
        source: 'Encode',
        page: 0
      }

      const inputParsing = router._def.inputs[0].parse(regulatoryRegionByTypeQuery)
      expect(inputParsing).toEqual(regulatoryRegionByTypeQuery)
    })

    test('outputs a single of regulatory region in correct format', () => {
      const regulatoryRegions = [{
        chr: 'chr1',
        start: 1157527,
        end: 1158185,
        biochemical_activity: 'ENH',
        biochemical_activity_description: 'Enhancer',
        type: 'candidate_cis_regulatory_element',
        source: 'ENCODE_EpiRaction',
        source_url: 'https://www.encodeproject.org/annotations/ENCSR831INH/'
      }]

      const inputParsing = router._def.output.parse(regulatoryRegions)
      expect(inputParsing).toEqual(regulatoryRegions)
    })

    test('has correct URL', () => {
      expect(openApi?.method).toBe('GET')
      expect(openApi?.path).toBe('/regulatory_regions/{type}')
    })

    test('Expects procedure to be a trpc query', () => {
      expect(router._def.query).toBeTruthy()
    })
  })
})
