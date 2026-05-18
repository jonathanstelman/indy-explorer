import { Button, Collapse, Layout } from 'antd'
import LocationFilters from '@/components/filters/LocationFilters'
import StatsFilters from '@/components/filters/StatsFilters'
import FeatureFilters from '@/components/filters/FeatureFilters'
import BlackoutDateFilters from '@/components/filters/BlackoutDateFilters'
import PeakRankingsFilters from '@/components/filters/PeakRankingsFilters'
import { useFilters } from '@/hooks/useFilters'

const ALL_KEYS = ['location']

export default function AppSidebar({ meta, allResorts }) {
  const { resetFilters } = useFilters()

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

  return (
    <Layout.Sider
      breakpoint="md"
      collapsedWidth="0"
      width={280}
      style={{
        background: '#fafafa',
        borderRight: '1px solid #e0e0e0',
        overflow: 'auto',
      }}
    >
      <div style={{ padding: '12px 16px 4px', display: 'flex', justifyContent: 'flex-end' }}>
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
    </Layout.Sider>
  )
}
