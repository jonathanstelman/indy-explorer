import { useState, useEffect, useRef } from 'react'
import DeckGL from '@deck.gl/react'
import { MapView, WebMercatorViewport, FlyToInterpolator } from '@deck.gl/core'
import { ScatterplotLayer } from '@deck.gl/layers'
import Map from 'react-map-gl/mapbox'
import 'mapbox-gl/dist/mapbox-gl.css'
import { useFilters } from '@/hooks/useFilters'
import { COLORS, FONTS, MAP_DOT_COLORS } from '@/theme'
import { formatVertical, formatAcres } from '@/utils/units'
import Panel from '@/components/common/Panel'

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN

// Row count varies per resort (Acreage/Lifts hidden for XC-only resorts, Trails (XC) shown
// only for alpine+XC resorts) — buildTooltipRows() is the single source of truth for which
// rows appear, used both to render the tooltip and to compute its height for clamping it
// within its container instead of letting it overflow and get clipped by Layout.Content's
// `overflow: hidden` when the map area is short.
const TOOLTIP_WIDTH = 260
const TOOLTIP_CHROME_HEIGHT = 20 // Panel's 10px top + 10px bottom padding
const TOOLTIP_ROW_HEIGHT = 25

function buildTooltipRows(r, unit) {
  const locationParts = r.country === 'United States'
    ? [r.city, r.state]
    : [r.city, r.state, r.country]
  const location = locationParts.filter(Boolean).join(', ')
  return [
    ['Resort',   r.name],
    ['Location', location || '—'],
    ['Vertical', formatVertical(r.vertical, unit)],
    // Alpine-only stats — no XC-only resort has acreage or lift data.
    ...(r.acres != null ? [['Acreage', formatAcres(r.acres, unit)]] : []),
    ...(r.num_lifts != null ? [['Lifts', r.num_lifts]] : []),
    ['Trails',   r.num_trails != null ? r.num_trails : '—'],
    // Per-resort presence check, not a global toggle — same pattern as the detail modal.
    // Suppressed for XC-only resorts: num_trails (from the main listing page) and
    // num_trails_xc (from the detail page's XC field) are always identical there, since
    // both describe the resort's one and only trail network — showing both reads as a
    // duplication bug rather than two independently-sourced confirmations of one number.
    ...(r.num_trails_xc != null && r.has_alpine ? [['Trails (XC)', r.num_trails_xc]] : []),
  ]
}

function tooltipHeight(rowCount) {
  return TOOLTIP_CHROME_HEIGHT + rowCount * TOOLTIP_ROW_HEIGHT
}

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

const MAP_OVERLAY_BTN = {
  width: 24,
  height: 24,
  borderRadius: '50%',
  background: COLORS.bgLayout,
  border: `1px solid ${COLORS.text}`,
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  pointerEvents: 'auto',
}

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

