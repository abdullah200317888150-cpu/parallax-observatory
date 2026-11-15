# Sources and acknowledgements

## Challenge

The user supplied the full NASA Space Apps **Planet X and SPHEREx** challenge brief in the project conversation. Objective: coordinates in, time-ordered SPHEREx sky images out; test on the five named targets.

- https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/

## Scientific data and processing references

- Native instrument pixel sampling (approximately 6.2 arcseconds): https://spherex.caltech.edu/page/instrument

- Current SIA2 discovery adapter: https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-access/
- SOURCE bit 21 is nominal alone: https://irsa.ipac.caltech.edu/onlinehelp/spherex/spherex/sp.html

- NASA/IPAC IRSA SPHEREx mission and release index: https://irsa.ipac.caltech.edu/Missions/spherex.html
- Official cutout tutorial; query and spectral-WCS approach adapted here: https://caltech-ipac.github.io/irsa-tutorials/spherex-cutouts/
- DR1 overview and citations: https://irsa.ipac.caltech.edu/data/SPHEREx/docs/overview_dr1.html
- DR1 spectral-image DOI: https://doi.org/10.26131/IRSA678
- IRSA program interfaces: https://irsa.ipac.caltech.edu/voapi.html
- Astropy FITS: https://docs.astropy.org/en/stable/io/fits/
- Reproject: https://reproject.readthedocs.io/

No actual SPHEREx imagery is bundled initially. Real imagery is retrieved from IRSA on request. The tutorial is entirely synthetic and visibly labeled.

## Required SPHEREx acknowledgement

This publication makes use of data products from the Spectro-Photometer for the History of the Universe, Epoch of Reionization and Ices Explorer (SPHEREx), which is a joint project of the Jet Propulsion Laboratory and the California Institute of Technology, and is funded by the National Aeronautics and Space Administration.

This research has made use of the NASA/IPAC Infrared Science Archive, which is funded by the National Aeronautics and Space Administration and operated by the California Institute of Technology.

## Interface and dependencies

- React: https://react.dev/ — MIT
- TypeScript: https://www.typescriptlang.org/ — Apache-2.0
- Vite: https://vite.dev/ — MIT
- Lucide icons: https://lucide.dev/ — ISC
- FastAPI: https://fastapi.tiangolo.com/ — MIT
- Astropy: https://www.astropy.org/ — BSD-3-Clause
- NumPy: https://numpy.org/ — BSD-3-Clause
- reproject: https://reproject.readthedocs.io/ — BSD-3-Clause
- Requests: https://requests.readthedocs.io/ — Apache-2.0
- Pillow: https://python-pillow.github.io/ — MIT-CMU
- Playwright: https://playwright.dev/ — Apache-2.0
- Fonts: DM Sans, Manrope, IBM Plex Mono, bundled locally through Fontsource; SIL Open Font License. System-font fallbacks also work offline.

Library/data rights remain with their respective owners. No NASA logo or generated scientific imagery is used.
