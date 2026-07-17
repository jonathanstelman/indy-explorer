# Planning

Current work-in-progress. Update this file at the start and end of every session.

---

## Current Branch

`feature/139-acreage-filter` — **#139 implemented, not yet committed/PR'd**: added `min_acres`/`max_acres` range filter, following the existing numeric-range-filter pattern exactly. Backend: query params + `range_filters` entry in `backend/main.py`, `acres: RangeField` on `MetaResponse` in `backend/models.py`. Frontend: `min_acres`/`max_acres` in `useFilters.js`, new `Acreage` `RangeSlider` in `StatsFilters.jsx` (placed between Vertical and Lifts per the established field-order convention). Acreage's slider uses a log-scale track (`logScale` prop on `RangeSlider`) since 83% of resorts sit under 1,000 acres but the range runs to 19,136 — a linear track crammed most resorts into a few pixels. The same log-scale treatment was tried on Lifts too but reverted per user feedback ("not smooth") — Lifts stays linear. Backend tests written first (TDD) in `test_resorts_feature_filters.py` and `test_meta_endpoint.py`, confirmed failing then passing. Verified live via Playwright against dev servers — both sliders filter map/table/count correctly and sync to the URL; zero new console errors or lint findings. All tests + Black pass. See `docs/decisions.md` for full detail. Remaining: commit, open PR, merge.

**Previously merged: #132 (2026-07-15, PR #142)**: dropped `vertical_meters`/`trail_length_km`/`acres_tt`/`vertical_tt` from `backend/models.py` (`Resort`, `ResortSummary`, `_NONNEG_BOUNDS`) and from `pipeline/prep_resort_data.py`'s computation + output columns; `feet_to_meters()` removed (its only caller). Regenerated `data/resorts.csv` locally (all inputs already cached — no live API calls). New backend test asserts the fields are gone from both models. Follow-up filed as **#138**: broader grep found `location_name_tt`/`num_trails_tt`/`num_lifts_tt`/`pr_total_tt` are also unused in the frontend today — out of this issue's scope, left for separate cleanup.

