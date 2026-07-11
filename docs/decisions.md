# Indy Explorer — Decisions Log

Architectural decisions, design choices, and resolved open questions.
Format for new entries:

---
## YYYY-MM-DD — Short description
**Issue:** #number (if applicable)  
**Decision:** What was decided.  
**Rationale:** Why, and what alternatives were considered.  
**Follow-up:** Open items or gotchas, if any.
---

---
## 2025-02-22 — Resort detail UI
**Issue:** #30  
**Decision:** Opens as a modal, triggered by clicking a map dot or table row.  
**Rationale:** Slide-over panel was considered and rejected.  
**Follow-up:** None — settled.

---
## 2026-03-08 — Rewrite architecture (initial planning)
**Issue:** #51–#55  
**Decision:** Monorepo with `/backend` (FastAPI), `/frontend` (Vite + React), `/pipeline`. `app.py` at repo root stays live on Streamlit Community Cloud during transition.  
**Rationale:** Clean separation of concerns; Streamlit remains the production app until the rewrite is stable.  
**Follow-up:** Remove `app.py` and Streamlit references once rewrite is live.

---
## 2026-03-08 — Resort IDs
**Issue:** #55  
**Decision:** Stable UUID v4 `resort_id` per resort, preserved across pipeline runs via `data/resort_id_map.csv` (columns: `resort_id`, `source`, `source_id`).  
**Rationale:** Indy Pass slugs and row indices change year to year and are unreliable as identifiers.  
**Follow-up:** None — settled.

---
## 2026-03-08 — Map library
**Issue:** #69  
**Decision:** `@deck.gl/react`, not standalone Mapbox GL JS.  
**Rationale:** Supports `onClick` per data point natively, enabling clickable map dots that open the resort detail modal. Pydeck in Streamlit could not do this.  
**Follow-up:** None — settled.

---
## 2026-03-08 — Deployment stack
**Issue:** #54  
**Decision:** Frontend on Vercel, backend on Fly.io (`backend/fly.toml`). Supabase (Postgres + Auth) deferred until data migration and auth are needed.  
**Rationale:** Keeps infrastructure simple during early rewrite phase.  
**Follow-up:** Revisit Supabase when auth or relational queries become necessary.

