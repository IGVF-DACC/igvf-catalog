import { ontologyRouters } from '../../datatypeRouters/nodes/ontologies'

describe('ontology routers', () => {
  test('router is defined and available', () => {
    expect('ontologyTerm' in ontologyRouters)
  })

  describe('it implements exact match', () => {
    let router: any
    let openApi: any

    beforeEach(() => {
      router = ontologyRouters.ontologyTerm
      openApi = router._def.meta?.openapi
    })

    test('implements OpenApi protocol', () => {
      expect(typeof openApi).toBe('object')
    })

    test('accepts pagination', () => {
      let inputParsing = router._def.inputs[0].parse({ term_id: 'abc' })
      expect(inputParsing.page).toEqual(0)

      inputParsing = router._def.inputs[0].parse({ term_id: 'abc', page: 1 })
      expect(inputParsing.page).toEqual(1)
    })

    test('accepts ontology query format', () => {
      const ontologyQuery = {
        term_id: 'GO_00001',
        name: 'ontology term',
        source: 'GO',
        subontology: 'biological_process',
        page: 1
      }

      const inputParsing = router._def.inputs[0].parse(ontologyQuery)
      expect(inputParsing).toEqual(ontologyQuery)
    })

    test('returns an array of ontology term in correct format', () => {
      const ontologyTerms = [{
        uri: 'example.org/GO_00001',
        term_id: 'GO_00001',
        name: 'ontology term',
        description: 'this is an ontology term',
        source: 'GO',
        subontology: 'biological_process',
        synonyms: ['toadfishes']
      }]

      const inputParsing = router._def.output.parse(ontologyTerms)
      expect(inputParsing).toEqual(ontologyTerms)
    })

    test('has correct URL', () => {
      expect(openApi?.method).toBe('GET')
      expect(openApi?.path).toBe('/ontology-terms')
    })

    test('Expects procedure to be a trpc query', () => {
      expect(router._def.query).toBeTruthy()
    })
  })
})
