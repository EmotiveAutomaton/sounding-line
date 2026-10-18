"""Authenticate and preserve D18's failed-attempt extraction checkpoints."""
import hashlib
from pathlib import Path
from .events_p5 import read, filehash
from .events_d4 import sealed, read_sealed, save
from .events_d18 import INPUTS as BASE_INPUTS

EXTRA_INPUTS = {'failed_plan', 'failed_binding', 'failed_receipt'}


def authenticate(inputs, config, roster, verified_pins=None):
    root = Path(inputs['failed_plan']).resolve().parent
    if Path(inputs['failed_binding']).resolve() != root/'output/BINDING.json' or Path(inputs['failed_receipt']).resolve() != root/'FAILED.json':
        raise ValueError('failed D18 references do not share exact root')
    plan,binding,failure=(read(inputs[k]) for k in ('failed_plan','failed_binding','failed_receipt'))
    expected={k:inputs[k] for k in BASE_INPUTS}
    if (plan['module']!='runners.drive.cards.events_d18' or plan['inputs']!=expected or plan['config']!=config
            or binding['paths']!=expected or binding['config']!=config or failure.get('status')!='FAILED'
            or (root/'output/SUMMARY.json').exists()):
        raise ValueError('failed D18 method/input/status differs')
    verified_pins=verified_pins or {}
    for path,digest in {**plan['pins'],**binding['pins']}.items():
        if verified_pins.get(path,digest)!=digest or path not in verified_pins and filehash(path)!=digest:
            raise ValueError('failed D18 source/input pin changed')
    checkpoints={};missing=False
    for item in roster:
        stem='sessions/'+hashlib.sha256(item['session'].encode()).hexdigest()[:24]
        path=root/'output'/(stem+'.json');vector_path=root/'output'/(stem+'.npy')
        if not sealed(path):
            missing=True;continue
        if missing:
            raise ValueError('failed D18 checkpoints do not form consecutive prefix')
        unit=read_sealed(path);read_sealed(vector_path)
        if (any(unit[k]!=item[k] for k in ('session','writer','session_order'))
                or unit['source_sha256']!=item['raw']['source_sha256'] or unit['p2_sha256']!=item['p2']['sha256']):
            raise ValueError('failed D18 checkpoint input identity differs')
        checkpoints[item['session']]=dict(file=str(path),vectors=str(vector_path),sha256=filehash(path),
            vectors_sha256=filehash(vector_path),seal_sha256=filehash(path.with_name(path.name+'.sha256')),
            vectors_seal_sha256=filehash(vector_path.with_name(vector_path.name+'.sha256')),
            elapsed_seconds=unit['elapsed_seconds'])
    receipt=dict(failed_plan=str(Path(inputs['failed_plan'])),failed_plan_sha256=filehash(inputs['failed_plan']),
        failed_binding_sha256=filehash(inputs['failed_binding']),failed_receipt_sha256=filehash(inputs['failed_receipt']),
        original_plan_pins=plan['pins'],original_input_pins=binding['pins'],reusable_checkpoints=checkpoints,
        original_attempt_retained=True,scientific_contrast_changed=False,
        repair='Only canonically unusable repeated selections, absent P2/prepared decisions, retain separate non-typed provenance and explicit source exclusions; no threshold or matching change')
    return receipt,checkpoints


def restore(checkpoint,path,vector_path):
    for name,digest in (('file','sha256'),('vectors','vectors_sha256')):
        if filehash(checkpoint[name])!=checkpoint[digest]:raise ValueError('failed D18 reusable checkpoint changed')
    unit=read_sealed(Path(checkpoint['file']));vectors=read_sealed(Path(checkpoint['vectors']))
    save(vector_path,vectors);save(path,unit)
    if filehash(path)!=checkpoint['sha256'] or filehash(vector_path)!=checkpoint['vectors_sha256']:
        raise ValueError('D18 reused checkpoint bytes differ')
    return unit,vectors
