import { Button, Collapse, Drawer, Layout, theme } from 'antd'
import { COLORS } from '@/theme'
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

  const items = [
    {
      key: 'location',
      label: 'Location',
      children: <LocationFilters meta={meta} allResorts={allResorts ?? []} />,
    },
    {
      key: 'resort-filters',
      label: 'Stats and Features',
      children: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          <StatsFilters meta={meta} />
          <FeatureFilters />
        </div>
      ),
    },
    {
      key: 'blackout',
      label: 'Blackout Dates',
      children: <BlackoutDateFilters />,
    },
    {
      key: 'peak-rankings',
      label: 'Peak Rankings',
      children: <PeakRankingsFilters meta={meta} />,
    },
  ]

  const content = (
    <>
      <div style={{ padding: '8px 16px 4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
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
        <Button type="link" size="small" danger onClick={resetFilters} style={{ padding: 0, marginLeft: 'auto' }}>
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
        width={280}
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
