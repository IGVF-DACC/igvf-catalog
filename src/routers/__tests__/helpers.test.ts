import { preProcessRegionParam } from '../datatypeRouters/_helpers'

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
})
