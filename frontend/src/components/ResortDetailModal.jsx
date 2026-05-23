import { useEffect, useRef, useState } from 'react'
import dayjs from 'dayjs'
import {
  Bar, BarChart, Cell, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis,
} from 'recharts'
import { Button, Calendar, Divider, Modal, Select, Skeleton, Space, Tag, Typography } from 'antd'
import { fetchResort } from '@/api/resorts'
import { classifyBlackoutDates } from '@/utils/blackout'
import { COLORS } from '@/theme'

// Persists the user's last-viewed month across modal opens
let sharedCalendarMonth = dayjs()

const { Title, Text, Link } = Typography

const BLACKOUT_COLORS = {
  standard: COLORS.error,
  ltt:      COLORS.primary,
}

const BLACKOUT_TEXT = {
  standard: COLORS.bgBase,
  ltt:      COLORS.text,
  both:     COLORS.text,
}

const FEATURES = [
  { key: 'has_alpine',        label: 'Alpine' },
  { key: 'has_cross_country', label: 'Cross-country' },
  { key: 'has_night_skiing',  label: 'Night skiing' },
  { key: 'has_terrain_parks', label: 'Terrain parks' },
  { key: 'has_snowshoeing',   label: 'Snowshoeing' },
  { key: 'is_dog_friendly',   label: 'Dog friendly' },
]

const PR_CATEGORIES = [
  { key: 'pr_snow',               label: 'Snow' },
  { key: 'pr_resiliency',         label: 'Resiliency' },
  { key: 'pr_size',               label: 'Size' },
  { key: 'pr_terrain_diversity',  label: 'Terrain' },
  { key: 'pr_challenge',          label: 'Challenge' },
  { key: 'pr_lifts',              label: 'Lifts' },
  { key: 'pr_crowd_flow',         label: 'Crowd Flow' },
  { key: 'pr_facilities',         label: 'Facilities' },
  { key: 'pr_navigation',         label: 'Navigation' },
  { key: 'pr_mountain_aesthetic', label: 'Aesthetic' },
]

const DIFFICULTY_COLORS = {
  Beginner:     '#00C44F',
  Intermediate: COLORS.primary,
  Advanced:     '#555555',
}

function fmt(value, unit) {
  if (value == null) return '—'
  return unit ? `${value.toLocaleString()} ${unit}` : value.toLocaleString()
}

function ElevationStats({ base, summit }) {
  if (base == null && summit == null) return null
  const drop = base != null && summit != null
    ? Math.round(Number(summit) - Number(base))
    : null
  const rows = [
    ['Summit', summit != null ? Number(summit).toLocaleString() : null],
    ['Drop',   drop   != null ? drop.toLocaleString()           : null],
    ['Base',   base   != null ? Number(base).toLocaleString()   : null],
  ].filter(([, v]) => v != null)

  return (
    <div>
      <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 8 }}>Elevation (ft)</Text>
      <div style={{ borderLeft: `2px solid ${COLORS.primary}`, paddingLeft: 10, display: 'flex', flexDirection: 'column', gap: 4 }}>
        {rows.map(([label, value]) => (
          <div key={label} style={{ height: 20, display: 'flex', alignItems: 'center' }}>
            <Text type="secondary" style={{ fontSize: 12 }}>{label}: </Text>
            <Text strong style={{ fontSize: 12 }}>{value}</Text>
          </div>
        ))}
      </div>
    </div>
  )
}

