import { useEffect, useRef, useState } from 'react'
import { Divider, Select, Slider, Typography, theme } from 'antd'
import { useFilters } from '@/hooks/useFilters'
import { FeatureToggle } from '@/components/filters/FeatureFilters'

const { Text } = Typography

function RangeSlider({ label, metaRange, minKey, maxKey }) {
  const { filters, setFilters } = useFilters()
  const { token } = theme.useToken()

  const metaMin = Math.floor(metaRange?.min ?? 0)
  const metaMax = Math.ceil(metaRange?.max ?? 10)

  const urlMin = filters[minKey] ?? metaMin
  const urlMax = filters[maxKey] ?? metaMax

  const [local, setLocal] = useState([urlMin, urlMax])

  // Reset local state when the URL value changes externally — adjusted during render
  // rather than via effect, per https://react.dev/learn/you-might-not-need-an-effect
  const [syncedRange, setSyncedRange] = useState([urlMin, urlMax])
  if (urlMin !== syncedRange[0] || urlMax !== syncedRange[1]) {
    setSyncedRange([urlMin, urlMax])
    setLocal([urlMin, urlMax])
  }

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
            {local[0]} – {local[1]}
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
        tooltip={{ formatter: v => v }}
      />
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: -4 }}>
        <Text type="secondary" style={{ fontSize: 10 }}>{metaMin}</Text>
        <Text type="secondary" style={{ fontSize: 10 }}>{metaMax}</Text>
      </div>
    </div>
  )
}

function CategoricalSelect({ label, filterKey, options }) {
  const { filters, setFilter } = useFilters()
  const urlValue = filters[filterKey]
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
  // Ref writes aren't allowed during render, so this stays in an effect. Deliberately
  // depends on urlKey (a stable string), not urlValue itself — urlValue is a fresh array
  // reference every render (filters[filterKey] is rebuilt from searchParams each time),
  // so depending on it directly reran this every render and clobbered ref.current back to
  // the stale URL value right after onChange had just set it to the in-progress selection,
  // silently breaking every multi-select filter's commit-on-close.
  useEffect(() => {
    ref.current = urlValue
  }, [urlKey])

  function onChange(v) {
    setLocal(v)
    ref.current = v
  }

  function onOpenChange(open) {
    if (!open) setFilter(filterKey, ref.current)
  }

  return (
    <div>
      <Text style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>{label}</Text>
      <Select
        mode="multiple"
        allowClear
        placeholder="Any"
        options={options}
        value={local}
        onChange={onChange}
        onOpenChange={onOpenChange}
        style={{ width: '100%' }}
      />
    </div>
  )
}

const SCORE_SLIDERS = [
  { label: 'Total score',          field: 'pr_total' },
  { label: 'Snow',                 field: 'pr_snow' },
  { label: 'Resiliency',           field: 'pr_resiliency' },
  { label: 'Size',                 field: 'pr_size' },
  { label: 'Terrain diversity',    field: 'pr_terrain_diversity' },
  { label: 'Challenge',            field: 'pr_challenge' },
  { label: 'Lifts',                field: 'pr_lifts' },
  { label: 'Crowd flow',           field: 'pr_crowd_flow' },
  { label: 'Facilities',           field: 'pr_facilities' },
  { label: 'Navigation',           field: 'pr_navigation' },
  { label: 'Mountain aesthetic',   field: 'pr_mountain_aesthetic' },
]

function toOptions(values) {
  return values.map(v => ({ label: v.charAt(0).toUpperCase() + v.slice(1), value: v }))
}

const CATEGORICAL_FILTERS = [
  {
    label: 'Lodging',
    key: 'pr_lodging',
    options: toOptions(['yes', 'limited', 'no']),
  },
  {
    label: 'Après ski',
    key: 'pr_apres_ski',
    options: toOptions(['extensive', 'moderate', 'limited']),
  },
  {
    label: 'Access road',
    key: 'pr_access_road',
    options: toOptions(['good', 'fair', 'acceptable']),
  },
  {
    label: 'Ability (low)',
    key: 'pr_ability_low',
    options: toOptions(['beginner', 'intermediate', 'advanced']),
  },
  {
    label: 'Ability (high)',
    key: 'pr_ability_high',
    options: toOptions(['beginner', 'intermediate', 'advanced', 'expert', 'extreme']),
  },
]

export default function PeakRankingsFilters({ meta }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <FeatureToggle label="Has Peak Rankings" filterKey="has_peak_rankings" />
      {SCORE_SLIDERS.map(({ label, field }) => (
        <RangeSlider
          key={field}
          label={label}
          metaRange={meta?.[field] ?? null}
          minKey={`${field}_min`}
          maxKey={`${field}_max`}
        />
      ))}

      <Divider style={{ margin: 0 }} />

      {CATEGORICAL_FILTERS.map(({ label, key, options }) => (
        <CategoricalSelect key={key} label={label} filterKey={key} options={options} />
      ))}

      <CategoricalSelect
        label="Pass Affiliation"
        filterKey="pass_affiliation"
        options={toOptions(meta?.pass_affiliations ?? [])}
      />
    </div>
  )
}
