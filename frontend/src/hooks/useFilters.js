import { useSearchParams } from 'react-router-dom'
import { useCallback } from 'react'

export function useFilters() {
  const [searchParams, setSearchParams] = useSearchParams()

  const filters = {
    // Location
    region: searchParams.getAll('region'),
    country: searchParams.getAll('country'),
    state: searchParams.getAll('state'),
    // Feature filters, range filters, date filters added in subsequent issues
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
