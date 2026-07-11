import { COLORS } from '@/theme'

// Single z-index contract for all custom popup surfaces. Anything meant to sit
// above this dim layer (e.g. a sticky sidebar header) must stay below OVERLAY_Z_INDEX.
export const OVERLAY_Z_INDEX = 8
export const PANEL_Z_INDEX = 9

export default function Overlay({ onDismiss }) {
  return (
    <div
      style={{ position: 'fixed', inset: 0, background: COLORS.bgOverlay, zIndex: OVERLAY_Z_INDEX }}
      onClick={onDismiss}
    />
  )
}
