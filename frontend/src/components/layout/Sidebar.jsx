import { Layout, Typography } from 'antd'

export default function AppSidebar() {
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
      <div style={{ padding: 16 }}>
        <Typography.Text
          type="secondary"
          style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em' }}
        >
          Filters
        </Typography.Text>
        <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 12 }}>
          {[...Array(5)].map((_, i) => (
            <div key={i} style={{ height: 32, borderRadius: 2, background: '#e8e8e8' }} />
          ))}
        </div>
      </div>
    </Layout.Sider>
  )
}
