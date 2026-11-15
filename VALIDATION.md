# Validation record

## Image display improvement

The viewer now defaults to high-quality interpolation for real previews and offers Pixel-exact display. The browser regression test checks that switching modes actually changes rendered pixels, not just button state. Output sizing grows for wide fields to avoid coarser-than-native sampling. Eleven backend tests and six browser workflows pass. A 6-arcminute SPHEREx cutout still contains roughly 59 native pixels across; smoothing does not add information. No AI upscaling, missing-pixel inpainting, or invented stars are used.

## Archive connection repair

The original TAP join timed out even when small catalog queries succeeded. The backend now uses the documented SIA2 image service, parses VOTable FIELD names instead of generated IDs, retries transient requests once, and reports the failing stage. A separate processing bug masked the nominal SOURCE bit (21); known-source pixels are now retained. Cache keys normalize integer and float fields of view.

Live SIA2 discovery succeeded for all five targets on detector D2: Barnard's Star 62 observations, Epsilon Indi B 89, WISE 0855 48, RW Aurigae 55, and R Draconis 92. Real WISE 0855 FITS downloads produced two aligned preview frames. Upstream 502/503 responses remain intermittent; successful loading for every target is not implied by catalog discovery.

Ten backend regression checks pass, including SIA FIELD-name parsing, detector/URL filtering, duplicate removal, HTTP retry, actionable timeout responses, SOURCE flag retention, cache normalization, and all-download-failure reporting. The initial failures below describe the earlier TAP implementation, not the current SIA2 search.

After the SOURCE-mask correction, Barnard's Star produced four real, wavelength-matched preview frames spanning 2025-08-25 to 2026-09-22. An actual Chromium browser loaded the built frontend through FastAPI, searched the default field, displayed ARCHIVE OBSERVATION, and retrieved both the real observation response and its PNG with HTTP 200. No API mocking was used in this check. Screenshot: `test-results/parallax-real-spherex.png`; verification script: `node verify-live.mjs` with a temporary backend on port 8010. The temporary server was stopped after verification. Visible motion or variability has not been scientifically measured.

## Completed local checks

- Production build: TypeScript type checking and Vite compilation passed.
- Browser workflows: all four Playwright tests passed on Chromium after bundling fonts locally. Checked playback/stepping, target changes, coordinate validation, annotation persistence across reload, real-result presentation with an explicitly mocked API, archive failure, coordinate URL restoration, mobile overflow, and modal dismissal.
- Backend: input validation, no synthetic fallback, FITS reprojection/flag masking, preview orientation, and cache reuse passed using synthetic FITS data or mocked network responses.
- Desktop (1280 px) and mobile (390 px) full-page screenshots were generated and visually inspected. Available under `test-results/parallax-desktop.png` and `test-results/parallax-mobile.png` after browser tests.
- A dedicated check covers serving the compiled frontend, a JS asset, and the API from the same FastAPI server.
- npm install audit reported zero known vulnerabilities at installation time.

## Live archive verification limit

`python -m backend.smoke_archive --process` attempted NASA/IPAC IRSA TAP queries and processing for every required target. It did not obtain scientific images from this environment.

| Target | Archive query outcome | Processing attempt |
| --- | --- | --- |
| Barnard's Star | HTTP 502 Proxy Error | HTTP 502 Proxy Error |
| Epsilon Indi B | HTTP 502 Proxy Error | HTTP 502 Proxy Error |
| WISE 0855 | HTTP 502 Proxy Error | HTTP 502 Proxy Error |
| RW Aurigae | HTTP 502 Proxy Error | Read timeout |
| R Draconis | Read timeout | HTTP 502 Proxy Error |

These failures prevent validation of the current remote table schema, actual FITS downloads, or visible motion/variability on the five targets. The adapter follows the official IRSA tutorial; live compatibility is still unverified. No discovery, real-object motion measurement, or successful real-data demo is claimed.

The app remains usable as a clearly labeled procedural tutorial. Real search errors are displayed explicitly. The frontend does not relabel tutorial frames as real data or substitute them for a successful archive result.

## Before presenting a scientific result

Run the smoke command from a network that can reach IRSA, confirm current release/table availability, and inspect the five target sequences. Verify wavelengths, proper-motion offsets, quality flags, saturation, and pixel orientation against original FITS data. A working viewer alone does not validate a discovery.
