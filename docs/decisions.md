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
