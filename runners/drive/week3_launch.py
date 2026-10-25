"""Launch only an owner-frozen Week 3 plan; register monitoring before work.

DESIGN CHECK: LESSONS 3-5. Failed pins, missing native identity or duplicate
attempt refuse. Launch success is not scientific completion. No research
selection, automatic retries, paid dispatch or publication occurs here.
"""
from pathlib import Path
import argparse
import ast
import importlib.util
import subprocess
import time
from runners.stage14.common import REPO, read, atomic, freeze, filehash, now
from runners.stage9.process_identity import native_identity
from runners.drive.cards.batch_runtime import check_files
from runners.drive.cards.week3_policy import admission


def closure(modules):
    pending, seen, sources = list(modules), set(), set()
    while pending:
        module = pending.pop()
        if module in seen: continue
        seen.add(module)
        parts = module.split('.')
        path = REPO.joinpath(*parts).with_suffix('.py')
        if not path.exists(): path = REPO.joinpath(*parts)/'__init__.py'
        if not path.exists(): continue
        sources.add(path)
        package = module if path.name == '__init__.py' else module.rpartition('.')[0]
        for index in range(1, len(parts)):
            init = REPO.joinpath(*parts[:index])/'__init__.py'
            if init.exists(): sources.add(init)
        for node in ast.walk(ast.parse(path.read_text(encoding='utf8'))):
            if isinstance(node, ast.Import): names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                name = importlib.util.resolve_name('.'*node.level+(node.module or ''), package) if node.level else node.module
                names = [name]+[name+'.'+a.name for a in node.names] if name else []
            else: continue
            pending.extend(n for n in names if n and n.split('.')[0] in {'runners','soundingline','corpora','tools'})
    return sources


def launch(root):
    root = Path(root).resolve()
    if not root.is_relative_to(REPO): raise ValueError('Run outside repository')
    if (root/'ATTEMPT.claim').exists(): raise ValueError('Existing attempt; inspect, do not resubmit')
    plan = read(root/'PLAN.json')
    check_files(plan['pins'])
    admission(plan)
    for path in closure([plan['module'], 'runners.drive.cards.batch_runtime_v5']):
        if plan['pins'].get(str(path)) != filehash(path): raise ValueError('Missing source closure pin: '+str(path))
    if not plan.get('owner_reviewed') or not plan.get('validation_receipts'):
        raise ValueError('Concrete owner review and validation required')
    for path in plan['validation_receipts']:
        if plan['pins'].get(path) != filehash(path): raise ValueError('Validation not pinned')
    config_path = REPO/'.agent-state/watch.json'
    paths = [(root/n).relative_to(REPO).as_posix() for n in ('COMPLETE.json','FAILED.json','PAUSED.json','MONITOR_FAILED.json')]
    config = read(config_path)
    for key in ('paths','urgent_paths'): config[key] = sorted(set(config.get(key, [])+paths))
    atomic(config_path, config)
    for path in closure([plan['module'], 'runners.drive.cards.batch_runtime_v5']):
        dest = root/'source_capsule'/path.relative_to(REPO)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(path.read_bytes())
    def quote(value): return "'"+str(value).replace("'", "''")+"'"
    cmd = ('Start-Process -WindowStyle Hidden -FilePath '+quote(REPO/'.venv/Scripts/python.exe')+
           ' -ArgumentList '+quote('-X utf8 -B -m runners.drive.cards.batch_runtime_v5 run '+str(root))+
           ' -WorkingDirectory '+quote(REPO)+' -RedirectStandardOutput '+quote(root/'stdout.log')+
           ' -RedirectStandardError '+quote(root/'stderr.log'))
    subprocess.run(['powershell','-NoProfile','-Command',cmd], check=True, timeout=30)
    deadline = time.monotonic()+30
    while not (root/'OWNER.json').exists():
        if time.monotonic() > deadline: raise TimeoutError('Native owner handshake')
        time.sleep(.2)
    owner = read(root/'OWNER.json')['native']
    if native_identity(owner['pid']) != owner: raise ValueError('Owner identity mismatch')
    config = read(config_path)
    config.setdefault('process_watches', []).append(dict(label=plan['card'], native=owner,
        failure_output=paths[-1], terminal_paths=paths[:-1]))
    atomic(config_path, config)
    freeze(root/'MONITOR_READY.json', dict(at=now(), owner_sha256=filehash(root/'OWNER.json'), watch_config_sha256=filehash(config_path)))
    return dict(root=str(root), native=owner, plan_sha256=filehash(root/'PLAN.json'))


if __name__ == '__main__':
    import json
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    print(json.dumps(launch(parser.parse_args().root)))
