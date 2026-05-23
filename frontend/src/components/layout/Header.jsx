import { Layout, Typography, theme } from 'antd'
import { FONTS } from '@/theme'

export default function AppHeader() {
  const { token } = theme.useToken()
  return (
    <Layout.Header
      style={{
        display: 'flex',
        alignItems: 'center',
        background: token.colorBgContainer,
        borderBottom: `1px solid ${token.colorBorder}`,
        padding: '0 24px',
        height: 56,
        lineHeight: '56px',
      }}
    >
      <Typography.Title
        level={3}
        style={{
          margin: 0,
          fontFamily: FONTS.display,
          letterSpacing: '0.05em',
          color: token.colorTextBase,
        }}
      >
        Indy Explorer
      </Typography.Title>
    </Layout.Header>
  )
}