function DifficultyChart({ beginner, intermediate, advanced }) {
  if (beginner == null && intermediate == null && advanced == null) return null
  const data = [
    { name: 'Beginner',     value: Number(beginner     || 0) },
    { name: 'Intermediate', value: Number(intermediate || 0) },
    { name: 'Advanced',     value: Number(advanced     || 0) },
  ].filter(d => d.value > 0)
  if (data.length === 0) return null
  return (
    <div>
      <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 8 }}>Trail Difficulty</Text>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, flexShrink: 0 }}>
          {data.map(d => (
            <span key={d.name} style={{ height: 20, fontSize: 12, display: 'flex', alignItems: 'center', gap: 4, whiteSpace: 'nowrap' }}>
              <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: DIFFICULTY_COLORS[d.name], flexShrink: 0 }} />
              <Text type="secondary" style={{ fontSize: 12 }}>{d.name}: </Text>
              <Text strong style={{ fontSize: 12 }}>{d.value}%</Text>
            </span>
          ))}
        </div>
        <ResponsiveContainer width="100%" height={90}>
          <PieChart>
            <Pie data={data} dataKey="value" cx="50%" cy="50%" outerRadius={40} isAnimationActive={false}>
              {data.map(entry => <Cell key={entry.name} fill={DIFFICULTY_COLORS[entry.name]} />)}
            </Pie>
            <Tooltip formatter={(v, name) => [`${v}%`, name]} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

