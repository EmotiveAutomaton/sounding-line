"""Exposed human bridge using the already validated chronological adapter.

DESIGN CHECK: LESSONS 3-5. NULL/ALTERNATIVE: source-replayed prior results are
descriptive reuse, never fresh confirmation. Controlled M4 must complete first.
No model calls, private text publication, or change to historical science.
"""
from pathlib import Path
from .common import RAW,ROOT,REPO,check_pins,digest,freeze,read


def prepare():
    old=REPO/'results/phase_2_4_stage_11_1/raw'
    plan=read(old/'branch_plans/S4-history-v1.json')
    admission=read(old/'continuation/S4-ADMISSION.json')
    keys=sorted({t['evaluator']['key'] for t in plan['tasks'] if t['kind']=='forecast'})
    if not 1<=len(keys)<=24:raise ValueError('human bridge target ceiling')
    from runners.stage11_1.branch_runtime import sources
    return freeze(RAW/'human-bridge/PLAN.json',dict(status='prepared',targets=keys,
        original_plan_sha256=digest(plan),temporal_admission_sha256=digest(admission),sources=sources(),
        requires='repair-v1/M4-ollama-test/AUDIT.json',
        execution='reapply original request parser/scorer to saved responses; no redundant inference',
        exposure='all records previously exposed; descriptive bridge, not new evidence or another sample',
        claims='source-labeled production/handling only; no private review duration, effort or lifelong values'))


def run(root=RAW):
    root=Path(root);plan=read(root/'human-bridge/PLAN.json')
    gate=read(root/plan['requires'])
    if gate.get('status')!='complete':raise ValueError('controlled context comparison incomplete')
    check_pins(plan['sources'])
    old=REPO/'results/phase_2_4_stage_11_1/raw'
    from runners.stage11_1 import branch_runtime as br,run_v3b
    def forbidden(*args,**kwargs):raise AssertionError('human bridge is offline; no inference')
    br.api=run_v3b.api=forbidden
    source=old/'branch_plans/S4-history-v1.json'
    if digest(read(source))!=plan['original_plan_sha256']:raise ValueError('human plan changed')
    if digest(read(old/'continuation/S4-ADMISSION.json'))!=plan['temporal_admission_sha256']:raise ValueError('chronology admission changed')
    receipt,outputs=br.execute(old,source,replay_only=True)
    analysis=br.analyze(old,source)
    freeze(root/'human-bridge/REPLAY.json',dict(receipt=receipt,outputs=outputs))
    freeze(ROOT/'HUMAN_BRIDGE.json',dict(status='complete',targets=len(plan['targets']),historical_finding='L395',
        cells=analysis['cells'],history_cost=analysis['history_cost'],new_calls=0,source_replay_calls=receipt['calls'],
        exposure=plan['exposure'],claims=plan['claims'],control_gate_sha256=digest(gate)))
    return freeze(root/'human-bridge/COMPLETE.json',dict(status='complete',plan_sha256=digest(plan),new_calls=0,
        scope='exposed descriptive bridge via exact historical replay, not an independent 11.2 replication'))


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');a=p.parse_args()
    print(prepare()['status'] if a.prepare else run()['status'])
