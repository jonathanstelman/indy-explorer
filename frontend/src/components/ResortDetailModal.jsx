import { useEffect, useRef, useState } from 'react'
import dayjs from 'dayjs'
import {
  Bar, BarChart, Cell, Pie, PieChart,
  ResponsiveContainer, XAxis,
} from 'recharts'
import { Button, Calendar, Divider, Modal, Select, Skeleton, Space, Typography } from 'antd'
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
  Beginner:     COLORS.success,     // chartreuse — green circle trail marker
  Intermediate: COLORS.accentBlue,  // electric blue — blue square trail marker
  Advanced:     COLORS.neutral,     // medium grey — black diamond trail marker
}

function prBarColor(val) {
  if (val > 8)  return COLORS.prTop
  if (val >= 7) return COLORS.primary
  if (val >= 5) return COLORS.prMid
  if (val >= 3) return COLORS.warning
  return COLORS.error
}

function SectionHeader({ children, color }) {
  return (
    <div style={{ borderLeft: `3px solid ${color}`, paddingLeft: 8, marginBottom: 8 }}>
      <Text strong>{children}</Text>
    </div>
  )
}

function fmt(value, unit) {
  if (value == null) return '—'
  return unit ? `${value.toLocaleString()} ${unit}` : value.toLocaleString()
}

function DifficultyChart({ beginner, intermediate, advanced, isMobile }) {
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
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'auto auto', columnGap: 8, rowGap: 4, flexShrink: 0 }}>
          {data.flatMap(d => [
            <span key={`${d.name}-l`} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: DIFFICULTY_COLORS[d.name], flexShrink: 0 }} />
              <Text type="secondary" style={{ fontSize: 12 }}>{d.name}</Text>
            </span>,
            <Text key={`${d.name}-v`} strong style={{ fontSize: 12 }}>{d.value}%</Text>,
          ])}
        </div>
        {!isMobile && (
          <ResponsiveContainer width="100%" height={70}>
            <PieChart>
              <Pie data={data} dataKey="value" cx="50%" cy="50%" outerRadius={30} isAnimationActive={false}>
                {data.map(entry => <Cell key={entry.name} fill={DIFFICULTY_COLORS[entry.name]} />)}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        )}
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
    <div style={{ maxWidth: 210 }}>
      <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>Snowfall (in)</Text>
      <ResponsiveContainer width="100%" height={90}>
        <BarChart data={data} margin={{ top: 16, right: 0, bottom: 0, left: -10 }}>
          <XAxis dataKey="label" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
          <Bar dataKey="inches" fill={COLORS.primary} isAnimationActive={false}
            label={{ position: 'top', fontSize: 11 }} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

function PeakRankings({ resort, isMobile }) {
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
      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? 'repeat(4, 1fr)' : 'repeat(5, 1fr)', gap: '10px 8px', marginBottom: 16 }}>
        {PR_CATEGORIES.map(({ key, label }) => {
          const val = resort[key]
          return (
            <div key={key}>
              <Text type="secondary" style={{ fontSize: 10 }}>{label}</Text>
              <div style={{ fontSize: 16, fontWeight: 600 }}>{val != null ? val : '—'}</div>
              <div style={{ height: 3, borderRadius: 1, background: COLORS.bgLayout, marginTop: 2 }}>
                {val != null && (
                  <div style={{ height: '100%', width: `${(val / 10) * 100}%`, background: prBarColor(val), borderRadius: 1 }} />
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

export default function ResortDetailModal({ resortId, onClose, isMobile = false }) {
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
          <SectionHeader color={COLORS.primary}>Features</SectionHeader>
          {isMobile ? (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 8px', marginTop: 8 }}>
              {FEATURES.map(({ key, label }) => {
                const val = resort[key]
                return (
                  <div key={key} style={{ display: 'flex', gap: 4, alignItems: 'baseline' }}>
                    <Text style={{ fontSize: 12 }}>{label}:</Text>
                    <Text style={{ fontSize: 12, fontWeight: 700, color: val === true ? COLORS.error : COLORS.textMuted }}>
                      {val === true ? 'Yes' : val === false ? 'No' : '—'}
                    </Text>
                  </div>
                )
              })}
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'auto auto 1fr auto auto 1fr auto auto', gap: '4px 4px', alignItems: 'baseline', marginTop: 8 }}>
              {[FEATURES.slice(0, 3), FEATURES.slice(3)].flatMap((row, rowIdx) =>
                row.flatMap(({ key, label }, colIdx) => {
                  const val = resort[key]
                  const cells = [
                    <Text key={`${key}-l`} style={{ fontSize: 12 }}>{label}:</Text>,
                    <Text key={`${key}-v`} style={{ fontSize: 12, fontWeight: 700, color: val === true ? COLORS.error : COLORS.textMuted, paddingRight: 4 }}>
                      {val === true ? 'Yes' : val === false ? 'No' : '—'}
                    </Text>,
                  ]
                  if (colIdx < 2) cells.push(<div key={`sp-${rowIdx}-${colIdx}`} />)
                  return cells
                })
              )}
            </div>
          )}

          <Divider />

          {/* Size */}
          <SectionHeader color={COLORS.accentBlue}>Size</SectionHeader>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', columnGap: 24, marginTop: 8 }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {[
                ['Lifts',             fmt(resort.num_lifts)],
                ['Trails',            fmt(resort.num_trails)],
                ['Trail length (mi)', fmt(resort.trail_length_mi)],
                ['Acreage (ac)',      fmt(resort.acres)],
              ].map(([label, value]) => (
                <div key={label}>
                  <Text type="secondary" style={{ fontSize: 11 }}>{label}</Text>
                  <div><Text>{value}</Text></div>
                </div>
              ))}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {[
                ['Summit (ft)',   fmt(resort.vertical_summit_ft)],
                ['Vertical (ft)', fmt(resort.vertical)],
                ['Base (ft)',     fmt(resort.vertical_base_ft)],
              ].map(([label, value]) => (
                <div key={label}>
                  <Text type="secondary" style={{ fontSize: 11 }}>{label}</Text>
                  <div><Text>{value}</Text></div>
                </div>
              ))}
            </div>
          </div>

          {hasCharts && (
            <>
              <Divider />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 32px', alignItems: 'start' }}>
                <DifficultyChart
                  beginner={resort.difficulty_beginner}
                  intermediate={resort.difficulty_intermediate}
                  advanced={resort.difficulty_advanced}
                  isMobile={isMobile}
                />
                <SnowfallChart avg={resort.snowfall_average_in} high={resort.snowfall_high_in} />
              </div>
            </>
          )}

          <Divider />

          {/* Blackout Dates */}
          <SectionHeader color={COLORS.error}>Blackout Dates</SectionHeader>
          <div style={{ marginTop: 8 }}>
            <BlackoutCalendar
              standardJson={resort.blackout_all_dates}
              lttJson={resort.ltt_blackout_all_dates}
            />
          </div>

          <Divider />

          {/* Peak Rankings */}
          <SectionHeader color={COLORS.success}>Peak Rankings</SectionHeader>
          <div style={{ marginTop: 8 }}>
            <PeakRankings resort={resort} isMobile={isMobile} />
          </div>
        </>
      )}
    </Modal>
  )
}