function SnowfallChart({ avg, high }) {
  if (avg == null && high == null) return null
  const data = [
    { label: 'Average', inches: avg != null ? Number(avg) : null },
    { label: 'Max',     inches: high != null ? Number(high) : null },
  ].filter(d => d.inches != null)
  if (data.length === 0) return null
  return (
    <div>
      <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>Snowfall (in)</Text>
      <ResponsiveContainer width="100%" height={90}>
        <BarChart data={data} margin={{ top: 16, right: 0, bottom: 0, left: 0 }}>
          <XAxis dataKey="label" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
          <Bar dataKey="inches" fill={COLORS.primary} isAnimationActive={false}
            label={{ position: 'top', fontSize: 11 }} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

function PeakRankings({ resort }) {
  if (resort.pr_total == null) return <Text type="secondary">No Peak Rankings data.</Text>

  const abilityRange = resort.pr_ability_low && resort.pr_ability_high
    ? resort.pr_ability_low === resort.pr_ability_high
      ? resort.pr_ability_low
      : `${resort.pr_ability_low} — ${resort.pr_ability_high}`
    : resort.pr_ability_low || resort.pr_ability_high || null

  const extras = [
    ['Lodging',         resort.pr_lodging],
    ['Après Ski',       resort.pr_apres_ski],
    ['Access Road',     resort.pr_access_road],
    ['Ability Range',   abilityRange],
    ['Pass',            resort.pr_pass_affiliation],
    ['Nearest Cities',  resort.pr_nearest_cities],
  ].filter(([, v]) => v)

  return (
    <div>
      {/* Score + ranks */}
      <div style={{ display: 'flex', gap: 24, marginBottom: 16 }}>
        <div>
          <Text type="secondary" style={{ fontSize: 11 }}>Total Score</Text>
          <div>
            <Text style={{ fontSize: 22, fontWeight: 700 }}>{resort.pr_total}</Text>
            <Text type="secondary" style={{ fontSize: 11 }}> / 100</Text>
          </div>
        </div>
        {resort.pr_overall_rank != null && (
          <div>
            <Text type="secondary" style={{ fontSize: 11 }}>Overall Rank</Text>
            <div><Text style={{ fontSize: 22, fontWeight: 700 }}>#{resort.pr_overall_rank}</Text></div>
          </div>
        )}
        {resort.pr_regional_rank != null && (
          <div>
            <Text type="secondary" style={{ fontSize: 11 }}>
              {resort.pr_region ? `${resort.pr_region} Rank` : 'Regional Rank'}
            </Text>
            <div><Text style={{ fontSize: 22, fontWeight: 700 }}>#{resort.pr_regional_rank}</Text></div>
          </div>
        )}
      </div>

      {/* 10-category grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '10px 8px', marginBottom: 16 }}>
        {PR_CATEGORIES.map(({ key, label }) => {
          const val = resort[key]
          return (
            <div key={key}>
              <Text type="secondary" style={{ fontSize: 10 }}>{label}</Text>
              <div style={{ fontSize: 16, fontWeight: 600 }}>{val != null ? val : '—'}</div>
              <div style={{ height: 3, borderRadius: 1, background: COLORS.bgLayout, marginTop: 2 }}>
                {val != null && (
                  <div style={{ height: '100%', width: `${(val / 10) * 100}%`, background: COLORS.primary, borderRadius: 1 }} />
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Extras */}
      {extras.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 24px' }}>
          {extras.map(([label, value]) => (
            <div key={label}>
              <Text type="secondary" style={{ fontSize: 11 }}>{label}</Text>
              <div><Text style={{ fontSize: 12 }}>{value}</Text></div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function BlackoutCalendar({ standardJson, lttJson }) {
  const classified = classifyBlackoutDates(standardJson, lttJson)
  const hasAny = classified.size > 0
  const hasLtt = [...classified.values()].some(v => v === 'ltt' || v === 'both')
  const [displayMonth, setDisplayMonth] = useState(sharedCalendarMonth)
  const today = useRef(dayjs())

  function setMonth(m) {
    sharedCalendarMonth = m
    setDisplayMonth(m)
  }

  if (!hasAny) return <Text type="secondary">No blackout dates.</Text>

  const yearOptions = Array.from({ length: 3 }, (_, i) => dayjs().year() - 1 + i)
    .map(y => ({ value: y, label: String(y) }))
  const monthOptions = [
    'Jan','Feb','Mar','Apr','May','Jun',
    'Jul','Aug','Sep','Oct','Nov','Dec',
  ].map((label, i) => ({ value: i, label }))

  function headerRender({ value }) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '4px 8px 8px' }}>
        <Space size={0}>
          <Button type="text" size="small" onClick={() => setMonth(value.subtract(1, 'month'))}>‹</Button>
          <Button type="text" size="small" onClick={() => setMonth(value.add(1, 'month'))}>›</Button>
        </Space>
        <Space size={4}>
          <Select
            size="small"
            value={value.year()}
            options={yearOptions}
            onChange={y => setMonth(value.year(y))}
            style={{ width: 80 }}
          />
          <Select
            size="small"
            value={value.month()}
            options={monthOptions}
            onChange={m => setMonth(value.month(m))}
            style={{ width: 70 }}
          />
        </Space>
      </div>
    )
  }

  function fullCellRender(current, info) {
    if (info.type !== 'date') return info.originNode
    const key = current.format('YYYY-MM-DD')
    const type = classified.get(key)
    const isToday = current.isSame(today.current, 'day')
    const inMonth = current.month() === displayMonth.month()

    const bg = type === 'both'
      ? `linear-gradient(135deg, ${COLORS.error} 50%, ${COLORS.primary} 50%)`
      : type ? BLACKOUT_COLORS[type] : 'transparent'

    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', opacity: inMonth ? 1 : 0.1 }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: 28,
          height: 28,
          borderRadius: '50%',
          background: bg,
          border: isToday ? `2px solid ${COLORS.text}` : 'none',
          color: type ? BLACKOUT_TEXT[type] : COLORS.text,
          fontSize: 14,
          fontFamily: 'inherit',
          lineHeight: 1,
          boxSizing: 'border-box',
        }}>
          {current.date()}
        </div>
      </div>
    )
  }

  return (
    <div>
      <Calendar
        fullscreen={false}
        mode="month"
        value={displayMonth}
        headerRender={headerRender}
        fullCellRender={fullCellRender}
        onPanelChange={val => setMonth(val)}
        onChange={val => setMonth(val)}
      />
      <Space style={{ marginTop: 8 }} size="middle">
        <Space size={6}>
          <span style={{ display: 'inline-block', width: 12, height: 12, borderRadius: '50%', background: COLORS.error }} />
          <Text style={{ fontSize: 11 }}>Standard</Text>
        </Space>
        {hasLtt && (
          <>
            <Space size={6}>
              <span style={{ display: 'inline-block', width: 12, height: 12, borderRadius: '50%', background: COLORS.primary }} />
              <Text style={{ fontSize: 11 }}>LTT</Text>
            </Space>
            <Space size={6}>
              <span style={{ display: 'inline-block', width: 12, height: 12, borderRadius: '50%', background: `linear-gradient(135deg, ${COLORS.error} 50%, ${COLORS.primary} 50%)` }} />
              <Text style={{ fontSize: 11 }}>Both</Text>
            </Space>
          </>
        )}
      </Space>
    </div>
  )
}

export default function ResortDetailModal({ resortId, onClose }) {
  const [resort, setResort] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!resortId) return
    setLoading(true)
    setResort(null)
    fetchResort(resortId)
      .then(setResort)
      .finally(() => setLoading(false))
  }, [resortId])

  const location = resort
    ? [resort.city, resort.state, resort.country].filter(Boolean).join(', ')
    : null

  const hasCharts = resort && (
    (resort.vertical_base_ft != null && resort.vertical_summit_ft != null) ||
    (resort.difficulty_beginner != null || resort.difficulty_intermediate != null || resort.difficulty_advanced != null) ||
    (resort.snowfall_average_in != null || resort.snowfall_high_in != null)
  )

  return (
    <Modal
      open={!!resortId}
      onCancel={onClose}
      footer={null}
      width={640}
      destroyOnHidden
      title={null}
      styles={{ body: { maxHeight: '85vh', overflowY: 'auto' } }}
    >
      {loading && <Skeleton active paragraph={{ rows: 8 }} />}

      {!loading && resort && (
        <>
          {/* Header */}
          <Title level={4} style={{ marginBottom: 2 }}>{resort.name}</Title>
          {location && <Text type="secondary">{location}</Text>}
          <div style={{ marginTop: 10 }}>
            <Space size="middle" wrap>
              <Link href={resort.indy_page} target="_blank">Indy Pass ↗</Link>
              {resort.website && <Link href={resort.website} target="_blank">Website ↗</Link>}
              {resort.reservation_url && <Link href={resort.reservation_url} target="_blank">Reservations ↗</Link>}
            </Space>
          </div>

          <Divider />

          {/* Features */}
          <Text strong>Features</Text>
          <div style={{ marginTop: 8 }}>
            <Space size={[8, 8]} wrap>
              {FEATURES.map(({ key, label }) => {
                const active = resort[key] === true
                const unknown = resort[key] == null
                return (
                  <Tag
                    key={key}
                    color={active ? 'success' : undefined}
                    style={{ opacity: unknown ? 0.4 : 1 }}
                  >
                    {label}
                  </Tag>
                )
              })}
            </Space>
          </div>

          <Divider />

          {/* Size */}
          <Text strong>Size</Text>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 24px', marginTop: 8 }}>
            {[
              ['Vertical',     fmt(resort.vertical,        'ft')],
              ['Acreage',      fmt(resort.acres,           'ac')],
              ['Trails',       fmt(resort.num_trails)],
              ['Lifts',        fmt(resort.num_lifts)],
              ['Trail length', fmt(resort.trail_length_mi, 'mi')],
            ].map(([label, value]) => (
              <div key={label}>
                <Text type="secondary" style={{ fontSize: 11 }}>{label}</Text>
                <div><Text>{value}</Text></div>
              </div>
            ))}
          </div>

          {hasCharts && (
            <>
              <Divider />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 32px', alignItems: 'start' }}>
                <ElevationStats base={resort.vertical_base_ft} summit={resort.vertical_summit_ft} />
                <DifficultyChart
                  beginner={resort.difficulty_beginner}
                  intermediate={resort.difficulty_intermediate}
                  advanced={resort.difficulty_advanced}
                />
              </div>
              {(resort.snowfall_average_in != null || resort.snowfall_high_in != null) && (
                <div style={{ marginTop: 16, maxWidth: 200 }}>
                  <SnowfallChart avg={resort.snowfall_average_in} high={resort.snowfall_high_in} />
                </div>
              )}
            </>
          )}

          <Divider />

          {/* Blackout Dates */}
          <Text strong>Blackout Dates</Text>
          <div style={{ marginTop: 8 }}>
            <BlackoutCalendar
              standardJson={resort.blackout_all_dates}
              lttJson={resort.ltt_blackout_all_dates}
            />
          </div>

          <Divider />

          {/* Peak Rankings */}
          <Text strong>Peak Rankings</Text>
          <div style={{ marginTop: 8 }}>
            <PeakRankings resort={resort} />
          </div>
        </>
      )}
    </Modal>
  )
}
