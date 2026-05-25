import { useEffect, useRef, useState } from 'react'
import { Button, Checkbox, ConfigProvider, Layout, Popover } from 'antd'
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
import { themeConfig, COLORS } from '@/theme'

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

  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => window.innerWidth < 768)
  const [sidebarWidth, setSidebarWidth] = useState(280)

  const [tableHeight, setTableHeight] = useState(DEFAULT_TABLE_HEIGHT)
  const [tableCollapsed, setTableCollapsed] = useState(false)

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
          />
          {!sidebarCollapsed && (
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
              <div style={{ padding: '12px 24px' }}>
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
                    height: 28,
                    background: COLORS.bgLayout,
                    borderTop: `1px solid ${COLORS.border}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0 16px',
                    cursor: tableCollapsed ? 'default' : 'ns-resize',
                    userSelect: 'none',
                  }}
                >
                  <Button
                    size="small"
                    onMouseDown={e => e.stopPropagation()}
                    onClick={() => setTableCollapsed(c => !c)}
                    style={{ borderColor: COLORS.error, color: COLORS.error }}
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
                        <Button size="small">Select Columns</Button>
                      </Popover>
                      <Button size="small" onClick={onDownloadCsv}>Download CSV</Button>
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
            <AppFooter lastUpdated={meta?.last_pipeline_run ? new Date(meta.last_pipeline_run).toLocaleDateString() : null} />
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
