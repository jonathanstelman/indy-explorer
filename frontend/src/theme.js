import { theme as antdTheme } from 'antd'

export const COLORS = {
  primary:       '#00c4d4',   // electric teal — UI accents, links, fills on dark
  success:       '#b4f000',   // chartreuse — high scores, active features, beginner trails
  warning:       '#ffc400',   // amber — mid scores, caution
  error:         '#ff006e',   // hot pink — low scores, alpine dots, standard blackouts
  neutral:       '#808080',
  accentBlue:    '#3d52ff',
  bgMidtone:        '#505050',   // charcoal — search band, table column headers, input borders
  inputPlaceholder: '#888888',   // electric blue — XC dots, intermediate trails
  accentPurple:  '#9b00e6',   // neon purple — Alpine+XC dots (pink + blue)
  primaryBorder: '#00b8c8',
  primaryHover:  '#00d9e8',
  primaryActive: '#0099a8',
  text:          '#0d0d0d',
  textMuted:     '#666666',
  border:        '#e0e0e0',
  bgBase:        '#ffffff',
  bgLayout:      '#f5f5f5',
  bgSidebar:     '#fafafa',
  bgHeader:      '#111111',   // near-black anchor — app header, table header, drag handle
  prMid:         '#8b6ab5',   // muted purple — middle tier (5–6) on PR score bars
  prTop:         '#40b050',   // rich green — top tier (9–10) on PR score bars
  bgOverlay:     'rgba(0,0,0,0.75)',
  shadow:        'rgba(0,0,0,0.15)',
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
  alpine: hexToRgba(COLORS.error,        200),  // hot pink
  xc:     hexToRgba(COLORS.accentBlue,   200),  // electric blue
  both:   hexToRgba(COLORS.accentPurple, 200),  // purple = pink + blue
  allied: hexToRgba(COLORS.neutral,      180),
}

const INPUT_TOKENS = {
  colorBorder:          COLORS.bgMidtone,
  colorTextPlaceholder: COLORS.inputPlaceholder,
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
  components: {
    Input:  INPUT_TOKENS,
    Select: INPUT_TOKENS,
    Button: { colorBorder: COLORS.bgMidtone },
  },
}
