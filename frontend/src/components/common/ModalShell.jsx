import { Modal } from 'antd'
import { COLORS } from '@/theme'

// Viewport-constrained antd Modal shell shared by HowToUseModal and ResortDetailModal:
// bold border + white inset frame on desktop, full-bleed on mobile, and a flex-column
// container so a flexShrink:0 header + flex:1 overflowY:auto body never overflow the
// viewport regardless of header height (no magic-number height estimates needed).
export default function ModalShell({ open, onClose, width, isMobile, destroyOnHidden, children }) {
  const gap = isMobile ? 0 : 24

  return (
    <Modal
      open={open}
      onCancel={onClose}
      footer={null}
      closable={false}
      centered={isMobile}
      width={isMobile ? '100%' : width}
      destroyOnHidden={destroyOnHidden}
      style={{
        top: isMobile ? undefined : gap,
        margin: isMobile ? 0 : '0 auto',
        padding: 0,
        maxWidth: isMobile ? '100vw' : undefined,
      }}
      styles={{
        wrapper: { padding: 0 },
        container: {
          padding: isMobile ? 0 : 2,
          border: isMobile ? undefined : `2px solid ${COLORS.bgHeader}`,
          overflow: 'hidden',
          borderRadius: isMobile ? 0 : undefined,
          display: 'flex',
          flexDirection: 'column',
          ...(isMobile ? { height: '100dvh' } : { maxHeight: `calc(100vh - ${gap * 2}px)` }),
        },
        body: {
          padding: 0,
          flex: 1,
          minHeight: 0,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        },
      }}
    >
      {children}
    </Modal>
  )
}
