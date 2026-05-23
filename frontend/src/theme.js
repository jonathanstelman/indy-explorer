import { theme as antdTheme } from 'antd'

export const COLORS = {
  primary:             '#00f5ff',
  success:             '#39ff14',
  warning:             '#ffdd00',
  error:               '#ff006e',
  neutral:             '#808080',
  primaryBorder:       '#00b8c8',
  primaryHover:        '#00d9e8',
  primaryActive:       '#0099a8',
  text:                '#0d0d0d',
  textMuted:           '#666666',
  border:              '#e0e0e0',
  bgBase:              '#ffffff',
  bgLayout:            '#f5f5f5',
  bgSidebar:           '#fafafa',
  bgHeader:            '#505050',
  bgOverlay:           'rgba(0,0,0,0.75)',
  shadow:              'rgba(0,0,0,0.15)',
  difficultyBeginner:  '#00C44F',
}

export function withAlpha(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return [r, g, b, alpha]
}

export const FONTS = {
  mono:    "'Space Mono', monospace",
  display: "'Bebas Neue', sans-serif",
}

// Deck.gl requires colors as [R, G, B, A] arrays (A: 0–255).
export const MAP_DOT_COLORS = {
  alpine: hexToRgba(COLORS.error,   200),
  xc:     hexToRgba(COLORS.primary, 200),
  both:   hexToRgba(COLORS.success, 200),
  allied: hexToRgba(COLORS.neutral, 180),
}

export const themeConfig = {
  algorithm: antdTheme.defaultAlgorithm,
  token: {
    colorPrimary:       COLORS.primary,
    colorSuccess:       COLORS.success,
    colorWarning:       COLORS.warning,
    colorError:         COLORS.error,
    colorInfo:          COLORS.primary,
    colorPrimaryBorder: COLORS.primaryBorder,
    colorPrimaryHover:  COLORS.primaryHover,
    colorPrimaryActive: COLORS.primaryActive,
    colorBgBase:        COLORS.bgBase,
    colorBgContainer:   COLORS.bgBase,
    colorBgLayout:      COLORS.bgLayout,
    colorTextBase:      COLORS.text,
    colorBorder:        COLORS.border,
    borderRadius:       2,
    fontFamily:         FONTS.mono,
  },
}
