import { useState } from 'react'
import { Layout, Popover, Typography, theme } from 'antd'
import { COLORS, FONTS } from '@/theme'

export default function AppFooter({ lastUpdated, isMobile }) {
  if (isMobile) return null
  const { token } = theme.useToken()
  const [feedbackOpen, setFeedbackOpen] = useState(false)

  const feedbackContent = (
    <div style={{ fontFamily: FONTS.mono, fontSize: 11, lineHeight: 1.8 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: COLORS.error, marginBottom: 2 }}>
        <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: COLORS.error, flexShrink: 0 }} />
        Improve this App
      </div>
      <ul style={{ margin: '0 0 0 12px', padding: 0 }}>
        <li><a href="https://github.com/jonathanstelman/indy-explorer/issues/new?labels=bug" target="_blank" rel="noreferrer" style={{ color: COLORS.text }}>Report a bug</a></li>
        <li><a href="https://github.com/jonathanstelman/indy-explorer/issues/new?labels=enhancement" target="_blank" rel="noreferrer" style={{ color: COLORS.text }}>Suggest a feature</a></li>
        <li><a href="https://github.com/users/jonathanstelman/projects/2" target="_blank" rel="noreferrer" style={{ color: COLORS.text }}>View project board</a></li>
      </ul>
    </div>
  )

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
        <Typography.Link style={{ color: token.colorSuccess }} href="https://peakrankings.com" target="_blank">Peak Rankings</Typography.Link>
        {', and '}
        <Typography.Link style={{ color: token.colorPrimary }} href="https://developers.google.com/maps/documentation/geocoding" target="_blank">Google Maps</Typography.Link>
      </Typography.Text>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
          Last updated: {lastUpdated ?? '—'}
        </Typography.Text>
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>·</Typography.Text>
        <Popover
          content={feedbackContent}
          trigger="click"
          open={feedbackOpen}
          onOpenChange={setFeedbackOpen}
          placement="topRight"
          arrow={false}
          overlayInnerStyle={{
            background: COLORS.bgBase,
            border: `2px solid ${COLORS.bgHeader}`,
            borderRadius: 4,
            padding: '8px 12px',
            boxShadow: 'none',
          }}
        >
          <Typography.Link style={{ fontSize: 12, color: token.colorTextSecondary }}>Feedback</Typography.Link>
        </Popover>
      </div>
    </Layout.Footer>
  )
}
