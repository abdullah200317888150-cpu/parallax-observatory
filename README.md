# PARALLAX

A public-facing SPHEREx sky explorer for **Planet X and SPHEREx**, NASA Space Apps Challenge. React + TypeScript + Vite frontend; Python + FastAPI + Astropy + reproject backend.

## Run locally

Dependencies are already installed in this workspace. To launch the built application with one server:

```powershell
cd C:\Users\Alan\nasa-app
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**. The frontend and API are served together. To edit the frontend with live reload, use the two-terminal development setup below.

Use Node 22+ and Python 3.12+ with compatible scientific wheels. Run these commands from `C:\Users\Alan\nasa-app`.

```powershell
npm.cmd install
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

In one terminal, start the backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

In another, start the frontend:

```powershell
npm.cmd run dev
```

Open **http://127.0.0.1:5173**. Vite proxies `/api` to the Python service. API documentation: http://127.0.0.1:8000/docs.

## What works

- Responsive observatory workspace with a procedural, clearly labeled tutorial sky. Tutorial motion and dates are illustrative, not scientific measurements.
- Coordinate input in decimal degrees, field of view from 1 to 30 arcminutes, and detector D1–D6 selection.
- Actual IRSA SIA2 image discovery and FITS cutout processing when the backend has archive access.
- Chronological playback, first/last blink mode, manual stepping, adjustable speed and brightness, coordinate grid, zoom, drag-to-pan when zoomed, fullscreen.
- Five challenge example fields: Barnard's Star, Epsilon Indi B, WISE 0855, RW Aurigae, R Draconis. Preset coordinates are approximate reference positions; high proper motion may place targets away from the center at other epochs. No live target resolution or proper-motion propagation is claimed.
- Tutorial comparison/difference illustration. These controls are deliberately disabled for real frames until PSF/bandpass matching supports trustworthy subtraction.
- Click-to-mark notes stored in localStorage, JSON export, and coordinate URLs (`?ra=...&dec=...&fov=...&band=D2`). Marks use normalized display positions, not scientific celestial coordinates.
- Explicit archive errors, quality information, original FITS links, source credits.

## Scientific pipeline

### Image display and resolution

Real frames default to high-quality browser smoothing, with a Pixel-exact option to inspect the preview grid. This changes display interpolation, not the underlying observations. SPHEREx spectral-image pixels cover approximately 6.15 arcseconds; a 6-arcminute field therefore contains only about 59 native pixels across. Upscaling cannot recover finer sky detail. Dark gaps represent masked/invalid data and are not filled in. Original FITS files remain linked for scientific inspection.

Previews use at least 256 pixels across, increasing for wide fields so that their output sampling stays at least as fine as nominal SPHEREx pixel sampling (up to the 30-arcminute input limit). New downloads report source cutout dimensions and their WCS-derived pixel scale. Existing narrow-field caches remain usable; their UI pixel-count estimate uses the nominal instrument scale.

The Python pipeline uses IRSA SIA2 image search for DR1 and QR3. It reads semantic VOTable FIELD names, filters by detector, validates IRSA file URLs, and samples at most 12 cutouts across the discovered time range. Two simultaneous downloads feed a common 256 by 256 TAN WCS. Previews are cached for six hours. SIA2 may lag newly ingested data by about a day; truncated results are rejected explicitly.

Pixels carrying flags other than SOURCE (bit 21) are masked conservatively. SOURCE alone is nominal and retained. The displayed flagged fraction still counts any flag, including SOURCE; it is not the fraction of invalid pixels. Wavelength at the requested position is read using the FITS alternate spectral WCS. When available, wavelengths within 3% of a selected observed wavelength are kept, maximizing compatible frame count and then time baseline. A common asinh stretch is applied to all retained frames; orientation is flipped for north-up browser display. Metadata records wavelength, processing version, flagged input fraction, source URL, output WCS, and stretch limits. Original pixel values remain in the upstream FITS files; the PNGs are display products only.

This is a visual exploration prototype. It does not measure proper motion, fit parallax, detect planets, provide calibrated light curves, or establish discoveries. Detector identity is not a precise bandpass match. PSF, wavelength, background, calibration, source crowding, and saturation can mimic changes. No spectra are fabricated. Large fields are downsampled; flagged-pixel masking can hide bright saturated targets. Each failed cutout is counted and reported.

Only one real processing request is accepted at a time to bound resource use. Cache files are local and expendable. Production deployment should add a job queue, persistent object storage, multi-user limits, robust date-range pagination, release/version filters, scientific quality-bit interpretation, proper bandpass/PSF matching, and catalog-based astrometry. Service errors identify the failed stage and distinguish timeouts, TLS/proxy failures, and upstream HTTP errors. Transient HTTP failures receive one retry.

## Validate

```powershell
npm.cmd run build
.\.venv\Scripts\python.exe -m pytest backend -q
npx.cmd playwright install chromium
npm.cmd run test:e2e
```

Browser tests cover playback, targets, validation, notes persistence, real-result presentation, archive failure, coordinate URLs, and mobile overflow. API tests check input rejection, absence of fabricated fallback, and synthetic FITS reprojection/flag masking. Mock-based tests validate behavior, not live science outcomes. See `VALIDATION.md` for checks actually run in this workspace.

For a live archive check, run `.\.venv\Scripts\python.exe -m backend.smoke_archive`; add `--process` to download and process sampled cutouts, and optionally `--target "WISE 0855"` to check one target. The original TAP join timed out. The SIA2 replacement has returned observations for all five targets, and real WISE 0855 cutouts have produced aligned previews. Intermittent upstream 502/503 responses remain possible. Restart the Python server after updating the backend.

## Project layout

```text
src/App.tsx           Workspace, playback, notes, search, guide
src/SkyCanvas.tsx     Tutorial renderer and real image viewer
src/data.ts          Example fields and tutorial frame metadata
src/styles.css       Responsive visual system
backend/main.py      FastAPI endpoints and request limits
backend/pipeline.py  IRSA query, FITS processing, alignment, cache
tests/               Browser workflow tests
```

## Data, credits, and AI assistance

See [SOURCES.md](./SOURCES.md). This independent student/hackathon prototype is not affiliated with or endorsed by NASA. NASA data access does not imply NASA endorsement. Source code, design, documentation, and tests were produced with assistance from OpenAI Codex. The tutorial star field is procedural code, not an observed sky image. Follow your event's current AI disclosure and submission rules.
