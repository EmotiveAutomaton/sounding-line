"""Exact retained-context continuation after a component cost stop.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 reread 2026-10-27.
NULL/ALTERNATIVE require unchanged plan, inputs and retained bytes; changed
evidence refuses before reuse. Execution copies complete construction only;
fresh verification rebuilds all original inputs. No score, reduced population,
new statistical method or scientific admission is introduced by this wrapper.
"""
from pathlib import Path
from runners.stage14.common import read,filehash,freeze
from . import week3_fic1_context_timing as original

FILES=('BINDING.json','CONTEXT.json','SUMMARY.json','EXECUTE_COST.json')


def source(inputs,config):
    if config not in (original.CONFIG,original.CONSTRUCTED) or set(inputs)!={'resume_manifest'}:
        raise ValueError('fixed continuation inputs required')
    manifest=read(inputs['resume_manifest']);root=Path(manifest['source_root']).resolve()
    if manifest['terminal_name'] not in ('COMPLETE.json','FAILED.json'):raise ValueError('invalid source terminal')
    for name,key in [('PLAN.json','plan_sha256'),(manifest['terminal_name'],'terminal_sha256')]:
        if filehash(root/name)!=manifest[key]:raise ValueError('source plan/terminal bytes differ')
    plan=read(root/'PLAN.json');terminal=read(root/manifest['terminal_name'])
    if plan['module']!='runners.drive.cards.week3_fic1_context_timing' or plan['config']!=config:
        raise ValueError('source handler configuration differs')
    if config==original.CONFIG and (manifest['terminal_name']!='FAILED.json' or terminal.get('failure_class')!='cost'):
        raise ValueError('full continuation requires recorded cost stop')
    if config==original.CONSTRUCTED and (manifest['terminal_name']!='COMPLETE.json' or not terminal.get('fresh_process_verified')):
        raise ValueError('native continuation requires verified constructed source')
    for path,h in plan['pins'].items():
        if filehash(path)!=h:raise ValueError('source pin differs')
    if set(manifest['files'])!=set(FILES):raise ValueError('complete retained construction required')
    for name,h in manifest['files'].items():
        if filehash(root/'output'/name)!=h:raise ValueError('retained source bytes differ')
    binding=read(root/'output/BINDING.json');summary=read(root/'output/SUMMARY.json')
    if binding['config']!=config or any(summary[k] for k in ['identification_computed','full_calibration_complete','scientific_admission']):
        raise ValueError('source scope differs')
    for path,h in binding['inputs'].items():
        if filehash(path)!=h:raise ValueError('bound input differs')
    return root,plan


def execute(output,inputs,config):
    root,plan=source(inputs,config);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    for name in FILES:
        payload=(root/'output'/name).read_bytes();dest=output/name
        if dest.exists():
            if dest.read_bytes()!=payload:raise ValueError('retained destination differs')
        else:dest.write_bytes(payload)
    return dict(status='complete',retained_construction=True,scientific_admission=False)


def verify(output,inputs,config):
    root,plan=source(inputs,config)
    result=original.verify(output,plan['inputs'],config)
    if any(filehash(Path(output)/name)!=filehash(root/'output'/name) for name in FILES):
        raise ValueError('retained output changed during replay')
    return dict(result,retained_construction_freshly_replayed=True)
