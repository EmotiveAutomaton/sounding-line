"""Three ordered source intakes; no scientific contrasts and no author decoding.

DESIGN CHECK: LESSONS 2-5. Correct bytes/schema replay; corruption, missing
licence or fields refuse. Source unavailability is not a scientific null.
"""
from pathlib import Path, PurePosixPath
import hashlib
import json
import time
import zipfile
import requests
from runners.stage14.common import freeze, read, filehash

LABELS = ('admiration amusement anger annoyance approval caring confusion curiosity '
          'desire disappointment disapproval disgust embarrassment excitement fear '
          'gratitude grief joy love nervousness optimism pride realization relief '
          'remorse sadness surprise neutral').split()
COLUMNS = ['text','id','subreddit','rater_id','example_very_unclear'] + LABELS
REVISION = 'add492243ff905527e67aeb8b80c082af02207c3'
SOURCES = [
 ('I1-readme','https://datadryad.org/api/v2/files/2197719/download',
  '528ff1c960b419e62c6e4679f728dbb2a838e4016cae17e4c697a95384f6a78c','CC0-1.0','readme.md'),
 ('I1-data','https://datadryad.org/api/v2/files/2197720/download',
  '456859176aece7ac40dc2303aec210490a90bb5d395f713ddf75ffb91fb82168','CC0-1.0','data.zip'),
 ('I2-data',f'https://huggingface.co/datasets/google-research-datasets/go_emotions/resolve/{REVISION}/raw/train-00000-of-00001.parquet',
  None,'Apache-2.0','go_emotions.parquet'),
 ('I3-eil','https://saifmohammad.com/WebDocs/Lexicons/NRC-Emotion-Intensity-Lexicon.zip',
  None,'noncommercial research; no redistribution','eil.zip'),
 ('I3-vad','https://saifmohammad.com/WebDocs/Lexicons/NRC-VAD-Lexicon-v2.1.zip',
  None,'noncommercial research; no redistribution','vad.zip'),
]


def archive_inventory(path):
    total = 0
    rows = []
    with zipfile.ZipFile(path) as archive:
        for entry in archive.infolist():
            name = PurePosixPath(entry.filename.replace('\\','/'))
            if name.is_absolute() or '..' in name.parts or ':' in str(name) or (entry.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Unsafe archive member')
            total += entry.file_size
            if total > 1024**3:
                raise ValueError('Archive expansion exceeds bound')
            rows.append(dict(name=entry.filename, bytes=entry.file_size, crc=entry.CRC))
    return rows


def read_goemotions(path):
    import pyarrow.parquet as pq
    # Explicit projection is load-bearing: never request or materialize author.
    table = pq.read_table(path, columns=COLUMNS, use_threads=False)
    frame = table.to_pandas(use_threads=False)
    if frame[COLUMNS].isnull().any().any():
        raise ValueError('Missing required GoEmotions field')
    if not frame[LABELS].isin([0,1]).all().all():
        raise ValueError('Nonbinary emotion label')
    if frame.duplicated(['id','rater_id']).any():
        raise ValueError('Duplicate comment-rater annotation')
    invariant = frame.groupby('id')[['text','subreddit']].nunique()
    if (invariant != 1).any().any():
        raise ValueError('Inconsistent comment payload')
    if not frame.example_very_unclear.isin([True,False]).all():
        raise ValueError('Invalid unclear flag')
    return frame


def inspect_sources(root, entries):
    checks = {}
    for item in entries:
        if item['status'] != 'downloaded':
            checks[item['id']] = dict(status='unsupported_at_source', reason=item['reason'])
            continue
        path = root/item['file']
        if path.stat().st_size != item['bytes'] or filehash(path) != item['sha256']:
            raise ValueError('Downloaded source mutation')
        if path.suffix == '.zip':
            checks[item['id']] = dict(status='archive_verified', members=archive_inventory(path))
        elif path.suffix == '.parquet':
            frame = read_goemotions(path)
            clear = frame.loc[~frame.example_very_unclear]
            checks[item['id']] = dict(status='schema_verified', rows=len(frame),
                comments=int(frame.id.nunique()), raters=int(frame.rater_id.nunique()),
                unclear_rows=int(frame.example_very_unclear.sum()), clear_rows=len(clear),
                comments_with_three_clear_raters=int((clear.groupby('id').size() >= 3).sum()),
                author_decoded=False, columns_read=COLUMNS)
        else:
            checks[item['id']] = dict(status='bytes_verified',bytes=path.stat().st_size)
    return checks


def execute(output, inputs, config):
    output = Path(output); output.mkdir(parents=True,exist_ok=True)
    if (output/'INTAKE.json').exists():
        saved = read(output/'INTAKE.json')
        if inspect_sources(output,saved['sources']) != saved['checks']:
            raise ValueError('Intake reentry mismatch')
        return saved
    entries=[]; total=0
    for ident,url,expected,licence,name in SOURCES:
        if (output/'YIELD_REQUEST.json').exists():
            return dict(status='yielded')
        path=output/name; temporary=output/(name+'.partial')
        source=inputs.get(ident)
        try:
            if path.exists(): raise ValueError('Unreceipted source already exists')
            digest=hashlib.sha256(); size=0
            if source:
                src=Path(source['path'])
                if filehash(src)!=source['sha256']: raise ValueError('Local source hash mismatch')
                with src.open('rb') as stream, temporary.open('xb') as target:
                    while block:=stream.read(1024*1024):
                        size+=len(block); digest.update(block);target.write(block)
                        if size>256*1024**2: raise ValueError('Per-file bound')
                final_url=url
            else:
                with requests.get(url,stream=True,timeout=(20,60),headers={'User-Agent':'Mozilla/5.0 (research source verification)'}) as response:
                    response.raise_for_status();final_url=response.url
                    with temporary.open('xb') as target:
                        started=time.monotonic()
                        for block in response.iter_content(1024*1024):
                            size+=len(block);digest.update(block);target.write(block)
                            if size>256*1024**2 or total+size>512*1024**2 or time.monotonic()-started>900:
                                raise ValueError('Download bound')
            hexdigest=digest.hexdigest()
            if expected and hexdigest!=expected: raise ValueError('Official source digest mismatch')
            temporary.replace(path); total+=size
            entry=dict(id=ident,status='downloaded',url=url,final_url=final_url,
                       file=name,bytes=size,sha256=hexdigest,licence=licence)
        except (requests.RequestException,ValueError,OSError) as exc:
            entry=dict(id=ident,status='unsupported_at_source',url=url,licence=licence,
                       reason=type(exc).__name__+': '+str(exc),partial_retained=temporary.exists())
        entries.append(entry);freeze(output/(ident+'.json'),entry)
    result=dict(sources=entries,checks=inspect_sources(output,entries),scientific_outcomes_computed=False)
    freeze(output/'INTAKE.json',result)
    return result


def verify(output, inputs, config):
    saved=read(Path(output)/'INTAKE.json')
    if inspect_sources(Path(output),saved['sources'])!=saved['checks']:
        raise ValueError('Independent intake replay mismatch')
    return dict(verified=True,all_source_bytes_replayed=True,author_decoded=False,
                scientific_outcomes_computed=False)
