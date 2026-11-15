"""Inspect one real target cutout without hiding a processing exception."""
from io import BytesIO
import logging
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
import astropy.units as u
from .pipeline import query_archive, output_wcs, process_cutout
from .archive_http import archive_get

if __name__ == '__main__':
    logging.getLogger('astropy').setLevel(logging.WARNING)
    ra, dec = 269.4521,4.6934
    rows=query_archive(ra,dec,6,'D2')
    row=rows[len(rows)//2]
    response=archive_get(row['url'],stage='FITS inspection',timeout=(10,45))
    with fits.open(BytesIO(response.content)) as hdul:
        data=hdul['IMAGE'].data
        flags=hdul['FLAGS'].data
        values, counts=np.unique(flags,return_counts=True)
        print({'shape':data.shape,'finite':int(np.isfinite(data).sum()),'flags':[(int(v),int(c)) for v,c in zip(values,counts)]},flush=True)
    result=process_cutout(row,SkyCoord(ra*u.deg,dec*u.deg),output_wcs(ra,dec,6))
    print({k:v for k,v in result.items() if k!='data'},flush=True)
