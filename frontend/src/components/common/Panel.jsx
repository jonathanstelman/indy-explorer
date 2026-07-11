import { COLORS } from '@/theme'

export const PANEL_STYLE = {
  background: COLORS.bgBase,
  border: `2px solid ${COLORS.bgHeader}`,
  borderRadius: 4,
}

export default function Panel({ children, onClose, closeLabel = 'Close', style, ...rest }) {
  return (
    <div style={{ ...PANEL_STYLE, position: 'relative', ...style }} {...rest}>
      {onClose && (
        <button
          onClick={onClose}
          aria-label={closeLabel}
          style={{
            position: 'absolute',
            top: 3,
            right: 5,
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: COLORS.textMuted,
            fontSize: 13,
            lineHeight: 1,
            padding: 0,
          }}
        >
          ×
        </button>
      )}
      {children}
    </div>
  )
}
