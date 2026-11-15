"""Run from project root: python -m uvicorn backend.main:app --port 8000"""
from threading import Lock
from pathlib import Path
from typing import Annotated, Literal
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from requests import RequestException
from .pipeline import CACHE, build_observations
from .archive_http import ArchiveError

app = FastAPI(title='PARALLAX Observatory', version='1.0.0', description='SPHEREx archive discovery and aligned cutout previews. No synthetic fallback.')
app.mount('/api/cache', StaticFiles(directory=CACHE), name='cache')
processing_lock = Lock()

@app.get('/api/health')
def health():
    return {'status': 'ok', 'source': 'NASA/IPAC IRSA', 'synthetic_fallback': False}

@app.get('/api/observations')
def observations(
    ra: Annotated[float, Query(ge=0, lt=360, allow_inf_nan=False)],
    dec: Annotated[float, Query(ge=-90, le=90, allow_inf_nan=False)],
    fov: Annotated[float, Query(ge=1, le=30, allow_inf_nan=False)] = 6,
    detector: Literal['D1', 'D2', 'D3', 'D4', 'D5', 'D6'] = 'D2',
):
    if not processing_lock.acquire(blocking=False):
        raise HTTPException(429, 'Another field is being prepared. Please retry shortly.')
    try:
        return build_observations(ra, dec, fov, detector)
    except ArchiveError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc
    except RequestException as exc:
        raise HTTPException(502, 'IRSA is unavailable or timed out. Please retry in a moment.') from exc
    except ValueError as exc:
        raise HTTPException(502, str(exc)) from exc
    finally:
        processing_lock.release()

# After `npm run build`, the same Python server can serve the complete application.
# API routes above take precedence over the static frontend.
DIST = Path(__file__).resolve().parents[1] / 'dist'
if DIST.is_dir():
    app.mount('/', StaticFiles(directory=DIST, html=True), name='frontend')
