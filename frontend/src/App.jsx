import { useEffect, useState } from 'react'
import { ConfigProvider, Layout } from 'antd'
import { useSearchParams } from 'react-router-dom'
import { useFilters } from '@/hooks/useFilters'
import { fetchResorts, fetchMeta } from '@/api/resorts'
import AppHeader from '@/components/layout/Header'
import AppSidebar from '@/components/layout/Sidebar'
import AppFooter from '@/components/layout/Footer'
import ResortToolbar from '@/components/ResortToolbar'
import ResortMap from '@/components/ResortMap'
import ResortDetailModal from '@/components/ResortDetailModal'
import { themeConfig } from '@/theme'

export default function App() {
  const [searchParams] = useSearchParams()
  const { filters } = useFilters()

  const [resorts, setResorts] = useState([])
  const [allResorts, setAllResorts] = useState([])
  const [meta, setMeta] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedResortId, setSelectedResortId] = useState(null)

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
                <ResortMap
                  resorts={resorts}
                  onResortClick={r => setSelectedResortId(r.resort_id)}
                />
              </div>
            </Layout.Content>
            <AppFooter />
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
