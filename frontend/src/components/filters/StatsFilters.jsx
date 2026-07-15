import { useEffect, useState } from 'react'
import { Slider, Typography, theme } from 'antd'
import { useFilters } from '@/hooks/useFilters'
import { useUnits } from '@/hooks/useUnits'
import { UNIT_LABELS, convertVertical, convertTrailLength } from '@/utils/units'

const { Text } = Typography

// Canonical converters, keyed by the same `kind` strings used in UNIT_LABELS/units.js.
const CONVERTERS = {
  vertical: convertVertical,
  trailLength: convertTrailLength,
}

// The slider itself always operates on the canonical ft/mi values from the backend (meta
// range, filter params) — `unitKind` only controls the *displayed* label/numbers, converted
// on the way out to text so filtering semantics never change with the toggle.
function RangeSlider({ label, unitKind, metaRange, minKey, maxKey }) {
  const { filters, setFilters } = useFilters()
  const { token } = theme.useToken()
  const { unit } = useUnits()

  const metaMin = Math.floor(metaRange?.min ?? 0)
  const metaMax = Math.ceil(metaRange?.max ?? 100)

  const urlMin = filters[minKey] ?? metaMin
  const urlMax = filters[maxKey] ?? metaMax

  const [local, setLocal] = useState([urlMin, urlMax])

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

  const convert = unitKind ? CONVERTERS[unitKind] : null
  const displayLabel = unitKind ? `${label} (${UNIT_LABELS[unitKind][unit === 'metric' ? 'metric' : 'imperial']})` : label
  const display = v => (convert ? convert(v, unit) : v).toLocaleString()

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
        <Text style={{ fontSize: 12 }}>{displayLabel}</Text>
        {!atDefault && (
          <Text style={{ fontSize: 11, color: token.colorError }}>
            {display(local[0])} – {display(local[1])}
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
        tooltip={{ formatter: display }}
      />
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: -4 }}>
        <Text type="secondary" style={{ fontSize: 10 }}>{display(metaMin)}</Text>
        <Text type="secondary" style={{ fontSize: 10 }}>{display(metaMax)}</Text>
      </div>
    </div>
  )
}

export default function StatsFilters({ meta }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <RangeSlider
        label="Vertical"
        unitKind="vertical"
        metaRange={meta?.vertical ?? null}
        minKey="min_vertical"
        maxKey="max_vertical"
      />
      <RangeSlider
        label="Lifts"
        metaRange={meta?.num_lifts ?? null}
        minKey="min_lifts"
        maxKey="max_lifts"
      />
      <RangeSlider
        label="Trails"
        metaRange={meta?.num_trails ?? null}
        minKey="min_trails"
        maxKey="max_trails"
      />
      <RangeSlider
        label="Trails (XC)"
        metaRange={meta?.num_trails_xc ?? null}
        minKey="min_trails_xc"
        maxKey="max_trails_xc"
      />
      <RangeSlider
        label="Trail Length (XC)"
        unitKind="trailLength"
        metaRange={meta?.trail_length_mi ?? null}
        minKey="min_trail_length"
        maxKey="max_trail_length"
      />
    </div>
  )
}
