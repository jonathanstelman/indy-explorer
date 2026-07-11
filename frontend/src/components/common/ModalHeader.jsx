import { COLORS, FONTS } from '@/theme'

// Fixed dark header bar shared by full-page modals (HowToUseModal, ResortDetailModal)
// and Panel-based popups that adopt the same chrome (App.jsx's Select Columns).
export default function ModalHeader({ title, subtitle, onClose, titleFontSize = 22 }) {
  return (
    <div style={{
      background: COLORS.bgHeader,
      padding: '10px 12px 10px 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 12,
      flexShrink: 0,
    }}>
      <div style={{ minWidth: 0 }}>
        <div style={{
          fontFamily: FONTS.display,
          fontSize: titleFontSize,
          letterSpacing: '0.04em',
          color: COLORS.error,
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        }}>
          {title}
        </div>
        {subtitle && (
          <div style={{ fontFamily: FONTS.mono, fontSize: 12, color: COLORS.textMuted, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {subtitle}
          </div>
        )}
      </div>
      <button
        onClick={onClose}
        aria-label="Close"
        style={{
          background: 'none',
          border: 'none',
          color: COLORS.error,
          fontSize: titleFontSize,
          fontWeight: 700,
          fontFamily: FONTS.mono,
          cursor: 'pointer',
          padding: '4px 10px',
          lineHeight: 1,
          flexShrink: 0,
        }}
      >
        ✕
      </button>
    </div>
  )
}
