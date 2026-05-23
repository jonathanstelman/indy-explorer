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
## 2026-05-22 — Resort detail modal and blackout calendar

**Issue:** #73  
**Decision:** Resort detail opens in an antd `Modal` (600px wide). Blackout dates render in an antd `Calendar` with `fullCellRender` — colored circles over each date (standard=magenta, LTT=cyan, both=diagonal split gradient). Today gets a border ring only (transparent fill so blackout color shows through). Out-of-month dates fade to 10% opacity. Month state persists across modal opens via a module-level variable (`sharedCalendarMonth`) that survives `destroyOnClose` unmounting. All three navigation paths (dropdowns, prev/next buttons, clicking an out-of-month date) route through the same `setMonth()` setter, which also updates the shared variable.  
**Rationale:** `fullCellRender` replaces the entire cell (vs. `cellRender` which appends below the date number, causing double rendering). Module-level variable chosen over context/localStorage to avoid prop drilling with no persistence requirement across page reloads. Color pair (magenta + cyan) selected for sufficient contrast against each other and against white text/dark text respectively.  
**Follow-up:** None — settled.

---
## 2026-05-22 — Resort detail charts and Peak Rankings (#74, #75)

**Issue:** #74, #75
**Decision:** Added three chart/stat sections to the resort detail modal. Elevation shown as a vertical stat stack (Summit/Drop/Base) with a cyan left-border accent — no chart, since any bar would imply proportionality from sea level that's visually misleading. Trail difficulty uses a Recharts PieChart with the legend to the left; colors borrow from ski trail convention bent toward the app theme (bright green #00C44F / cyan / graphite #555). Snowfall is a simple two-bar Recharts BarChart (average vs. max). Peak Rankings (#75) is pure data: total score + ranks prominently at top, 10 category scores in a 5-column grid with mini progress bars (0–10 scale), and an extras grid for lodging, après, access road, ability range, nearest cities, and pass affiliation. Recharts added as a dependency.
**Rationale:** Elevation chart approaches (stacked bar, waterfall) all imply sea-level proportionality; stat boxes are unambiguous. Difficulty colors chosen for colorblind accessibility — green/cyan/graphite separate by both hue and value. Peak Rankings section hidden entirely when pr_total is null.
**Follow-up:** Row alignment between ElevationStats and DifficultyChart legend is imperfect (tracked as a polish task).

---
## 2026-05-17 — Filter state
**Issue:** #64  
**Decision:** URL query params.  
**Rationale:** Users can save and share search results by copying the URL — no auth or saved-search feature needed.  
**Follow-up:** Implement before Issues #14–#18. Ensure filter params are kept clean and human-readable (e.g., `?pass=ikon&region=northeast`).
