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

// Internal resolution of the log-scale slider track; unrelated to the real-world values.
const LOG_SLIDER_STEPS = 1000

function logDomain(min, max) {
  const logMin = Math.log10(Math.max(min, 1))
  const logMax = Math.log10(Math.max(max, min + 1))
  return [logMin, logMax]
}

function toLogPos(v, min, max, logMin, logMax) {
  if (v <= min) return 0
  if (v >= max) return LOG_SLIDER_STEPS
  return Math.round(((Math.log10(v) - logMin) / (logMax - logMin)) * LOG_SLIDER_STEPS)
}

function fromLogPos(pos, min, max, logMin, logMax) {
  if (pos <= 0) return min
  if (pos >= LOG_SLIDER_STEPS) return max
  return Math.round(10 ** (logMin + (pos / LOG_SLIDER_STEPS) * (logMax - logMin)))
}

// The slider itself always operates on the canonical ft/mi values from the backend (meta
// range, filter params) — `unitKind` only controls the *displayed* label/numbers, converted
// on the way out to text so filtering semantics never change with the toggle.
//
// `logScale` remaps the track to log10 space so a field with a long tail of outliers (e.g.
// acreage, where a handful of huge combined European resorts stretch the linear range out to
// ~19,000 while most resorts sit under 1,000) doesn't collapse most of its resorts into the
// first few pixels. Real-world values (local state, URL filters, tooltip text) are unaffected —
// only the Slider's own position/drag space is log-mapped.
function RangeSlider({ label, unitKind, metaRange, minKey, maxKey, logScale = false }) {
  const { filters, setFilters } = useFilters()
  const { token } = theme.useToken()
  const { unit } = useUnits()

  const metaMin = Math.floor(metaRange?.min ?? 0)
  const metaMax = Math.ceil(metaRange?.max ?? 100)
  const [logMin, logMax] = logScale ? logDomain(metaMin, metaMax) : [null, null]

  const urlMin = filters[minKey] ?? metaMin
  const urlMax = filters[maxKey] ?? metaMax

  const [local, setLocal] = useState([urlMin, urlMax])

  useEffect(() => {
    setLocal([filters[minKey] ?? metaMin, filters[maxKey] ?? metaMax])
  }, [filters[minKey], filters[maxKey], metaMin, metaMax])

  function onChangeComplete(rawValue) {
    const [min, max] = logScale
      ? rawValue.map(p => fromLogPos(p, metaMin, metaMax, logMin, logMax))
      : rawValue
    setFilters({
      [minKey]: min === metaMin ? null : min,
      [maxKey]: max === metaMax ? null : max,
    })
  }

  const atDefault = local[0] === metaMin && local[1] === metaMax

  const convert = unitKind ? CONVERTERS[unitKind] : null
  const displayLabel = unitKind ? `${label} (${UNIT_LABELS[unitKind][unit === 'metric' ? 'metric' : 'imperial']})` : label
  const display = v => (convert ? convert(v, unit) : v).toLocaleString()

  const sliderValue = logScale
    ? local.map(v => toLogPos(v, metaMin, metaMax, logMin, logMax))
    : local
  const sliderMin = logScale ? 0 : metaMin
  const sliderMax = logScale ? LOG_SLIDER_STEPS : metaMax
  const handleChange = logScale
    ? positions => setLocal(positions.map(p => fromLogPos(p, metaMin, metaMax, logMin, logMax)))
    : setLocal
  const tooltipFormatter = logScale
    ? pos => display(fromLogPos(pos, metaMin, metaMax, logMin, logMax))
    : display

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
        min={sliderMin}
        max={sliderMax}
        value={sliderValue}
        onChange={handleChange}
        onChangeComplete={onChangeComplete}
        disabled={metaRange === null}
        tooltip={{ formatter: tooltipFormatter }}
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
        label="Acreage"
        metaRange={meta?.acres ?? null}
        minKey="min_acres"
        maxKey="max_acres"
        logScale
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
