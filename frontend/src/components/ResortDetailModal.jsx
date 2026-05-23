import { useEffect, useRef, useState } from 'react'
import dayjs from 'dayjs'

// Persists the user's last-viewed month across modal opens
let sharedCalendarMonth = dayjs()
import { Button, Calendar, Divider, Modal, Select, Skeleton, Space, Tag, Typography } from 'antd'
import { fetchResort } from '@/api/resorts'
import { classifyBlackoutDates } from '@/utils/blackout'
import { COLORS } from '@/theme'

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

function fmt(value, unit) {
  if (value == null) return '—'
  return unit ? `${value.toLocaleString()} ${unit}` : value.toLocaleString()
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

  return (
    <Modal
      open={!!resortId}
      onCancel={onClose}
      footer={null}
      width={600}
      destroyOnClose
      title={null}
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
              ['Vertical',     fmt(resort.vertical,       'ft')],
              ['Acreage',      fmt(resort.acres,          'ac')],
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

          <Divider />

          {/* Blackout Dates */}
          <Text strong>Blackout Dates</Text>
          <div style={{ marginTop: 8 }}>
            <BlackoutCalendar
              standardJson={resort.blackout_all_dates}
              lttJson={resort.ltt_blackout_all_dates}
            />
          </div>
        </>
      )}
    </Modal>
  )
}
