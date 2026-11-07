"""Bounded public backlog retrieval and schema probe, never scientific scoring.

DESIGN CHECK: LESSONS 2-5. Wrong hashes, archive members and missing required
columns refuse. A prefix measures cost/schema only, never population outcomes.
"""
from pathlib import Path,PurePosixPath
import hashlib,io,tarfile,time
import requests
import pyarrow as pa
from runners.stage14.common import freeze,read,filehash


def fetch(path,url,max_bytes,expected=None,prefix=False):
    path=Path(path);partial=path.with_suffix(path.suffix+'.partial');size=0;digest=hashlib.sha256();start=time.monotonic()
    with requests.get(url,stream=True,timeout=(20,60)) as response:
        response.raise_for_status();length=response.headers.get('Content-Length')
        with partial.open('xb') as f:
            for block in response.iter_content(1024*1024):
                if prefix:block=block[:max_bytes-size]
                size+=len(block)
                if size>max_bytes:raise ValueError('Source byte bound')
                digest.update(block);f.write(block)
                if prefix and size>=max_bytes:break
    h=digest.hexdigest()
    if expected and h!=expected:raise ValueError('Published SHA-256 mismatch')
    partial.replace(path)
    return dict(url=url,bytes=size,sha256=h,content_length=length,wall_seconds=time.monotonic()-start,prefix_only=prefix)


def moral_header(path):
    with tarfile.open(path,'r|gz') as archive:
        entry=next(iter(archive));name=PurePosixPath(entry.name.replace('\\','/'))
        if not entry.isfile() or name.is_absolute() or '..' in name.parts:raise ValueError('Unsafe tar member')
        with archive.extractfile(entry) as f:
            header=f.readline(100000).decode('utf-8-sig').strip()
        columns=[x.strip('"') for x in header.split(',')]
        required={'ResponseID','ExtendedSessionID','UserID','Intervention','Saved','AttributeLevel','ScenarioType','ScenarioTypeStrict'}
        if not required<=set(columns):raise ValueError('Required choice/source columns absent')
        return dict(member=entry.name,expanded_bytes=entry.size,columns=columns)


def chess_prefix(path,limit=8*1024**2):
    start=time.process_time()
    with pa.input_stream(str(path),compression='zstd') as f:data=f.read(limit)
    text=data.decode('utf8');return dict(decompressed_bytes=len(data),events=text.count('[Event '),
        evaluations=text.count('[%eval '),clocks=text.count('[%clk '),cpu_seconds=time.process_time()-start)


def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if config['card']=='B2':
        path=output/'SharedResponses.csv.tar.gz'
        source=fetch(path,config['url'],config['max_bytes'],config['expected_sha256'])
        result=dict(source=source,schema=moral_header(path),scientific_outcomes_computed=False)
    else:
        path=output/'chess-prefix.pgn.zst'
        source=fetch(path,config['url'],config['max_bytes'],prefix=True)
        result=dict(source=source,probe=chess_prefix(path),scientific_outcomes_computed=False)
    freeze(output/'INTAKE.json',result);return result


def verify(output,inputs,config):
    output=Path(output);result=read(output/'INTAKE.json');source=result['source']
    path=output/('SharedResponses.csv.tar.gz' if config['card']=='B2' else 'chess-prefix.pgn.zst')
    assert filehash(path)==source['sha256'] and path.stat().st_size==source['bytes']
    if config['card']=='B2':assert moral_header(path)==result['schema']
    else:
        probe=chess_prefix(path)
        for key in ('decompressed_bytes','events','evaluations','clocks'):assert probe[key]==result['probe'][key]
    return dict(verified=True,source_and_schema_replayed=True,scientific_outcomes_computed=False)
