import { useEffect, useState } from 'react'
import { Input, Typography } from 'antd'
import { useFilters } from '@/hooks/useFilters'
import { COLORS } from '@/theme'

export default function ResortToolbar({ count, loading }) {
  const { filters, setFilter } = useFilters()
  const [localSearch, setLocalSearch] = useState(filters.search ?? '')

  // Reset local state when URL changes externally (e.g. on reset) — adjusted during
  // render rather than via effect, per https://react.dev/learn/you-might-not-need-an-effect
  const [syncedSearch, setSyncedSearch] = useState(filters.search ?? '')
  if ((filters.search ?? '') !== syncedSearch) {
    setSyncedSearch(filters.search ?? '')
    setLocalSearch(filters.search ?? '')
  }

  // Debounce URL update while user types
  useEffect(() => {
    const t = setTimeout(() => setFilter('search', localSearch || null), 300)
    return () => clearTimeout(t)
  }, [localSearch])

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
      <Input.Search
        placeholder="Search resorts..."
        value={localSearch}
        onChange={e => setLocalSearch(e.target.value)}
        loading={loading}
        allowClear
        style={{ maxWidth: 360 }}
      />
      <Typography.Text style={{ fontSize: 12, whiteSpace: 'nowrap', color: COLORS.success }}>
        {count} resort{count !== 1 ? 's' : ''} found
      </Typography.Text>
    </div>
  )
}
