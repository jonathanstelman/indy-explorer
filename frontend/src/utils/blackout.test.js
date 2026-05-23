import { describe, it, expect } from 'vitest'
import { classifyBlackoutDates } from './blackout'

describe('classifyBlackoutDates', () => {
  it('returns empty map when both inputs are empty', () => {
    expect(classifyBlackoutDates('[]', '[]').size).toBe(0)
  })

  it('returns empty map for null/undefined inputs', () => {
    expect(classifyBlackoutDates(null, null).size).toBe(0)
    expect(classifyBlackoutDates(undefined, undefined).size).toBe(0)
  })

  it('classifies standard-only dates', () => {
    const result = classifyBlackoutDates('["2025-12-25", "2025-12-26"]', '[]')
    expect(result.get('2025-12-25')).toBe('standard')
    expect(result.get('2025-12-26')).toBe('standard')
  })

  it('classifies ltt-only dates', () => {
    const result = classifyBlackoutDates('[]', '["2026-01-01", "2026-01-02"]')
    expect(result.get('2026-01-01')).toBe('ltt')
    expect(result.get('2026-01-02')).toBe('ltt')
  })

  it('classifies overlapping dates as both', () => {
    const result = classifyBlackoutDates('["2025-12-25"]', '["2025-12-25", "2026-01-01"]')
    expect(result.get('2025-12-25')).toBe('both')
    expect(result.get('2026-01-01')).toBe('ltt')
  })
})
