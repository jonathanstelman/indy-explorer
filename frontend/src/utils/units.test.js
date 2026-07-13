import { describe, it, expect } from 'vitest'
import {
  formatVertical, formatTrailLength, formatSnowfall, formatAcres,
  convertVertical, convertTrailLength, convertSnowfall, convertAcres,
} from './units'

describe('convert* helpers', () => {
  it('convertVertical returns a plain number, no suffix', () => {
    expect(convertVertical(1851, 'imperial')).toBe(1851)
    expect(convertVertical(1851, 'metric')).toBe(564)
    expect(convertVertical(null, 'metric')).toBe(null)
  })

  it('convertTrailLength returns a plain number, no suffix', () => {
    expect(convertTrailLength(15, 'imperial')).toBe(15)
    expect(convertTrailLength(15, 'metric')).toBe(24.1)
    expect(convertTrailLength(null, 'imperial')).toBe(null)
  })

  it('convertSnowfall returns a plain number, no suffix', () => {
    expect(convertSnowfall(120, 'imperial')).toBe(120)
    expect(convertSnowfall(120, 'metric')).toBe(305)
    expect(convertSnowfall(null, 'metric')).toBe(null)
  })

  it('convertAcres returns a plain number, no suffix', () => {
    expect(convertAcres(500, 'imperial')).toBe(500)
    expect(convertAcres(500, 'metric')).toBe(202.3)
    expect(convertAcres(null, 'imperial')).toBe(null)
  })
})

describe('formatVertical', () => {
  it('formats imperial as whole feet', () => {
    expect(formatVertical(1851, 'imperial')).toBe('1,851 ft')
  })

  it('formats metric as whole meters', () => {
    expect(formatVertical(1851, 'metric')).toBe('564 m')
  })

  it('returns em dash for null/undefined', () => {
    expect(formatVertical(null, 'imperial')).toBe('—')
    expect(formatVertical(undefined, 'metric')).toBe('—')
  })
})

describe('formatTrailLength', () => {
  it('formats imperial as miles with 1 decimal', () => {
    expect(formatTrailLength(15, 'imperial')).toBe('15.0 mi')
  })

  it('formats metric as km with 1 decimal', () => {
    expect(formatTrailLength(15, 'metric')).toBe('24.1 km')
  })

  it('returns em dash for null', () => {
    expect(formatTrailLength(null, 'imperial')).toBe('—')
  })
})

describe('formatSnowfall', () => {
  it('formats imperial as whole inches', () => {
    expect(formatSnowfall(120, 'imperial')).toBe('120 in')
  })

  it('formats metric as whole centimeters', () => {
    expect(formatSnowfall(120, 'metric')).toBe('305 cm')
  })

  it('returns em dash for null', () => {
    expect(formatSnowfall(null, 'metric')).toBe('—')
  })
})

describe('formatAcres', () => {
  it('formats imperial as whole acres', () => {
    expect(formatAcres(500, 'imperial')).toBe('500 ac')
  })

  it('formats metric as hectares with 1 decimal', () => {
    expect(formatAcres(500, 'metric')).toBe('202.3 ha')
  })

  it('returns em dash for null', () => {
    expect(formatAcres(null, 'imperial')).toBe('—')
  })
})
