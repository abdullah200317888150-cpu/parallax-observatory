from io import BytesIO
from unittest.mock import patch
import numpy as np
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
from fastapi.testclient import TestClient
from .main import app
from .pipeline import output_wcs, process_cutout, build_observations, preview_size

client = TestClient(app)

def test_built_frontend_and_api_share_one_server():
    import re
    from pathlib import Path
    import pytest
    if not (Path(__file__).resolve().parents[1] / 'dist/index.html').exists():
        pytest.skip('Build the frontend to validate single-server serving.')
    response = client.get('/')
    assert response.status_code == 200
    assert 'PARALLAX' in response.text
    asset = re.search(r'src="(/assets/[^\"]+\.js)"', response.text)
    assert asset is not None
    assert client.get(asset.group(1)).status_code == 200
    assert client.get('/api/health').status_code == 200

def test_invalid_coordinates_and_detector_never_query_archive():
    with patch('backend.main.build_observations') as build:
        for q in ['ra=360&dec=0', 'ra=12&dec=91', 'ra=12&dec=0&fov=100', 'ra=12&dec=0&detector=INVALID', 'ra=nan&dec=0']:
            assert client.get('/api/observations?' + q).status_code == 422
        build.assert_not_called()

def test_service_has_no_simulated_fallback():
    with patch('backend.main.build_observations', return_value={'frames': [], 'warnings': []}):
        response = client.get('/api/observations?ra=10&dec=-20')
        assert response.json()['frames'] == []
    assert client.get('/api/health').json()['synthetic_fallback'] is False

def test_reprojection_preserves_target_and_flags():
    grid = output_wcs(10, 20, 6, size=32)
    data = np.ones((32, 32), dtype='float32')
    data[16, 16] = 100
    flags = np.full((32, 32), 1 << 21, dtype='int32')
    flags[:2] |= 1
    hdu = fits.HDUList([fits.PrimaryHDU(), fits.ImageHDU(data, grid.to_header(), name='IMAGE'), fits.ImageHDU(flags, name='FLAGS')])
    buffer = BytesIO()
    hdu.writeto(buffer)
    class Response:
        content = buffer.getvalue()
        def raise_for_status(self): pass
    with patch('backend.pipeline.requests.get', return_value=Response()):
        out = process_cutout({'url':'https://irsa.ipac.caltech.edu/example','mjd':61000}, SkyCoord(10*u.deg,20*u.deg), grid, size=32)
    # Every pixel is SOURCE-flagged, but only the transient rows are invalid.
    assert out['flagged_fraction'] == 1.0
    assert np.unravel_index(np.nanargmax(out['data']), out['data'].shape) == (16,16)
    assert np.isnan(out['data'][0]).all()

def test_preview_export_is_north_up_and_cache_avoids_requery(tmp_path):
    from PIL import Image
    rows = [{'url':'https://irsa.ipac.caltech.edu/example1', 'mjd':61000}, {'url':'https://irsa.ipac.caltech.edu/example2', 'mjd':61001}]
    def synthetic_process(row, coord, grid, size=256):
        data = np.ones((size,size))
        data[10,40] = 100
        return {'data':data, 'date':f"2025-11-{int(row['mjd']-60999):02d}T00:00:00Z", 'source_url':row['url'], 'wavelength':1.2, 'flagged_fraction':0.0, 'version':'TEST'}
    with patch('backend.pipeline.CACHE', tmp_path), patch('backend.pipeline.query_archive', return_value=rows) as query, patch('backend.pipeline.process_cutout', side_effect=synthetic_process):
        result = build_observations(10,20,6,'D2')
        cached = build_observations(10.0,20.0,6.0,'D2')
        query.assert_called_once()
    assert len(result['frames']) == 2
    assert result == cached
    preview = np.array(Image.open(next(tmp_path.glob('*/0.png'))))
    assert preview[245,40,0] > preview[10,40,0]
    assert result['frames'][0]['source_url'] == rows[0]['url']

def test_wide_previews_do_not_downsample_below_native_pixel_sampling():
    assert preview_size(6) == 256
    assert preview_size(30) > 256
    assert 30*60/preview_size(30) <= 6.15
    assert preview_size(30) <= 512
