from types import SimpleNamespace
from unittest.mock import patch
import pytest
import requests
from .archive_http import ArchiveError, archive_get
from .pipeline import query_archive, build_observations
from .test_api import client

CATALOG = b'''<?xml version="1.0"?>
<VOTABLE version="1.3" xmlns="http://www.ivoa.net/xml/VOTable/v1.3">
<RESOURCE type="results"><INFO name="QUERY_STATUS" value="OK"/><TABLE>
<FIELD ID="col_0" name="access_url" datatype="char" arraysize="*"/>
<FIELD ID="col_1" name="t_min" datatype="double"/>
<FIELD ID="col_2" name="energy_bandpassname" datatype="char" arraysize="*"/>
<DATA><TABLEDATA>
<TR><TD>https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/level2/test.fits</TD><TD>61000</TD><TD>SPHEREx-D2</TD></TR>
<TR><TD>https://example.com/untrusted.fits</TD><TD>61001</TD><TD>SPHEREx-D2</TD></TR>
<TR><TD>https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/level2/other.fits</TD><TD>61002</TD><TD>SPHEREx-D1</TD></TR>
</TABLEDATA></DATA></TABLE></RESOURCE></VOTABLE>'''

def test_sia_uses_field_names_filters_detector_and_untrusted_urls_and_deduplicates():
    with patch('backend.pipeline.archive_get', return_value=SimpleNamespace(content=CATALOG)) as get:
        rows = query_archive(10,20,6,'D2')
    assert len(rows) == 1
    assert rows[0]['mjd'] == 61000
    assert rows[0]['url'].endswith('?center=10,20d&size=0.1')
    assert {c.kwargs['params']['COLLECTION'] for c in get.call_args_list} == {'spherex_dr1','spherex_qr3'}

def test_sia_rejects_service_error_even_with_http_200():
    xml = b'<VOTABLE><RESOURCE><INFO name="QUERY_STATUS" value="ERROR">Unavailable</INFO></RESOURCE></VOTABLE>'
    with patch('backend.pipeline.archive_get', return_value=SimpleNamespace(content=xml)):
        with pytest.raises(ArchiveError, match='service reported'):
            query_archive(10,20,6,'D2')

def test_transient_http_error_is_retried_once():
    bad = requests.Response()
    bad.status_code = 503
    good = requests.Response()
    good.status_code = 200
    with patch('backend.archive_http.requests.get', side_effect=[bad,good]) as get:
        assert archive_get('https://irsa.ipac.caltech.edu/SIA',stage='Image search') is good
        assert get.call_count == 2

def test_timeouts_produce_actionable_504_and_release_request_lock():
    with patch('backend.archive_http.requests.get', side_effect=requests.Timeout()) as get:
        with pytest.raises(ArchiveError) as caught:
            archive_get('https://irsa.ipac.caltech.edu/SIA',stage='Image search')
        assert get.call_count == 2
        assert caught.value.status_code == 504
    with patch('backend.main.build_observations', side_effect=ArchiveError('Image search: timeout after retry',504)):
        response = client.get('/api/observations?ra=10&dec=20')
        assert response.status_code == 504
        assert 'Image search' in response.json()['detail']
    with patch('backend.main.build_observations',return_value={'frames':[]}):
        assert client.get('/api/observations?ra=10&dec=20').status_code == 200

def test_all_cutout_failures_are_not_misreported_as_no_observations(tmp_path):
    with patch('backend.pipeline.CACHE',tmp_path), patch('backend.pipeline.query_archive',return_value=[{'url':'test','mjd':61000}]), patch('backend.pipeline.process_cutout',side_effect=ArchiveError('FITS cutout download: HTTP 502')):
        with pytest.raises(ArchiveError,match='Found 1 archive observations.*FITS cutout download'):
            build_observations(10,20,6,'D2')
