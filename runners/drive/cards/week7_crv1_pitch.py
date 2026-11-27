"""Paired-clip CRV1 pitch comparison. Only aggregate differences leave memory."""
from collections import Counter
from pathlib import Path
import io
import math
import re
import struct
import zipfile

import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly
from .week7_lgh1_sound_v1 import _pitch_and_fraction


def audio_members(archive, path):
    # The published ZIP stores wrapped 32-bit offsets. Check every local header
    # before allowing ZipFile to decode members and verify their CRCs.
    previous = -1
    with path.open('rb') as stream:
        for entry in archive.infolist():
            offset = entry.header_offset % (2**32)
            if offset <= previous:
                offset += 2**32
            if not previous < offset < archive.start_dir:
                raise ValueError('Unordered ZIP offsets')
            stream.seek(offset)
            header = stream.read(30)
            if header[:4] != b'PK\x03\x04':
                raise ValueError('Missing member header')
            name = stream.read(struct.unpack_from('<H', header, 26)[0]).decode()
            if name != entry.filename:
                raise ValueError('Local member name differs')
            entry.header_offset = previous = offset
        end = archive.start_dir
        for entry in reversed(archive.infolist()):
            entry._end_offset = end
            end = entry.header_offset
    return inventory(archive, '.wav')


def inventory(archive, suffix):
    found = {}
    for entry in archive.infolist():
        p = Path(entry.filename)
        if p.suffix.lower() != suffix or '__MACOSX' in p.parts or not re.fullmatch(r'[A-Za-z]{3}\d{2}[BD]', p.stem):
            continue
        if p.stem in found:
            raise ValueError('Duplicate recording key')
        found[p.stem] = entry
    return found


def annotation(data):
    encoding = 'utf-16' if data[:2] in (b'\xff\xfe', b'\xfe\xff') else 'utf-8-sig'
    # Praat permits a quoted mark to span lines. Preserve its nonempty status.
    text = re.sub(r'"(?:[^"]|"")*"', lambda m: m[0].replace('\n',' ').replace('\r',' '), data.decode(encoding))
    lines = [s.strip() for s in text.splitlines() if s.strip()]
    if lines[2].startswith('xmin'):
        def field(line):
            return line.split('=', 1)[1].strip()
        if field(lines[5]) != '1' or field(lines[8]) != '"IntervalTier"' or field(lines[9]) != '"silences"':
            raise ValueError('Unexpected long-format tier')
        start, end = float(field(lines[2])), float(field(lines[3]))
        n = int(field(lines[12]))
        cells = [(float(field(lines[i+1])), float(field(lines[i+2])), field(lines[i+3])) for i in range(13,len(lines),4)]
    else:
        if lines[5:8] != ['1', '"IntervalTier"', '"silences"']:
            raise ValueError('Unexpected short-format tier')
        start, end, n = float(lines[2]), float(lines[3]), int(lines[10])
        cells = [(float(lines[i]),float(lines[i+1]),lines[i+2]) for i in range(11,len(lines),3)]
    if start != 0 or len(cells) != n or not all(0 <= a < b <= end+1e-8 for a,b,_ in cells):
        raise ValueError('Invalid annotation bounds')
    if any(abs(first[1]-second[0]) > 1e-8 for first,second in zip(cells,cells[1:])):
        raise ValueError('Noncontiguous annotation')
    return end, [(a,b) for a,b,tag in cells if tag != '""']


def summarize_clip(rate, samples, grid):
    end, intervals = grid
    if abs(len(samples)-end*rate) > 1.0001:
        return None, 'clock'
    x = samples.astype(float)
    if samples.dtype == np.uint8:
        x -= 128
    if x.ndim == 2:
        x = x.mean(axis=1)
    if x.ndim != 1 or not np.isfinite(x).all():
        raise ValueError('Invalid waveform')
    common = math.gcd(rate,8000)
    pitch = []
    for a,b in intervals:
        segment = x[math.floor(a*rate):math.floor(b*rate)]
        if len(segment) < math.ceil(.04*rate):
            continue
        mono = resample_poly(segment,8000//common,rate//common)
        voiced,_ = _pitch_and_fraction(mono,8000)
        pitch.extend(voiced)
    if len(pitch) < 10:
        return None,'low_voicing'
    q = np.percentile(12*np.log2(pitch),[25,50,75])
    return np.array([q[1],q[2]-q[0]]),'ok'


def aggregate(differences):
    values = np.asarray(differences)
    if len(values) < 20:
        return {'n':len(values),'status':'below_support'}
    rng = np.random.default_rng(20261125)
    estimates = values.mean(axis=0)
    draws = values[rng.integers(len(values),size=(2000,len(values)))].mean(axis=1)
    limits = np.percentile(draws,[2.5,97.5],axis=0)
    return {'n':len(values),'draws':2000,'unit':'semitones','direction':'infant minus adult',
            'contrasts':{key:{'mean':float(estimates[i]),'interval':limits[:,i].tolist()} for i,key in enumerate(('pitch_height','pitch_spread'))}}


def compare(raw_path, grid_path, progress):
    counts = Counter()
    differences = []
    with zipfile.ZipFile(raw_path) as raw, zipfile.ZipFile(grid_path) as grids:
        wav = audio_members(raw,raw_path)
        ann = inventory(grids,'.textgrid')
        if set(wav) != set(ann):
            raise ValueError('Recording and annotation inventories differ')
        ids = sorted({key[:-1] for key in wav})
        for i,person in enumerate(ids,1):
            if not all(person+role in wav for role in 'BD'):
                counts['missing_partner'] += 1
                continue
            values,flags = [],[]
            for role in 'BD':
                key = person+role
                rate,samples = wavfile.read(io.BytesIO(raw.read(wav[key])))
                value,flag = summarize_clip(rate,samples,annotation(grids.read(ann[key])))
                flags.append(flag)
                values.append(value)
            if 'clock' in flags:
                counts['clock'] += 1
            elif 'low_voicing' in flags:
                counts['low_voicing'] += 1
            else:
                differences.append(values[0]-values[1])
            if i%10 == 0:
                progress(i)
    return {'inventory_people':len(ids),'exclusions':dict(counts),'paired':aggregate(differences)}

