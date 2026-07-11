import { COLORS, FONTS } from '@/theme'
import ModalShell from '@/components/common/ModalShell'
import ModalHeader from '@/components/common/ModalHeader'

function Btn({ children, variant }) {
  const isDanger = variant === 'danger'
  return (
    <span style={{
      display: 'inline-block',
      background: isDanger ? COLORS.error : COLORS.bgHeader,
      color: isDanger ? '#ffffff' : COLORS.error,
      fontFamily: FONTS.mono,
      fontSize: 12,
      fontWeight: 700,
      padding: '1px 6px',
      borderRadius: 2,
      border: `1px solid ${isDanger ? COLORS.error : COLORS.bgMidtone}`,
      whiteSpace: 'nowrap',
      verticalAlign: 'middle',
    }}>
      {children}
    </span>
  )
}

function desktopSections() {
  return [
    {
      heading: 'Filters',
      body: <>
        The sidebar on the left lets you filter by region, terrain type, features, blackout dates, and Peak Rankings score.
        Use the <Btn>≪</Btn> button in the header to collapse or expand it.
      </>,
    },
    {
      heading: 'Map',
      body: <>
        Each dot is a resort — <span style={{ color: COLORS.error }}>pink</span> = alpine, <span style={{ color: COLORS.accentBlue }}>blue</span> = cross-country, <span style={{ color: COLORS.accentPurple }}>purple</span> = both. Click any dot to open its detail view.
      </>,
    },
    {
      heading: 'Table',
      body: <>
        Click <Btn variant="danger">▲ Expand data table</Btn> at the bottom to show the sortable resort table. Click any row to open the detail view.
      </>,
    },
    {
      heading: 'Resort detail',
      body: <>
        Opens from any map dot or table row. Shows trail breakdown, snowfall, blackout dates, and Peak Rankings score.
      </>,
    },
  ]
}

function mobileSections() {
  return [
    {
      heading: 'Filters',
      body: <>
        Tap the <Btn>≫</Btn> button in the top-left to open the filter sidebar. Filter by region, features, blackout dates, and Peak Rankings score.
      </>,
    },
    {
      heading: 'Map & Table',
      body: <>
        Switch views using the <Btn>Map</Btn> and <Btn>Table</Btn> tabs at the bottom of the screen. Dots are color-coded: <span style={{ color: COLORS.error }}>pink</span> = alpine, <span style={{ color: COLORS.accentBlue }}>blue</span> = cross-country, <span style={{ color: COLORS.accentPurple }}>purple</span> = both.
      </>,
    },
    {
      heading: 'Resort detail',
      body: <>
        Tap any map dot or table row to open the resort detail view — trail breakdown, snowfall, blackout dates, and Peak Rankings score.
      </>,
    },
  ]
}

export default function HowToUseModal({ open, onClose, isMobile }) {
  const sections = isMobile ? mobileSections() : desktopSections()

  return (
    <ModalShell open={open} onClose={onClose} width={500} isMobile={isMobile}>
      <ModalHeader title="How to use Indy Explorer" onClose={onClose} />

      {/* Scrollable content */}
      <div style={{ flex: 1, minHeight: 0, overflowY: 'auto', padding: '16px 24px 24px' }}>
        <p style={{ fontFamily: FONTS.mono, fontSize: 13, color: COLORS.textMuted, marginTop: 0, marginBottom: 20, lineHeight: 1.6 }}>
          Indy Explorer helps you find the right{' '}
          <span style={{ color: COLORS.error }}>Indy Pass</span>{' '}
          resort — filter by location, features, and dates, then dig into the data.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {sections.map(({ heading, body }) => (
            <div key={heading} style={{ borderLeft: `3px solid ${COLORS.primary}`, paddingLeft: 12 }}>
              <div style={{ fontFamily: FONTS.mono, fontWeight: 700, fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em', color: COLORS.primary, marginBottom: 4 }}>
                {heading}
              </div>
              <div style={{ fontFamily: FONTS.mono, fontSize: 12, color: COLORS.text, lineHeight: 1.6 }}>
                {body}
              </div>
            </div>
          ))}
        </div>

        <div style={{ marginTop: 20, borderTop: `1px solid ${COLORS.border}`, paddingTop: 12, fontFamily: FONTS.mono, fontSize: 11, color: COLORS.textMuted }}>
          Data from Indy Pass, Peak Rankings, and Google Maps. Not affiliated with Indy Pass.
        </div>
      </div>
    </ModalShell>
  )
}
