"""One offline semantic verifier for partial units, complete blocks and scoring.

DESIGN CHECK: LESSONS3-5. Under either hypothesis original RAW is authoritative;
rehashing a forged parse, execution, feedback or cost cannot make it pass. A fresh
scratch execution reconstructs requests and all derived values with model APIs
forbidden. Only observed wall-clock metadata is inherited; scientific values and
required cost keys are regenerated. The immutable producer remains untouched.
"""
from contextlib import ExitStack
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
from . import ollama, gear3_io
from .contracts import digest

VOLATILE = {'at', 'finished_at', 'created_at', 'wall_seconds', 'representation_seconds', 'cpu_seconds'}


def verify_route(task, row, arm, profile, original, training, ghost_root):
    from .gear3_batch import dispatch
    original = Path(original).resolve()
    before = gear3_io.inventory(original)
    if not before: raise ValueError('absent original route evidence')
    consumed = set(); pending = []
    def read(name):
        return json.loads((original/name).read_text(encoding='utf8'))
    # Inventories are checked independently of semantic reconstruction.
    for name in before:
        if name.endswith('COMPLETE.json'):
            complete = read(name)
            if 'files' in complete:
                folder = (original/name).parent
                expected = {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in folder.rglob('*') if p.is_file() and p != original/name}
                if complete['files'] != expected: raise ValueError('nested original inventory differs')
    model_names = [n for n in before if n.endswith('MODEL.json')]
    if not model_names: raise ValueError('missing model identity evidence')
    model = read(model_names[0])
    if (model['model']['name'] != profile.model or model['model']['digest'] != profile.model_digest
            or model['server']['version'] != profile.server_version
            or model['configuration']['details']['quantization_level'] != profile.quantization
            or model['reader_profile'] != __import__('dataclasses').asdict(profile)):
        raise ValueError('recorded serving identity differs')
    def forbidden(*a, **k): raise ValueError('offline replay attempted model/network access')
    with tempfile.TemporaryDirectory(prefix='g3-replay-') as temp, ExitStack() as stack:
        scratch = Path(temp)/'route'
        original_write = ollama.write_new
        def inherited(value, old, location=()):
            if isinstance(value, dict) and isinstance(old, dict):
                if set(value) != set(old): raise ValueError('semantic key set differs: '+str(location))
                return {k: deepcopy(old[k]) if k in VOLATILE else inherited(v, old[k], location+(k,))
                        for k,v in value.items()}
            if isinstance(value, list) and isinstance(old, list):
                if len(value) != len(old): raise ValueError('semantic list length differs: '+str(location))
                return [inherited(v,o,location+(str(i),)) for i,(v,o) in enumerate(zip(value,old))]
            if value != old: raise ValueError('semantic evidence differs: '+str(location))
            return value
        def write(path, value):
            name = path.relative_to(scratch).as_posix()
            if name not in before or name in consumed: raise ValueError('replay file order/inventory differs: '+name)
            old = read(name)  # mutate only freshly computed values
            if path.name == 'REQUEST.json':
                if 'cloud_reservation' in old: value['cloud_reservation'] = deepcopy(old['cloud_reservation'])
                pending.append((name, deepcopy(value['request'])))
            # Executor command paths differ across Linux production and local replay.
            # Source hashes/frame/output are rechecked; only path spelling is inherited.
            if path.name == 'RAW.json' and 'command' in value:
                cmd, prior = value['command'], old.get('command', [])
                if (len(cmd) != 6 or len(prior) != 6 or cmd[1:4] != prior[1:4]
                        or Path(prior[4].replace(chr(92),'/')).name != 'executor_worker.py'):
                    raise ValueError('executor command contract differs')
                value['command'] = deepcopy(prior)
                current_lines=[json.loads(line) for line in value['stdout'].splitlines()]
                prior_lines=[json.loads(line) for line in old['stdout'].splitlines()]
                if len(current_lines)!=2 or len(prior_lines)!=2:
                    raise ValueError('native protocol line count differs')
                if type(prior_lines[0].get('pid')) is not int:
                    raise ValueError('missing native producer identity')
                current_lines[0]['pid']=prior_lines[0]['pid']
                inherited(current_lines,prior_lines,(name,'decoded native output'))
                value['stdout']=old['stdout']  # preserve original serialization after semantic comparison
            rebuilt = inherited(value, old, (name,))
            value.clear(); value.update(rebuilt)
            original_write(path, value); consumed.add(name)
        def raw_api(path, payload=None, **kwargs):
            if path != '/api/chat' or len(pending) != 1: return forbidden()
            name, expected = pending.pop()
            if payload != expected: raise ValueError('literal request ordering differs')
            return read(str(Path(name).with_name('RAW.json')).replace(chr(92),'/'))
        # Avoid inheriting a live cloud journal or committing scratch evidence.
        token = gear3_io._ACTIVE.set(None)
        stack.callback(gear3_io._ACTIVE.reset, token)
        # Existing modules sometimes bind write_new at import time.
        for name, module in list(sys.modules.items()):
            if name.startswith('runners.stage10.') and getattr(module,'write_new',None) is original_write:
                stack.enter_context(patch.object(module,'write_new',write))
        stack.enter_context(patch.object(ollama,'identity',lambda **kw: deepcopy(model) if kw.get('profile') == profile else forbidden()))
        stack.enter_context(patch.object(ollama,'api',raw_api))
        stack.enter_context(patch.object(ollama.urllib.request,'urlopen',forbidden))
        result = dispatch(task,row,arm,profile,scratch,training,ghost_root)
        if pending or consumed != set(before): raise ValueError('unconsumed original evidence or calls')
    if gear3_io.inventory(original) != before: raise ValueError('offline replay modified original evidence')
    return result
