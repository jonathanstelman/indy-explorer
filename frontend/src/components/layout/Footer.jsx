import { Layout, Typography, theme } from 'antd'

export default function AppFooter({ lastUpdated }) {
  const { token } = theme.useToken()
  return (
    <Layout.Footer
      style={{
        background: token.colorBgContainer,
        borderTop: `1px solid ${token.colorBorder}`,
        padding: '8px 24px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '4px 16px',
      }}
    >
      <Typography.Text type="secondary" style={{ fontSize: 12 }}>
        Data sourced from{' '}
        <Typography.Link style={{ color: token.colorError }} href="https://www.indyskipass.com" target="_blank">Indy Pass</Typography.Link>
        {', '}
        <Typography.Link style={{ color: token.colorError }} href="https://peakrankings.com" target="_blank">Peak Rankings</Typography.Link>
        {', and '}
        <Typography.Link style={{ color: token.colorError }} href="https://developers.google.com/maps/documentation/geocoding" target="_blank">Google Maps</Typography.Link>
      </Typography.Text>
      <Typography.Text type="secondary" style={{ fontSize: 12 }}>
        Last updated: {lastUpdated ?? '—'}
      </Typography.Text>
    </Layout.Footer>
  )
}
