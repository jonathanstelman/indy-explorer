import { useEffect, useMemo, useRef, useState } from 'react'
import { Button, Checkbox, ConfigProvider, Layout } from 'antd'
import { useSearchParams } from 'react-router-dom'
import { useFilters } from '@/hooks/useFilters'
import { useUnits } from '@/hooks/useUnits'
import { fetchResorts, fetchMeta } from '@/api/resorts'
import AppHeader from '@/components/layout/Header'
import AppSidebar from '@/components/layout/Sidebar'
import AppFooter from '@/components/layout/Footer'
import ResortToolbar from '@/components/ResortToolbar'
import ResortMap from '@/components/ResortMap'
import ResortTable, { COLUMN_DEFS, HEADER_BY_FIELD, COL_GROUPS } from '@/components/ResortTable'
import ResortDetailModal from '@/components/ResortDetailModal'
import HowToUseModal from '@/components/HowToUseModal'
import Panel from '@/components/common/Panel'
import Overlay, { PANEL_Z_INDEX } from '@/components/common/Overlay'
import ModalHeader from '@/components/common/ModalHeader'
import { themeConfig, COLORS, FONTS, withAlpha } from '@/theme'

const DEFAULT_TABLE_HEIGHT = 260
const MIN_TABLE_HEIGHT = 100
const MAX_TABLE_HEIGHT_RATIO = 0.7

const TOOLBAR_BTN_STYLE = { color: COLORS.success, '--toolbar-btn-hover-bg': withAlpha(COLORS.success, 0.15) }

