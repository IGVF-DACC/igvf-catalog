<<<<<<< Updated upstream
import { distanceGeneVariant } from '../../datatypeRouters/_helpers'
=======
import { distanceGeneVariant, expandPreferredAssayTitles, withExpandedAssayTitles } from '../../datatypeRouters/_helpers'
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
=======

describe('expandPreferredAssayTitles', () => {
  it('adds Perturb-seq alongside TAP-seq', () => {
    expect(expandPreferredAssayTitles(['TAP-seq'])).toEqual(['TAP-seq', 'Perturb-seq'])
  })

  it('does not duplicate Perturb-seq if already present', () => {
    expect(expandPreferredAssayTitles(['TAP-seq', 'Perturb-seq'])).toEqual(['TAP-seq', 'Perturb-seq'])
  })

  it('leaves titles with no grouping untouched', () => {
    expect(expandPreferredAssayTitles(['STARR-seq'])).toEqual(['STARR-seq'])
  })

  it('passes through null and undefined', () => {
    expect(expandPreferredAssayTitles(null)).toBeNull()
    expect(expandPreferredAssayTitles(undefined)).toBeNull()
  })

  it('passes through an empty array', () => {
    expect(expandPreferredAssayTitles([])).toEqual([])
  })
})

describe('withExpandedAssayTitles', () => {
  it('expands preferred_assay_titles on every record that has the field', () => {
    const records = [
      { method: 'Perturb-seq', preferred_assay_titles: ['TAP-seq'] },
      { method: 'STARR-seq', preferred_assay_titles: ['STARR-seq'] }
    ]
    expect(withExpandedAssayTitles(records)).toEqual([
      { method: 'Perturb-seq', preferred_assay_titles: ['TAP-seq', 'Perturb-seq'] },
      { method: 'STARR-seq', preferred_assay_titles: ['STARR-seq'] }
    ])
  })

  it('leaves records without the field untouched', () => {
    const records = [{ method: 'ClinGen' }]
    expect(withExpandedAssayTitles(records)).toEqual([{ method: 'ClinGen' }])
  })

  it('handles an empty array', () => {
    expect(withExpandedAssayTitles([])).toEqual([])
  })
})
>>>>>>> Stashed changes
