import { transcriptsRouters } from '../../datatypeRouters/nodes/transcripts'

describe('genes routers', () => {
  test('router is defined and available', () => {
    expect('transcripts' in transcriptsRouters)
  })

  describe('it implements general query', () => {
    let router: any
    let openApi: any

    beforeEach(() => {
      router = transcriptsRouters.transcripts
      openApi = router._def.meta?.openapi
    })

    test('implements OpenApi protocol', () => {
      expect(typeof openApi).toBe('object')
    })

    test('accepts pagination', () => {
      let inputParsing = router._def.inputs[0].parse({ transcript_type: 'lncRNA' })
      expect(inputParsing.page).toEqual(0)

      inputParsing = router._def.inputs[0].parse({ gene_type: 'lncRNA', page: 1 })
      expect(inputParsing.page).toEqual(1)
    })

    test('accepts transcript query format', () => {
      const transcriptQuery = {
        organism: 'human',
        region: 'chr1:12345-54321',
        transcript_type: 'lncRNA',
        page: 0
      }

      const inputParsing = router._def.inputs[0].parse(transcriptQuery)
      expect(inputParsing).toEqual(transcriptQuery)
    })

    test('returns an array of transcripts in correct format', () => {
      const transcripts = [{
        _id: 'ENST00000353224',
        transcript_type: 'protein_coding',
        chr: 'chr20',
        start: 9537369,
        end: 9839076,
        transcript_name: 'PAK5-201',
        gene_name: 'PAK5',
        source: 'GENCODE',
        version: 'v43',
        source_url: 'https://www.gencodegenes.org/human/'
      }]

      const outputParsing = router._def.output.parse(transcripts)
      expect(outputParsing).toEqual(transcripts)
    })

    test('has correct URL', () => {
      expect(openApi?.method).toBe('GET')
      expect(openApi?.path).toBe('/transcripts')
    })

    test('Expects procedure to be a trpc query', () => {
      expect(router._def.query).toBeTruthy()
    })
  })
})