**Same PR, unrelated UI consistency pass** (no issue — ad hoc live-review polish): color tokens (unit picker, "?" button, How-to-use unit chips → `COLORS.error`), field display order normalized across map tooltip / sidebar filters / table / detail modal (Vertical→Summit→Base, Acreage→Lifts→Trails→Trails (XC)→Trail Length (XC); table's Allied/Reservations/Blackout/LTT column order), hide-when-null for XC-only resorts' Acreage/Lifts/Summit/Base/Trail Length (XC) (tooltip height calc refactored to match via a shared `buildTooltipRows()`), Allied added to the detail modal's Features grid, a few antd deprecation/dead-code cleanups. Filed **#139** (no acreage filter despite acreage being shown prominently), **#140** (Peak Rankings Pass Affiliation filter), **#141** (pre-existing `npm run lint` findings — a real conditional-hook bug in `Footer.jsx` plus a `setState`-in-effect cluster). See `docs/decisions.md` for full detail.

**Next up (after #139 merges):** open backlog: **#138** (unused `_tt` fields, P3), **#140** (Peak Rankings Pass Affiliation filter), **#141** (lint cleanup — includes a real `Footer.jsx` conditional-hook bug), **#136** (data-changed pipeline verification, scheduled ~Nov 2026), plus older backlog **#21**/**#22**. No priority set among #138/#140/#141 yet — ask the user which to pick up.

**#134 merged (2026-07-14, PR #137)**: `generate_resort_locations_csv()` (`pipeline/utils.py`) is now incremental by default (reads existing `resort_locations.csv`, geocodes only resorts missing by name, appends rather than overwrites); `full=True` re-geocodes everything as an explicit escape hatch. `step_geocode()` (`pipeline/pipeline.py`) no longer skips the whole step when the cache file exists — it always runs, now cheap when nothing's missing. `docs/ops-runbook.md` updated to drop the stale "full refresh ~quarterly" guidance.

**#77 merged and closed (2026-07-13, PR #135); no-change path verified live**: first real `workflow_dispatch` run succeeded (4m12s — 277 pages scraped, validation passed with zero soft-nulls, timestamp-only guard fired correctly, PR step no-op'd with no noise). The `automated-data-update` label was missing from the repo (workflow referenced it but it was never created) — created 2026-07-13.

**Data-changed path verification split into #136**, scheduled ~early November 2026 (Indy Pass resort data typically doesn't shift until next-season info is published Oct/Nov) — no longer blocking delivery. Checklist (PR opens correctly, PR body renders correctly, diff scoped to `data/`, update-in-place on a second run, hard-fail path, `full=true` input, weekly cron) lives on the issue, not here.

Minor follow-up from run annotations: `actions/*@v4` + `create-pull-request@v6` target deprecated Node 20 in both workflows — trivial version bumps for a future housekeeping pass.

**#83 merged (2026-07-13)**, PR #133: data validation on `Resort` Pydantic model — bounded `field_validator`s (soft log+null) plus hard `indy_page` URL constraint. See `docs/decisions.md` for rationale.

**#128 (unit selector) merged and deployed (2026-07-13)**, PR #131. Follow-up issue **#132** opened (low priority): drop now-unused `vertical_meters`/`trail_length_km` (and check `vertical_tt`/`acres_tt`) from the pipeline/backend model now that the frontend converts client-side instead of reading precomputed columns.

**#118 merged and deployed (2026-07-12):** AG Grid Theming API migration — see `docs/decisions.md` for the full trail (real prior styling was mostly silently broken; row hover, checkmark contrast fix, header separator investigation).

**#11 merged and deployed (2026-07-12):** Parser `-xc` extraction, `num_trails_xc` + 3 `difficulty_*_xc` columns in `resorts.csv` output, backend model/filters/meta, and frontend surfacing (sidebar slider, table columns, map tooltip, detail modal difficulty chart). Frontend went through several UI iterations after live review — a `view`/display-mode concept (shared `ViewSelector`, independent URL filter, mode-aware hiding) was built, polished, then removed entirely once the real scope was named as one filterable field (`num_trails_xc`) and three display-only ones — not enough to justify it. Final shape: `has_alpine`/`has_cross_country` are ordinary boolean filters; `Trails (XC)` is a plain always-shown sidebar slider; `num_trails_xc`/`difficulty_*_xc` are ordinary optional table columns; the map tooltip's XC row is a per-resort presence check (suppressed for XC-only resorts, where it's always identical to `Trails`), matching the detail modal's existing pattern. See `docs/decisions.md` for the full history and reusable UI patterns worth keeping. Frontend auto-deployed via Vercel, backend manually deployed to Fly.io — verified live in production (`/meta` and `/resorts` both serving real `num_trails_xc`/`difficulty_*_xc` values).

## Status (as of 2026-07-11)

### React rewrite — feature complete and deployed

- **#51–#64** Backend (FastAPI endpoints, data model), frontend shell, API client, location filters
- **#65–#68** Filter sidebar (features, blackout dates, Peak Rankings), resort results count
- **#69–#71** Map component, tooltips (quadrant-aware positioning), auto-zoom
- **#72–#75** Resort data table (AG Grid), detail modal, charts, Peak Rankings section
- **#76** Pipeline output compatibility (backup step, pipeline metadata, README)
- **#100** Deployed: backend at `https://indy-explorer-backend.fly.dev`, frontend at `https://indy-explorer.vercel.app`

### Epic 7: Pre-release polish — done, #102 closed (2026-07-14)

Target: public launch on Indy Pass Facebook groups ahead of ski season. All P0/P1/P2 items complete; app is live. #132/#134/#136 are separate follow-up issues filed during Epic 7 work — not part of the closed checklist, still open below.

| # | Description | Priority | Status |
|---|---|---|---|
| #103 | Mobile: filter sidebar inaccessible | P0 | Done |
| #104 | Bug: "Last updated" not populating | P0 | Done |
| #105 | Mobile: toolbar and footer layout broken | P0 | Done |
| #106 | Cold start: keep Fly.io machine warm | P1 | Done |
| #107 | Design: theme color pass | P2 | Done |
| #109 | UX: Peak Rankings visual encoding | P2 | Done |
| #108 | UX: "How to use" first-load popover | P2 | Done |
| #110 | UX: "Help improve this app" feedback section | P2 | Done |
| #83 | Data validation on Resort Pydantic model | P1 | Done |
| #77 | GitHub Actions scheduled pipeline | P1 | Done (cron deferred) |
| #11 | Bug: alpine+XC metrics parsing | P1 | Done |
| #118 | AG Grid Theming API migration | P2 | Done |
| #128 | Unit selector (imperial/metric) | P2 | Done |
| #132 | Drop unused vertical_meters/trail_length_km | P3 | Done (2026-07-15) |
| #134 | Bug: geocoding all-or-nothing, new resorts get no city/state/country | P2 | Done |
| #136 | Verify automated pipeline data-changed path against real source data | P3 | Open, scheduled ~Nov 2026 |
| #138 | Remaining unused `_tt` tooltip fields (location_name_tt, num_trails_tt, num_lifts_tt, pr_total_tt) | P3 | Open, not started |

**#113 merged and deployed (2026-05-30):**
- Map/Table tab switcher, footer hidden, unified attribution ⓘ in tab bar
- Collapsible map legend (top-left, outside DeckGL, format_list_bulleted icon)
- Modal: responsive features/PR grids, pie chart hidden on mobile
- PR score bars: 5-color scale (prMid #8b6ab5, prTop #40b050)

**#114 merged (2026-05-30):**
- Trail Difficulty legend always visible on mobile (pie chart hidden, legend shown)
- Trail Difficulty + Snowfall always side-by-side (removed mobile single-column override)

**#115 merged (2026-05-31):**
- Peak Rankings bars: continuous HSL color scale replacing 5-step discrete palette
- Anchor stops at 1/4/7/9 (calibrated to actual score distribution, bell curve ~5–6)
- Added `hexToHsl` helper and `prScore1`/`prScore10` tokens to theme.js

### UI polish queue (#116)

Small tasks interspersed with larger feature work. Check off here and in the GitHub issue as completed.

- [x] Simplify resort tooltips
- [x] Pinned filter section headers in sidebar
- [x] Expand LTT → "Learn to Turn" throughout
- [x] Sidebar: Planning section (blackout dates + reservation), has-blackouts toggle, Has Peak Rankings toggle
- [x] Align data table buttons
- [x] Reduce height of bar elements on mobile

**#119 merged (2026-07-11):**
- HowToUseModal: fixed antd v6 `styles.container` key (was `styles.content`, silently ignored), modal now content-sized on desktop, 2px white frame around dark header
- Drawer deprecation: `width={280}` → `size={280}`
- Created #118: AG Grid Theming API migration (console warning accepted for now)

**#110 merged (2026-07-11):**
- Desktop footer: "Feedback" link opens a centered fixed panel (dark border, dark overlay, dismissible)
- Mobile ⓘ popup: attribution + "Improve this App" section merged into unified panel above tab bar
- "Select Columns" popover: replaced antd Popover with centered fixed panel (desktop) and absolute panel above tab bar (mobile), both with dark overlay
- ⓘ and Select Columns panels share dark overlay that dismisses on click
- All popup surfaces now use consistent design language: `2px solid COLORS.bgHeader` border, `borderRadius: 4`, no arrow, dark overlay
- Popup content: colored dot + section title (matching sidebar), bulleted black links, muted footnotes
- Created #120: refactor all modal/popup surfaces into shared primitives (DRY)
- Created #121: retire Streamlit app (React now has full feature parity)

**#120 merged (2026-07-11), PR #127:**
- New shared primitives: `frontend/src/components/common/Panel.jsx` (bordered box + optional close button, exports `PANEL_STYLE`), `Overlay.jsx` (dim/dismiss layer, exports `OVERLAY_Z_INDEX`/`PANEL_Z_INDEX`), `ModalHeader.jsx` (dark title bar + close button), `ModalShell.jsx` (antd Modal viewport-constraint wrapper)
- Applied across Select Columns, mobile ⓘ, Feedback popover, Map Legend/Attribution, the map hover tooltip, `HowToUseModal`, and `ResortDetailModal` — every popup/modal surface in the app now shares these primitives
- Audited actual dim behavior across desktop/mobile × sidebar-expanded/collapsed (pixel-sampled, not just visual) and found real inconsistencies: Feedback/Map Legend/Attribution had 0% dim, Select Columns had 75% dim with a genuine bug (sidebar's sticky section headers used `zIndex: 10` vs. the overlay's `zIndex: 8`, so all four section headers punched through undimmed), and mobile ⓘ had 75% dim vs. desktop's 0% equivalent
- Collapsed to 2 dim tiers per user direction (75% felt "overdone"): **ambient** (no dim — Feedback, Map Legend, Map Attribution/desktop ⓘ) and **soft** (~45% — How To Use, Resort Detail, Select Columns, mobile ⓘ). `COLORS.bgOverlay` changed from `rgba(0,0,0,0.75)` to `rgba(0,0,0,0.45)` to match antd's default modal mask
- Fixed the sidebar z-index leak: `Sidebar.jsx` `stickyHeader` zIndex dropped from 10 to 1
- Fixed map hover tooltip clipping (`Layout.Content`'s `overflow: hidden` could clip it when the map area was short) by clamping its position instead of open-ended CSS flip math; gave it the shared bordered style
- Fixed `ResortDetailModal` overflowing past the viewport (only `body` was height-capped, not the modal as a whole) — now matches `HowToUseModal`'s pattern; both gained a bold border + white inset frame
- Contained Map Legend/Attribution within the map area (`overflow: hidden` on the map wrapper) so they can't spill onto the table's drag-handle bar when the map area is short
- Gave Select Columns a header (title + close button) and more width (340px → 440px) — it was cramped and had no title
- Extracted `ModalHeader`/`ModalShell` so the big-surface header/viewport-constraint pattern is shared between `HowToUseModal`, `ResortDetailModal`, and Select Columns instead of copy-pasted three times — net −48 lines despite adding two new files

**#121 merged (2026-07-11):** Streamlit `app.py` replaced with redirect page at `legacy/app.py`. Streamlit Community Cloud redeploy complete — old URL now shows the retirement notice.

**#118 merged (2026-07-12):**
- `ResortTable.jsx` migrated from AG Grid's legacy CSS-file theming (`ag-grid.css`/`ag-theme-quartz.css` + `className="ag-theme-quartz"`) to the Theming API (`themeQuartz.withParams(...)` passed via the `theme` prop) — clears AG Grid console error #239. `ResortTable.css` deleted; header background/hover/text now native theme params instead of CSS class overrides.
- Under the old CSS-conflict mode, every `--ag-*` CSS variable in the previous `GRID_THEME_VARS` was silently ignored (not just font-family) — row hover, selection color, border color, font size, and padding were all rendering AG's own hardcoded defaults, not the intended values. Rebuilt `GRID_THEME` to reproduce the real prior look (25px compact rows, system-sans font, no vertical grid lines in the data area, invisible header separators) rather than the never-actually-applied original design.
- Deliberate cosmetic upgrades bundled in since the row hover/link colors were effectively blank/wrong before: row hover is now full-saturation `COLORS.success` (chartreuse) — a fun, on-theme addition since there was no working hover before; link cell text moved from `COLORS.accentBlue` to `COLORS.accentPurple` (blue clashed badly against the new chartreuse hover); added `FONTS.sans` token for the grid's system-sans stack.
- Small cosmetic pass in the same branch: header "?" (How to use) button recolored to `COLORS.primary` (was `COLORS.textMuted`, nearly invisible on the dark header); added hover states to the footer's "Data sourced from" links (underline) and the "Select Columns"/"Download CSV"/"Feedback" controls (light background tint) via two new global utility classes in `index.css` (`.link-hover-underline`, `.toolbar-btn-hover`) — colors passed in per-instance via CSS custom properties from `COLORS`, keeping literal color values out of the CSS file.
- Also fixed `Footer.jsx`'s unrelated pre-existing antd deprecation warning (`overlayInnerStyle` → `styles.container`, same fix pattern as #119's `HowToUseModal`) — console is now fully clean on load, zero warnings or errors.
- Follow-up caught after the first commit: `BoolCell`'s true-value checkmark used `COLORS.success` — same color as the new chartreuse row hover, so checkmarks vanished on hover (green-on-green). Changed to `COLORS.bgHeader` (near-black), trading the green "yes" cue for guaranteed legibility against both white and hovered rows.

**#83 done (2026-07-13):** see Current Branch section above and `docs/decisions.md` for full detail.

**#77 revised scope:** Pipeline runs on a schedule and opens a PR against main rather than auto-committing. Human reviews the data diff before merging. Pre-PR sanity check runs `load_resorts()` against the new CSV — any Pydantic validation failures abort the job before a PR is opened. See issue for full acceptance criteria.

### Future enhancements (post-launch)

| # | Description |
|---|---|
| #21 | Include all resorts, filter down to Indy |
| #22 | Add RV parking data/filter |

Check the project board: https://github.com/users/jonathanstelman/projects/2
