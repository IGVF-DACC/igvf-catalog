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
        full_name: 'BTB/POZ domain-containing protein 3',
        source: 'UniProt',
        dbxrefs: [
          {
            name: 'BindingDB',
            id: 'Q04917'
          }
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
})
