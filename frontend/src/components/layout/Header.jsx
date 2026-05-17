import { Layout, Typography } from 'antd'

export default function AppHeader() {
  return (
    <Layout.Header
      style={{
        display: 'flex',
        alignItems: 'center',
        background: '#ffffff',
        borderBottom: '1px solid #e0e0e0',
        padding: '0 24px',
        height: 56,
        lineHeight: '56px',
      }}
    >
      <Typography.Title
        level={3}
        style={{
          margin: 0,
          fontFamily: "'Bebas Neue', sans-serif",
          letterSpacing: '0.05em',
          color: '#0d0d0d',
        }}
      >
        Indy Explorer
      </Typography.Title>
    </Layout.Header>
  )
}
