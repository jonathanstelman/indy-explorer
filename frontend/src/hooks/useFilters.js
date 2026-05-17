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
