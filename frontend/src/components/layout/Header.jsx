import { Button, Divider, Layout, Typography } from 'antd'
import { COLORS, FONTS } from '@/theme'
import UnitToggle from '@/components/common/UnitToggle'

export default function AppHeader({ sidebarCollapsed, onToggleSidebar, onHowToUse, isMobile }) {
  const height = isMobile ? 40 : 56
  return (
    <Layout.Header
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        background: COLORS.bgHeader,
        padding: '0 24px',
        height,
        lineHeight: `${height}px`,
      }}
    >
      <Button
        type="text"
        onClick={onToggleSidebar}
        aria-label={sidebarCollapsed ? 'Expand filters' : 'Collapse filters'}
        style={{ color: COLORS.error, padding: '0 6px', flexShrink: 0, lineHeight: 1, display: 'flex', alignItems: 'center' }}
      >
        <svg width="16" height="12" viewBox="0 0 16 12" fill="none" style={{ display: 'block', transform: 'translateY(-1px)' }}>
          {sidebarCollapsed ? <>
            <path d="M3 2L7 6L3 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M8 2L12 6L8 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </> : <>
            <path d="M13 2L9 6L13 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M8 2L4 6L8 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </>}
        </svg>
      </Button>
      <Divider vertical style={{ height: 20, margin: '0 4px' }} />
      <Typography.Title
        level={3}
        style={{
          margin: 0,
          fontFamily: FONTS.display,
          letterSpacing: '0.08em',
          color: COLORS.error,
          fontWeight: 400,
          fontSize: isMobile ? 20 : 28,
          WebkitFontSmoothing: 'antialiased',
          WebkitTextStroke: `0.5px ${COLORS.error}`,
          flex: 1,
        }}
      >
        Indy Explorer
      </Typography.Title>
      <UnitToggle style={{ fontSize: isMobile ? 12 : 13 }} />
      <Button
        type="text"
        onClick={onHowToUse}
        aria-label="How to use"
        style={{
          color: COLORS.error,
          fontFamily: FONTS.mono,
          fontSize: isMobile ? 12 : 13,
          padding: '0 8px',
          flexShrink: 0,
          lineHeight: 1,
        }}
      >
        ?
      </Button>
    </Layout.Header>
  )
}