---
## 2026-03-08 — Data delivery
**Issue:** #55  
**Decision:** `data/resorts.csv` is committed to the repo. FastAPI reads it via `load_resorts()` at startup. The scheduled pipeline (Issue #77) commits the updated file; a new Fly.io deploy picks it up.  
**Rationale:** No external storage or volume mounts needed at this scale.  
**Follow-up:** Revisit if CSV size or update frequency becomes a problem.

---
## 2026-05-17 — Filter state
**Issue:** #64  
**Decision:** URL query params.  
**Rationale:** Users can save and share search results by copying the URL — no auth or saved-search feature needed.  
**Follow-up:** Implement before Issues #14–#18. Ensure filter params are kept clean and human-readable (e.g., `?pass=ikon&region=northeast`).

---
## 2026-05-25 — Mobile sidebar: Drawer overlay pattern
**Issue:** #103, #105
**Decision:** On mobile (< 768px), `AppSidebar` renders as an Ant Design `Drawer` overlay instead of a `Layout.Sider` push column. Desktop keeps the push layout with drag-to-resize. The `isMobile` flag is set on mount and updated on resize. The Drawer is `closable={false}`; the close affordance is a double-chevron SVG in the content header row. The same chevron (in the app header) toggles both desktop and mobile.
**Rationale:** A layout column on mobile squeezed the content area to ~80px, making the footer and table unusable. Overlay keeps content full-width. Ant Design `Drawer` handles the backdrop, animation, and scroll-lock.
**Follow-up:** Touch drag-to-resize on desktop sidebar not implemented (nice-to-have).

---
## 2026-05-22 — Resort detail modal and blackout calendar
**Issue:** #73  
**Decision:** Resort detail opens in an antd `Modal` (600px wide). Blackout dates render in an antd `Calendar` with `fullCellRender` — colored circles over each date (standard=magenta, LTT=cyan, both=diagonal split gradient). Today gets a border ring only (transparent fill so blackout color shows through). Out-of-month dates fade to 10% opacity. Month state persists across modal opens via a module-level variable (`sharedCalendarMonth`) that survives `destroyOnClose` unmounting. All three navigation paths (dropdowns, prev/next buttons, clicking an out-of-month date) route through the same `setMonth()` setter, which also updates the shared variable.  
**Rationale:** `fullCellRender` replaces the entire cell (vs. `cellRender` which appends below the date number, causing double rendering). Module-level variable chosen over context/localStorage to avoid prop drilling with no persistence requirement across page reloads. Color pair (magenta + cyan) selected for sufficient contrast against each other and against white text/dark text respectively.  
**Follow-up:** None — settled.

---
## 2026-05-22 — Resort detail charts and Peak Rankings (#74, #75)
**Issue:** #74, #75  
**Decision:** Added three chart/stat sections to the resort detail modal. Elevation shown as a vertical stat stack (Summit/Drop/Base) with a cyan left-border accent — no chart, since any bar would imply proportionality from sea level that's visually misleading. Trail difficulty uses a Recharts PieChart with the legend to the left; colors follow ski trail convention (green `COLORS.difficultyBeginner` / cyan / graphite `COLORS.textMuted`). Snowfall is a simple two-bar Recharts BarChart (average vs. max). Peak Rankings (#75) is pure data: total score + ranks prominently at top, 10 category scores in a 5-column grid with mini progress bars (0–10 scale), and an extras grid for lodging, après, access road, ability range, nearest cities, and pass affiliation. Recharts added as a dependency.  
**Rationale:** Elevation chart approaches (stacked bar, waterfall) all imply sea-level proportionality; stat boxes are unambiguous. Difficulty colors chosen for colorblind accessibility — green/cyan/graphite separate by both hue and value. Peak Rankings section hidden entirely when pr_total is null.  
**Follow-up:** None — settled.

---
## 2026-05-23 — Resort data table implementation (#72)
**Issue:** #72  
**Decision:** AG Grid Community Edition (v35) with explicit `width` on every column in `COLUMN_DEFS`. No auto-sizing.  
**Rationale:** `autoSizeAllColumns()` is unreliable in v35 — inflates columns with long headers disproportionately to data density. `maxWidth` in `defaultColDef` initializes all columns to that value rather than acting as a ceiling. Explicit widths tuned per-column are the only reliable approach at this version.  
**Follow-up:** Revisit auto-sizing if AG Grid fixes the behavior in a future release.

---
## 2026-05-23 — Table toolbar lifted to App.jsx drag handle
**Issue:** #72  
**Decision:** Table controls (Select Columns popover, Download CSV, Full screen) live in App.jsx's drag handle row, not inside ResortTable. ResortTable is a `forwardRef` component; App.jsx holds `gridRef` and calls AG Grid APIs directly. `COLUMN_DEFS`, `HEADER_BY_FIELD`, and `COL_GROUPS` are named exports from ResortTable.jsx.  
**Rationale:** Consolidating the drag handle and toolbar into one row eliminates a redundant UI strip and removes duplicate search bars (the table quick-filter conflicted with the sidebar search). The `forwardRef` pattern keeps ResortTable a pure grid renderer with no toolbar concerns.  
**Follow-up:** None — settled.

---
## 2026-05-24 — Pipeline backup strategy and data deployment approach
**Issue:** #76, #77
**Decision:** Pipeline backs up `resorts.csv`, `resort_id_map.csv`, and `pipeline_metadata.json` to `backups/YYYY-MM-DDTHH-MM-SS/` before any steps run, keeping the 10 most recent. Cache HTML is excluded (large, regenerable). Naming convention uses ISO 8601 with hyphens replacing colons. Automated pipeline (#77) will open a PR rather than auto-committing to main — human reviews the data diff before merging. Pre-PR sanity check runs `load_resorts()` against the new CSV; requires #83 (Pydantic validation) first.
**Rationale:** App seasonality means bad data could go unnoticed for months. PR-based promotion gives a human gate without requiring a staging environment. Backup-before-run gives a fast local restore path without touching git history.
**Follow-up:** #83 must be completed before #77's validation step is implemented.

---
## 2026-05-23 — Centralized color system in theme.js
**Issue:** #72 (polish)  
**Decision:** All color values in `frontend/src/` must reference named tokens from `COLORS` in `src/theme.js`. No hardcoded hex or rgba strings in `.jsx` or `.css` files. CSS files bridge to theme values via CSS custom properties set in `GRID_THEME_VARS` (e.g. `--indy-header-bg`). The `withAlpha(hex, alpha)` utility generates rgba strings from theme hex values.  
**Rationale:** One audit found `COLORS.accent` (undefined), two unique greens, and three similar greys scattered across components. Centralizing prevents drift and makes visual changes a single-file edit.  
**Follow-up:** When adding new colors, add to `COLORS` in theme.js first, then reference by name.

---
## 2026-05-24 — Deployment: Fly.io + Vercel split
**Issue:** #100  
**Decision:** Backend on Fly.io (`indy-explorer-backend`, region `ewr`), frontend on Vercel. Frontend proxies `/api/:path*` → `https://indy-explorer-backend.fly.dev/:path*` via `vercel.json` rewrite — no CORS config needed. Docker image built from repo root so `data/` is baked in at deploy time (not read from a volume).  
**Rationale:** Vercel is purpose-built for static SPAs (CDN, zero-config GitHub auto-deploy). Fly.io handles the containerized FastAPI. All-Fly.io was considered but requires nginx and has no global CDN equivalent. Baking `data/` into the image keeps the backend stateless and dead-simple to deploy; after a pipeline data update, redeploy the backend.  
**Follow-up:** After a pipeline data update, both `data/resorts.csv` must be committed to main AND the backend must be redeployed (`flyctl deploy --config backend/fly.toml`) for new data to appear in the live app.

---
## 2026-05-25 — Keep Fly.io machine warm to eliminate cold starts
**Issue:** #106
**Decision:** Set `min_machines_running = 1` in `backend/fly.toml` (was 0). One machine runs continuously instead of spinning down on idle.
**Rationale:** With `min_machines_running = 0`, the first request after any idle period incurred a ~2–3s cold start — bad first impression for Facebook link clicks. Cost is ~$3–4/month in prepaid Fly.io credits.
**Follow-up:** None.

---
## 2026-05-31 — UI polish batch: tooltips, sidebar filters, mobile chrome
**Issue:** #116 / #117
**Decision:** Map tooltip reduced from 14 rows to 6 (Resort, Location, Acres, Vertical, Trails, Lifts); US resorts omit country from Location. Sidebar "Blackout Dates" section renamed "Planning" and absorbs Reservation Required; sub-headings added for Lift Ticket / Learn to Turn. LTT expanded to "Learn to Turn" throughout. New Yes/No toggles for "Has Peak Rankings" and "Blackout dates" (`has_blackouts` backend param added). `FeatureToggle` exported and reused rather than duplicated. Sticky section headers added to sidebar. Mobile chrome slimmed (header 56→40px, tab bar 48→36px). Playwright added as frontend dev dependency for UI verification.
**Rationale:** Tooltip was overwhelming quick-glance UX — detail belongs in the modal. "Planning" groups logistically-related filters (reservations, blackouts) that were scattered. LTT is not a known initialism outside Indy Pass context. Mobile chrome consumed ~30% of screen on small phones.
**Follow-up:** `has_blackouts` Yes/No toggle for Learn to Turn blackouts not added (would require separate backend param — deferred).

---
## 2026-07-11 — Popup/popover design language: unified dark-border panel
**Issue:** #110
**Decision:** All popup surfaces (feedback footer, mobile ⓘ, Select Columns) use a consistent pattern: `2px solid COLORS.bgHeader` border, `borderRadius: 4`, no arrow, dark `COLORS.bgOverlay` overlay that dismisses on click. Desktop "Select Columns" and footer feedback use `position: fixed` centered panels; mobile panels are `position: absolute` above the tab bar. antd Popover dropped for these surfaces in favor of hand-rolled divs to guarantee consistent styling. Popup content uses colored dot + section title (matching sidebar), bulleted `COLORS.text` links, smaller muted footnotes (`fontSize: 10`).
**Rationale:** Each surface was previously bespoke (antd Popover with overrides, custom divs, different borders/shadows). Unifying removes visual drift and makes future changes easier. antd Popover's placement logic was unreliable on short viewports — fixed centering is more predictable.
**Follow-up:** #120 tracks extracting these into shared primitives so the pattern doesn't have to be re-implemented per surface.

---
## 2026-05-25 — Theme color pass: 80s ski-punk palette
**Issue:** #107
**Decision:** Expanded color palette in `theme.js` with `accentBlue` (#3d52ff), `accentPurple` (#9b00e6), `bgMidtone` (#505050), deepened `primary` to #00c4d4 and `success` to #b4f000 (chartreuse). Map dots: pink=alpine, electric blue=XC, purple=both (pink+blue=purple). Difficulty pie chart: chartreuse=beginner, blue=intermediate, grey=advanced (matches real trail markers). PR bars colored by score value (green/yellow/pink). Dark anchor bands: near-black header, charcoal search band and table drag handle, charcoal table column headers. Features section redesigned as "Label: Yes/No" grid. Neon colors used on dark surfaces; functional colors carry semantic meaning throughout.
**Rationale:** Original theme used only hot pink and pale cyan; neons were invisible on white. Key insight: neons only work on dark surfaces — structural dark bands provide the canvas. Color choices are functional (map dot mixing, trail marker convention, traffic-light PR scores) not purely decorative.
**Follow-up:** Dark mode (future) will unlock full neon palette across the whole surface.

---
## 2026-07-11 — Retire Streamlit app; replace with redirect page
**Issue:** #121
**Decision:** `app.py` replaced with a minimal Streamlit redirect page (~17 lines) and moved to `legacy/app.py` (along with `.streamlit/config.toml` → `legacy/.streamlit/config.toml`). All 1480 lines of Streamlit app code removed. `README.md` rewritten to present the React/FastAPI stack as the primary app. `CLAUDE.md` updated to describe `legacy/app.py` as "redirect notice only." Button color set to `accentBlue` (#3d52ff). Page content centered via CSS injection.
**Rationale:** React app has full feature parity and loads instantly (no cold start). Streamlit had a 5–10s cold start that was the main user complaint. Keeping `app.py` as a live redirect rather than deleting it preserves the Community Cloud URL so existing bookmarks and shared links forward correctly.
**Follow-up:** After redeploying on Streamlit Community Cloud, confirm the live redirect works before merging this PR.

---
## 2026-07-11 — Playwright MCP output directory
**Issue:** #124
**Decision:** Playwright MCP artifacts (screenshots, accessibility snapshots, console/network logs) are scoped to `.playwright-mcp/` at the repo root, which is now gitignored. `CLAUDE.md` documents the convention: pass `filename` as `.playwright-mcp/<name>.png` on `browser_take_screenshot` calls.
**Rationale:** A screenshot taken with a bare filename landed at the repo root as untracked cruft. `.playwright-mcp/` was already the tool's default location for snapshot/console log files, so it was reused rather than introducing a second directory.
**Follow-up:** None — settled. Confirmed Playwright MCP works end-to-end against the local dev servers (navigate, snapshot, screenshot) once a macOS system-permission prompt was cleared.

---
## 2026-07-11 — Shared Panel/Overlay primitives + unified dim-focus tiers
**Issue:** #120
**Decision:** Extracted `frontend/src/components/common/Panel.jsx` (bordered box, optional close button, exports `PANEL_STYLE` for antd consumers) and `Overlay.jsx` (dismiss-on-click dim layer, exports `OVERLAY_Z_INDEX`/`PANEL_Z_INDEX`). Applied across Select Columns and mobile ⓘ (App.jsx), the Feedback popover (Footer.jsx), Map Legend/Attribution (ResortMap.jsx), and the map hover tooltip. Settled on two dim tiers: **ambient** (no dim — Feedback, Map Legend, Map Attribution/desktop ⓘ) and **soft** (~45% — How To Use, Resort Detail, Select Columns, mobile ⓘ). `COLORS.bgOverlay` changed from `rgba(0,0,0,0.75)` to `rgba(0,0,0,0.45)` to match antd's default modal mask.
**Rationale:** Before touching code, audited actual dim behavior with pixel-sampled screenshots (not just visual inspection — a genuine leak, described below, was invisible to the eye but showed up clearly in RGB deltas) across desktop/mobile × sidebar-expanded/collapsed. Found real inconsistencies: Feedback and Map Legend/Attribution had 0% dim, Select Columns had 75% dim with a bug — the sidebar's Collapse section headers all set `zIndex: 10` (`Sidebar.jsx`) against the overlay's `zIndex: 8`, so every section header (not just the expanded one) punched through undimmed — and mobile ⓘ had 75% dim vs. its desktop equivalent's 0%. User's call: 75% read as overdone for anything, so both "should dim" surfaces converge on one soft value instead of a 3-tier system.
**Follow-up:** Fixed the leak at the source — `Sidebar.jsx`'s `stickyHeader` zIndex dropped from 10 to 1, since it only needs to clear its own scrolled-under content locally, not app-wide overlays. Follow-on fixes to the map tooltip and the two full-page modals are logged separately below.

---
## 2026-07-11 — Map tooltip clipping fix, and full-modal border consistency
**Issue:** #120
**Decision:** The map hover tooltip (`MapTooltip` in `ResortMap.jsx`) now clamps its position within the map container instead of using CSS `flip`-to-opposite-side math (`bottom: calc(100% - y + 8)`), and adopts `Panel`'s bordered style like the Legend/Attribution it shares the map with. `onHover` now computes clamped `left`/`top` pixel values directly, bounded to `[4, container size − tooltip size − 4]` on both axes. `ResortDetailModal` was reworked to match `HowToUseModal`'s already-correct viewport-constrained layout (fixed dark header, independently scrollable body capped to `calc(100vh - ...)`, mobile full-screen) instead of only capping the inner `body` to `85vh` with no cap on the modal as a whole. Both `HowToUseModal` and `ResortDetailModal` now also get a `2px solid COLORS.bgHeader` border around the whole modal (desktop only — mobile stays edge-to-edge), matching the small-popup border language established above, layered outside the existing 2px white inset frame (not replacing it — a border-only version read as a flat double-ring; user preferred keeping the white gap between the border and the dark header).
**Rationale:** The tooltip clip was a real, if narrow, bug: `Layout.Content` has `overflow: hidden` (App.jsx), and when the map area is short (table expanded) and a hovered dot sits near the container's bottom edge, the flipped tooltip's calculated top could land above `Layout.Content`'s own top edge and get silently clipped, hiding the "Resort"/"Location" rows. Diagnosed via `elementFromPoint` first, which was a dead end — the tooltip's `pointer-events: none` makes hit-testing skip it regardless of visual paint order — then confirmed via ancestor `overflow`/rect inspection and pixel-level before/after screenshots. `ResortDetailModal` had the same class of bug (only `body` was height-capped, not the modal as a whole) plus no border at all, both caught by the user directly. Bold borders on the two full modals were a deliberate design call (not just consistency): the app's "bold, high-contrast" aesthetic direction (`docs/design.md`) favors it over a plain white antd edge, at the cost of modals losing a bit of "bigger, different kind of surface" distinction from the small popups.
**Follow-up:** None — settled.

---
## 2026-07-11 — Map area now clips its own overlays (Legend/Attribution/Tooltip)
**Issue:** #120
**Decision:** The desktop and mobile map wrapper `div`s in `App.jsx` gained `overflow: hidden`. `MapLegend` and `MapAttribution` (`ResortMap.jsx`) gained `maxHeight: calc(100% - 16px)` + `overflowY: auto` so they scroll internally rather than overflowing when the map area is short.
**Rationale:** With a short map area (table expanded), the Legend panel — anchored `top: 8, left: 8` with no height constraint — could grow taller than the map itself and visually spill onto the "Hide data table" drag-handle bar below it, a section the user correctly identified as not part of the map. Since the map wrapper had no `overflow` set, nothing stopped an absolutely-positioned child from rendering past its bottom edge into the next flex sibling. The fix contains the map's own decorations to the map's own box — the same principle as the tooltip clamp above, applied to Legend/Attribution, which didn't need clamping before because their fixed anchor position was never tested against a short container.
**Follow-up:** None — settled.

---
## 2026-07-11 — Select Columns gets the same header/border treatment as full modals
**Issue:** #120
**Decision:** The Select Columns panel (`columnsPanel()` helper in `App.jsx`, used by both the desktop centered popup and the mobile above-tab-bar popup) now has a dark `bgHeader` title bar ("SELECT COLUMNS") with a close button, matching `HowToUseModal`/`ResortDetailModal`'s header — including the same 2px white inset frame between the outer border and the header (`padding: 2` on the `Panel`, not just a flush border). Desktop width increased from 340px to 440px. The panel is now a flex column (`Panel` sets `overflow: hidden`; an inner `div` handles the independent scroll), same structural pattern as the two full modals.
**Rationale:** The user pointed out the panel felt cramped (dense 2-column checkbox groups in a 340px box) and had no title at all — no context for what the popup was if you saw it out of context. It's the most content-heavy of the small popups, so it made sense to borrow the full-modal treatment rather than stay in the bare small-popup style used by Feedback/Legend/Attribution/tooltip, which are much lighter-weight by comparison. Applied to mobile too, per explicit confirmation, despite the tighter vertical space.
**Follow-up:** None — settled.

---
## 2026-07-11 — Extracted ModalHeader/ModalShell: the big-surface pattern was copy-pasted, not shared
**Issue:** #120
**Decision:** New `frontend/src/components/common/ModalHeader.jsx` (title/subtitle/onClose/titleFontSize → the dark header bar + close button) and `ModalShell.jsx` (wraps antd `Modal` with the viewport-constrained desktop/mobile sizing: bold border + white inset frame on desktop, full-bleed on mobile). `HowToUseModal.jsx` and `ResortDetailModal.jsx` now both use `ModalShell` + `ModalHeader` instead of independently duplicating the same ~20-line `Modal` `styles` block and the same header markup. `App.jsx`'s `columnsPanel()` now uses `ModalHeader` inside its `Panel` wrapper instead of a third hand-copy of the header. `ModalShell` also replaces the old magic-number `calc(100vh - ${gap*2+60}px)` / `+76` height estimates with a flex-column layout (`container: {display:'flex', flexDirection:'column', maxHeight: calc(100vh - gap*2)}`, body `flex:1, minHeight:0`) — the header is `flexShrink:0` and content is `flex:1, overflowY:auto`, so it self-sizes correctly regardless of header height instead of needing a hand-tuned pixel constant per modal.
**Rationale:** Prompted by the user directly asking whether the modal work was actually DRY. It wasn't — three files independently reimplemented the same dark-header-bar-with-close-button chrome, and two of them duplicated the entire antd `Modal` viewport-constraint config byte-for-byte (only width and a `destroyOnHidden` flag differed). Verified no visual regression: screenshotted all three surfaces (desktop + mobile) before and after and confirmed pixel-identical output.
**Follow-up:** None — settled.
