import { Layout } from 'antd'
import LocationFilters from '@/components/filters/LocationFilters'

export default function AppSidebar({ meta, allResorts }) {
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
      <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 24 }}>
        <LocationFilters meta={meta} allResorts={allResorts ?? []} />
      </div>
    </Layout.Sider>
  )
}
