import { useState, useEffect, useRef } from 'react'
import DeckGL from '@deck.gl/react'
import { MapView, WebMercatorViewport, FlyToInterpolator } from '@deck.gl/core'
import { ScatterplotLayer } from '@deck.gl/layers'
import Map from 'react-map-gl/mapbox'
import 'mapbox-gl/dist/mapbox-gl.css'
import { useFilters } from '@/hooks/useFilters'
import { COLORS, FONTS, MAP_DOT_COLORS } from '@/theme'

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN

const INITIAL_VIEW_STATE = {
  latitude: 44,
  longitude: -95,
  zoom: 3,
  pitch: 0,
  bearing: 0,
}

const MAX_AUTO_ZOOM = 8.0

const REGION_ZOOM = {
  Midwest: 4.8,
  East: 5.7,
  Japan: 4.4,
  'Mid-Atlantic': 5.2,
  Europe: 3.6,
  Canada: 3.7,
  West: 4.3,
  Rockies: 4.4,
}

const COUNTRY_ZOOM = {
  Austria: 5.6,
  Canada: 3.7,
  Chile: 3.5,
  Czechia: 5.2,
  Finland: 4.2,
  Italy: 5.0,
  Japan: 4.6,
  Norway: 4.2,
  Slovenia: 5.6,
  Spain: 4.8,
  Sweden: 4.2,
  Switzerland: 5.3,
  'Türkiye': 4.2,
  'United Kingdom': 4.0,
  'United States': 3.3,
}

const MIN_RADIUS = 5000
const MAX_RADIUS = 50000

const LEGEND_ITEMS = [
  { color: MAP_DOT_COLORS.alpine, label: 'Alpine' },
  { color: MAP_DOT_COLORS.xc,     label: 'Cross-country' },
  { color: MAP_DOT_COLORS.both,   label: 'Alpine + XC' },
  { color: MAP_DOT_COLORS.allied, label: 'Allied resort' },
]

function getDotColor(r) {
  if (r.is_allied) return MAP_DOT_COLORS.allied
  if (r.has_cross_country && !r.has_alpine) return MAP_DOT_COLORS.xc
  if (r.has_alpine && r.has_cross_country) return MAP_DOT_COLORS.both
  return MAP_DOT_COLORS.alpine
}

function getDotRadius(r) {
  if (r.has_cross_country && !r.has_alpine) return MIN_RADIUS
  let radius
  if (r.acres) {
    radius = r.acres * 30
  } else {
    const trails = r.num_trails ?? 5
    const vertical = r.vertical ?? 300
    const lifts = r.num_lifts ?? 0
    radius = 2 * (50 * trails + 1.5 * vertical + 5 * lifts)
  }
  return Math.min(MAX_RADIUS, Math.max(MIN_RADIUS, radius))
}

function fitViewToResorts(resorts, width, height, filters) {
  if (!resorts.length) return { ...INITIAL_VIEW_STATE, transitionDuration: 800, transitionInterpolator: new FlyToInterpolator() }

  const lngs = resorts.map(r => r.longitude)
  const lats = resorts.map(r => r.latitude)
  const minLng = Math.min(...lngs)
  const maxLng = Math.max(...lngs)
  const minLat = Math.min(...lats)
  const maxLat = Math.max(...lats)

  const viewport = new WebMercatorViewport({ width: width || 800, height: height || 600 })
  const { longitude, latitude, zoom } = viewport.fitBounds(
    [[minLng, minLat], [maxLng, maxLat]],
    { padding: 60 }
  )

  let finalZoom = Math.min(zoom, MAX_AUTO_ZOOM)

  // Apply single-selection zoom overrides, matching Streamlit priority: state > country > region
  const { region, country, state } = filters
  if (state.length === 1) {
    // state zoom handled by fitBounds — just cap it
  } else if (country.length === 1) {
    finalZoom = COUNTRY_ZOOM[country[0]] ?? finalZoom
  } else if (region.length === 1) {
    finalZoom = REGION_ZOOM[region[0]] ?? finalZoom
  }

  return {
    longitude,
    latitude,
    zoom: finalZoom,
    pitch: 0,
    bearing: 0,
    transitionDuration: 800,
    transitionInterpolator: new FlyToInterpolator(),
  }
}

