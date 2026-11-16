"""Exact operational service proof for the R18 accounting census.

DESIGN CHECK: LESSONS 3-5. No scientific direction changes this gate. A known
non-budget watcher and the native venv forwarder of an already authenticated
interpreter may remain. Changed code, command, PID identity or unknown reader
refuses. This module only reads; no service launch, stop or registry writes.
"""
from pathlib import Path
import json
import os
import sqlite3
import stat
import psutil
from .batch_runtime import REPO, filehash
from runners.stage9.process_identity import native_identity

WATCHER = REPO/'tools/codex_watch.py'
STATE = REPO/'.agent-state'
VENV = REPO/'.venv/Scripts/python.exe'
BASE = Path('C:/Python313/python.exe')
WINDOWLESS = Path('C:/Python313/pythonw.exe')
CODE_PINS = {
    str(WATCHER):'a9043fe92536f9dd188cdc438092ebf41088e41ef009db169454b75ef2843403',
    str(REPO/'tools/codex_common.py'):'f2594b4815d1f7ebd90135b8a9b06802b9d524a8aa7db19635212789b6d55656',
    str(REPO/'tools/codex_queue_api.py'):'d8093f56e216989cdb48af2170efb4524b16f14184560243fbe806a05a0cec45',
    str(REPO/'runners/stage9/process_identity.py'):'a17bc3ca37ffafea5b272acc7bea0d1536049e11e870fc04471fefb1cee84a35',
}
IMAGE_PINS = {
    str(VENV):'d70fced7f461f38f9f224d8673fb74e96e4facb4283ff4e8697543b457fea8a0',
    str(BASE):'7d96a4ed35d6e596cd9dd8933feafc66349cc21f75be3b15c89fd336e50140c1',
    str(WINDOWLESS):'084061e07ae200522a756f390e92c6ad7256e486792c81eb3d0f8a5da27b2c0d',
}


def need(value,message):
    if not value:raise ValueError(message)


def key(native):
    need(set(native)=={'pid','created_ticks','executable'} and type(native['pid']) is int
         and native['pid']>0 and type(native['created_ticks']) is int and native['created_ticks']>0
         and isinstance(native['executable'],str) and native['executable'], 'Invalid service native identity')
    return native['pid'],native['created_ticks'],native['executable']


def regular(path):
    path=Path(path)
    # Reject every ancestor before resolve can conceal a reparse traversal.
    for ancestor in [*reversed(path.absolute().parents),path.absolute()]:
        info=ancestor.lstat()
        need(not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400,
             'Linked service source/image')
    need(stat.S_ISREG(path.lstat().st_mode),'Nonregular service source/image')
    return path


def check_pins(pins):
    for name,digest in pins.items():
        path=regular(name);before=path.stat()
        need(filehash(path)==digest,'Service source/image bytes changed')
        after=path.stat()
        need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==
             (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'Service file changed during check')


def observe(pid):
    """Bind command/cwd/parent to one creation identity; errors stay unknown."""
    first=native_identity(pid)
    if first is None:return None
    try:
        process=psutil.Process(pid)
        row=dict(native=first,command=process.cmdline(),cwd=process.cwd(),parent_pid=process.ppid())
    except psutil.NoSuchProcess:
        # Confirm disappearance natively; a PID may already have been reused.
        need(native_identity(pid) is None,'Process changed during observation')
        return None
    last=native_identity(pid)
    need(last==first,'Native identity changed during observation')
    return row


def watcher_boot():
    """Read only its startup binding, never invoke the watcher's mutating CLI."""
    path=regular(STATE/'runtime.sqlite')
    db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=5)
    try:
        row=db.execute("SELECT value FROM meta WHERE key='watcher'").fetchone()
        need(row is not None,'Watcher startup binding absent')
        return json.loads(row[0])
    finally:db.close()


def watcher_compatibility(record):
    need(record.get('kind')=='sounding-line-durable-watcher' and record.get('owner_reviewed') is True,
         'Unreviewed non-budget service')
    need(record['source_pins']==CODE_PINS,'Different watcher implementation')
    need(record['image_pins']=={str(WINDOWLESS):IMAGE_PINS[str(WINDOWLESS)]},'Different watcher image')
    check_pins(CODE_PINS);check_pins(record['image_pins'])
    native=record['native'];key(native)
    need(native['executable']==str(WINDOWLESS),'Different watcher interpreter')
    expected=[str(WINDOWLESS),'-B',str(WATCHER),'run']
    need(record['command']==expected and Path(record['cwd'])==REPO,'Different watcher command or cwd')
    boot=watcher_boot()
    need(boot==record['startup'] and boot['pid']==native['pid'],'Watcher startup changed')
    for name,field in ((WATCHER,'source_sha256'),(REPO/'tools/codex_common.py','common_sha256'),
                       (REPO/'tools/codex_queue_api.py','queue_api_sha256')):
        need(boot[field]==CODE_PINS[str(name)],'Loaded watcher code differs')
    birth=native['created_ticks']/10_000_000-11644473600
    need(0<=boot['started']-birth<=60,'Watcher startup and creation time differ')
    for name in CODE_PINS:
        need(Path(name).stat().st_mtime<=birth,'Watcher dependency changed since process creation')
    current=observe(native['pid'])
    if current is None:return None
    need(current['native']==native,'Watcher PID identity changed')
    need(current['command']==record['command'] and current['cwd']==record['cwd'],
         'Live watcher command or cwd changed')
    return native


def forwarder_pair(parent,child):
    """Only the pinned native venv launcher of a known interpreter; no Python module bypass."""
    a,b=parent['native'],child['native'];key(a);key(b)
    return (a['pid']==child['parent_pid'] and a['executable']==str(VENV)
            and b['executable']==str(BASE) and parent['command']==child['command']
            and bool(parent['command']) and parent['command'][0]==str(VENV)
            and parent['cwd']==child['cwd'] and Path(parent['cwd'])==REPO
            and 0<=b['created_ticks']-a['created_ticks']<=50_000_000)


def check_census(compatible,classify,images):
    need(images==IMAGE_PINS,'Different reviewed Python forwarding images')
    check_pins(images)
    allowed={key(row) for row in compatible}
    # The caller is already the reviewed transition entrypoint. Its C launcher
    # only forwards to this exact child, rather than reading an accounting file.
    caller=observe(os.getpid());need(caller is not None,'Census caller vanished')
    allowed.add(key(caller['native']))
    observed={os.getpid():caller}
    for process in psutil.process_iter(['pid','name']):
        if 'python' not in (process.info['name'] or '').lower():continue
        row=observe(process.pid)
        if row is not None:observed[process.pid]=row
    for row in tuple(observed.values()):
        if key(row['native']) not in allowed:continue
        parent=observed.get(row['parent_pid'])
        if parent is not None and forwarder_pair(parent,row):allowed.add(key(parent['native']))
    for row in observed.values():
        if key(row['native']) in allowed:continue
        classification=classify(row['command'],row['cwd'])
        if classification=='outside_workspace':continue
        # A matching module name or frozen plan alone never proves ownership.
        # OWNER is written before claim; serialize around that short boundary.
        raise RuntimeError('Unmigrated or unexplained workspace Python reader: '+str(row['native']['pid']))
    # A live source edit or binary replacement cannot be hidden by a long census.
    check_pins(images)
    return {'python_processes':len(observed),'compatible_native_identities':len(allowed)}
