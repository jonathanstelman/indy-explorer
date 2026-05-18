import { useEffect, useState } from 'react'
import { ConfigProvider, Layout, theme as antdTheme } from 'antd'
import { useSearchParams } from 'react-router-dom'
import { useFilters } from '@/hooks/useFilters'
import { fetchResorts, fetchMeta } from '@/api/resorts'
import AppHeader from '@/components/layout/Header'
import AppSidebar from '@/components/layout/Sidebar'
import AppFooter from '@/components/layout/Footer'
import ResortToolbar from '@/components/ResortToolbar'
import ResortMap from '@/components/ResortMap'

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
  const [searchParams] = useSearchParams()
  const { filters } = useFilters()

  const [resorts, setResorts] = useState([])
  const [allResorts, setAllResorts] = useState([])
  const [meta, setMeta] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

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

  return (
    <ConfigProvider theme={themeConfig}>
      <Layout style={{ height: '100%' }}>
        <AppHeader />
        <Layout>
          <AppSidebar meta={meta} allResorts={allResorts} />
          <Layout>
            <Layout.Content style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              <div style={{ padding: '12px 24px' }}>
                <ResortToolbar count={resorts.length} loading={loading} />
              </div>
              <div style={{ flex: 1, position: 'relative' }}>
                <ResortMap resorts={resorts} />
              </div>
            </Layout.Content>
            <AppFooter />
          </Layout>
        </Layout>
      </Layout>
    </ConfigProvider>
  )
}