function MapTooltip({ info, unit }) {
  const { resort: r, left, top } = info
  const rows = buildTooltipRows(r, unit)
  return (
    <Panel style={{
      position: 'absolute',
      pointerEvents: 'none',
      zIndex: 1,
      left,
      top,
      color: COLORS.text,
      padding: '10px 12px',
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
    </Panel>
  )
}


function MapLegend() {
  const [open, setOpen] = useState(true)

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        style={{ position: 'absolute', top: 8, left: 8, ...MAP_OVERLAY_BTN }}
      >
        <svg viewBox="0 0 24 24" width="14" height="14" fill={COLORS.text}>
          <path d="M4 10.5c-.83 0-1.5.67-1.5 1.5s.67 1.5 1.5 1.5 1.5-.67 1.5-1.5-.67-1.5-1.5-1.5zm0-6c-.83 0-1.5.67-1.5 1.5S3.17 7.5 4 7.5 5.5 6.83 5.5 6 4.83 4.5 4 4.5zm0 12c-.83 0-1.5.68-1.5 1.5s.68 1.5 1.5 1.5 1.5-.68 1.5-1.5-.67-1.5-1.5-1.5zM7 19h14v-2H7v2zm0-6h14v-2H7v2zm0-8v2h14V5H7z" />
        </svg>
      </button>
    )
  }

  return (
    <Panel
      onClose={() => setOpen(false)}
      style={{
        position: 'absolute',
        top: 8,
        left: 8,
        maxHeight: 'calc(100% - 16px)',
        overflowY: 'auto',
        padding: '8px 12px 8px 12px',
        display: 'flex',
        flexDirection: 'column',
        gap: 6,
        pointerEvents: 'auto',
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
    </Panel>
  )
}



function MapAttribution() {
  const [open, setOpen] = useState(false)
  if (open) {
    return (
      <Panel
        onClose={() => setOpen(false)}
        style={{
          position: 'absolute',
          top: 8,
          right: 8,
          maxHeight: 'calc(100% - 16px)',
          overflowY: 'auto',
          padding: '8px 12px',
          display: 'flex',
          flexDirection: 'column',
          gap: 6,
          pointerEvents: 'auto',
        }}
      >
        {[
          { href: 'https://www.mapbox.com/about/maps/', label: '© Mapbox' },
          { href: 'https://www.openstreetmap.org/copyright', label: '© OpenStreetMap' },
          { href: 'https://www.mapbox.com/map-feedback/', label: 'Improve this map' },
        ].map(({ href, label }) => (
          <a key={href} href={href} target="_blank" rel="noreferrer"
            style={{ color: COLORS.text, fontSize: 11, fontFamily: FONTS.mono, textDecoration: 'none' }}
          >
            {label}
          </a>
        ))}
      </Panel>
    )
  }

  return (
    <button
      onClick={() => setOpen(true)}
      style={{ position: 'absolute', top: 8, right: 8, ...MAP_OVERLAY_BTN, color: COLORS.text, fontSize: 13, fontStyle: 'italic', fontFamily: 'serif', lineHeight: 1 }}
    >
      i
    </button>
  )
}

export default function ResortMap({ resorts = [], onResortClick, unit = 'imperial', isMobile }) {
  const containerRef = useRef()
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE)
  const [tooltipInfo, setTooltipInfo] = useState(null)
  const [containerSize, setContainerSize] = useState({ width: 0, height: 0 })
  const { filters } = useFilters()


  // Track the location key we last zoomed to — only re-fit when location filters actually change
  const lastZoomedLocationKey = useRef(null)

  // Tracked in state (rather than read from containerRef during the onHover callback below)
  // since ref values can't be read while constructing the layer during render.
  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const observer = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect
      setContainerSize({ width, height })
    })
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  const validResorts = resorts
    .filter(r => r.latitude && r.longitude)
    .sort((a, b) => getDotRadius(b) - getDotRadius(a))

  // Fire when resorts updates (i.e. after the API responds), not when filters change.
  // This ensures we zoom to the correct resort set, not the stale one from the previous render.
  useEffect(() => {
    const locationKey = JSON.stringify([filters.region, filters.country, filters.state])
    if (locationKey === lastZoomedLocationKey.current) return
    lastZoomedLocationKey.current = locationKey

    ;(() => {
      const el = containerRef.current
      const { width, height } = el ? el.getBoundingClientRect() : {}
      setViewState(fitViewToResorts(validResorts, width, height, filters))
    })()
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
      const { width, height } = containerSize
      const th = tooltipHeight(buildTooltipRows(object, unit).length)
      const left = x > width / 2
        ? Math.max(4, x - 8 - TOOLTIP_WIDTH)
        : Math.max(4, Math.min(x + 8, width - TOOLTIP_WIDTH - 4))
      const top = y > height / 2
        ? Math.max(4, y - 8 - th)
        : Math.max(4, Math.min(y + 8, height - th - 4))
      setTooltipInfo({ resort: object, left, top })
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
      <MapLegend />
      {!isMobile && <MapAttribution />}
      {tooltipInfo && <MapTooltip info={tooltipInfo} unit={unit} />}
    </div>
  )
}
