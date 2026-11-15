"""Bounded connectivity probes; prints no proxy credentials or environment values."""
from concurrent.futures import ThreadPoolExecutor
import json
import requests
from io import BytesIO
from astropy.table import Table

URL = 'https://irsa.ipac.caltech.edu/TAP/sync'
QUERY = "SELECT TOP 1 a.uri, p.time_bounds_lower FROM spherex.artifact a JOIN spherex.plane p ON a.planeid = p.planeid WHERE 1 = CONTAINS(POINT('ICRS', 269.4521, 4.6934), p.poly) AND p.energy_bandpassname = 'SPHEREx-D2' ORDER BY p.time_bounds_lower"

def probe(case):
    name, method, url, params = case
    try:
        kwargs = {'data' if method == 'POST' else 'params':params}
        r = requests.request(method, url, timeout=(8,20), **kwargs)
        result = {'probe':name, 'status':r.status_code, 'content_type':r.headers.get('Content-Type'), 'body':r.text[:700]}
        if name.startswith('SIA') and r.ok:
            try:
                t=Table.read(BytesIO(r.content),format='votable')
                result.update(rows=len(t),columns=t.colnames)
            except Exception as exc:
                result.update(parse_error=str(exc),tail=r.text[-2000:])
        return result
    except requests.RequestException as exc:
        return {'probe':name,'error_type':type(exc).__name__}

if __name__ == '__main__':
    cases = [
        ('availability','GET','https://irsa.ipac.caltech.edu/TAP/availability',{}),
        ('SIA DR1','GET','https://irsa.ipac.caltech.edu/SIA',{'COLLECTION':'spherex_dr1','POS':'CIRCLE 269.4521 4.6934 0.00001'}),
        ('SIA QR3','GET','https://irsa.ipac.caltech.edu/SIA',{'COLLECTION':'spherex_qr3','POS':'CIRCLE 269.4521 4.6934 0.00001'}),
        ('small GET','GET',URL,{'QUERY':'SELECT TOP 1 table_name FROM TAP_SCHEMA.tables','FORMAT':'csv','LANG':'ADQL','REQUEST':'doQuery'}),
        ('SPHEREx GET','GET',URL,{'QUERY':QUERY,'FORMAT':'csv','LANG':'ADQL','REQUEST':'doQuery'}),
        ('SPHEREx POST','POST',URL,{'QUERY':QUERY,'FORMAT':'csv','LANG':'ADQL','REQUEST':'doQuery'}),
    ]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(probe, cases):
            print(json.dumps(result),flush=True)
