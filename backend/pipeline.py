"""IRSA SIA2 discovery and WCS-aligned SPHEREx previews.

Discovery uses IRSA's documented SIA2 service, avoiding a costly TAP join:
https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-access/
No synthetic data is returned by this module.
"""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from time import time
from urllib.parse import urlparse

import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.time import Time
from astropy.wcs import WCS
from astropy.wcs.utils import proj_plane_pixel_scales
import numpy as np
from PIL import Image
from reproject import reproject_interp
import requests
from astropy.table import Table
from xml.etree import ElementTree
from .archive_http import ArchiveError, archive_get

CACHE = Path(__file__).parent / 'cache'
CACHE.mkdir(exist_ok=True)
TAP = 'https://irsa.ipac.caltech.edu/TAP/sync'
SIA = 'https://irsa.ipac.caltech.edu/SIA'


def query_archive(ra: float, dec: float, fov: float, detector: str) -> list[dict]:
    def search_collection(collection):
        response = archive_get(SIA, stage=f'Image search ({collection})', params={
            'COLLECTION': collection, 'POS': f'CIRCLE {ra} {dec} 0.000001',
            'MAXREC': 2000,
        })
        try:
            root = ElementTree.fromstring(response.content)
            for info in root.iter():
                if info.tag.rsplit('}',1)[-1] == 'INFO' and info.get('name') == 'QUERY_STATUS' and info.get('value') in ('ERROR','OVERFLOW'):
                    raise ArchiveError(f'Image search ({collection}): the service reported an error or truncated result. Try a less crowded field or inspect the archive directly.')
            # IRSA uses generated FIELD IDs (col_0, ...) and semantic FIELD names.
            table = Table.read(BytesIO(response.content), format='votable', use_names_over_ids=True)
            required = {'access_url','t_min','energy_bandpassname'}
            if not required.issubset(table.colnames):
                raise ValueError('Missing SIA columns')
            return table
        except (ElementTree.ParseError, ValueError, KeyError) as exc:
            raise ArchiveError(f'Image search ({collection}): IRSA returned an invalid image catalog response.') from exc
    with ThreadPoolExecutor(max_workers=2) as pool:
        tables = list(pool.map(search_collection, ['spherex_dr1', 'spherex_qr3']))
    rows, seen = [], set()
    for table in tables:
        for row in table:
            if str(row['energy_bandpassname']) != f'SPHEREx-{detector}':
                continue
            url = str(row['access_url'])
            parsed = urlparse(url)
            if parsed.scheme != 'https' or parsed.hostname != 'irsa.ipac.caltech.edu' or parsed.port not in (None,443):
                continue
            if not parsed.path.startswith(('/ibe/data/spherex/dr1/level2/', '/ibe/data/spherex/qr3/level2/')):
                continue
            if url in seen or np.ma.is_masked(row['t_min']):
                continue
            mjd = float(row['t_min'])
            if not np.isfinite(mjd):
                continue
            seen.add(url)
            rows.append({'url': url + ('&' if '?' in url else '?') + f'center={ra},{dec}d&size={fov/60}', 'mjd': mjd})
    rows.sort(key=lambda r: r['mjd'])
    return rows


def preview_size(fov: float) -> int:
    """Keep display sampling at least as fine as nominal 6.15 arcsec pixels."""
    return max(256, min(512, int(np.ceil(fov * 60 / 6.15))))


def output_wcs(ra: float, dec: float, fov: float, size: int = 256) -> WCS:
    wcs = WCS(naxis=2)
    wcs.wcs.crpix = [(size + 1) / 2] * 2
    wcs.wcs.cdelt = np.array([-fov/60/size, fov/60/size])
    wcs.wcs.crval = [ra, dec]
    wcs.wcs.ctype = ['RA---TAN', 'DEC--TAN']
    return wcs


def process_cutout(row: dict, coord: SkyCoord, grid: WCS, size: int = 256) -> dict:
    response = archive_get(row['url'], stage='FITS cutout download', timeout=(10,45))
    if len(response.content) > 30_000_000:
        raise ValueError('Cutout exceeds the 30 MB processing limit.')
    with fits.open(BytesIO(response.content), memmap=False) as hdul:
        image = hdul['IMAGE']
        data = np.asarray(image.data, dtype=float).copy()
        spatial = WCS(image.header).celestial
        native_width, native_height = int(data.shape[1]), int(data.shape[0])
        native_scale = float(np.median(proj_plane_pixel_scales(spatial)) * 3600)
        wavelength = None
        try:
            x, y = spatial.world_to_pixel(coord)
            spectral = WCS(image.header, fobj=hdul, key='W')
            spectral.sip = None
            wave, _ = spectral.pixel_to_world(x, y)
            wavelength = float(wave.to_value(u.micrometer))
            if not np.isfinite(wavelength):
                wavelength = None
        except (KeyError, ValueError, TypeError, AttributeError):
            pass
        flagged = 0.0
        if 'FLAGS' in hdul:
            flags = np.asarray(hdul['FLAGS'].data)
            flagged = float(np.count_nonzero(flags) / flags.size)
            # SOURCE (bit 21) marks known sources and is nominal by itself.
            # Masking it would erase the targets, sometimes the entire cutout.
            # https://irsa.ipac.caltech.edu/onlinehelp/spherex/spherex/sp.html
            bad = (flags.astype(np.uint64) & np.uint64(0xFFFFFFFF ^ (1 << 21))) != 0
            data[bad] = np.nan
        aligned, footprint = reproject_interp((data, spatial), grid, shape_out=(size, size))
        aligned[footprint < .5] = np.nan
        if np.count_nonzero(np.isfinite(aligned)) < size*size*.05:
            raise ValueError('Too little unflagged sky coverage in this observation.')
        version = str(hdul[0].header.get('VERSION', 'unknown'))
    return {'data': aligned, 'date': Time(row['mjd'], format='mjd').isot + 'Z', 'source_url': row['url'], 'wavelength': wavelength, 'flagged_fraction': flagged, 'version': version, 'native_width': native_width, 'native_height': native_height, 'native_pixel_scale_arcsec': native_scale}


