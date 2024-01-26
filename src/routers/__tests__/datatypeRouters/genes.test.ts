import { genesRouters } from '../../datatypeRouters/nodes/genes'

describe('genes routers', () => {
  test('router is defined and available', () => {
    expect('genes' in genesRouters)
  })

  describe('it implements general query', () => {
    let router: any
    let openApi: any

    beforeEach(() => {
      router = genesRouters.genes
      openApi = router._def.meta?.openapi
    })

    test('implements OpenApi protocol', () => {
      expect(typeof openApi).toBe('object')
    })

    test('accepts pagination', () => {
      let inputParsing = router._def.inputs[0].parse({ gene_type: 'miRNA' })
      expect(inputParsing.page).toEqual(0)

      inputParsing = router._def.inputs[0].parse({ gene_type: 'miRNA', page: 1 })
      expect(inputParsing.page).toEqual(1)
    })

    test('accepts gene query format', () => {
      const geneQuery = {
        organism: 'human',
        region: 'chr1:12345-54321',
        gene_type: 'miRNA',
        page: 0
      }

      const inputParsing = router._def.inputs[0].parse(geneQuery)
      expect(inputParsing).toEqual(geneQuery)
    })

    test('returns an array of genes in correct format', () => {
      const genes = [{
        _id: 'ENSG00000207644',
        gene_type: 'miRNA',
        chr: 'chr19',
        start: 53669156,
        end: 53669254,
        gene_name: 'MIR512-2',
        source: 'GENCODE',
        version: 'v43',
        source_url: 'https://www.gencodegenes.org/human/'
      }]

      const outputParsing = router._def.output.parse(genes)
      expect(outputParsing).toEqual(genes)
    })

    test('has correct URL', () => {
      expect(openApi?.method).toBe('GET')
      expect(openApi?.path).toBe('/genes')
    })

    test('Expects procedure to be a trpc query', () => {
      expect(router._def.query).toBeTruthy()
    })
  })
})
