import { proteinsRouters } from '../../datatypeRouters/nodes/proteins'

describe('proteins routers', () => {
  test('router is defined and available', () => {
    expect('transcripts' in proteinsRouters)
  })

  describe('it implements general query', () => {
    let router: any
    let openApi: any

    beforeEach(() => {
      router = proteinsRouters.proteins
      openApi = router._def.meta?.openapi
    })

    test('implements OpenApi protocol', () => {
      expect(typeof openApi).toBe('object')
    })

    test('accepts pagination', () => {
      let inputParsing = router._def.inputs[0].parse({ name: 'BTBD3_HUMAN' })
      expect(inputParsing.page).toEqual(0)

      inputParsing = router._def.inputs[0].parse({ gene_type: 'BTBD3_HUMAN', page: 1 })
      expect(inputParsing.page).toEqual(1)
    })

    test('accepts protein query format', () => {
      const proteinQuery = {
        name: 'BTBD3_HUMAN',
        page: 0
      }

      const inputParsing = router._def.inputs[0].parse(proteinQuery)
      expect(inputParsing).toEqual(proteinQuery)
    })

    test('returns an array of transcripts in correct format', () => {
      const proteins = [{
        _id: 'Q9Y2F9',
        name: 'BTBD3_HUMAN',
        source: 'UniProt',
        dbxrefs: [
          'BindingDB:Q04917'
        ],
        source_url: 'https://www.uniprot.org/help/downloads'
      }]

      const outputParsing = router._def.output.parse(proteins)
      expect(outputParsing).toEqual(proteins)
    })

    test('has correct URL', () => {
      expect(openApi?.method).toBe('GET')
      expect(openApi?.path).toBe('/proteins')
    })

    test('Expects procedure to be a trpc query', () => {
      expect(router._def.query).toBeTruthy()
    })
  })

  describe('it implements exact match by ID', () => {
    let router: any
    let openApi: any

    beforeEach(() => {
      router = proteinsRouters.proteinID
      openApi = router._def.meta?.openapi
    })

    test('implements OpenApi protocol', () => {
      expect(typeof openApi).toBe('object')
    })

    test('accepts protein by ID format', () => {
      const proteinByIDQuery = {
        id: 'Q9Y2F9'
      }

      const inputParsing = router._def.inputs[0].parse(proteinByIDQuery)
      expect(inputParsing).toEqual(proteinByIDQuery)
    })

    test('outputs a single protein in correct format', () => {
      const protein = {
        _id: 'Q9Y2F9',
        name: 'BTBD3_HUMAN',
        source: 'UniProt',
        dbxrefs: [
          'BindingDB:Q04917'
        ],
        source_url: 'https://www.uniprot.org/help/downloads'
      }

      const inputParsing = router._def.output.parse(protein)
      expect(inputParsing).toEqual(protein)
    })

    test('has correct URL', () => {
      expect(openApi?.method).toBe('GET')
      expect(openApi?.path).toBe('/proteins/{id}')
    })

    test('Expects procedure to be a trpc query', () => {
      expect(router._def.query).toBeTruthy()
    })
  })
})
