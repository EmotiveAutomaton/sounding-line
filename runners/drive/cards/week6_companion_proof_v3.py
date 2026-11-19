"""Read-only proof for a reviewed counted TP23 reader, not a Python exemption.

DESIGN CHECK: infrastructure/immutable-evidence lessons. Under either scientific
direction, changed source, stale identity, missing ownership or an uncounted
reader must refuse. Only a complete, unchanged protocol proof admits coexistence.
No foreign process, lease, output, environment or configuration is modified.
"""
from datetime import datetime, timezone
from pathlib import Path
import json
import math
import psutil
from . import week6_process_services_v1 as service
from .batch_runtime import REPO, filehash

KIND = 'tompathy-counted-tp23-exact-v3'
CARD = 'ToMpathy-readers-preflight-20261115'
THREADS = ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS')
SLOTS = (REPO/'results/.cpu-slots-20261017',REPO/'results/.cpu-slots-20261107')
need = service.need

def unique(pairs):
    result={}
    for k,v in pairs:
        need(k not in result,'Duplicate companion metadata key');result[k]=v
    return result

def stable_json(path):
    path=service.regular(path);before=path.stat();payload=path.read_bytes();after=path.stat()
    need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==
         (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'Companion metadata changed during read')
    return json.loads(payload,object_pairs_hook=unique)

def stamp(value):
    t=datetime.fromisoformat(value);need(t.tzinfo is not None,'Naive companion timestamp')
    return t.timestamp()

def canonical_command(command, record):
    """Resolve only the one reviewed literal alias, never arbitrary arguments."""
    need(isinstance(command, list) and command and all(isinstance(x, str) for x in command),
         'Malformed companion command')
    result = list(command)
    if result[0] == '.local/readers-venv/Scripts/python.exe':
        candidate = Path(record['root']) / result[0]
        service.regular(candidate)
        need(candidate.resolve() == Path(record['venv']).resolve(),
             'Relative companion executable resolves elsewhere')
        result[0] = record['venv']
    return result


def command_values(command, record, output):
    """Only complete owner-reviewed argument vectors, including aggregation."""
    commands=record['commands']
    need(isinstance(commands,list) and commands and
         all(isinstance(c,list) and all(isinstance(x,str) for x in c) for c in commands),
         'Missing exact companion commands')
    need(len({tuple(c) for c in commands})==len(commands),'Duplicate companion commands')
    need(canonical_command(command, record) in commands,'Different companion command argument')
    need(command.count('--output')==1,'Different companion output binding')
    value=command[command.index('--output')+1]
    need((Path(record['root'])/value).resolve()==output.resolve(),'Companion output argument differs')
    return command


def environment(pid):
    raw=psutil.Process(pid).environ()
    return {key:raw.get(key) for key in (*THREADS,'CUDA_VISIBLE_DEVICES')}

def prove_lease(path, lease, record, at=None):
    root=Path(record['root']);output=Path(lease['output']);native=lease['native'];service.key(native)
    need(output.parent==root/'.local/trigger','Different companion output directory')
    need(lease['card']==CARD and lease['projected_peak_ram_GiB']==6,'Different counted companion role or reservation')
    need(record['kind']==KIND and record['owner_reviewed'] is True,'Unreviewed companion protocol')
    source_pins=record['source_pins'];images=record['image_pins']
    launcher=root/'scripts/engine-readers-job.py';helper=root/'scripts/engine-two-day-job.py'
    need(all(str(p) in source_pins for p in (launcher,helper,REPO/'runners/drive/cards/week5_policy_v2.py')),
         'Companion shared-resource source closure missing')
    need(set(images)=={record['venv'],record['base']} and native['executable']==record['base'],
         'Different companion executable')
    service.check_pins(source_pins);service.check_pins(images)
    before={str(p):filehash(service.regular(p)) for p in (path,output/'owner.json',output/'plan.json',root/'.local/bench/two-day-scoring.lock')}
    need(stable_json(path)==lease,'Companion lease changed before proof')
    owner=stable_json(output/'owner.json');plan=stable_json(output/'plan.json')
    need(owner==dict(lease,lease=str(path)),'Companion lease and owner differ')
    need(stable_json(root/'.local/bench/two-day-scoring.lock')==lease,'Companion exclusive ownership differs')
    need(plan['card']=='TP23' and plan['threads']==2 and type(plan['hours']) in (int,float)
         and math.isfinite(plan['hours']) and 0<plan['hours']<=8,'Different companion resource contract')
    need(plan['launcherSha256']==source_pins[str(launcher)],'Companion loaded launcher differs')
    manifest=plan['snapshotFiles'];need(manifest and manifest==record['snapshot_files'],'Unreviewed companion code snapshot')
    pinned={}
    for name,digest in manifest.items():
        relative=Path(name);need(not relative.is_absolute() and '..' not in relative.parts,'Escaping snapshot path')
        pinned[str(output/'code'/relative)]=digest
    actual={p.relative_to(output/'code').as_posix() for p in (output/'code').rglob('*')
            if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    need(actual==set(manifest),'Companion snapshot inventory differs');service.check_pins(pinned)
    birth=native['created_ticks']/10_000_000-11644473600
    need(0<=stamp(lease['at'])-birth<=120,'Companion lease creation differs')
    deadline=stamp(plan['deadlineAt']);current=(at or datetime.now(timezone.utc)).timestamp()
    need(0<=deadline-birth-plan['hours']*3600<=120 and birth<=current<=deadline,'Companion deadline differs or expired')
    need(all(Path(p).stat().st_mtime<=birth for p in source_pins),'Companion shared code changed after process creation')
    worker=service.observe(native['pid']);need(worker is not None and worker['native']==native,'Stale companion native identity')
    need(Path(worker['cwd'])==root,'Different companion cwd');command_values(worker['command'],record,output)
    parent=service.observe(worker['parent_pid']);need(parent is not None,'Missing companion native forwarder')
    need(parent['native']['executable']==record['venv'] and canonical_command(worker['command'],record)[0]==record['venv']
         and parent['command']==worker['command'] and parent['cwd']==worker['cwd']
         and 0<=native['created_ticks']-parent['native']['created_ticks']<=50_000_000,
         'Different companion forwarding relationship')
    env=environment(native['pid']);need(all(env[k] in ('1','2') for k in THREADS) and env['CUDA_VISIBLE_DEVICES']=='-1',
         'Different live companion thread or GPU environment')
    for p,h in before.items():need(filehash(service.regular(p))==h,'Companion ownership changed during proof')
    service.check_pins(source_pins);service.check_pins(images);service.check_pins(pinned)
    need(service.observe(native['pid'])==worker and service.observe(parent['native']['pid'])==parent,
         'Companion process changed during proof')
    return [native,parent['native']]

def reader_compatibility(record):
    need(record.get('kind')==KIND and record.get('owner_reviewed') is True,'Unreviewed companion protocol')
    found=[]
    for directory in SLOTS:
        for path in directory.glob('slot-*.json'):
            lease=stable_json(path)
            if lease.get('card')==CARD:found.append((path,lease))
    need(len(found)<=1,'Multiple companion readers contradict the reviewed exclusive lease')
    # No active lease grants no exemption: census still rejects uncounted readers.
    return prove_lease(*found[0],record) if found else []
