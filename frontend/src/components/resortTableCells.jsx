import { COLORS } from '@/theme'

export function BoolCell({ value }) {
  if (value === true)  return <span style={{ color: COLORS.bgHeader }}>✓</span>
  if (value === false) return <span style={{ color: COLORS.neutral  }}>✗</span>
  return <span style={{ color: COLORS.textMuted }}>—</span>
}

export function LinkCell({ value }) {
  if (!value) return <span style={{ color: COLORS.textMuted }}>—</span>
  return (
    <a
      href={value}
      target="_blank"
      rel="noreferrer"
      onClick={e => e.stopPropagation()}
      style={{ color: COLORS.accentPurple }}
    >
      {value}
    </a>
  )
}
