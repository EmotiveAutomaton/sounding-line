"""Explicit September 29 corrective cards, separate from the retained campaign.

DESIGN CHECK: LESSONS 3-5. NULL: changed originals, missing gates or insufficient
whole-family capacity refuse. ALTERNATIVE: full original rosters, immutable inputs
and complete consumers run under the earlier Thursday endpoint. No refit or retry.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse
from .common import RAW,REPO,read,freeze,filehash,now
from .prepare import capsule
from .queue import topological
from .healing_reader import fixtures,request

HEAL=RAW/'healing-v1'


def declare(raw=HEAL):
    from . import dispatch
    from .detectors import cached_model,model_pins
    contract=dict(stage=13,version='healing-v1',approval_basis='September 29 ordinary curator request: thorough validity, needed healing, Thursday morning',
        reporting='2026-10-01T05:00:00+00:00',final_review='2026-10-01T11:00:00+00:00',deadline='2026-10-01T13:00:00+00:00',
        timezone='America/Los_Angeles',deadline_basis='assumed Thursday 06:00 PDT pending optional preference',cpu_threads=1,paid_compute=False,
        original_contract_sha256=filehash(RAW/'CONTRACT.json'),original_results_unchanged=True,reader_interface_attempts=1)
    freeze(raw/'CONTRACT.json',contract)
    freeze(raw/'ALLOCATION.json',dict(gear=2,cpu_workers=6,cpu_threads=1,priority='below_normal',gpu_workers=1,paid_compute=False))
    # A full-roster input-only check is required before this capsule is declared.
    check=read(REPO/'.agent-state/stage13-setup/HEALING-20260929-FULL-REALIZATION-R2.json')
    if not check['admitted']:raise ValueError('full-roster realization failed')
    source,pins=capsule(raw,'healing-v1');cards=[]
    def add(name,action,args,requires=(),gates=(),resource='cpu',wall=3600,kind='producer',paths=()):
        inputs={str(p):filehash(raw/p) for p in paths}
        c=dict(id=name,action=action,args=args,requires=list(requires),gates=list(gates),resource=resource,wall_seconds=wall,kind=kind,
               input_pins=inputs,source_pins=pins,question='Complete corrective family under HEALING_20260929; exposed source, original attempts retained')
        cards.append(c);return name
    training='../sources/coauthor-v3-train.json'
    paths=sorted((RAW/'blocks/core-v1').glob('context-*.json'))
    memory=[r for p in paths for r in read(p)]
    if len(memory)!=check['rows'] or len({r['key'] for r in memory})!=len(memory):raise ValueError('memory roster differs')
    freeze(raw/'blocks/memory-all.json',memory)
    # Freeze original cached model files, not only a mutable cache alias.
    cache=cached_model('openai-community/gpt2-medium')
    model_paths=[str(cache/n) for n in model_pins(cache)]
    mg=add('memory-admission','healing-memory-admission',dict(rows='blocks/memory-all.json',training=training),wall=1800,kind='infrastructure',paths=['blocks/memory-all.json',training,*model_paths])
    memory_ids=[]
    for i,p in enumerate(paths):
        rel='../'+p.relative_to(RAW).as_posix()
        memory_ids.append(add(f'memory-{i:03d}','healing-memory-batch',dict(rows=rel,training=training),requires=[mg],gates=[mg],wall=10800,paths=[rel,training,'../jobs/core-v1-lm-admission/ADMISSION.json',*model_paths]))
    add('memory-summary','healing-memory-summary',dict(blocks=memory_ids,rows='blocks/memory-all.json'),requires=memory_ids,kind='consumer',wall=900,paths=['blocks/memory-all.json'])
    old_admit=read(RAW/'blocks/core-v1/qwen-admission.json')
    admit=fixtures()+[r for r in old_admit if not r.get('control')]
    if len(admit)!=7:raise ValueError('original training admission roster differs')
    for r in admit:request(r['views']['D'],'direct')
    freeze(raw/'blocks/reader-admission.json',admit)
    model='../../jobs/core-v1-B-fit';modelpath='../jobs/core-v1-B-fit/MODEL.json'
    qg=add('reader-admission','qwen-keyed-admission',dict(rows='blocks/reader-admission.json',model=model,views=['D'],arms=['direct']),resource='gpu',wall=3600,kind='infrastructure',paths=['blocks/reader-admission.json',modelpath])
    qids=[]
    for p in sorted((RAW/'blocks/core-v1').glob('qwen-*.json')):
        if not (p.name.startswith('qwen-calibration-') or p.name.startswith('qwen-reserve-')):continue
        rows=read(p)
        for r in rows:
            for v in ('A','B','C','D'):
                for a in ('direct','joint','without-goals','without-execution','equal-direct'):request(r['views'][v],a)
        rel='../'+p.relative_to(RAW).as_posix()
        qids.append(add('reader-'+p.stem[5:],'qwen-keyed-batch',dict(rows=rel,model=model,views=['A','B','C','D']),requires=[qg],gates=[qg],resource='gpu',wall=28800,paths=[rel,modelpath]))
    add('reader-summary','qwen-keyed-summary',dict(blocks=qids),requires=qids+[qg],gates=[qg],wall=1800,kind='consumer')
    tr='core-v1-roberta-training-g2r1';cal='core-v1-roberta-evaluate-g2r1'
    checkpoint=RAW/'jobs'/tr/'best'
    strong_paths=['../sources/opai-conditional-reserve.json',f'../jobs/{tr}/TRAINED.json',f'../jobs/{cal}/CALIBRATION.json']+[str(p) for p in checkpoint.iterdir() if p.is_file()]
    strong=add('strong-extension','healing-strong-extension',dict(training=tr,calibration=cal,rows='sources/opai-conditional-reserve.json'),resource='gpu',wall=7200,paths=strong_paths)
    paired_paths=[]
    for family in ('core-v1-A-reserve-summary-g2r1','reserve-extension-v1-summary-g2r1'):
        rel=f'../manifests/{family}.json';a=read(raw/rel)['args'];paired_paths += [rel,'../'+a['rows'],f"../jobs/{a['located']}/MODEL.json",f"../jobs/{a['selection']}/SELECTION.json"]
        paired_paths += [f'../jobs/{n}/PREDICTIONS.json' for n in a['blocks']]
    paired_paths += [f'../jobs/{cal}/CALIBRATION.json']+[str(p) for p in (RAW/'jobs'/cal/'rows').glob('*.json')]
    add('detector-comparison','healing-detector-comparison',dict(strong=strong),requires=[strong],wall=7200,kind='consumer',paths=sorted(set(paired_paths)))
    # Frozen capacity consumers release whole families from measured costs.
    mc=add('memory-capacity','healing-family-capacity',dict(family='memory',pilot=memory_ids[0],blocks=memory_ids),requires=[memory_ids[0]],wall=600,kind='infrastructure')
    qc=add('reader-capacity','healing-family-capacity',dict(family='reader',pilot=qg,blocks=qids),requires=[qg],gates=[qg],wall=600,kind='infrastructure')
    for c in cards:
        if c['id'] in memory_ids[1:]:c['requires'].append(mc);c['gates'].append(mc)
        if c['id'] in qids:c['requires'].append(qc);c['gates'].append(qc)
    for c in topological(cards):freeze(raw/'manifests'/f"{c['id']}.json",c)
    declared=dict(cards=[c['id'] for c in topological(cards)],source_capsule=source,source_pins=pins,dispatcher_sha256=filehash(Path(dispatch.__file__)),
        python_site_packages=str(REPO/'.venv/Lib/site-packages'),cpu_workers=6,free_host_floor_GiB=12,contract_sha256=filehash(raw/'CONTRACT.json'),
        manifest_hashes={c['id']:filehash(raw/'manifests'/f"{c['id']}.json") for c in cards})
    freeze(raw/'DECLARED.json',declared)
    pilot=[mg,qg,memory_ids[0]]
    freeze(raw/'plans/admission.json',dict(declared,id='admission',cards=pilot))
    freeze(raw/'plans/main.json',dict(declared,id='main'))
    return declared


def admit(raw=HEAL):
    from .worker import verify
    from .dispatch import inventory
    d=read(raw/'DECLARED.json');cards=[read(raw/'manifests'/f'{n}.json') for n in d['cards']]
    for n in ('memory-admission','reader-admission','memory-000'):verify(raw/'jobs'/n)
    mem=read(raw/'jobs/memory-000/COMPLETE.json')
    qrows=read(raw/'jobs/reader-admission/PREDICTIONS.json')['rows']
    reader=read(raw/'jobs/reader-admission/ADMISSION.json')['admitted']
    memory=read(raw/'jobs/memory-admission/ADMISSION.json')['admitted']
    if not memory:raise ValueError('memory admission refused')
    # Per-family conservative measured ceilings include consumers, setup and audit.
    qcalls=sum(len(read(raw/c['args']['rows']))*20 for c in cards if c['action']=='qwen-keyed-batch')
    qmax=max(r['call']['wall_seconds'] for r in qrows)
    memory_seconds=3*mem['wall_seconds']*sum(c['action']=='healing-memory-batch' for c in cards)/6+3600
    reader_seconds=2*qmax*qcalls+3600 if reader else 0
    old=read(RAW/'jobs/core-v1-roberta-evaluate-g2r1/COMPLETE.json')
    detector_seconds=3*old['wall_seconds']+7200
    required=max(memory_seconds,reader_seconds+detector_seconds)+3600
    remaining=(datetime.fromisoformat(read(raw/'CONTRACT.json')['reporting'])-datetime.now(timezone.utc)).total_seconds()
    if required>=remaining:raise ValueError(f'whole families need {required:.0f}s; only {remaining:.0f}s before reporting')
    receipt=dict(at=now(),reader_admitted=reader,memory_admitted=memory,reader_calls=qcalls,reader_max_admission_call_seconds=qmax,
        memory_seconds=memory_seconds,reader_seconds=reader_seconds,detector_seconds=detector_seconds,total_with_audit_seconds=required,available_seconds=remaining,
        original_rosters_retained=True,no_outcome_based_extension=True)
    freeze(raw/'CAPACITY.json',receipt)
    freeze(raw/'plans/main.json',dict(d,id='main'))
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['declare','admit']);a=p.parse_args()
    print((declare if a.mode=='declare' else admit)())


def capacity(card,out,raw,tick):
    args=card['args'];family=args['family']
    pilot=read(raw/'jobs'/args['pilot']/'COMPLETE.json')
    if family=='memory':
        needed=3*pilot['wall_seconds']*len(args['blocks'])/6+7200
        details=dict(pilot_seconds=pilot['wall_seconds'],blocks=len(args['blocks']),multiplier=3,workers=6)
    elif family=='reader':
        rows=read(raw/'jobs'/args['pilot']/'PREDICTIONS.json')['rows']
        worst=max(r['call']['wall_seconds'] for r in rows)
        calls=sum(len(read(raw/read(raw/'manifests'/f'{n}.json')['args']['rows']))*20 for n in args['blocks'])
        needed=2*worst*calls+14400
        details=dict(max_admission_call_seconds=worst,calls=calls,multiplier=2)
    else:raise ValueError('unknown capacity family')
    available=(datetime.fromisoformat(read(raw/'CONTRACT.json')['reporting'])-datetime.now(timezone.utc)).total_seconds()
    result=dict(at=now(),admitted=needed<available,family=family,estimated_seconds_with_consumer_and_audit=needed,available_seconds=available,details=details,
        policy='whole original family, outcome independent measured cost; no partial best-case extension')
    freeze(out/'ADMISSION.json',result);return result
