const FT_PER_M = 3.28084
const MI_PER_KM = 0.621371
const IN_PER_CM = 0.393701
const AC_PER_HA = 2.47105

export const UNIT_LABELS = {
  vertical: { imperial: 'ft', metric: 'm' },
  trailLength: { imperial: 'mi', metric: 'km' },
  snowfall: { imperial: 'in', metric: 'cm' },
  acreage: { imperial: 'ac', metric: 'ha' },
}

function toDisplayNumber(value, digits) {
  return Number(value.toFixed(digits))
}

// Raw conversions — inputs are always the canonical imperial value (ft / mi / in / acres).
// Return a plain number (no unit suffix) for callers that already label the unit elsewhere
// (e.g. table column headers).
export function convertVertical(ft, unit) {
  if (ft == null) return null
  return unit === 'metric' ? toDisplayNumber(ft / FT_PER_M, 0) : toDisplayNumber(ft, 0)
}

export function convertTrailLength(mi, unit) {
  if (mi == null) return null
  return unit === 'metric' ? toDisplayNumber(mi / MI_PER_KM, 1) : toDisplayNumber(mi, 1)
}

export function convertSnowfall(inches, unit) {
  if (inches == null) return null
  return unit === 'metric' ? toDisplayNumber(inches / IN_PER_CM, 0) : toDisplayNumber(inches, 0)
}

export function convertAcres(acres, unit) {
  if (acres == null) return null
  return unit === 'metric' ? toDisplayNumber(acres / AC_PER_HA, 1) : toDisplayNumber(acres, 0)
}

function withSuffix(value, digits, suffix) {
  if (value == null) return '—'
  return `${value.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits })} ${suffix}`
}

export function formatVertical(ft, unit) {
  return withSuffix(convertVertical(ft, unit), 0, UNIT_LABELS.vertical[unit === 'metric' ? 'metric' : 'imperial'])
}

export function formatTrailLength(mi, unit) {
  return withSuffix(convertTrailLength(mi, unit), 1, UNIT_LABELS.trailLength[unit === 'metric' ? 'metric' : 'imperial'])
}

export function formatSnowfall(inches, unit) {
  return withSuffix(convertSnowfall(inches, unit), 0, UNIT_LABELS.snowfall[unit === 'metric' ? 'metric' : 'imperial'])
}

export function formatAcres(acres, unit) {
  const digits = unit === 'metric' ? 1 : 0
  return withSuffix(convertAcres(acres, unit), digits, UNIT_LABELS.acreage[unit === 'metric' ? 'metric' : 'imperial'])
}
