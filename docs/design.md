# Indy Explorer — UI Design Document
*Last updated: May 2026 | Framework: Ant Design (antd v6) + React*

---

## 1. Aesthetic Direction

**Theme: 80s Ski-Punk Neon**

The visual identity draws from vintage ski culture — think 1984 Salomon posters, neon-lit lodge signs, and the unapologetic maximalism of early snowboard graphics. Bold neon colors against near-black backgrounds. High contrast. A little dangerous-looking.

This is not a corporate dashboard. It should feel like it was designed by someone who skis hard and stays up too late.

**Mood references:**
- Vintage Salomon, Rossignol, and K2 ski graphics (1980–1992)
- Neon arcade signage
- Early snowboard magazine layouts (powder, TransWorld SNOWboarding)
- Retro CRT screen glow

---

## 2. Color Palette

**Light mode is the default.** Dark mode is available as an optional alternate theme, auto-detected from system preference with a manual override toggle in the top nav.

### Core Colors — Light Mode (Default)
| Role | Token | Hex | Notes |
|------|-------|-----|-------|
| Primary | `colorPrimary` | `#00f5ff` | Electric cyan — main interactive color |
| Danger / Accent | `colorError` | `#ff006e` | Hot pink — warnings, alerts, emphasis |
| Success | `colorSuccess` | `#39ff14` | Neon green — open/available status |
| Warning | `colorWarning` | `#ffdd00` | Yellow — limited availability, caution |
| Background | `colorBgBase` | `#ffffff` | White — reads ski, alpine, snow |
| Surface | `colorBgContainer` | `#ffffff` | Cards, panels |
| Elevated | `colorBgElevated` | `#ffffff` | Modals, popovers |
| Text Primary | `colorTextBase` | `#0d0d0d` | Near-black |
| Text Secondary | `colorTextSecondary` | `#333333` | Subdued labels |

### Core Colors — Dark Mode (Optional)
| Role | Token | Hex | Notes |
|------|-------|-----|-------|
| Background | `colorBgBase` | `#0a0a0a` | Near-black — neon-maximalist look |
| Surface | `colorBgContainer` | `#141414` | Slightly lifted surface |
| Elevated | `colorBgElevated` | `#1a1a1a` | Modals, popovers |
| Text Primary | `colorTextBase` | `#f0f0f0` | Off-white |
| Text Secondary | `colorTextSecondary` | `#999999` | Subdued labels |
| *(accent colors same as light mode)* | | | Cyan/pink/green all carry over |

### Semantic Color Usage
- **Cyan (`#00f5ff`)** — primary actions, links, active states, selected items
- **Hot pink (`#ff006e`)** — destructive actions, error states, "closed" resort status
- **Neon green (`#39ff14`)** — "open" resort status, success confirmations
- **Yellow (`#ffdd00`)** — partial open (some trails), warnings
- **White/off-white** — primary text, headings

### Glow Effects
The neon palette only reads as neon against dark backgrounds. Key glows:
```
Primary glow:   0 0 12px 2px rgba(0, 245, 255, 0.6)
Secondary glow: 0 0 20px 4px rgba(0, 245, 255, 0.4)
Pink glow:      0 0 10px 2px rgba(255, 0, 110, 0.5)
Green glow:     0 0 8px 2px rgba(57, 255, 20, 0.4)
```

> ⚠️ **Critical:** The white-background version of this theme loses most of its character. Dark background is non-negotiable for the intended aesthetic.

---

## 3. Typography

### Recommended Pairing
| Role | Font | Style |
|------|------|-------|
| Display / Headings | **Bebas Neue** | All-caps, condensed, aggressive |
| Body / UI | **Space Mono** | Monospace adds a retro-tech feel |

**Why monospace for body:** It reinforces the retro-tech / CRT aesthetic without going full gimmick. It's also highly readable at small sizes for data-dense interfaces.

**Avoid:** Inter, Roboto, SF Pro, or any "neutral" sans-serif — they'll immediately kill the aesthetic.

### Type Scale (approximate)
```
Display:  48–64px, Bebas Neue, letter-spacing: 0.05em
H1:       32px, Bebas Neue
H2:       24px, Bebas Neue
Body:     14px, Space Mono
Label:    12px, Space Mono, uppercase, letter-spacing: 0.08em
```

---

## 4. Ant Design Config

Light mode is implemented in `frontend/src/theme.js`. Dark mode tokens for future implementation:

### Dark Mode Config
```jsx
import { theme } from 'antd'

const darkThemeConfig = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary:       '#00f5ff',
    colorSuccess:       '#39ff14',
    colorWarning:       '#ffdd00',
    colorError:         '#ff006e',
    colorInfo:          '#00f5ff',
    colorPrimaryBorder: '#00b8c8',
    colorPrimaryHover:  '#00d9e8',
    colorPrimaryActive: '#0099a8',
    borderRadius:       2,
    colorBgBase:        '#0a0a0a',
    colorBgContainer:   '#141414',
    colorBgElevated:    '#1a1a1a',
    colorBgLayout:      '#0d0d0d',
    colorBgSpotlight:   'rgba(0, 245, 255, 0.15)',
    colorBgMask:        'rgba(0, 0, 0, 0.75)',
    colorTextBase:      '#f0f0f0',
    colorTextSecondary: '#aaaaaa',
    colorTextTertiary:  '#666666',
    colorTextDisabled:  '#333333',
    colorBorder:        '#00f5ff',
    colorBorderSecondary: '#2a2a2a',
    colorPrimaryBg:     '#001a1f',
    colorPrimaryBgHover: '#002a33',
  },
}
```

### Theme Switching Pattern
```jsx
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
const [isDark, setIsDark] = useState(prefersDark)

// Toggle in top nav:
// <Switch checked={isDark} onChange={setIsDark} />
```

---

## 5. Component Guidelines

### Resort Status Badges
- Open → `colorSuccess` (`#39ff14`) with green glow
- Closed → `colorError` (`#ff006e`) with pink glow
- Limited → `colorWarning` (`#ffdd00`)
- Unknown / Off-season → `colorTextDisabled`

### Data Tables
- Header row: dark charcoal background (`#505050`), white text — implemented
- Sorted column: faint cyan column highlight
- Avoid heavy grid lines — subtle `colorBorderSecondary` only

### Buttons
- **Primary:** Cyan fill, near-black text, cyan glow on hover
- **Default:** Transparent, cyan border, cyan text — ghost style
- **Danger:** Hot pink fill or border

---

## 6. Motion & Atmosphere

- **Glow pulse on load:** Key elements (logo, primary CTA) can have a subtle glow pulse animation on page load
- **Hover glows:** All interactive elements transition from no-glow to glow on hover (150ms ease)
- **No flashy page transitions** — keep motion purposeful, not decorative
- **Consider:** A very subtle CRT scanline texture overlay on the page background (low opacity, does not affect readability)

---

## 7. Open Questions

- [ ] Logo / wordmark style — retro badge? text-only? illustrated icon?
- [ ] Dark mode implementation — dark map tiles needed (Mapbox dark styles)
- [ ] Scanline/grain texture on page background, or clean bg sufficient?
- [ ] Font licensing — Google Fonts is currently used; self-hosting may be preferred for performance
- [ ] Mobile layout — dense data tables need adaptation; consider simplified card view on small screens
