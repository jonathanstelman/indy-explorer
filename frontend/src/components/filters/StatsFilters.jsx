import { useEffect, useState } from 'react'
import { Slider, Typography, theme } from 'antd'
import { useFilters } from '@/hooks/useFilters'

const { Text } = Typography

function RangeSlider({ label, metaRange, minKey, maxKey }) {
  const { filters, setFilters } = useFilters()
  const { token } = theme.useToken()

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

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
        <Text style={{ fontSize: 12 }}>{label}</Text>
        {!atDefault && (
          <Text style={{ fontSize: 11, color: token.colorError }}>
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
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: -4 }}>
        <Text type="secondary" style={{ fontSize: 10 }}>{metaMin.toLocaleString()}</Text>
        <Text type="secondary" style={{ fontSize: 10 }}>{metaMax.toLocaleString()}</Text>
      </div>
    </div>
  )
}

export default function StatsFilters({ meta }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
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
        label="Trails (XC)"
        metaRange={meta?.num_trails_xc ?? null}
        minKey="min_trails_xc"
        maxKey="max_trails_xc"
      />
      <RangeSlider
        label="Lifts"
        metaRange={meta?.num_lifts ?? null}
        minKey="min_lifts"
        maxKey="max_lifts"
      />
      <RangeSlider
        label="Trail Length XC (mi)"
        metaRange={meta?.trail_length_mi ?? null}
        minKey="min_trail_length"
        maxKey="max_trail_length"
      />
    </div>
  )
}
