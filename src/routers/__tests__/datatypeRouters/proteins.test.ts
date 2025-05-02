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
      let inputParsing = router._def.inputs[0].parse({ protein_name: 'BTBD3_HUMAN' })
      expect(inputParsing.page).toEqual(0)

      inputParsing = router._def.inputs[0].parse({ gene_type: 'BTBD3_HUMAN', page: 1 })
      expect(inputParsing.page).toEqual(1)
    })

    test('accepts protein query format', () => {
      const proteinQuery = {
        organism: 'Homo sapiens',
        name: 'BTBD3_HUMAN',
        page: 0
      }

      const inputParsing = router._def.inputs[0].parse(proteinQuery)
      expect(inputParsing).toEqual(proteinQuery)
    })

    test('returns an array of proteins in correct format', () => {
      const proteins = [{
        _id: 'ENSP00000329982',
        names: ['OR4F3_HUMAN'],
        full_names: ['Olfactory receptor 4F3/4F16/4F29'],
        source: 'GENCODE',
        organism: 'Homo sapiens',
        dbxrefs: [
          {
            name: 'BindingDB',
            id: 'Q04917'
          }
        ],
        source_url: 'https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_43/gencode.v43.chr_patch_hapl_scaff.annotation.gtf.gz'
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
