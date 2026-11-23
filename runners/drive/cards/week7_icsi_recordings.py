"""LGH1 original ICSI transcript and assigned-channel binding under amendment CO."""
from collections import Counter, defaultdict
import hashlib
import io
from pathlib import Path, PurePosixPath
import re
import subprocess
import wave
import xml.etree.ElementTree as ET

import numpy as np
from .week7_lgh1_sound_v1 import _pitch_and_fraction, relative_measures


LIMIT = 'Laughter that overlaps speech is not in the sample, and that may be a kind of its own.'


def editions(bundle):
    """Select native meeting MRTs only. Refuse competing bytes for the same meeting."""
    selected = {}
    for name in bundle.namelist():
        path = PurePosixPath(name)
        if path.suffix.lower() != '.mrt' or path.stem.lower() == 'preambles':
            continue
        if not re.fullmatch(r'[A-Za-z]+[0-9]+', path.stem):
            raise ValueError('Unrecognized original transcript edition')
        data = bundle.read(name)
        if ET.fromstring(data).get('Session') != path.stem:
            raise ValueError('Transcript meeting and filename disagree')
        if path.stem in selected and data != bundle.read(selected[path.stem]):
            raise ValueError('Competing original meeting editions')
        selected[path.stem] = name
    if not selected:
        raise ValueError('No original meeting editions')
    return selected


def timed(start, end):
    try:
        a, b = float(start), float(end)
    except (TypeError, ValueError):
        return None
    return (a, b) if 0 <= a < b < float('inf') else None


def transcript(data):
    tree = ET.fromstring(data)
    assigned = {}
    for entry in tree.iter('Participant'):
        person, channel = entry.get('Name'), entry.get('Channel')
        if not person:
            continue
        if channel and not re.fullmatch(r'chan[0-9AB]', channel):
            raise ValueError('Invalid ICSI channel')
        if person in assigned and assigned[person] != channel:
            raise ValueError('Inconsistent participant channel')
        assigned[person] = channel
    users = Counter(c for c in assigned.values() if c)
    shared = {p for p,c in assigned.items() if c and users[c] > 1}
    counts = Counter()
    counts['shared_channel_assignments'] = len(shared)
    marks, speech, references = [], [], defaultdict(list)
    mixed_by_person = defaultdict(Counter)
    for person in assigned:
        mixed_by_person[person]
    for seg in tree.iter('Segment'):
        person = seg.get('Participant')
        bounds = timed(seg.get('StartTime'), seg.get('EndTime'))
        vocals = list(seg.iter('VocalSound'))
        laughs = [v for v in vocals if 'laugh' in v.get('Description','').lower()]
        lexical = any(t.strip() for t in seg.itertext())
        if lexical and bounds and person:
            speech.append(dict(speaker=person,start=bounds[0],end=bounds[1]))
            if not vocals:
                references[person].append(bounds)
        if not laughs:
            continue
        isolated = len(seg) == 1 and seg[0] is laughs[0] and not lexical
        counts['laughter_marks'] += len(laughs)
        if person:
            mixed_by_person[person]['marks'] += len(laughs)
            mixed_by_person[person]['mixed'] += 0 if isolated else len(laughs)
        if not isolated:
            counts['mixed_utterances'] += 1
            counts['mixed_marks'] += len(laughs)
            continue
        counts['laughter_only_utterances'] += 1
        if not person or not bounds:
            counts['missing_actor_or_time'] += 1
            continue
        marks.append(dict(speaker=person,start=bounds[0],end=bounds[1],label='vocal'))
        if not assigned.get(person) or person in shared:
            counts['unbound_or_shared_mic'] += 1
    channels = {p:c for p,c in assigned.items() if c and p not in shared}
    return channels, marks, speech, references, mixed_by_person, counts


def decode_sphere(path, expected, decoder):
    if path.stat().st_size != expected['bytes']:
        raise ValueError('ICSI source length changed')
    with path.open('rb') as stream:
        header = stream.read(1024).split(b'end_head')[0].decode('ascii')
        stream.seek(0)
        if hashlib.file_digest(stream,'sha256').hexdigest() != expected['sha256']:
            raise ValueError('ICSI source digest changed')
    fields = {line.split()[0]:line.split()[-1] for line in header.splitlines()[2:] if len(line.split())>=3}
    if fields['channel_count']!='1' or not 8000 <= int(fields['sample_rate']) <= 96000:
        raise ValueError('Unsupported ICSI headset')
    # LDC's Windows binary writes stdout in text mode, expanding each LF to CRLF.
    # Restore that exact transport encoding and verify the provider's PCM checksum.
    result = subprocess.run([str(decoder),'-p','-f','wav',str(path)],capture_output=True,check=True)
    wav_bytes = result.stdout.replace(b'\r\n',b'\n')
    with wave.open(io.BytesIO(wav_bytes)) as wav:
        rate = wav.getframerate()
        n = wav.getnframes()
        if (wav.getnchannels()!=1 or wav.getsampwidth()!=2 or n!=int(fields['sample_count'])
                or rate!=int(fields['sample_rate'])):
            raise ValueError('Decoded ICSI header mismatch')
        audio = np.frombuffer(wav.readframes(n),dtype='<i2')
    if len(audio)!=n or (int(audio.sum(dtype=np.int64)) % 65536 != int(fields['sample_checksum']) % 65536):
        raise ValueError('Decoded ICSI samples failed original checksum')
    return audio,rate


def union(intervals):
    merged = []
    for start,end in sorted(intervals):
        if merged and start<=merged[-1][1]:
            merged[-1]=(merged[-1][0],max(end,merged[-1][1]))
        else:
            merged.append((start,end))
    return merged


def samples(audio, rate, bounds):
    a,b=(round(t*rate) for t in bounds)
    if a<0 or b>len(audio) or a>=b:
        return np.empty(0)
    return audio[a:b].astype(float)/32768.


def channel_features(audio,rate,reference,marks):
    pitches = []
    energy,size = 0.,0
    for bounds in union(reference):
        x=samples(audio,rate,bounds)
        if not len(x):
            continue
        voiced,_=_pitch_and_fraction(x,rate)
        pitches.extend(voiced)
        energy+=float(x@x)
        size+=len(x)
    base_pitch = float(np.median(pitches)) if pitches else None
    base_level = np.sqrt(energy/size) if size else 0.
    for event in marks:
        x=samples(audio,rate,(event['start'],event['end']))
        if not len(x):
            yield None
        else:
            values=relative_measures(x,rate,base_pitch,base_level)
            values['duration_seconds']=event['end']-event['start']
            yield values
