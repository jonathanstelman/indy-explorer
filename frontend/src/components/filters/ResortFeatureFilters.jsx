import { useEffect, useState } from 'react'
import { Button, Slider, Typography } from 'antd'
import { useFilters } from '@/hooks/useFilters'

const { Text } = Typography

function SectionLabel({ children }) {
  return (
    <Text
      type="secondary"
      style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em' }}
    >
      {children}
    </Text>
  )
}

function RangeSlider({ label, metaRange, minKey, maxKey }) {
  const { filters, setFilters } = useFilters()

  const metaMin = Math.floor(metaRange?.min ?? 0)
  const metaMax = Math.ceil(metaRange?.max ?? 100)

  const urlMin = filters[minKey] ?? metaMin
  const urlMax = filters[maxKey] ?? metaMax

  const [local, setLocal] = useState([urlMin, urlMax])

  // Sync when URL changes (back/forward) or meta loads
  useEffect(() => {
    setLocal([filters[minKey] ?? metaMin, filters[maxKey] ?? metaMax])
  }, [filters[minKey], filters[maxKey], metaMin, metaMax])

  function onChangeComplete([min, max]) {
    setFilters({
      [minKey]: min === metaMin ? null : min,
      [maxKey]: max === metaMax ? null : max,
    })
  }

  const atDefault = local[0] === metaMin && local[1] === metaMax

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
        <Text style={{ fontSize: 12 }}>{label}</Text>
        {!atDefault && (
          <Text type="secondary" style={{ fontSize: 11 }}>
            {local[0].toLocaleString()} – {local[1].toLocaleString()}
          </Text>
        )}
      </div>
      <Slider
        range
        min={metaMin}
        max={metaMax}
        value={local}
        onChange={setLocal}
        onChangeComplete={onChangeComplete}
        disabled={metaRange === null}
        tooltip={{ formatter: v => v.toLocaleString() }}
      />
    </div>
  )
}

function FeatureToggle({ label, filterKey }) {
  const { filters, setFilter } = useFilters()
  const current = filters[filterKey]
  const yesActive = current === undefined || current === true
  const noActive  = current === undefined || current === false

  function toggleYes() {
    if (current === true) setFilter(filterKey, null)   // yes → both (clear param)
    else                  setFilter(filterKey, true)   // both or no → yes only
  }

  function toggleNo() {
    if (current === false) setFilter(filterKey, null)  // no → both (clear param)
    else                   setFilter(filterKey, false) // both or yes → no only
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
  { label: 'Alpine skiing',       key: 'has_alpine' },
  { label: 'Cross-country',       key: 'has_cross_country' },
  { label: 'Night skiing',        key: 'has_night_skiing' },
  { label: 'Terrain parks',       key: 'has_terrain_parks' },
  { label: 'Dog friendly',        key: 'is_dog_friendly' },
  { label: 'Snowshoeing',         key: 'has_snowshoeing' },
  { label: 'Allied resort',       key: 'is_allied' },
  { label: 'Reservation required', key: 'reservation_required' },
]

export default function ResortFeatureFilters({ meta }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <SectionLabel>Stats</SectionLabel>

      <RangeSlider
        label="Vertical (ft)"
        metaRange={meta?.vertical ?? null}
        minKey="min_vertical"
        maxKey="max_vertical"
      />
      <RangeSlider
        label="Trails"
        metaRange={meta?.num_trails ?? null}
        minKey="min_trails"
        maxKey="max_trails"
      />
      <RangeSlider
        label="Lifts"
        metaRange={meta?.num_lifts ?? null}
        minKey="min_lifts"
        maxKey="max_lifts"
      />
      <RangeSlider
        label="Trail length (mi)"
        metaRange={meta?.trail_length_mi ?? null}
        minKey="min_trail_length"
        maxKey="max_trail_length"
      />

      <SectionLabel style={{ marginTop: 8 }}>Features</SectionLabel>

      {BOOLEAN_FILTERS.map(({ label, key }) => (
        <FeatureToggle key={key} label={label} filterKey={key} />
      ))}
    </div>
  )
}
