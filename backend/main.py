from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from typing import Optional

from data import load_resorts
from models import ResortSummary

_resorts: list[ResortSummary] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _resorts
    _resorts = [ResortSummary(**r.model_dump()) for r in load_resorts()]
    yield


app = FastAPI(title="Indy Explorer API", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/resorts", response_model=list[ResortSummary])
def get_resorts(
    search: Optional[str] = Query(default=None),
    region: list[str] = Query(default=[]),
    country: Optional[str] = Query(default=None),
    state: Optional[str] = Query(default=None),
):
    results = _resorts

    if search:
        term = search.lower()
        results = [
            r
            for r in results
            if term in (r.name or '').lower()
            or term in (r.city or '').lower()
            or term in (r.state or '').lower()
            or term in (r.country or '').lower()
        ]

    if region:
        region_set = {v.lower() for v in region}
        results = [r for r in results if (r.region or '').lower() in region_set]

    if country:
        c = country.lower()
        results = [r for r in results if (r.country or '').lower() == c]

    if state:
        s = state.lower()
        results = [r for r in results if (r.state or '').lower() == s]

    return results