export default function App() {
  const [searchParams] = useSearchParams()
  const { filters } = useFilters()
  const { unit } = useUnits()

  const [resorts, setResorts] = useState([])
  const [allResorts, setAllResorts] = useState([])
  const [meta, setMeta] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedResortId, setSelectedResortId] = useState(null)

  const [isMobile, setIsMobile] = useState(() => window.innerWidth < 768)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => window.innerWidth < 768)
  const [sidebarWidth, setSidebarWidth] = useState(280)

  useEffect(() => {
    const handler = () => setIsMobile(window.innerWidth < 768)
    window.addEventListener('resize', handler)
    return () => window.removeEventListener('resize', handler)
  }, [])

  const [tableHeight, setTableHeight] = useState(DEFAULT_TABLE_HEIGHT)
  const [tableCollapsed, setTableCollapsed] = useState(false)
  const [mobileTab, setMobileTab] = useState('map')
  const [infoOpen, setInfoOpen] = useState(false)
  const [howToUseOpen, setHowToUseOpen] = useState(() => !localStorage.getItem('indy-how-to-use-seen'))

  function openHowToUse() { setHowToUseOpen(true) }
  function closeHowToUse() {
    localStorage.setItem('indy-how-to-use-seen', '1')
    setHowToUseOpen(false)
  }

  const tableRef = useRef()
  const [colsOpen,      setColsOpen]      = useState(false)
  const [colVisibility, setColVisibility] = useState(
    () => Object.fromEntries(COLUMN_DEFS.map(c => [c.field, true]))
  )

  // Displayed columns flow declaratively from the user's Select Columns choices — this
  // (rather than imperative tableRef.current?.api.applyColumnState calls) is what keeps
  // visibility correct across grid remounts (e.g. switching mobile tabs or collapsing/
  // expanding the table), since colVisibility is the single source of truth re-applied
  // on every render instead of a one-off imperative call that a remount would lose.
  const columnDefs = useMemo(
    () => COLUMN_DEFS.map(c => ({
      ...c,
      hide: !colVisibility[c.field],
    })),
    [colVisibility]
  )

  // Fetch meta and full unfiltered resort list once on mount
  useEffect(() => {
    fetchMeta()
      .then(setMeta)
      .catch(e => console.error('Failed to load meta:', e))
    fetchResorts({})
      .then(setAllResorts)
      .catch(e => console.error('Failed to load all resorts:', e))
  }, [])

  // Fetch resorts whenever filters change
  useEffect(() => {
    setLoading(true)
    setError(null)
    fetchResorts(filters)
      .then(setResorts)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [searchParams.toString()])

  function onDownloadCsv() {
    tableRef.current?.api.exportDataAsCsv({ fileName: 'indy-resorts.csv' })
  }

  // Visibility flows into the grid declaratively via the memoized columnDefs
  // above — no imperative applyColumnState needed here.
  function toggleColumn(field) {
    setColVisibility(prev => ({ ...prev, [field]: !prev[field] }))
  }

  function toggleGroup(group) {
    const allChecked = group.fields.every(f => colVisibility[f])
    const next = !allChecked
    setColVisibility(prev => ({ ...prev, ...Object.fromEntries(group.fields.map(f => [f, next])) }))
  }

  const colsContent = (
    <div style={{ padding: '4px 0' }}>
      {COL_GROUPS.map(group => {
        const allChecked  = group.fields.every(f => colVisibility[f])
        const someChecked = group.fields.some(f => colVisibility[f])
        return (
          <div key={group.label} style={{ marginBottom: 8 }}>
            <div style={{ padding: '4px 12px 2px' }}>
              <Checkbox
                checked={allChecked}
                indeterminate={someChecked && !allChecked}
                onChange={() => toggleGroup(group)}
                style={{ marginInlineStart: 0 }}
              >
                <span style={{ fontSize: 10, fontWeight: 900, color: COLORS.text, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  {group.label}
                </span>
              </Checkbox>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', padding: '0 12px 0 28px' }}>
              {group.fields.map(field => (
                <Checkbox
                  key={field}
                  checked={colVisibility[field]}
                  onChange={() => toggleColumn(field)}
                  style={{ fontSize: 11, marginInlineStart: 0, padding: '2px 0' }}
                >
                  {HEADER_BY_FIELD[field]}
                </Checkbox>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )

  function columnsPanel(style) {
    return (
      <Panel style={{ ...style, display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: 2 }}>
        <ModalHeader title="Select Columns" titleFontSize={20} onClose={() => setColsOpen(false)} />
        <div style={{ overflowY: 'auto' }}>
          {colsContent}
        </div>
      </Panel>
    )
  }

  const lastUpdated = meta?.last_pipeline_run ? new Date(meta.last_pipeline_run).toLocaleDateString() : '—'
  const attributionContent = (
    <div style={{ fontFamily: FONTS.mono, fontSize: 11, lineHeight: 1.8 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: COLORS.primary, marginBottom: 2 }}>
        <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: COLORS.primary, flexShrink: 0 }} />
        Map Tiles
      </div>
      <ul style={{ margin: '0 0 0 14px', padding: 0 }}>
        <li><a href="https://www.mapbox.com/about/maps/" target="_blank" rel="noreferrer" style={{ color: COLORS.text }}>Mapbox</a></li>
        <li><a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer" style={{ color: COLORS.text }}>OpenStreetMap</a></li>
      </ul>
      <div style={{ marginLeft: 14, fontSize: 10, lineHeight: 2 }}>
        <a href="https://www.mapbox.com/map-feedback/" target="_blank" rel="noreferrer" style={{ color: COLORS.textMuted }}>Improve this map</a>
      </div>
      <div style={{ borderTop: `1px solid ${COLORS.bgHeader}`, margin: '6px 0' }} />
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: COLORS.accentBlue, marginBottom: 2 }}>
        <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: COLORS.accentBlue, flexShrink: 0 }} />
        Data Sources
      </div>
      <ul style={{ margin: '0 0 0 14px', padding: 0 }}>
        <li><a href="https://www.indyskipass.com" target="_blank" rel="noreferrer" style={{ color: COLORS.text }}>Indy Pass</a></li>
        <li><a href="https://peakrankings.com" target="_blank" rel="noreferrer" style={{ color: COLORS.text }}>Peak Rankings</a></li>
        <li><a href="https://developers.google.com/maps/documentation/geocoding" target="_blank" rel="noreferrer" style={{ color: COLORS.text }}>Google Maps</a></li>
      </ul>
      <div style={{ color: COLORS.textMuted, fontSize: 10, lineHeight: 2, textAlign: 'right' }}>Last updated: {lastUpdated}</div>
    </div>
  )

  function startSidebarDrag(e) {
    e.preventDefault()
    const startX = e.clientX
    const startW = sidebarWidth
    function onMove(ev) {
      setSidebarWidth(Math.max(200, Math.min(480, startW + (ev.clientX - startX))))
    }
    function onUp() {
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
  }

  function startDrag(e) {
    e.preventDefault()
    const startY = e.clientY
    const startH = tableHeight

    function onMove(ev) {
      const maxH = window.innerHeight * MAX_TABLE_HEIGHT_RATIO
      setTableHeight(Math.max(MIN_TABLE_HEIGHT, Math.min(maxH, startH + (startY - ev.clientY))))
    }
    function onUp() {
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
  }

  if (isMobile) {
    return (
      <ConfigProvider theme={themeConfig}>
        <Layout style={{ height: '100%' }}>
          <AppHeader sidebarCollapsed={sidebarCollapsed} onToggleSidebar={() => setSidebarCollapsed(c => !c)} onHowToUse={openHowToUse} isMobile />
          <Layout>
            <AppSidebar
              meta={meta}
              allResorts={allResorts}
              collapsed={sidebarCollapsed}
              width={sidebarWidth}
              isMobile={isMobile}
              onClose={() => setSidebarCollapsed(true)}
            />
            <Layout>
              <Layout.Content style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                <div style={{ padding: '4px 12px', borderBottom: `1px solid ${COLORS.bgHeader}`, background: COLORS.bgMidtone, flexShrink: 0 }}>
                  <ResortToolbar count={resorts.length} loading={loading} />
                </div>

                <div style={{ flex: 1, position: 'relative', minHeight: 0, overflow: 'hidden' }}>
                  {mobileTab === 'map' && (
                    <ResortMap
                      resorts={resorts}
                      onResortClick={r => setSelectedResortId(r.resort_id)}
                      unit={unit}
                      isMobile
                    />
                  )}
                  {mobileTab === 'table' && (
                    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                      <div style={{ display: 'flex', gap: 8, padding: '2px 12px', background: COLORS.bgHeader, borderBottom: `1px solid ${COLORS.border}`, flexShrink: 0, justifyContent: 'flex-end' }}>
                        <Button className="toolbar-btn-hover" type="text" size="small" onClick={() => setColsOpen(o => !o)} style={TOOLBAR_BTN_STYLE}>Select Columns</Button>
                        <Button className="toolbar-btn-hover" type="text" size="small" onClick={onDownloadCsv} style={TOOLBAR_BTN_STYLE}>Download CSV</Button>
                      </div>
                      <div style={{ flex: 1, minHeight: 0 }}>
                        <ResortTable
                          ref={tableRef}
                          resorts={resorts}
                          columnDefs={columnDefs}
                          unit={unit}
                          onRowClick={setSelectedResortId}
                        />
                      </div>
                    </div>
                  )}
                </div>

                <div style={{ position: 'relative', flexShrink: 0 }}>
                  {colsOpen && mobileTab === 'table' && columnsPanel({
                    position: 'absolute',
                    bottom: 'calc(100% + 8px)',
                    left: 12,
                    right: 12,
                    maxHeight: 420,
                    zIndex: PANEL_Z_INDEX,
                  })}
                  {infoOpen && (
                    <Panel style={{
                      position: 'absolute',
                      bottom: 'calc(100% + 8px)',
                      right: 8,
                      maxWidth: 'calc(100% - 16px)',
                      padding: '8px 12px',
                      zIndex: PANEL_Z_INDEX,
                    }}>
                      {attributionContent}
                      <div style={{ borderTop: `1px solid ${COLORS.bgHeader}`, marginTop: 6, paddingTop: 6, fontFamily: FONTS.mono, fontSize: 11, lineHeight: 1.8 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: COLORS.error, marginBottom: 2 }}>
                          <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: COLORS.error, flexShrink: 0 }} />
                          Improve this App
                        </div>
                        <ul style={{ margin: '0 0 0 12px', padding: 0 }}>
                          <li><a href="https://github.com/jonathanstelman/indy-explorer/issues/new?labels=bug" target="_blank" rel="noreferrer" style={{ color: COLORS.text }}>Report a bug</a></li>
                          <li><a href="https://github.com/jonathanstelman/indy-explorer/issues/new?labels=enhancement" target="_blank" rel="noreferrer" style={{ color: COLORS.text }}>Suggest a feature</a></li>
                          <li><a href="https://github.com/users/jonathanstelman/projects/2" target="_blank" rel="noreferrer" style={{ color: COLORS.text }}>Project board</a></li>
                        </ul>
                      </div>
                    </Panel>
                  )}
                  <div style={{ display: 'flex', background: COLORS.bgHeader, borderTop: `1px solid ${COLORS.border}` }}>
                    {['map', 'table'].map(tab => (
                      <button
                        key={tab}
                        onClick={() => setMobileTab(tab)}
                        style={{
                          flex: 1,
                          height: 36,
                          background: 'transparent',
                          border: 'none',
                          borderTop: `2px solid ${mobileTab === tab ? COLORS.error : 'transparent'}`,
                          color: mobileTab === tab ? COLORS.error : COLORS.textMuted,
                          fontFamily: FONTS.mono,
                          fontSize: 13,
                          fontWeight: mobileTab === tab ? 700 : 400,
                          cursor: 'pointer',
                          textTransform: 'uppercase',
                          letterSpacing: '0.08em',
                        }}
                      >
                        {tab === 'map' ? 'Map' : 'Table'}
                      </button>
                    ))}
                    <button
                      onClick={() => setInfoOpen(o => !o)}
                      style={{
                        width: 44,
                        height: 36,
                        flexShrink: 0,
                        background: 'transparent',
                        border: 'none',
                        borderTop: `2px solid ${infoOpen ? COLORS.primary : 'transparent'}`,
                        color: infoOpen ? COLORS.primary : COLORS.textMuted,
                        fontSize: 18,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      ⓘ
                    </button>
                  </div>
                </div>
              </Layout.Content>
            </Layout>
          </Layout>
        </Layout>
        {(colsOpen || infoOpen) && (
          <Overlay onDismiss={() => { setColsOpen(false); setInfoOpen(false) }} />
        )}
        <ResortDetailModal
          resortId={selectedResortId}
          onClose={() => setSelectedResortId(null)}
          unit={unit}
          isMobile={isMobile}
        />
        <HowToUseModal open={howToUseOpen} onClose={closeHowToUse} isMobile />
      </ConfigProvider>
    )
  }

  return (
    <ConfigProvider theme={themeConfig}>
      <Layout style={{ height: '100%' }}>
        <AppHeader sidebarCollapsed={sidebarCollapsed} onToggleSidebar={() => setSidebarCollapsed(c => !c)} onHowToUse={openHowToUse} />
        <Layout>
          <AppSidebar
            meta={meta}
            allResorts={allResorts}
            collapsed={sidebarCollapsed}
            width={sidebarWidth}
            isMobile={isMobile}
            onClose={() => setSidebarCollapsed(true)}
          />
          {!isMobile && !sidebarCollapsed && (
            <div
              onMouseDown={startSidebarDrag}
              style={{
                width: 4,
                flexShrink: 0,
                cursor: 'ew-resize',
                background: COLORS.border,
                zIndex: 1,
              }}
            />
          )}
          <Layout>
            <Layout.Content style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              <div style={{ padding: '8px 24px', borderBottom: `1px solid ${COLORS.bgHeader}`, background: COLORS.bgMidtone }}>
                <ResortToolbar count={resorts.length} loading={loading} />
              </div>
              <div style={{ flex: 1, position: 'relative', minHeight: 0, overflow: 'hidden' }}>
                <ResortMap
                  resorts={resorts}
                  onResortClick={r => setSelectedResortId(r.resort_id)}
                  unit={unit}
                />
              </div>

              {/* Table panel */}
              <div style={{ flexShrink: 0 }}>
                {/* Drag handle */}
                <div
                  onMouseDown={tableCollapsed ? undefined : startDrag}
                  style={{
                    minHeight: 28,
                    background: COLORS.bgHeader,
                    borderTop: `1px solid ${COLORS.bgHeader}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    rowGap: 4,
                    padding: '4px 16px',
                    cursor: tableCollapsed ? 'default' : 'ns-resize',
                    userSelect: 'none',
                  }}
                >
                  <Button
                    type="primary"
                    danger
                    size="small"
                    onMouseDown={e => e.stopPropagation()}
                    onClick={() => setTableCollapsed(c => !c)}
                  >
                    {tableCollapsed ? '▲ Expand data table' : '▼ Hide data table'}
                  </Button>
                  {!tableCollapsed && (
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }} onMouseDown={e => e.stopPropagation()}>
                        <Button className="toolbar-btn-hover" type="text" size="small" onClick={() => setColsOpen(o => !o)} style={TOOLBAR_BTN_STYLE}>Select Columns</Button>
                      <Button className="toolbar-btn-hover" type="text" size="small" onClick={onDownloadCsv} style={TOOLBAR_BTN_STYLE}>Download CSV</Button>
                    </div>
                  )}
                </div>

                {/* Table */}
                {!tableCollapsed && (
                  <div style={{ height: tableHeight, overflow: 'hidden' }}>
                    <ResortTable
                      ref={tableRef}
                      resorts={resorts}
                      columnDefs={columnDefs}
                      unit={unit}
                      onRowClick={setSelectedResortId}
                    />
                  </div>
                )}
              </div>
            </Layout.Content>
            <AppFooter lastUpdated={lastUpdated} isMobile={isMobile} />
          </Layout>
        </Layout>
      </Layout>
      <ResortDetailModal
        resortId={selectedResortId}
        onClose={() => setSelectedResortId(null)}
        unit={unit}
      />
      <HowToUseModal open={howToUseOpen} onClose={closeHowToUse} />
      {colsOpen && (
        <>
          <Overlay onDismiss={() => setColsOpen(false)} />
          {columnsPanel({
            position: 'fixed',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: 440,
            maxHeight: 'calc(100vh - 48px)',
            zIndex: PANEL_Z_INDEX,
          })}
        </>
      )}
    </ConfigProvider>
  )
}
