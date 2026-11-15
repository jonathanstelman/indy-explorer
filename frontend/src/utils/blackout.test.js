import { describe, it, expect } from 'vitest'
import { BLACKOUT_SEASON, classifyBlackoutDates, parseNotes } from './blackout'

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

describe('parseNotes', () => {
  it('parses a JSON list of note strings', () => {
    expect(parseNotes('["CLOSED FOR 26/27 DUE TO WILDFIRE"]')).toEqual([
      'CLOSED FOR 26/27 DUE TO WILDFIRE',
    ])
  })

  it('returns an empty list for empty, missing, or malformed input', () => {
    expect(parseNotes('[]')).toEqual([])
    expect(parseNotes(null)).toEqual([])
    expect(parseNotes(undefined)).toEqual([])
    expect(parseNotes('not json')).toEqual([])
  })

  it('drops blank and non-string entries', () => {
    expect(parseNotes('["a", "", "  ", 3, null]')).toEqual(['a'])
  })
})

describe('BLACKOUT_SEASON', () => {
  it('names the season and says the list is still being compiled', () => {
    expect(BLACKOUT_SEASON.label).toBe('26/27')
    expect(BLACKOUT_SEASON.notice).toMatch(/26\/27/)
    expect(BLACKOUT_SEASON.notice).toMatch(/still adding/i)
  })

  it("links to Indy's blackout dates page", () => {
    expect(BLACKOUT_SEASON.link).toEqual({
      text: 'indyskipass.com',
      url: 'https://www.indyskipass.com/blackout-dates-reservations',
    })
    expect(BLACKOUT_SEASON.notice).not.toMatch(/indyskipass\.com/)
  })
})
