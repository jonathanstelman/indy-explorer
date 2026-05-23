# Planning

Current work-in-progress. Update this file at the start and end of every session.

---

## Current Branch

`main` (no active feature branch)

## Status (as of 2026-05-23)

### React rewrite — feature complete

All user-facing work is merged to main:

- **#51–#64** Backend (FastAPI endpoints, data model), frontend shell, API client, location filters
- **#65–#68** Filter sidebar (features, blackout dates, Peak Rankings), resort results count
- **#69–#71** Map component, tooltips (quadrant-aware positioning), auto-zoom
- **#72–#75** Resort data table (AG Grid), detail modal, charts, Peak Rankings section
- **#70** Map tooltip smart positioning — merged with #72–#75 branch

### Remaining open

| # | Description | Type |
|---|---|---|
| #76 | Pipeline output compatibility | Infrastructure |
| #77 | GitHub Actions scheduled pipeline | Infrastructure |
| #83 | Data validation on Resort Pydantic model | Backend hardening |
| #11 | Bug: metrics parsing for alpine+XC resorts | Pre-rewrite bug |
| #21 | Include all resorts, filter down to Indy | Future enhancement |
| #22 | Add RV parking data/filter | Future enhancement |

**Next up:** #76 and #77 are the remaining rewrite-blocking items. Once done, the React app is deployable as a replacement for the Streamlit version.

Check the project board: https://github.com/users/jonathanstelman/projects/2
