# Planning

Current work-in-progress. Update this file at the start and end of every session.

---

## Current Branch

`feature/100-deploy-fly-vercel` — deployment config; PR open, pending merge + Vercel setup

## Status (as of 2026-05-24)

### React rewrite — feature complete

All user-facing work is merged to main:

- **#51–#64** Backend (FastAPI endpoints, data model), frontend shell, API client, location filters
- **#65–#68** Filter sidebar (features, blackout dates, Peak Rankings), resort results count
- **#69–#71** Map component, tooltips (quadrant-aware positioning), auto-zoom
- **#72–#75** Resort data table (AG Grid), detail modal, charts, Peak Rankings section
- **#70** Map tooltip smart positioning — merged with #72–#75 branch

### Deployment — in progress (#100)

- **Backend (Fly.io):** Live at `https://indy-explorer-backend.fly.dev` ✓
- **Frontend (Vercel):** Pending — merge #100 branch first, then create Vercel project pointing to `main`

### Remaining open

| # | Description | Type | Notes |
|---|---|---|---|
| #76 | Pipeline output compatibility | Infrastructure | **Done** ✓ |
| #100 | Deploy backend to Fly.io + frontend to Vercel | Infrastructure | Backend live ✓; frontend pending Vercel setup |
| #83 | Data validation on Resort Pydantic model | Backend hardening | Must be done before #77 |
| #77 | GitHub Actions scheduled pipeline | Infrastructure | Depends on #83; revised to PR-based data promotion (no auto-commit to main) |
| #11 | Bug: metrics parsing for alpine+XC resorts | Pre-rewrite bug | |
| #21 | Include all resorts, filter down to Indy | Future enhancement | |
| #22 | Add RV parking data/filter | Future enhancement | |

**Next up:** Merge #100 → finish Vercel setup → #83 → #77.

**#77 revised scope:** Pipeline runs on a schedule and opens a PR against main rather than auto-committing. Human reviews the data diff before merging. Pre-PR sanity check runs `load_resorts()` against the new CSV — any Pydantic validation failures abort the job before a PR is opened. See issue for full acceptance criteria.

Check the project board: https://github.com/users/jonathanstelman/projects/2
