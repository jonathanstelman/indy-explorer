import { ConfigProvider, Layout, theme as antdTheme } from 'antd'
import AppHeader from '@/components/layout/Header'
import AppSidebar from '@/components/layout/Sidebar'
import AppFooter from '@/components/layout/Footer'

const themeConfig = {
  algorithm: antdTheme.defaultAlgorithm,
  token: {
    colorPrimary: '#00f5ff',
    colorSuccess: '#39ff14',
    colorWarning: '#ffdd00',
    colorError: '#ff006e',
    colorInfo: '#00f5ff',
    colorPrimaryBorder: '#00b8c8',
    colorPrimaryHover: '#00d9e8',
    colorPrimaryActive: '#0099a8',
    colorBgBase: '#ffffff',
    colorBgContainer: '#ffffff',
    colorBgLayout: '#f5f5f5',
    colorTextBase: '#0d0d0d',
    colorBorder: '#e0e0e0',
    borderRadius: 2,
    fontFamily: "'Space Mono', monospace",
  },
}

export default function App() {
  return (
    <ConfigProvider theme={themeConfig}>
      <Layout style={{ height: '100%' }}>
        <AppHeader />
        <Layout>
          <AppSidebar />
          <Layout>
            <Layout.Content style={{ overflow: 'auto', padding: 24 }}>
              <div style={{ height: 200, background: '#f0f0f0', borderRadius: 4, marginBottom: 16 }} />
              <div style={{ height: 400, background: '#f0f0f0', borderRadius: 4 }} />
            </Layout.Content>
            <AppFooter />
          </Layout>
        </Layout>
      </Layout>
    </ConfigProvider>
  )
}
