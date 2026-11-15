"""Run explicitly to verify live archive access. Never supplies simulated data.

python -m backend.smoke_archive [--process]
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import logging
from .pipeline import query_archive, build_observations

TARGETS = [
    ("Barnard's Star", 269.4521, 4.6934),
    ('Epsilon Indi B', 330.8417, -56.7858),
    ('WISE 0855', 133.795129, -7.245147),
    ('RW Aurigae', 76.9565, 30.4014),
    ('R Draconis', 248.4804, 66.7527),
]

def check(item):
    name, ra, dec = item
    try:
        rows = query_archive(ra, dec, 6, 'D2')
        return {'target': name, 'observations': len(rows), 'first_mjd': rows[0]['mjd'] if rows else None, 'last_mjd': rows[-1]['mjd'] if rows else None}
    except Exception as exc:
        return {'target': name, 'error': str(exc)}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--process', action='store_true')
    parser.add_argument('--target', choices=[item[0] for item in TARGETS])
    args = parser.parse_args()
    logging.getLogger('astropy').setLevel(logging.WARNING)
    selected = [item for item in TARGETS if args.target is None or item[0] == args.target]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(check, selected):
            print(json.dumps(result), flush=True)
    if args.process:
        for name, ra, dec in selected:
            try:
                result = build_observations(ra, dec, 6, 'D2')
                print(json.dumps({'processed': name, 'frames': len(result['frames']), 'warnings': result['warnings']}), flush=True)
            except Exception as exc:
                print(json.dumps({'processed': name, 'error': str(exc)}), flush=True)
