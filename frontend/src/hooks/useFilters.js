import { useSearchParams } from 'react-router-dom'
import { useCallback } from 'react'

export function useFilters() {
  const [searchParams, setSearchParams] = useSearchParams()

  function getNum(key) {
    const v = searchParams.get(key)
    return v !== null ? Number(v) : undefined
  }

  function getBool(key) {
    const v = searchParams.get(key)
    if (v === 'true') return true    // yes only
    if (v === 'false') return false  // no only
    return undefined                 // absent = both active = no filter
  }

  const filters = {
    // Search
    search: searchParams.get('search'),
    // Location
    region: searchParams.getAll('region'),
    country: searchParams.getAll('country'),
    state: searchParams.getAll('state'),
    // Numeric range filters
    min_vertical: getNum('min_vertical'),
    max_vertical: getNum('max_vertical'),
    min_trails: getNum('min_trails'),
    max_trails: getNum('max_trails'),
    min_lifts: getNum('min_lifts'),
    max_lifts: getNum('max_lifts'),
    min_trail_length: getNum('min_trail_length'),
    max_trail_length: getNum('max_trail_length'),
    // Boolean feature toggles
    has_alpine: getBool('has_alpine'),
    has_cross_country: getBool('has_cross_country'),
    has_night_skiing: getBool('has_night_skiing'),
    has_terrain_parks: getBool('has_terrain_parks'),
    is_dog_friendly: getBool('is_dog_friendly'),
    has_snowshoeing: getBool('has_snowshoeing'),
    is_allied: getBool('is_allied'),
    reservation_required: getBool('reservation_required'),
    ltt_available: getBool('ltt_available'),
    has_peak_rankings: getBool('has_peak_rankings'),
    has_blackouts: getBool('has_blackouts'),
    // Blackout date range filters (YYYY-MM-DD strings)
    blackout_date_from: searchParams.get('blackout_date_from'),
    blackout_date_to: searchParams.get('blackout_date_to'),
    ltt_date_from: searchParams.get('ltt_date_from'),
    ltt_date_to: searchParams.get('ltt_date_to'),
    // Peak Rankings score range filters
    pr_total_min: getNum('pr_total_min'),
    pr_total_max: getNum('pr_total_max'),
    pr_snow_min: getNum('pr_snow_min'),
    pr_snow_max: getNum('pr_snow_max'),
    pr_resiliency_min: getNum('pr_resiliency_min'),
    pr_resiliency_max: getNum('pr_resiliency_max'),
    pr_size_min: getNum('pr_size_min'),
    pr_size_max: getNum('pr_size_max'),
    pr_terrain_diversity_min: getNum('pr_terrain_diversity_min'),
    pr_terrain_diversity_max: getNum('pr_terrain_diversity_max'),
    pr_challenge_min: getNum('pr_challenge_min'),
    pr_challenge_max: getNum('pr_challenge_max'),
    pr_lifts_min: getNum('pr_lifts_min'),
    pr_lifts_max: getNum('pr_lifts_max'),
    pr_crowd_flow_min: getNum('pr_crowd_flow_min'),
    pr_crowd_flow_max: getNum('pr_crowd_flow_max'),
    pr_facilities_min: getNum('pr_facilities_min'),
    pr_facilities_max: getNum('pr_facilities_max'),
    pr_navigation_min: getNum('pr_navigation_min'),
    pr_navigation_max: getNum('pr_navigation_max'),
    pr_mountain_aesthetic_min: getNum('pr_mountain_aesthetic_min'),
    pr_mountain_aesthetic_max: getNum('pr_mountain_aesthetic_max'),
    // Peak Rankings categorical filters
    pr_lodging: searchParams.getAll('pr_lodging'),
    pr_apres_ski: searchParams.getAll('pr_apres_ski'),
    pr_access_road: searchParams.getAll('pr_access_road'),
    pr_ability_low: searchParams.getAll('pr_ability_low'),
    pr_ability_high: searchParams.getAll('pr_ability_high'),
  }

  function applyUpdates(next, updates) {
    for (const [key, value] of Object.entries(updates)) {
      const isEmpty =
        value === null ||
        value === undefined ||
        value === '' ||
        (Array.isArray(value) && value.length === 0)
      if (isEmpty) {
        next.delete(key)
      } else if (Array.isArray(value)) {
        next.delete(key)
        value.forEach(v => next.append(key, v))
      } else {
        next.set(key, String(value))
      }
    }
  }

  const setFilter = useCallback(
    (key, value) => {
      setSearchParams(prev => {
        const next = new URLSearchParams(prev)
        applyUpdates(next, { [key]: value })
        return next
      })
    },
    [setSearchParams]
  )

  const setFilters = useCallback(
    (updates) => {
      setSearchParams(prev => {
        const next = new URLSearchParams(prev)
        applyUpdates(next, updates)
        return next
      })
    },
    [setSearchParams]
  )

  const resetFilters = useCallback(() => {
    setSearchParams(new URLSearchParams())
  }, [setSearchParams])

  return { filters, setFilter, setFilters, resetFilters }
}
