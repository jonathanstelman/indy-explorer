import { useEffect, useRef, useState } from 'react'
import { Button, Checkbox, ConfigProvider, Layout, Popover, Typography } from 'antd'
import { useSearchParams } from 'react-router-dom'
import { useFilters } from '@/hooks/useFilters'
import { fetchResorts, fetchMeta } from '@/api/resorts'
import AppHeader from '@/components/layout/Header'
import AppSidebar from '@/components/layout/Sidebar'
import AppFooter from '@/components/layout/Footer'
import ResortToolbar from '@/components/ResortToolbar'
import ResortMap from '@/components/ResortMap'
import ResortTable, { COLUMN_DEFS, HEADER_BY_FIELD, COL_GROUPS } from '@/components/ResortTable'
import ResortDetailModal from '@/components/ResortDetailModal'
import { themeConfig, COLORS, FONTS } from '@/theme'

const DEFAULT_TABLE_HEIGHT = 260
const MIN_TABLE_HEIGHT = 100
const MAX_TABLE_HEIGHT_RATIO = 0.7

export default function App() {
  const [searchParams] = useSearchParams()
  const { filters } = useFilters()

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

  const tableRef = useRef()
  const [colsOpen,      setColsOpen]      = useState(false)
  const [colVisibility, setColVisibility] = useState(
    () => Object.fromEntries(COLUMN_DEFS.map(c => [c.field, true]))
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

  function toggleColumn(field) {
    const next = !colVisibility[field]
    setColVisibility(prev => ({ ...prev, [field]: next }))
    tableRef.current?.api.applyColumnState({ state: [{ colId: field, hide: !next }] })
  }

  function toggleGroup(group) {
    const allChecked = group.fields.every(f => colVisibility[f])
    const next = !allChecked
    setColVisibility(prev => ({ ...prev, ...Object.fromEntries(group.fields.map(f => [f, next])) }))
    tableRef.current?.api.applyColumnState({ state: group.fields.map(f => ({ colId: f, hide: !next })) })
  }

  const colsContent = (
    <div style={{ width: 340, maxHeight: 420, overflowY: 'auto', padding: '4px 0' }}>
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

  const lastUpdated = meta?.last_pipeline_run ? new Date(meta.last_pipeline_run).toLocaleDateString() : '—'
  const attributionContent = (
    <div style={{ fontFamily: FONTS.mono, fontSize: 11, lineHeight: 1.6 }}>
      <div>
        Data sourced from{' '}
        <Typography.Link style={{ color: COLORS.error }} href="https://www.indyskipass.com" target="_blank">Indy Pass</Typography.Link>
        {', '}
        <Typography.Link style={{ color: COLORS.success }} href="https://peakrankings.com" target="_blank">Peak Rankings</Typography.Link>
        {', and '}
        <Typography.Link style={{ color: COLORS.primary }} href="https://developers.google.com/maps/documentation/geocoding" target="_blank">Google Maps</Typography.Link>
      </div>
      <div style={{ color: COLORS.textMuted, marginTop: 4 }}>Last updated: {lastUpdated}</div>
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
          <AppHeader sidebarCollapsed={sidebarCollapsed} onToggleSidebar={() => setSidebarCollapsed(c => !c)} />
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
                <div style={{ padding: '8px 12px', borderBottom: `1px solid ${COLORS.bgHeader}`, background: COLORS.bgMidtone, flexShrink: 0 }}>
                  <ResortToolbar count={resorts.length} loading={loading} />
                </div>

                <div style={{ flex: 1, position: 'relative', minHeight: 0 }}>
                  {mobileTab === 'map' && (
                    <ResortMap
                      resorts={resorts}
                      onResortClick={r => setSelectedResortId(r.resort_id)}
                    />
                  )}
                  {mobileTab === 'table' && (
                    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                      <div style={{ display: 'flex', gap: 8, padding: '4px 12px', background: COLORS.bgHeader, borderBottom: `1px solid ${COLORS.border}`, flexShrink: 0 }}>
                        <Popover
                          content={colsContent}
                          title="Show / hide columns"
                          trigger="click"
                          open={colsOpen}
                          onOpenChange={setColsOpen}
                          placement="topLeft"
                        >
                          <Button type="text" size="small" style={{ color: COLORS.success }}>Select Columns</Button>
                        </Popover>
                        <Button type="text" size="small" onClick={onDownloadCsv} style={{ color: COLORS.success }}>Download CSV</Button>
                      </div>
                      <div style={{ flex: 1, minHeight: 0 }}>
                        <ResortTable
                          ref={tableRef}
                          resorts={resorts}
                          onRowClick={setSelectedResortId}
                        />
                      </div>
                    </div>
                  )}
                </div>

                <div style={{ display: 'flex', background: COLORS.bgHeader, borderTop: `1px solid ${COLORS.border}`, flexShrink: 0 }}>
                  {['map', 'table'].map(tab => (
                    <button
                      key={tab}
                      onClick={() => setMobileTab(tab)}
                      style={{
                        flex: 1,
                        height: 48,
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
                  <Popover
                    content={attributionContent}
                    trigger="click"
                    open={infoOpen}
                    onOpenChange={setInfoOpen}
                    placement="topRight"
                  >
                    <button
                      style={{
                        width: 44,
                        height: 48,
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
                  </Popover>
                </div>
              </Layout.Content>
            </Layout>
          </Layout>
        </Layout>
        <ResortDetailModal
          resortId={selectedResortId}
          onClose={() => setSelectedResortId(null)}
          isMobile={isMobile}
        />
      </ConfigProvider>
    )
  }

  return (
    <ConfigProvider theme={themeConfig}>
      <Layout style={{ height: '100%' }}>
        <AppHeader sidebarCollapsed={sidebarCollapsed} onToggleSidebar={() => setSidebarCollapsed(c => !c)} />
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
              <div style={{ flex: 1, position: 'relative', minHeight: 0 }}>
                <ResortMap
                  resorts={resorts}
                  onResortClick={r => setSelectedResortId(r.resort_id)}
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
                    <div style={{ display: 'flex', gap: 8 }} onMouseDown={e => e.stopPropagation()}>
                      <Popover
                        content={colsContent}
                        title="Show / hide columns"
                        trigger="click"
                        open={colsOpen}
                        onOpenChange={setColsOpen}
                        placement="bottomRight"
                      >
                        <Button type="text" size="small" style={{ color: COLORS.success }}>Select Columns</Button>
                      </Popover>
                      <Button type="text" size="small" onClick={onDownloadCsv} style={{ color: COLORS.success }}>Download CSV</Button>
                    </div>
                  )}
                </div>

                {/* Table */}
                {!tableCollapsed && (
                  <div style={{ height: tableHeight, overflow: 'hidden' }}>
                    <ResortTable
                      ref={tableRef}
                      resorts={resorts}
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
      />
    </ConfigProvider>
  )
}
