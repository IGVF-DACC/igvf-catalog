import { motifsRouters } from '../../datatypeRouters/nodes/motifs'

describe('motif routers', () => {
  test('router is defined and available', () => {
    expect('motifs' in motifsRouters)
  })

  describe('it implements general query', () => {
    let router: any
    let openApi: any

    beforeEach(() => {
      router = motifsRouters.motifs
      openApi = router._def.meta?.openapi
    })

    test('implements OpenApi protocol', () => {
      expect(typeof openApi).toBe('object')
    })

    test('accepts motif query format', () => {
      const motifQuery = {
        name: 'ATF1_HUMAN',
        source: 'HOCOMOCOv11'
      }

      const inputParsing = router._def.inputs[0].parse(motifQuery)
      expect(inputParsing).toEqual(motifQuery)
    })

    test('returns an array of variants in correct format', () => {
      const motifs = [{
        _id: 'AHR_HUMAN_HOCOMOCOv11',
        tf_name: 'AHR_HUMAN',
        length: 9,
        pwm: [
          [
            '0.049659785047587994',
            '-0.7112292711652767',
            '0.37218581437481474',
            '0.007118345755727385'
          ]
        ],
        source: 'HOCOMOCOv11',
        source_url: 'hocomoco11.autosome.org/motif/AHR_HUMAN.H11MO.0.B'
      }]

      const outputParsing = router._def.output.parse(motifs)
      expect(outputParsing).toEqual(motifs)
    })

    test('has correct URL', () => {
      expect(openApi?.method).toBe('GET')
      expect(openApi?.path).toBe('/motifs')
    })

    test('Expects procedure to be a trpc query', () => {
      expect(router._def.query).toBeTruthy()
    })
  })
})