def build_observations(ra: float, dec: float, fov: float, detector: str) -> dict:
    size = preview_size(fov)
    version = 'v3-sia-source' if size == 256 else 'v4-wide'
    key = sha256(f'{version}:{ra:.7f}:{dec:.7f}:{fov:g}:{detector}'.encode()).hexdigest()[:24]
    folder = CACHE / key
    manifest = folder / 'manifest.json'
    if manifest.exists() and time() - manifest.stat().st_mtime < 21600:
        return json.loads(manifest.read_text())
    rows = query_archive(ra, dec, fov, detector)
    if not rows:
        return {'frames': [], 'warnings': ['No DR1 or QR3 cutouts found for this coordinate and detector.']}
    # Sample the discovered time range instead of using only consecutive exposures.
    indices = np.unique(np.linspace(0, len(rows)-1, min(12, len(rows)), dtype=int))
    coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg)
    grid = output_wcs(ra, dec, fov, size=size)
    errors = []
    def safe_process(i):
        try:
            return process_cutout(rows[i], coord, grid, size=size)
        except Exception as exc:
            errors.append(str(exc) if isinstance(exc,ArchiveError) else type(exc).__name__)
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        processed = [r for r in pool.map(safe_process, indices) if r is not None]
    warnings = ['Visual exploration only: PSF and calibration differences can mimic changes. No discovery or variability measurement is implied.']
    if errors:
        warnings.append(f'{len(errors)} sampled cutouts could not be processed or had insufficient unflagged coverage.')
    if not processed and errors:
        raise ArchiveError(f'Found {len(rows)} archive observations, but none of the {len(indices)} sampled cutouts could be prepared. First failure: {errors[0]}')
    # Detector identity alone does not ensure equal wavelengths with a linear variable filter.
    known = [r for r in processed if r['wavelength'] is not None]
    if known:
        # Use an observed wavelength as anchor. A median between sparse groups
        # can reject every frame even when each group contains usable data.
        def group_score(candidate):
            group = [r for r in known if abs(r['wavelength']-candidate['wavelength'])/candidate['wavelength'] <= .03]
            times = [Time(r['date']).mjd for r in group]
            return len(group), max(times)-min(times)
        anchor = max(known, key=group_score)['wavelength']
        matched = [r for r in known if abs(r['wavelength']-anchor)/anchor <= .03]
        if len(matched) != len(processed):
            warnings.append('Frames without a central wavelength or differing by more than 3% from the selected observed wavelength were excluded. This is a preview filter, not a calibrated bandpass match.')
        processed = matched
    else:
        warnings.append('Central wavelengths could not be extracted. Apparent brightness changes cannot be interpreted reliably.')
    if not processed:
        return {'frames': [], 'warnings': warnings}
    if len(processed) == 1:
        warnings.append('Only one usable wavelength-matched frame remains. Motion cannot be assessed from a single observation; try another detector.')
    processed.sort(key=lambda r: r['date'])
    pixels = np.concatenate([r['data'][np.isfinite(r['data'])] for r in processed])
    lo, hi = np.percentile(pixels, [3, 99.7])
    span = max(float(hi-lo), 1e-12)
    folder.mkdir(exist_ok=True)
    frames = []
    for i, item in enumerate(processed):
        data = item.pop('data')
        valid = np.isfinite(data)
        norm = np.arcsinh(np.maximum(np.nan_to_num(data, nan=lo)-lo, 0)/span*10)/np.arcsinh(10)
        gray = np.uint8(np.clip(norm, 0, 1)*255)
        rgb = np.stack([gray*.94, gray*.97, gray], axis=-1).astype('uint8')
        rgb[~valid] = [8, 14, 21]
        # WCS pixel coordinates increase upwards; browser image coordinates increase downwards.
        Image.fromarray(np.flipud(rgb)).save(folder / f'{i}.png')
        frames.append({'id': f'{key}-{i}', 'image': f'/api/cache/{key}/{i}.png', **item})
    result = {'frames': frames, 'warnings': warnings, 'detector': detector, 'coordinate': {'ra': ra, 'dec': dec}, 'fov_arcmin': fov, 'source': 'NASA/IPAC IRSA SPHEREx DR1 + QR3', 'wcs': grid.to_header_string(), 'stretch': {'low': float(lo), 'high': float(hi), 'method': 'shared asinh'}, 'found': len(rows)}
    temp = folder / 'manifest.tmp'
    temp.write_text(json.dumps(result), encoding='utf-8')
    temp.replace(manifest)
    return result
