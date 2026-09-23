"""One bounded, checkpointed Stage 12 card; no detached scientific children.

DESIGN CHECK: LESSONS 3-5. NULL: complete evidence replays without dispatch.
ALTERNATIVE: cancellation, deadline, source drift, cost exhaustion or an unknown
previous attempt stops only this card. Its full reservation remains on crash;
success requires the handler's complete roster and controls, never exit alone.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import time
import traceback
from datetime import datetime, timezone
from .common import RAW, ROOT, REPO, read, freeze, atomic, filehash, check_pins, admit, limit_process, own_cpu, now
from runners.stage9.process_identity import native_identity
from tools.codex_common import singleton

def handler(name):
    if name=='casebook':
        from .casebook import run
        return run
    if name=='local-operator-compile':
        from .local_operator import compile
        return compile
    if name in ('retention-access-compile','retention-access-run'):
        from . import retention_access
        return retention_access.compile if name.endswith('compile') else retention_access.run
    if name=='local-capacity-wait':
        from .capacity_wait import run
        return run
    if name=='native-expertise':
        from .expertise import run
        return run
    if name in ('native-model-import','native-causal-review','native-practice-review'):
        from . import native_shared
        return getattr(native_shared,name.removeprefix('native-').replace('-','_'))
    if name in ('shared-compose','shared-expertise'):
        from .shared_extensions import compose,expertise
        return compose if name=='shared-compose' else expertise
    if name=='shared-model-import':
        from .shared_model import import_model
        return import_model
    if name in ('retention-compile','retention-run'):
        from . import retention
        return retention.compile if name.endswith('compile') else retention.run
    if name=='discrete-run':
        from .discrete import run
        return run
    if name=='git-reader-compile':
        from .git_context import compile_reader
        return compile_reader
    if name=='aries-compile':
        from .aries import compile
        return compile
    if name in ('local-interpretation-compile','local-interpretation-run'):
        from . import local_interpretation
        return local_interpretation.compile if name.endswith('compile') else local_interpretation.run
    if name in ('tiny-fit','tiny-causal'):
        from . import tiny
        return tiny.fit if name=='tiny-fit' else tiny.causal
    if name in ('primary-analysis-freeze','primary-analysis'):
        from . import primary_analysis
        return primary_analysis.freeze_analysis if name=='primary-analysis-freeze' else primary_analysis.consume
    if name in ('context-compile','context-run'):
        from . import context_battery
        return context_battery.compile if name=='context-compile' else context_battery.run
    if name=='ghost-local':
        from .ghost_bridge import consume
        return consume
    if name in ('local-capacity','local-canary'):
        from . import canary
        return canary.capacity if name=='local-capacity' else canary.run
    if name=='broad-population':
        from .population import build
        return build
    if name=='fixture':
        def fixture(out,card,pulse,raw):
            if card.get('rehearsal') is not True:raise ValueError('fixture is not scientific work')
            if card['id']=='fixture-fails':raise ValueError('deliberate rehearsal failure')
            return dict(status='complete',kind='infrastructure',controls=dict(known_answer=True))
        return fixture
    if name in ('inventory','runtime'):
        from . import audit
        return getattr(audit,name)
    if name=='git-context':
        from .git_context import run
        return run
    if name in ('ghost-reference','continuing','tiny-rehearsal'):
        from . import controlled
        return getattr(controlled,name.replace('-','_'))
    from . import studies
    return getattr(studies,name.replace('-','_'))

def run(card_path,raw=RAW):
    raw=Path(raw);card_path=Path(card_path);card=read(card_path)
    out=raw/'jobs'/card['id'];out.mkdir(parents=True,exist_ok=True)
    limit_process()
    with singleton(raw/'locks'/(card['id']+'.lock')):
        check_pins(card['source_pins'])
        if card.get('contract_sha256') and filehash(raw/'CONTRACT.json')!=card['contract_sha256']:
            raise ValueError('original week contract changed')
        for name,h in card.get('inputs',{}).items():
            if filehash(name)!=h:raise ValueError('bound input changed: '+name)
        dependencies={}
        for name in card.get('needs',[]):
            path=REPO/name
            if not path.exists():raise ValueError('missing prerequisite: '+name)
            if path.name=='COMPLETE.json':
                parent=read(path)
                if str(parent.get('status','')).lower()!='complete':raise ValueError('prerequisite not complete')
                for output,h in parent.get('output_files',{}).items():
                    if filehash(path.parent/output)!=h:raise ValueError('prerequisite output changed')
                summary=path.with_name('SUMMARY.json')
                if summary.exists():
                    evidence=read(summary)
                    if evidence.get('status')!='complete' or not all(evidence.get('controls',{}).values()):
                        raise ValueError('prerequisite controls not complete')
                    for output,h in evidence.get('files',{}).items():
                        if filehash(path.parent/output)!=h:raise ValueError('prerequisite binary/source member changed')
            dependencies[name]=filehash(path)
        complete=out/'COMPLETE.json'
        if complete.exists():
            r=read(complete)
            if r['manifest_sha256']!=filehash(card_path):raise ValueError('completed manifest differs')
            for n,h in r['output_files'].items():
                if filehash(out/n)!=h:raise ValueError('complete output changed')
            for n,h in read(out/'SUMMARY.json').get('files',{}).items():
                if filehash(out/n)!=h:raise ValueError('completed binary/source member changed')
            # Every card's final verified record names its semantic replay recipe.
            return r
        if (out/'START.json').exists():
            raise RuntimeError('previous attempt not reconciled; reserve retained; no automatic retry')
        contract=read(raw/'CONTRACT.json');admit(card,contract,raw)
        t0=time.monotonic();cpu0=own_cpu();charge=raw/'charges'/(card['id']+'.json')
        reserve=dict(cpu_seconds=card.get('cpu_seconds',0.),gpu_seconds=0.,diagnostic_gpu_seconds=0.,
                     host_cpu_seconds=0.,state='reserved',at=now(),job=card['id'])
        freeze(charge,reserve)
        freeze(out/'START.json',dict(at=now(),native=native_identity(),manifest_sha256=filehash(card_path)))
        freeze(out/'DEPENDENCIES.json',dependencies)
        def pulse(**details):
            used=own_cpu()-cpu0
            if (raw/'CANCEL.json').exists():raise TimeoutError('requested natural-boundary stop')
            if used>card['cpu_seconds'] or time.monotonic()-t0>card['wall_seconds']:
                raise TimeoutError('card resource ceiling')
            if datetime.now(timezone.utc)>=datetime.fromisoformat(contract['reporting']):
                raise TimeoutError('reporting reserve reached')
            atomic(out/'STATUS.json',dict(status='running',at=now(),native=native_identity(),cpu_seconds=used,
                                         wall_seconds=time.monotonic()-t0,**details))
        try:
            pulse(phase='starting')
            if card['handler'] in ('inventory','runtime'):
                summary=handler(card['handler'])(out,pulse)
            else:
                summary=handler(card['handler'])(out,card,pulse,raw)
            pulse(phase='semantic-completion-check')
            if summary.get('status')!='complete' or not summary.get('controls') or not all(summary['controls'].values()):
                raise ValueError('handler did not complete its declared controls and population')
            freeze(out/'SUMMARY.json',summary)
            files={p.name:filehash(p) for p in out.glob('*.json') if p.name not in ('STATUS.json','START.json','COMPLETE.json')}
            r=freeze(complete,dict(status='complete',at=now(),manifest_sha256=filehash(card_path),output_files=files,
                                  kind=summary['kind'],scientific_landing='requires full internal write-through'))
            atomic(out/'STATUS.json',dict(status='complete',at=now(),cpu_seconds=own_cpu()-cpu0))
            atomic(charge,dict(reserve,cpu_seconds=own_cpu()-cpu0,state='complete',wall_seconds=time.monotonic()-t0))
            return r
        except BaseException as exc:
            freeze(out/'FAILED.json',dict(status='failed',at=now(),error=repr(exc),traceback=traceback.format_exc(),
                                        outcome='incomplete card; no scientific verdict'))
            atomic(charge,dict(reserve,cpu_seconds=own_cpu()-cpu0,state='failed',wall_seconds=time.monotonic()-t0))
            raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--card',required=True,type=Path);p.add_argument('--raw',type=Path,default=RAW)
    a=p.parse_args();run(a.card,a.raw)
