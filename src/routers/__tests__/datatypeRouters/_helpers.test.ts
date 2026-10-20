import { distanceGeneVariant } from '../../datatypeRouters/_helpers'

describe('distanceGeneVariant', () => {
  it('measures distance to the gene start (TSS) for a + strand gene', () => {
    // chr15:81000922-81005788, + strand - TSS is the start (81000922), not the end.
    expect(distanceGeneVariant(81000922, 81005788, '+', 81099009)).toBe(98087)
  })

  it('measures distance to the gene end (TSS) for a - strand gene', () => {
    // Same coordinates on the - strand - TSS flips to the end (81005788).
    expect(distanceGeneVariant(81000922, 81005788, '-', 81099009)).toBe(93221)
  })

  it('returns 0 when the position is exactly at the TSS', () => {
    expect(distanceGeneVariant(1000, 2000, '+', 1000)).toBe(0)
    expect(distanceGeneVariant(1000, 2000, '-', 2000)).toBe(0)
  })
})
