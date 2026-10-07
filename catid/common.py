"""Shared helpers: timestamps, sessions (visits), bursts, label loading."""
import json, re, datetime as dt
import numpy as np

def ts(fname):
    """PXL_YYYYMMDD_HHMMSSmmm -> UTC datetime (Pixel names files in UTC)."""
    m = re.search(r'PXL_(\d{8})_(\d{6})(\d{3})', fname)
    return dt.datetime.strptime(m[1] + m[2], '%Y%m%d%H%M%S').replace(tzinfo=dt.timezone.utc) + dt.timedelta(milliseconds=int(m[3]))

def local(fname):  # photos are in US Pacific (EXIF local = UTC-7 in summer)
    return ts(fname) - dt.timedelta(hours=7)

def sessions(files, gap_h=3.0):
    """Visit id per file: new visit whenever there is a >gap_h hour gap between consecutive photos."""
    order = sorted(set(files), key=ts); sid, out, prev = -1, {}, None
    for f in order:
        if prev is None or (ts(f) - ts(prev)).total_seconds() > gap_h * 3600: sid += 1
        out[f] = sid; prev = f
    return np.array([out[f] for f in files])

def load(work):
    dets = json.load(open(f'{work}/dets.json'))
    files = [d['file'] for d in dets]
    return dets, np.array([ts(f).timestamp() for f in files]), sessions(files)
