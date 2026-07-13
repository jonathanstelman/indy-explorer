import { Button, Collapse, Drawer, Layout, theme } from 'antd'
import { COLORS } from '@/theme'
import UnitToggle from '@/components/common/UnitToggle'
import LocationFilters from '@/components/filters/LocationFilters'
import StatsFilters from '@/components/filters/StatsFilters'
import FeatureFilters from '@/components/filters/FeatureFilters'
import BlackoutDateFilters from '@/components/filters/BlackoutDateFilters'
import PeakRankingsFilters from '@/components/filters/PeakRankingsFilters'
import { useFilters } from '@/hooks/useFilters'

const ALL_KEYS = ['location']

export default function AppSidebar({ meta, allResorts, collapsed, width, isMobile, onClose }) {
  const { resetFilters } = useFilters()
  const { token } = theme.useToken()

  function sectionLabel(text, color) {
    return (
      <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: color, flexShrink: 0 }} />
        {text}
      </span>
    )
  }

  // zIndex only needs to clear this panel's own scrolled-under content, not app-wide
  // overlays — see OVERLAY_Z_INDEX in components/common/Overlay.jsx.
  const stickyHeader = { position: 'sticky', top: 0, zIndex: 1, background: token.colorBgLayout }

  const items = [
    {
      key: 'location',
      label: sectionLabel('Location', COLORS.primary),
      styles: { header: stickyHeader },
      children: <LocationFilters meta={meta} allResorts={allResorts ?? []} />,
    },
    {
      key: 'resort-filters',
      label: sectionLabel('Stats and Features', COLORS.accentBlue),
      styles: { header: stickyHeader },
      children: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          <StatsFilters meta={meta} />
          <FeatureFilters />
        </div>
      ),
    },
    {
      key: 'blackout',
      label: sectionLabel('Planning', COLORS.error),
      styles: { header: stickyHeader },
      children: <BlackoutDateFilters />,
    },
    {
      key: 'peak-rankings',
      label: sectionLabel('Peak Rankings', COLORS.success),
      styles: { header: stickyHeader },
      children: <PeakRankingsFilters meta={meta} />,
    },
  ]

  const content = (
    <>
      <div style={{ padding: '8px 16px 4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {isMobile && (
            <button
              onClick={onClose}
              style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center', color: COLORS.error }}
            >
              <svg width="16" height="12" viewBox="0 0 16 12" fill="none" style={{ display: 'block', transform: 'translateY(-1px)' }}>
                <path d="M13 2L9 6L13 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M8 2L4 6L8 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          )}
          <UnitToggle style={{ fontSize: 12, padding: '0 4px' }} />
        </div>
        <Button type="link" size="small" danger onClick={resetFilters} style={{ padding: 0 }}>
          Reset all filters
        </Button>
      </div>
      <Collapse
        defaultActiveKey={ALL_KEYS}
        items={items}
        ghost
        style={{ padding: '8px 0' }}
      />
    </>
  )

  if (isMobile) {
    return (
      <Drawer
        title={null}
        closable={false}
        placement="left"
        open={!collapsed}
        onClose={onClose}
        size={280}
        styles={{ body: { padding: 0, background: token.colorBgLayout } }}
      >
        {content}
      </Drawer>
    )
  }

  return (
    <Layout.Sider
      collapsed={collapsed}
      collapsedWidth={0}
      width={width}
      style={{
        background: token.colorBgLayout,
        overflow: 'auto',
      }}
    >
      {content}
    </Layout.Sider>
  )
}
