# Planning

Current work-in-progress. Update this file at the start and end of every session.

---

## Current Branch

`main` (no active feature branch)

## Status (as of 2026-05-30)

### React rewrite — feature complete and deployed

- **#51–#64** Backend (FastAPI endpoints, data model), frontend shell, API client, location filters
- **#65–#68** Filter sidebar (features, blackout dates, Peak Rankings), resort results count
- **#69–#71** Map component, tooltips (quadrant-aware positioning), auto-zoom
- **#72–#75** Resort data table (AG Grid), detail modal, charts, Peak Rankings section
- **#76** Pipeline output compatibility (backup step, pipeline metadata, README)
- **#100** Deployed: backend at `https://indy-explorer-backend.fly.dev`, frontend at `https://indy-explorer.vercel.app`

### Epic 7: Pre-release polish — in progress (#102)

Target: public launch on Indy Pass Facebook groups ahead of ski season.

| # | Description | Priority | Status |
|---|---|---|---|
| #103 | Mobile: filter sidebar inaccessible | P0 | Done |
| #104 | Bug: "Last updated" not populating | P0 | Done |
| #105 | Mobile: toolbar and footer layout broken | P0 | Done |
| #106 | Cold start: keep Fly.io machine warm | P1 | Done |
| #107 | Design: theme color pass | P2 | Done |
| #109 | UX: Peak Rankings visual encoding | P2 | Done |
| #108 | UX: "How to use" first-load popover | P2 | |
| #110 | UX: "Help improve this app" feedback section | P2 | |
| #83 | Data validation on Resort Pydantic model | P1 (deferred) | Blocks #77 |
| #77 | GitHub Actions scheduled pipeline | P1 (deferred) | Depends on #83 |
| #11 | Bug: alpine+XC metrics parsing | P1 | |

**#113 merged and deployed (2026-05-30):**
- Map/Table tab switcher, footer hidden, unified attribution ⓘ in tab bar
- Collapsible map legend (top-left, outside DeckGL, format_list_bulleted icon)
- Modal: responsive features/PR grids, pie chart hidden on mobile
- PR score bars: 5-color scale (prMid #8b6ab5, prTop #40b050)

**Next up:** #108 ("How to use" first-load popover) or #110 ("Help improve this app" feedback section).

**#83/#77 deferred:** Cosmetic P2 issues take priority over automated pipeline work — the data being a day or two out-of-date isn't consequential right now.

**#77 revised scope:** Pipeline runs on a schedule and opens a PR against main rather than auto-committing. Human reviews the data diff before merging. Pre-PR sanity check runs `load_resorts()` against the new CSV — any Pydantic validation failures abort the job before a PR is opened. See issue for full acceptance criteria.

### Future enhancements (post-launch)

| # | Description |
|---|---|
| #21 | Include all resorts, filter down to Indy |
| #22 | Add RV parking data/filter |

Check the project board: https://github.com/users/jonathanstelman/projects/2
