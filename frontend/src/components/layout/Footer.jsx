import { Layout, Typography } from 'antd'

export default function AppFooter({ lastUpdated }) {
  return (
    <Layout.Footer
      style={{
        background: '#ffffff',
        borderTop: '1px solid #e0e0e0',
        padding: '8px 24px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}
    >
      <Typography.Text type="secondary" style={{ fontSize: 12 }}>
        Data sourced from{' '}
        <Typography.Link href="https://www.indyskipass.com" target="_blank">
          Indy Pass
        </Typography.Link>
      </Typography.Text>
      <Typography.Text type="secondary" style={{ fontSize: 12 }}>
        Last updated: {lastUpdated ?? '—'}
      </Typography.Text>
    </Layout.Footer>
  )
}
