import { Button, Typography } from 'antd'
import { useFilters } from '@/hooks/useFilters'

const { Text } = Typography

export function FeatureToggle({ label, filterKey }) {
  const { filters, setFilter } = useFilters()
  const current = filters[filterKey]
  const yesActive = current === undefined || current === true
  const noActive  = current === undefined || current === false

  function toggleYes() {
    if (current === true) setFilter(filterKey, null)
    else                  setFilter(filterKey, true)
  }

  function toggleNo() {
    if (current === false) setFilter(filterKey, null)
    else                   setFilter(filterKey, false)
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
      <Text style={{ fontSize: 12, flex: 1 }}>{label}</Text>
      <Button.Group size="small">
        <Button type={yesActive ? 'primary' : 'default'} onClick={toggleYes}>Yes</Button>
        <Button type={noActive  ? 'primary' : 'default'} onClick={toggleNo}>No</Button>
      </Button.Group>
    </div>
  )
}

const BOOLEAN_FILTERS = [
  { label: 'Alpine skiing',        key: 'has_alpine' },
  { label: 'Cross-country',        key: 'has_cross_country' },
  { label: 'Night skiing',         key: 'has_night_skiing' },
  { label: 'Terrain parks',        key: 'has_terrain_parks' },
  { label: 'Dog friendly',         key: 'is_dog_friendly' },
  { label: 'Snowshoeing',          key: 'has_snowshoeing' },
  { label: 'Allied resort',        key: 'is_allied' },
]

export default function FeatureFilters() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {BOOLEAN_FILTERS.map(({ label, key }) => (
        <FeatureToggle key={key} label={label} filterKey={key} />
      ))}
    </div>
  )
}
