import { validRegion, preProcessRegionParam } from '../datatypeRouters/_helpers'

describe('.validRegion', () => {
  test('returns null for invalid region', () => {
    expect(validRegion('myInvalidRegion')).toBe(null)
  })

  test('returns null if region is valid but incomplete', () => {
    expect(validRegion('chr1:123')).toBe(null)
  })

  test('returns correct components for valid region', () => {
    const chr = 'chr22'
    const start = '123'
    const end = '321'
    const region = `${chr}:${start}-${end}`

    const breakdown = validRegion(region) as string[]

    expect(breakdown[1]).toBe(chr)
    expect(breakdown[2]).toBe(start)
    expect(breakdown[3]).toBe(end)
  })
})

describe('.preProcessRegionParam', () => {
  test('takes an input with a region string and break down into components', () => {
    const input = {
      region: 'chr1:12345-54321',
      other: 'parameter',
      another: 'parameter too'
    }

    const processed = preProcessRegionParam(input)

    expect(processed.chr).toBe('chr1')
    expect(processed.start).toBe('gte:12345')
    expect(processed.end).toBe('lte:54321')
  })

  test('removes old region parameter', () => {
    const input = {
      region: 'chr1:12345-54321',
      other: 'parameter',
      another: 'parameter too'
    }

    const processed = preProcessRegionParam(input)

    expect(processed.region).toBe(undefined)
    expect(processed.other).toBe('parameter')
    expect(processed.another).toBe('parameter too')
  })

  test('fails if parameter is invalid', () => {
    const input = {
      region: '1:12345-54321'
    }

    try {
      preProcessRegionParam(input)
    } catch {
      expect(true).toBe(true)
      return
    }

    fail('Invalid region format raise exception for no query params')
  })

  test('should not fail if parameter is not present', () => {
    const input = {
      other: 'parameter',
      another: 'parameter too'
    }

    try {
      preProcessRegionParam(input)
    } catch {
      throw new Error('Should not raise exception')
    }

    expect(true).toBe(true)
  })

  test('sets a range if single field is passed', () => {
    const input = {
      region: 'chr1:12345-54321'
    }

    const processed = preProcessRegionParam(input, 'position')
    expect(processed.position).toBe('range:12345-54321')
    expect(processed.chr).toBe('chr1')

    expect(processed.region).toBe(undefined)
    expect(processed.start).toBe(undefined)
    expect(processed.end).toBe(undefined)
  })
})
