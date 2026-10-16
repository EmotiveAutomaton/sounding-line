"""Pinned public dataset intake v2; identity-encoding transport repair.

Original v1 failure retained; no scientific outcome or scoring changed.

DESIGN CHECK: LESSONS 2-5 / CONTROLS read 2026-10-14. NULL: wrong license,
oversized/incomplete downloads, missing schema or duplicate attempts refuse.
ALTERNATIVE: retained source bytes and parsed row counts agree with an immutable
manifest. No cross-dataset identity joins, model calls or public raw data.
"""
import csv,os,sys,time,threading,traceback
from pathlib import Path
import requests
from runners.stage14.common import REPO,freeze,atomic,filehash,read,now,check_pins,limits
from runners.stage9.process_identity import native_identity
from .queue import require_resources,resource_snapshot

ROOT=REPO/'results/phase_2_4_stage_15/raw/intake-v2'


def fetch(url,path,limit,job):
    """Serial unauthenticated GET, byte ceiling and no retry/resume."""
    total=0
    session=requests.Session();session.trust_env=False
    with session, session.get(url,timeout=(20,60),stream=True,headers={'User-Agent':'SoundingLine-public-research-intake','Accept-Encoding':'identity'}) as r:
        r.raise_for_status()
        if r.headers.get('Content-Encoding','identity').lower() not in ('','identity'):
            raise ValueError('server ignored identity transfer encoding')
        length=int(r.headers.get('Content-Length','0'))
        if length>limit:raise ValueError('declared download exceeds ceiling')
        with path.open('xb') as f:
            for chunk in r.iter_content(1024**2):
                total+=len(chunk)
                if total>limit:raise ValueError('download exceeds ceiling')
                f.write(chunk)
                if total % (8*1024**2)<1024**2:
                    require_resources(resource_snapshot());atomic(ROOT/'PROGRESS.json',dict(at=now(),job=job,phase='download',bytes=total))
        if length and total!=length:raise ValueError('incomplete download')
    return dict(bytes=total,sha256=filehash(path),source=url)


def run(plan_path):
    limits();plan=read(plan_path);check_pins(plan['pins']);require_resources(resource_snapshot())
    ROOT.mkdir(parents=True,exist_ok=True)
    with (ROOT/'ATTEMPT.claim').open('x',encoding='utf8') as f:f.write(now())
    freeze(ROOT/'OWNER.json',dict(at=now(),native=native_identity(),plan_sha256=filehash(plan_path)))
    stop=threading.Event()
    def timer():
        if stop.wait(plan['max_wall_seconds']):return
        atomic(ROOT/'FAILED.json',dict(status='FAILED',at=now(),reason='finite intake deadline'));os._exit(124)
    threading.Thread(target=timer,daemon=True).start();census=[]
    try:
        csv.field_size_limit(20*1024**2)
        for job in plan['datasets']:
            folder=ROOT/job['id'];folder.mkdir(exist_ok=False)
            license_receipt=fetch(job['license_url'],folder/'LICENSE_SOURCE.md',2*1024**2,job['id'])
            license_text=(folder/'LICENSE_SOURCE.md').read_text(encoding='utf8').lower()
            if not ('cc-by-4.0' in license_text or 'creative commons attribution 4.0' in license_text):
                raise ValueError('expected public data license not present')
            meta=fetch(job['url'],folder/'source.csv',job['max_bytes'],job['id'])
            n=0
            with (folder/'source.csv').open(encoding='utf-8-sig',newline='') as f:
                reader=csv.DictReader(f);fields=reader.fieldnames
                if not fields or len(fields)!=len(set(fields)):raise ValueError('invalid CSV schema')
                for row in reader:
                    if None in row or any(v is None for v in row.values()):raise ValueError('CSV field count mismatch')
                    n+=1
                    if n%10000==0:atomic(ROOT/'PROGRESS.json',dict(at=now(),job=job['id'],phase='schema_census',rows=n))
            if n==0:raise ValueError('empty dataset')
            census.append(dict(dataset=job['id'],revision=job['revision'],rows=n,columns=fields,license='CC-BY-4.0',
                source=meta,license_source=license_receipt,scientific_admission=False,
                exposure='Downloaded and schema-counted; no label distribution/model fitting or cross-dataset joins.'))
        freeze(ROOT/'CENSUS.json',census);check_pins(plan['pins'])
        freeze(ROOT/'COMPLETE.json',dict(status='COMPLETE',at=now(),outputs={p.relative_to(ROOT).as_posix():filehash(p)
            for p in ROOT.rglob('*') if p.is_file() and p.name not in ('PROGRESS.json','ATTEMPT.claim')},
            plan_sha256=filehash(plan_path),inference_calls=0,provider_spend_cents=0,scientific_admission=False))
    except BaseException as e:
        freeze(ROOT/'FAILED.json',dict(status='FAILED',at=now(),error=str(e),traceback=traceback.format_exc()));raise
    finally:stop.set()


if __name__=='__main__':run(Path(sys.argv[1]))
