# Planning

Current work-in-progress. Update this file at the start and end of every session.

---

## Current Branch

`main` (no active feature branch)

## Status (as of 2026-05-25)

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
| #106 | Cold start: keep Fly.io machine warm | P1 | |
| #83 | Data validation on Resort Pydantic model | P1 | Blocks #77 |
| #77 | GitHub Actions scheduled pipeline | P1 | Depends on #83 |
| #11 | Bug: alpine+XC metrics parsing | P1 | |
| #108 | Design: theme color pass | P2 | |
| #107 | UX: Peak Rankings visual encoding | P2 | |
| #109 | UX: "How to use" first-load popover | P2 | |
| #110 | UX: "Help improve this app" feedback section | P2 | |

**Next up:** #106 (cold start / keep Fly.io warm) or #83 (Pydantic data validation, blocks #77).

**#77 revised scope:** Pipeline runs on a schedule and opens a PR against main rather than auto-committing. Human reviews the data diff before merging. Pre-PR sanity check runs `load_resorts()` against the new CSV — any Pydantic validation failures abort the job before a PR is opened. See issue for full acceptance criteria.

### Future enhancements (post-launch)

| # | Description |
|---|---|
| #21 | Include all resorts, filter down to Indy |
| #22 | Add RV parking data/filter |

Check the project board: https://github.com/users/jonathanstelman/projects/2
