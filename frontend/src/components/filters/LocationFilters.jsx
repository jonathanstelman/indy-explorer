import { useEffect, useRef, useState } from 'react'
import { Select } from 'antd'
import { useFilters } from '@/hooks/useFilters'

function toOptions(values) {
  return values.map(v => ({ label: v, value: v }))
}

function unique(arr) {
  return [...new Set(arr.filter(Boolean))].sort()
}

function useDeferredFilter(urlValue, filterKey) {
  const { setFilter } = useFilters()
  const [local, setLocal] = useState(urlValue)
  const ref = useRef(urlValue)

  // Reset local state when the URL value changes externally — adjusted during render
  // rather than via effect, per https://react.dev/learn/you-might-not-need-an-effect
  const urlKey = JSON.stringify(urlValue)
  const [syncedKey, setSyncedKey] = useState(urlKey)
  if (urlKey !== syncedKey) {
    setSyncedKey(urlKey)
    setLocal(urlValue)
  }
  // Ref writes aren't allowed during render, so this stays in an effect
  useEffect(() => {
    ref.current = urlValue
  }, [urlKey, urlValue])

  function onChange(v) {
    setLocal(v)
    ref.current = v
  }

  function onOpenChange(open) {
    if (!open) setFilter(filterKey, ref.current)
  }

  return { local, onChange, onOpenChange }
}

export default function LocationFilters({ meta, allResorts }) {
  const { filters } = useFilters()

  // Options cascade using committed filter values, but each field ignores its own filter
  const regionOptions = toOptions(meta?.regions ?? [])

  const countryOptions = toOptions(unique(
    allResorts
      .filter(r => filters.region.length === 0 || filters.region.includes(r.region))
      .map(r => r.country)
  ))

  const stateOptions = toOptions(unique(
    allResorts
      .filter(r => filters.region.length === 0 || filters.region.includes(r.region))
      .filter(r => filters.country.length === 0 || filters.country.includes(r.country))
      .map(r => r.state)
  ))

  const region = useDeferredFilter(filters.region, 'region')
  const country = useDeferredFilter(filters.country, 'country')
  const state = useDeferredFilter(filters.state, 'state')

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <Select
        mode="multiple"
        allowClear
        placeholder="All regions"
        options={regionOptions}
        value={region.local}
        onChange={region.onChange}
        onOpenChange={region.onOpenChange}
        style={{ width: '100%' }}
      />

      <Select
        mode="multiple"
        allowClear
        placeholder="All countries"
        options={countryOptions}
        value={country.local}
        onChange={country.onChange}
        onOpenChange={country.onOpenChange}
        style={{ width: '100%' }}
      />

      <Select
        mode="multiple"
        allowClear
        placeholder="All states / provinces"
        options={stateOptions}
        value={state.local}
        onChange={state.onChange}
        onOpenChange={state.onOpenChange}
        style={{ width: '100%' }}
      />
    </div>
  )
}
