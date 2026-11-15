function parseDates(json) {
  if (!json) return []
  try {
    return JSON.parse(json)
  } catch {
    return []
  }
}

// Returns a Map<dateString, 'standard' | 'ltt' | 'both'>
export function classifyBlackoutDates(standardJson, lttJson) {
  const standard = new Set(parseDates(standardJson))
  const ltt = new Set(parseDates(lttJson))
  const result = new Map()
  for (const d of standard) result.set(d, ltt.has(d) ? 'both' : 'standard')
  for (const d of ltt) if (!result.has(d)) result.set(d, 'ltt')
  return result
}

// Season the blackout data covers. Update with the pipeline's season (utils.SEASON_START_YEAR)
// and drop the "still adding" wording once Indy says its lists are complete.
export const BLACKOUT_SEASON = {
  label: '26/27',
  // Rendered as: notice + " check " + link + " before you go." (see BlackoutSeasonNotice)
  notice: 'Showing 26/27 blackout dates. Indy is still adding resorts and dates, so',
  link: {
    text: 'indyskipass.com',
    url: 'https://www.indyskipass.com/blackout-dates-reservations',
  },
}

// Indy's free-text notes for a resort (closures, "only available ..." windows, TBDs),
// stored as a JSON list string.
export function parseNotes(json) {
  return parseDates(json).filter(n => typeof n === 'string' && n.trim())
}
