import { DatePicker, Divider, Typography } from 'antd'
import dayjs from 'dayjs'
import { useFilters } from '@/hooks/useFilters'
import { FeatureToggle } from '@/components/filters/FeatureFilters'

const { Text } = Typography

function SectionHeading({ children }) {
  return (
    <Divider orientation="left" orientationMargin={0} plain style={{ margin: '4px 0' }}>
      <Text type="secondary" style={{ fontSize: 11 }}>{children}</Text>
    </Divider>
  )
}

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

export default function BlackoutDateFilters() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <FeatureToggle label="Reservation required" filterKey="reservation_required" />
      <SectionHeading>Lift Ticket</SectionHeading>
      <FeatureToggle label="Blackout dates" filterKey="has_blackouts" />
      <BlackoutRangePicker
        label="Available on"
        fromKey="blackout_date_from"
        toKey="blackout_date_to"
      />
      <SectionHeading>Learn to Turn</SectionHeading>
      <FeatureToggle label="Offered" filterKey="ltt_available" />
      <BlackoutRangePicker
        label="Available on"
        fromKey="ltt_date_from"
        toKey="ltt_date_to"
      />
    </div>
  )
}
