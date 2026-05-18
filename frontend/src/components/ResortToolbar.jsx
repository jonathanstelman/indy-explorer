import { useEffect, useState } from 'react'
import { Input, Typography } from 'antd'
import { useFilters } from '@/hooks/useFilters'

export default function ResortToolbar({ count, loading }) {
  const { filters, setFilter } = useFilters()
  const [localSearch, setLocalSearch] = useState(filters.search ?? '')

  // Sync local state when URL changes (e.g. on reset)
  useEffect(() => {
    setLocalSearch(filters.search ?? '')
  }, [filters.search])

  // Debounce URL update while user types
  useEffect(() => {
    const t = setTimeout(() => setFilter('search', localSearch || null), 300)
    return () => clearTimeout(t)
  }, [localSearch])

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
      <Input.Search
        placeholder="Search resorts..."
        value={localSearch}
        onChange={e => setLocalSearch(e.target.value)}
        loading={loading}
        allowClear
        style={{ maxWidth: 360 }}
      />
      <Typography.Text type="secondary" style={{ fontSize: 12, whiteSpace: 'nowrap' }}>
        {count} resort{count !== 1 ? 's' : ''} found
      </Typography.Text>
    </div>
  )
}
