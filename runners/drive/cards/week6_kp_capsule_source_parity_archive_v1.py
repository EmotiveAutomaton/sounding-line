"""Read one native-complete sealed KP projection, without reconstructing D33.

DESIGN CHECK: LESSONS2/3/5. No filtering, selected subset or new source route.
Changed complete/plan/seal/native/code/bytes or mixed constructed/real kind refuses.
"""
from pathlib import Path
import gzip
import hashlib
import json
import stat
import math
from .week6_kp_source_v1 import digest,read
from . import week6_kp_source_stage_parity_archive_v1 as stage
from runners.stage9.process_identity import native_identity


def regular(path):
    path=Path(path).absolute()
    for q in [*reversed(path.parents),path]:
        info=q.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:
            raise ValueError('Linked capsule source')
    if not stat.S_ISREG(path.stat().st_mode):raise ValueError('Nonregular capsule source')
    return path


def load_authenticated(inputs,*,decisions):
    if decisions!=stage.DECISIONS:raise ValueError('Original KP source decisions differ')
    complete=regular(inputs['source_stage_complete']);root=complete.parent
    if complete.name!='COMPLETE.json' or digest(complete)!=inputs['source_stage_complete_sha256']:
        raise ValueError('Native source-stage completion pin differs')
    if any((root/name).exists() for name in ('FAILED.json','PAUSED.json','MONITOR_FAILED.json')):
        raise ValueError('Ambiguous or unreconciled source-stage terminal')
    done=read(complete)
    if done.get('status')!='COMPLETE' or done.get('fresh_process_verified') is not True:
        raise ValueError('Source stage lacks full native completion/replay')
    for name in ('PLAN.json','OWNER.json','EXECUTE_NATIVE.json','VERIFY_NATIVE.json',
                 'EXECUTE_CHILD.json','VERIFY_CHILD.json','VERIFIED.json',
                 'EXECUTE_JOB_USAGE.json','VERIFY_JOB_USAGE.json',
                 'EXECUTE_ENVIRONMENT.json','VERIFY_ENVIRONMENT.json','ADMISSION.json',
                 'output/SEAL.json','output/BINDING.json','output/CORPUS.json.gz'):
        if digest(regular(root/name))!=done['outputs'][name]:
            raise ValueError('Native source-stage artifact changed: '+name)
    plan=read(root/'PLAN.json');owner=read(root/'OWNER.json')
    if owner.get('plan_sha256')!=digest(root/'PLAN.json'):
        raise ValueError('Source-stage owner/plan differs')
    if plan.get('module')!='runners.drive.cards.week6_kp_source_stage_parity_archive_v1':
        raise ValueError('Wrong complete source module')
    for name in ('OWNER.json','EXECUTE_NATIVE.json','VERIFY_NATIVE.json','EXECUTE_CHILD.json','VERIFY_CHILD.json'):
        native=read(root/name)['native']
        if native_identity(native['pid'])==native:raise ValueError('Source-stage native remains live')
    total=0.
    for operation in ('EXECUTE','VERIFY'):
        usage=read(root/(operation+'_JOB_USAGE.json'))
        cpu=usage['cpu_seconds']
        if (usage.get('exit_code')!=0 or usage.get('includes_all_descendants_and_exited_processes') is not True
                or type(cpu) not in (int,float) or not math.isfinite(cpu) or cpu<0
                or usage.get('termination_margin_cpu_seconds')!=0):
            raise ValueError('Source-stage whole-Job completion proof differs')
        total+=cpu
        env=read(root/(operation+'_ENVIRONMENT.json'))
        if env.get('threads')!=2 or any(pool['num_threads']>2 for pool in env['pools']):
            raise ValueError('Source-stage numerical threads differ')
    if done['cpu_seconds']!=total:raise ValueError('Source-stage terminal/native cost differs')
    lease=Path(read(root/'ADMISSION.json')['lease'])
    if lease.exists() and read(lease).get('native')==owner['native']:
        raise ValueError('Source-stage owned lease remains')
    if read(root/'VERIFIED.json').get('full_independent_source_projection') is not True:
        raise ValueError('Full source replay proof missing')
    seal=read(root/'output/SEAL.json')
    if seal.get('metadata_resolution')!=stage.original.metadata_resolution():
        raise ValueError('Exact archived metadata proof differs')
    if digest(root/'output/SEAL.json')!=inputs['source_stage_seal_sha256'] or seal['schema']!=stage.SCHEMA:
        raise ValueError('Sealed source identity differs')
    if seal['source_decisions']!=decisions or plan['config']['source_decisions']!=decisions:
        raise ValueError('Sealed source decisions differ')
    expected={'constructed-fixture-only':'constructed-literal-walsh-v1',
              'original-D33-only':'authenticated-D33'}.get(inputs.get('data_access'))
    if expected is None or seal['source_kind']!=expected or plan['config']['source_kind']!=expected:
        raise ValueError('Constructed/real capsule substitution')
    if seal['source_completion_sha256']!=inputs['original_source_completion_sha256']:
        raise ValueError('Original D33/invented source identity differs')
    expected_modules={str(Path(x).resolve()) for x in (stage.__file__,stage.original.__file__,stage.fixture.__file__)}
    if set(seal['module_pins'])!=expected_modules:raise ValueError('Sealed mapper closure differs')
    if read(root/'output/BINDING.json')!=dict(inputs=plan['inputs'],config=plan['config']):
        raise ValueError('Sealed source plan/input binding differs')
    for name,pin in seal['module_pins'].items():
        if digest(regular(name))!=pin:raise ValueError('Sealed mapper source changed')
    packed=root/'output/CORPUS.json.gz'
    if digest(packed)!=seal['corpus_sha256']:raise ValueError('Sealed corpus bytes differ')
    size=seal['json_bytes']
    if type(size) is not int or not 0<size<=stage.MAX_JSON_BYTES:raise ValueError('Invalid capsule size')
    with gzip.open(packed,'rb') as stream:payload=stream.read(size+1)
    if len(payload)!=size or hashlib.sha256(payload).hexdigest()!=seal['json_sha256']:
        raise ValueError('Sealed decompressed corpus differs')
    corpus=stage.validate(json.loads(payload),expected)
    if len(corpus['rows'])!=seal['rows'] or corpus['source_completion_sha256']!=seal['source_completion_sha256']:
        raise ValueError('Sealed original denominator or lineage differs')
    if digest(complete)!=inputs['source_stage_complete_sha256']:
        raise ValueError('Completion changed while loading capsule')
    return corpus
