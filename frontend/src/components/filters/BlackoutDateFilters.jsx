import { Button, DatePicker, Typography } from 'antd'
import dayjs from 'dayjs'
import { useFilters } from '@/hooks/useFilters'

const { Text } = Typography

function BlackoutRangePicker({ label, fromKey, toKey }) {
  const { filters, setFilters } = useFilters()
  const from = filters[fromKey]
  const to = filters[toKey]
  const value = from && to ? [dayjs(from), dayjs(to)] : null

  function onChange(_, [fromStr, toStr]) {
    setFilters({
      [fromKey]: fromStr || null,
      [toKey]: toStr || null,
    })
  }

  return (
    <div>
      <Text style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>{label}</Text>
      <DatePicker.RangePicker
        value={value}
        onChange={onChange}
        format="YYYY-MM-DD"
        style={{ width: '100%' }}
      />
    </div>
  )
}

function LttAvailableToggle() {
  const { filters, setFilter } = useFilters()
  const current = filters.ltt_available
  const yesActive = current === undefined || current === true
  const noActive  = current === undefined || current === false

  function toggleYes() {
    if (current === true) setFilter('ltt_available', null)
    else                  setFilter('ltt_available', true)
  }

  function toggleNo() {
    if (current === false) setFilter('ltt_available', null)
    else                   setFilter('ltt_available', false)
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
      <Text style={{ fontSize: 12, flex: 1 }}>LTT available</Text>
      <Button.Group size="small">
        <Button type={yesActive ? 'primary' : 'default'} onClick={toggleYes}>Yes</Button>
        <Button type={noActive  ? 'primary' : 'default'} onClick={toggleNo}>No</Button>
      </Button.Group>
    </div>
  )
}

export default function BlackoutDateFilters() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <BlackoutRangePicker
        label="Lift ticket available on"
        fromKey="blackout_date_from"
        toKey="blackout_date_to"
      />
      <LttAvailableToggle />
      <BlackoutRangePicker
        label="LTT available on"
        fromKey="ltt_date_from"
        toKey="ltt_date_to"
      />
    </div>
  )
}