function MapTooltip({ info }) {
  const { resort: r, x, y, flipX, flipY } = info
  const location = [r.city, r.state, r.country].filter(Boolean).join(', ')
  const rows = [
    ['Resort',         r.name],
    ['Location',       location || '—'],
    ['Acres',          r.acres != null ? r.acres.toLocaleString() : '—'],
    ['Vertical',       r.vertical != null ? `${r.vertical.toLocaleString()} ft` : '—'],
    ['Trails',         r.num_trails != null ? r.num_trails : '—'],
    ['Lifts',          r.num_lifts != null ? r.num_lifts : '—'],
    ['Alpine',         yesNo(r.has_alpine)],
    ['Cross-country',  yesNo(r.has_cross_country)],
    ['Night skiing',   yesNo(r.has_night_skiing)],
    ['Terrain parks',  yesNo(r.has_terrain_parks)],
    ['Dog friendly',   yesNo(r.is_dog_friendly)],
    ['Reservations',   r.reservation_status ?? '—'],
    ['Blackout dates', r.blackout_count > 0 ? 'Yes' : 'No'],
    ['Peak score',     r.pr_total != null ? r.pr_total : '—'],
  ]
  return (
    <div style={{
      position: 'absolute',
      pointerEvents: 'none',
      zIndex: 1,
      ...(flipX ? { right: `calc(100% - ${x - 8}px)` } : { left: x + 8 }),
      ...(flipY ? { bottom: `calc(100% - ${y - 8}px)` } : { top: y + 8 }),
      backgroundColor: COLORS.bgBase,
      color: COLORS.text,
      border: `1px solid ${COLORS.border}`,
      borderRadius: 4,
      padding: '10px 12px',
      boxShadow: `0 2px 8px ${COLORS.shadow}`,
      fontSize: 12,
      fontFamily: FONTS.mono,
      whiteSpace: 'nowrap',
    }}>
      <table style={{ borderCollapse: 'collapse' }}>
        <tbody>
          {rows.map(([label, value]) => (
            <tr key={label}>
              <td style={{ padding: '2px 8px 2px 0', color: COLORS.textMuted }}>{label}</td>
              <td style={{ padding: '2px 0', fontWeight: 500 }}>{value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function MapAttribution() {
  const [expanded, setExpanded] = useState(false)
  return (
    <div style={{ position: 'absolute', top: 8, right: 8, zIndex: 10, fontFamily: FONTS.mono, fontSize: 11 }}>
      {expanded ? (
        <div style={{ background: 'rgba(255,255,255,0.9)', padding: '4px 8px', borderRadius: 2, display: 'flex', gap: 6, alignItems: 'center', whiteSpace: 'nowrap', boxShadow: `0 1px 4px ${COLORS.shadow}` }}>
          <a href="https://www.mapbox.com/about/maps/" target="_blank" rel="noreferrer" style={{ color: COLORS.text }}>© Mapbox</a>
          <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer" style={{ color: COLORS.text }}>© OpenStreetMap</a>
          <a href="https://www.mapbox.com/map-feedback/" target="_blank" rel="noreferrer" style={{ color: COLORS.text }}>Improve this map</a>
          <button onClick={() => setExpanded(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '0 0 0 4px', color: COLORS.textMuted, fontSize: 13, lineHeight: 1 }}>✕</button>
        </div>
      ) : (
        <button
          onClick={() => setExpanded(true)}
          style={{ width: 20, height: 20, borderRadius: '50%', background: 'rgba(255,255,255,0.9)', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, color: COLORS.text, boxShadow: `0 1px 4px ${COLORS.shadow}` }}
        >
          ⓘ
        </button>
      )}
    </div>
  )
}

function MapLegend() {
  return (
    <div
      style={{
        position: 'absolute',
        bottom: 32,
        left: 16,
        background: COLORS.bgBase,
        border: `2px solid ${COLORS.bgHeader}`,
        borderRadius: 4,
        padding: '8px 12px',
        display: 'flex',
        flexDirection: 'column',
        gap: 6,
        pointerEvents: 'none',
      }}
    >
      {LEGEND_ITEMS.map(({ color, label }) => (
        <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              background: `rgba(${color[0]},${color[1]},${color[2]},${(color[3] / 255).toFixed(2)})`,
              flexShrink: 0,
            }}
          />
          <span style={{ color: COLORS.text, fontSize: 11, fontFamily: FONTS.mono }}>
            {label}
          </span>
        </div>
      ))}
    </div>
  )
}

function yesNo(val) {
  if (val === true) return 'Yes'
  if (val === false) return 'No'
  return '—'
}


export default function ResortMap({ resorts = [], onResortClick }) {
  const containerRef = useRef()
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE)
  const [tooltipInfo, setTooltipInfo] = useState(null)
  const { filters } = useFilters()


  // Track the location key we last zoomed to — only re-fit when location filters actually change
  const lastZoomedLocationKey = useRef(null)

  const validResorts = resorts
    .filter(r => r.latitude && r.longitude)
    .sort((a, b) => getDotRadius(b) - getDotRadius(a))

  // Fire when resorts updates (i.e. after the API responds), not when filters change.
  // This ensures we zoom to the correct resort set, not the stale one from the previous render.
  useEffect(() => {
    const locationKey = JSON.stringify([filters.region, filters.country, filters.state])
    if (locationKey === lastZoomedLocationKey.current) return
    lastZoomedLocationKey.current = locationKey

    const el = containerRef.current
    const { width, height } = el ? el.getBoundingClientRect() : {}
    setViewState(fitViewToResorts(validResorts, width, height, filters))
  }, [resorts])

  const layer = new ScatterplotLayer({
    id: 'resorts',
    data: validResorts,
    pickable: true,
    autoHighlight: true,
    highlightColor: [255, 255, 255, 120],
    getPosition: r => [r.longitude, r.latitude],
    getRadius: getDotRadius,
    getFillColor: getDotColor,
    radiusUnits: 'meters',
    onClick: ({ object }) => onResortClick?.(object),
    onHover: ({ object, x, y }) => {
      if (!object) { setTooltipInfo(null); return }
      const { width, height } = containerRef.current?.getBoundingClientRect() ?? {}
      setTooltipInfo({ resort: object, x, y, flipX: x > width / 2, flipY: y > height / 2 })
    },
  })

  return (
    <div ref={containerRef} style={{ position: 'relative', width: '100%', height: '100%' }}>
      <DeckGL
        views={new MapView({ repeat: true })}
        viewState={viewState}
        onViewStateChange={({ viewState: vs }) => setViewState(vs)}
        controller
        layers={[layer]}
        style={{ width: '100%', height: '100%' }}
      >
        <Map
          mapStyle="mapbox://styles/mapbox/light-v11"
          mapboxAccessToken={MAPBOX_TOKEN}
          projection="mercator"
          attributionControl={false}
        />
      </DeckGL>
      <MapAttribution />
      <MapLegend />
      {tooltipInfo && <MapTooltip info={tooltipInfo} />}
    </div>
  )
}
