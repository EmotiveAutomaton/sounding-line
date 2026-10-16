"""Bounded PRISM/MultiPref source intake, no inference or cross-source joins.

DESIGN CHECK: LESSONS 2-5 read 2026-10-14. NULL: drifted notice, malformed JSONL,
duplicate attempt, truncation or size/resource violations refuse completion.
ALTERNATIVE: pinned public files and local schema census bind to one manifest.
Field presence is not semantic validation, anonymity proof or model admission.
"""
import json
import os
from pathlib import Path
import threading
import traceback
import requests

from runners.stage14.common import REPO, read, freeze, atomic, check_pins, filehash, limits, now
from runners.stage9.process_identity import native_identity
from .queue import resource_snapshot, require_resources

ROOT = REPO / 'results/phase_2_4_stage_15/raw/public-jsonl-v1'


def fetch(url, path, ceiling, pulse):
    session = requests.Session()
    session.trust_env = False
    total = 0
    with session, session.get(url, timeout=(20,60), stream=True,
            headers={'User-Agent':'SoundingLine-public-research-intake', 'Accept-Encoding':'identity'}) as response:
        response.raise_for_status()
        if response.headers.get('Content-Encoding','identity').lower() not in ('','identity'):
            raise ValueError('unexpected transfer encoding')
        length = int(response.headers.get('Content-Length','0'))
        if length > ceiling:
            raise ValueError('declared size exceeds ceiling')
        with path.open('xb') as output:
            for chunk in response.iter_content(1024**2):
                total += len(chunk)
                if total > ceiling:
                    raise ValueError('download exceeds ceiling')
                output.write(chunk)
                pulse(total)
        if length and length != total:
            raise ValueError('incomplete download')
    return dict(bytes=total, sha256=filehash(path), source=url)


def census(path):
    count = 0
    fields = set()
    with path.open(encoding='utf8') as stream:
        for line in stream:
            if len(line) > 32 * 1024**2:
                raise ValueError('JSONL record exceeds bound')
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError('JSONL record is not an object')
            fields.update(row)
            count += 1
    if count == 0:
        raise ValueError('empty dataset')
    return dict(rows=count, fields=sorted(fields), scientific_admission=False)


def run(plan_path):
    limits()
    plan = read(plan_path)
    check_pins(plan['pins'])
    require_resources(resource_snapshot())
    with (ROOT/'ATTEMPT.claim').open('x', encoding='utf8') as f:
        f.write(now())
    freeze(ROOT/'OWNER.json', dict(at=now(), native=native_identity(), plan_sha256=filehash(plan_path)))
    stop = threading.Event()
    def deadline():
        if not stop.wait(plan['max_wall_seconds']):
            atomic(ROOT/'FAILED.json', dict(status='FAILED', at=now(), reason='finite intake deadline'))
            os._exit(124)
    threading.Thread(target=deadline, daemon=True).start()
    records = []
    try:
        for dataset in plan['datasets']:
            folder = ROOT / dataset['name']
            folder.mkdir(exist_ok=False)
            for item in dataset['files']:
                path = folder / item['name']
                if path.parent != folder or path.name != item['name']:
                    raise ValueError('nonlocal destination')
                def pulse(size):
                    require_resources(resource_snapshot())
                    atomic(ROOT/'PROGRESS.json', dict(at=now(), dataset=dataset['name'], file=item['name'], bytes=size))
                meta = fetch(item['url'], path, item['ceiling'], pulse)
                if item.get('expected_sha256') and meta['sha256'] != item['expected_sha256']:
                    raise ValueError('pinned notice mismatch')
                shape = census(path) if path.suffix == '.jsonl' else None
                records.append(dict(dataset=dataset['name'], revision=dataset['revision'], name=item['name'],
                                    license=dataset['license'], meta=meta, census=shape))
        check_pins(plan['pins'])
        freeze(ROOT/'CENSUS.json', records)
        freeze(ROOT/'COMPLETE.json', dict(status='COMPLETE', at=now(), inference_calls=0, provider_spend_cents=0,
            scientific_admission=False, plan_sha256=filehash(plan_path), outputs={p.relative_to(ROOT).as_posix():filehash(p)
            for p in ROOT.rglob('*') if p.is_file() and p.name not in ('PROGRESS.json','ATTEMPT.claim')}))
    except BaseException as e:
        freeze(ROOT/'FAILED.json', dict(status='FAILED', at=now(), error=str(e), traceback=traceback.format_exc()))
        raise
    finally:
        stop.set()


if __name__ == '__main__':
    import sys
    run(Path(sys.argv[1]))
