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
        term_name: 'ontology term',
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
        term_name: 'ontology term',
        description: 'this is an ontology term',
        source: 'GO',
        subontology: 'biological_process'
      }]

      const inputParsing = router._def.output.parse(ontologyTerms)
      expect(inputParsing).toEqual(ontologyTerms)
    })

    test('has correct URL', () => {
      expect(openApi?.method).toBe('GET')
      expect(openApi?.path).toBe('/ontology_terms')
    })

    test('Expects procedure to be a trpc query', () => {
      expect(router._def.query).toBeTruthy()
    })
  })

  describe('it implements exact match by ID', () => {
    let router: any
    let openApi: any

    beforeEach(() => {
      router = ontologyRouters.ontologyTermID
      openApi = router._def.meta?.openapi
    })

    test('implements OpenApi protocol', () => {
      expect(typeof openApi).toBe('object')
    })

    test('accepts ontology query format', () => {
      const ontologyIDQuery = {
        id: 'GO_00001'
      }

      const inputParsing = router._def.inputs[0].parse(ontologyIDQuery)
      expect(inputParsing).toEqual(ontologyIDQuery)
    })

    test('outputs a single of ontology term in correct format', () => {
      const ontologyTerm = {
        uri: 'example.org/GO_00001',
        term_id: 'GO_00001',
        term_name: 'ontology term',
        description: 'this is an ontology term',
        source: 'GO',
        subontology: 'biological_process'
      }

      const inputParsing = router._def.output.parse(ontologyTerm)
      expect(inputParsing).toEqual(ontologyTerm)
    })

    test('has correct URL', () => {
      expect(openApi?.method).toBe('GET')
      expect(openApi?.path).toBe('/ontology_terms/{id}')
    })

    test('Expects procedure to be a trpc query', () => {
      expect(router._def.query).toBeTruthy()
    })
  })

  describe('it implements fuzzy text search by term name', () => {
    let router: any
    let openApi: any

    beforeEach(() => {
      router = ontologyRouters.ontologyTermSearch
      openApi = router._def.meta?.openapi
    })

    test('implements OpenApi protocol', () => {
      expect(typeof openApi).toBe('object')
    })

    test('accepts pagination', () => {
      let inputParsing = router._def.inputs[0].parse({ term: 'abc' })
      expect(inputParsing.page).toEqual(0)

      inputParsing = router._def.inputs[0].parse({ term: 'abc', page: 1 })
      expect(inputParsing.page).toEqual(1)
    })

    test('accepts ontology query format', () => {
      const ontologyQuery = {
        term: 'brain',
        page: 1
      }

      const inputParsing = router._def.inputs[0].parse(ontologyQuery)
      expect(inputParsing).toEqual(ontologyQuery)
    })

    test('returns an array of ontology term in correct format', () => {
      const ontologyTerms = [{
        uri: 'example.org/GO_00001',
        term_id: 'GO_00001',
        term_name: 'ontology term',
        description: 'this is an ontology term',
        source: 'GO',
        subontology: 'biological_process'
      }]

      const inputParsing = router._def.output.parse(ontologyTerms)
      expect(inputParsing).toEqual(ontologyTerms)
    })

    test('has correct URL', () => {
      expect(openApi?.method).toBe('GET')
      expect(openApi?.path).toBe('/ontology_terms/search/{term}')
    })

    test('Expects procedure to be a trpc query', () => {
      expect(router._def.query).toBeTruthy()
    })
  })

  describe('aliases', () => {
    describe('it implements an exact match in GO - biological processes', () => {
      let router: any
      let openApi: any

      beforeEach(() => {
        router = ontologyRouters.ontologyGoTermBP
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
        const subontologyQuery = {
          term_id: 'GO_00001',
          term_name: 'ontology term',
          page: 1
        }

        const inputParsing = router._def.inputs[0].parse(subontologyQuery)
        expect(inputParsing).toEqual(subontologyQuery)
      })

      test('returns an array of ontology term in correct format', () => {
        const ontologyTerms = [{
          uri: 'example.org/GO_00001',
          term_id: 'GO_00001',
          term_name: 'ontology term',
          description: 'this is an ontology term',
          source: 'GO',
          subontology: 'biological_process'
        }]

        const inputParsing = router._def.output.parse(ontologyTerms)
        expect(inputParsing).toEqual(ontologyTerms)
      })

      test('has correct URL', () => {
        expect(openApi?.method).toBe('GET')
        expect(openApi?.path).toBe('/go-bp-terms')
      })

      test('Expects procedure to be a trpc query', () => {
        expect(router._def.query).toBeTruthy()
      })
    })

    describe('it implements an exact match in GO - molecular function', () => {
      let router: any
      let openApi: any

      beforeEach(() => {
        router = ontologyRouters.ontologyGoTermMF
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
        const subontologyQuery = {
          term_id: 'GO_00001',
          term_name: 'ontology term',
          page: 1
        }

        const inputParsing = router._def.inputs[0].parse(subontologyQuery)
        expect(inputParsing).toEqual(subontologyQuery)
      })

      test('returns an array of ontology term in correct format', () => {
        const ontologyTerms = [{
          uri: 'example.org/GO_00001',
          term_id: 'GO_00001',
          term_name: 'ontology term',
          description: 'this is an ontology term',
          source: 'GO',
          subontology: 'molecular_function'
        }]

        const inputParsing = router._def.output.parse(ontologyTerms)
        expect(inputParsing).toEqual(ontologyTerms)
      })

      test('has correct URL', () => {
        expect(openApi?.method).toBe('GET')
        expect(openApi?.path).toBe('/go-mf-terms')
      })

      test('Expects procedure to be a trpc query', () => {
        expect(router._def.query).toBeTruthy()
      })
    })

    describe('it implements an exact match in GO - molecular function', () => {
      let router: any
      let openApi: any

      beforeEach(() => {
        router = ontologyRouters.ontologyGoTermCC
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
        const subontologyQuery = {
          term_id: 'GO_00001',
          term_name: 'ontology term',
          page: 1
        }

        const inputParsing = router._def.inputs[0].parse(subontologyQuery)
        expect(inputParsing).toEqual(subontologyQuery)
      })

      test('returns an array of ontology term in correct format', () => {
        const ontologyTerms = [{
          uri: 'example.org/GO_00001',
          term_id: 'GO_00001',
          term_name: 'ontology term',
          description: 'this is an ontology term',
          source: 'GO',
          subontology: 'cellular_component'
        }]

        const inputParsing = router._def.output.parse(ontologyTerms)
        expect(inputParsing).toEqual(ontologyTerms)
      })

      test('has correct URL', () => {
        expect(openApi?.method).toBe('GET')
        expect(openApi?.path).toBe('/go-cc-terms')
      })

      test('Expects procedure to be a trpc query', () => {
        expect(router._def.query).toBeTruthy()
      })
    })
  })
})
