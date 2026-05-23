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
