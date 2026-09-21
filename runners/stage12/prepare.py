"""Freeze the opening cards and first successors before dispatch.

DESIGN CHECK: LESSONS 2-5; CONTROLS 6-7. NULL: source identities, recipes and
candidate order remain fixed regardless of results. ALTERNATIVE: changed input,
missing handler, duplicate produce, ambiguous privacy or budget prevents launch.
Unavailable future-source hashes stay waiting rather than receiving dummy data.
"""
from __future__ import annotations
import argparse
import shutil
from pathlib import Path
from .common import REPO,ROOT,RAW,read,freeze,filehash,digest,pin,SEED,native_command

def source_files():
    names=[]
    for folder in ['runners/stage9','runners/stage10','runners/stage11','runners/stage11_1','runners/stage11_2','runners/stage12','soundingline']:
        names.extend(p for p in (REPO/folder).rglob('*.py') if '__pycache__' not in p.parts)
    names.extend(REPO/p for p in ['runners/__init__.py','runners/run_queue.py','runners/queue_status.py','runners/gear3.py','tools/codex_common.py'])
    return sorted(set(p for p in names if p.exists()))

def prepare(raw=RAW):
    raw=Path(raw);raw.mkdir(parents=True,exist_ok=True)
    contract=read(REPO/'.agent-state/stage12-setup/T0.json')
    freeze(raw/'CONTRACT.json',contract)
    # Conservative setup allowance includes operator-side validation/preparation
    # commands outside card workers. It is not measured CPU utilization.
    freeze(raw/'charges/setup-reserve.json',dict(cpu_seconds=7200.,state='conservative setup reserve',
        scope='non-card setup and verification; actual CPU not retrospectively fabricated',gpu_seconds=0.,diagnostic_gpu_seconds=0.,host_cpu_seconds=0.))
    pins=pin(source_files());freeze(raw/'SOURCES-v1.json',pins)
    capsule=raw/'source-v1'
    for name,h in pins.items():
        archive=raw/'source-archive-v1'/name;archive.parent.mkdir(parents=True,exist_ok=True)
        if archive.exists() and filehash(archive)!=h:raise ValueError('source archive differs')
        if not archive.exists():archive.write_bytes((REPO/name).read_bytes())
        if not (name.replace('\\','/').startswith('runners/stage12/') or name.replace('\\','/')=='runners/__init__.py'):continue
        p=capsule/name;p.parent.mkdir(parents=True,exist_ok=True)
        if p.exists() and filehash(p)!=h:raise ValueError('source capsule differs')
        if not p.exists():p.write_bytes((REPO/name).read_bytes())
    cohort_path=REPO/'results/phase_2_4_stage_11_1/raw/COHORT-v3.json';cohort=read(cohort_path)
    candidates=[];seen=set()
    for r in sorted(cohort['discovery'],key=lambda r:digest([SEED,'packet-zero',r['key']])):
        if r['writer'] not in seen:candidates.append(r['key']);seen.add(r['writer'])
    candidates += [r['key'] for r in sorted(cohort['discovery'],key=lambda r:digest([SEED,'packet-zero',r['key']])) if r['key'] not in candidates]
    from runners.stage10.ghost import envelopes
    public=REPO/'results/phase_2_4_stage_10/raw/interface-v3/ghost-public'
    rows,_=envelopes(public);ghost=[];seen=set()
    for r in sorted(rows,key=lambda r:digest([SEED,'ghost',r['envelope']['task_id']])):
        if r['envelope']['declared_context']['operation'] in ('reading','opportunity') and r['case_id'] not in seen:
            ghost.append(r['envelope']['task_id']);seen.add(r['case_id'])
    if len(ghost)!=16:raise ValueError('retained sixteen-case support changed')
    commits=native_command(['git','rev-list','--max-count=16','9d193b75cb117c999f197ca0319ff946656eba3f']).decode().splitlines()
    base=dict(seed=SEED,source_pins=pins,resource='cpu',gpu_seconds=0.,diagnostic_gpu_seconds=0.)
    def card(identifier,handler,question,cpu=3600,needs=(),**extra):
        result=dict(base,id=identifier,handler=handler,question=question,cpu_seconds=cpu,
            wall_seconds=max(3600,cpu*2),needs=[str((raw/'jobs'/n/'COMPLETE.json').relative_to(REPO)) for n in needs],
            candidate_ids=[],inputs={})
        result.update(extra)
        return result
    cards=[
        card('S12-00','inventory','What usable independent human source support and prior exposure are actually retained?',7200),
        card('S12-01','runtime','Which measured components account for retained call wall time, and which telemetry is missing?',3600),
        card('S12-02','packet-zero','Can source-bound packets separate supported located actions from hypotheses and unknown goals?',3600,
             candidate_ids=candidates[:8],inputs={str(cohort_path):filehash(cohort_path)}),
        card('S12-03','human-freeze','Freeze the capable history comparison from eligible source support and training-only controls.',3600,needs=['S12-00'],per_writer_cap=16),
        card('S12-04','ghost-reference','Run all finite rivals on sixteen retained constructed cases without inventing local-goal labels.',7200,
             candidate_ids=ghost,inputs={str(public/'PUBLIC_MANIFEST.json'):filehash(public/'PUBLIC_MANIFEST.json')}),
        card('S12-05','git-context','Which recorded file operations become identifiable with parent history and stated commit context?',7200,
             candidate_ids=commits,opportunities=24),
        card('S12-06','tiny-rehearsal','Rehearse the causal consumer and shared two-setting ownership contract before any neural fit.',3600),
        card('S12-07','cloud-packet','Prepare the exact S-P1 capable-reader request and capped review packet without dispatch.',3600,needs=['S12-03']),
        card('S12-A','cloud-result','Compare the frozen capable history arms only after complete approved raw retrieval.',7200,needs=['S12-03','S12-07']),
        card('S12-B','process-context','Replay direct, review, account and cheap rivals across both human evidence views.',7200,
             candidate_ids=candidates[:16],inputs={str(cohort_path):filehash(cohort_path)}),
        card('S12-C','continuing','Validate same-evidence updating and whole bundles against independent marginals.',7200,
             candidate_ids=[f'dev-{i:04d}' for i in range(16)])]
    cards[8]['needs'].append(str((raw/'inputs/CAPABLE_READER_RESULTS.json').relative_to(REPO)))
    for c in cards:
        # This setup pass only schedules implemented handlers. Deferred future
        # leaves below are not represented as completed implementations.
        from .worker import handler
        handler(c['handler'])
        freeze(raw/'manifests'/(c['id']+'.json'),c)
    plan=dict(schema='s12.native-queue.1',cards=[c['id'] for c in cards],source_pins=pins,
        manifest_hashes={c['id']:filehash(raw/'manifests'/(c['id']+'.json')) for c in cards},
        source_capsule=str(capsule),contract_sha256=filehash(raw/'CONTRACT.json'),
        semantics='finite pass; deferred or failed cards do not block independent work; no whole-campaign completion implied')
    freeze(raw/'OPENING_QUEUE.json',plan)
    leaves={
      'A1':dict(parent='S12-A',arms=['own_history','no_history','training_donor','training_prior','persistence'],waiting='admitted capable reader and new specific funding'),
      'A2':dict(parent='S12-A',arms=['raw_history','retrieval','frozen_coherent_account','predictive_bank'],waiting='separate frozen development reader requests'),
      'B1':dict(parent='S12-B',arms=['artifact','diff','diff_plus_stated_message'],waiting='CPU source comparisons opening; reader Git comparison follows canary'),
      'B2':dict(parent='S12-04',arms=['E0','E1','E2','direct_likelihood','direct_read','coherent_account'],waiting='frozen Ghost V19 local export and learned reader admission'),
      'B3':dict(parent='S12-B',arms=['reverse_external_request','forward_consequence'],waiting='one permitted ARIES intake adapter; no author-adoption relabelling'),
      'C1':dict(parent='S12-C',arms=['same_observations','reordered','true_relation','plausible_false','irrelevant','unstructured','matched_reread'],waiting='bounded learned reader requests after canary'),
      'C2':dict(parent='S12-C',arms=['true_frame_then_true_observation','false_frame_then_true_observation'],waiting='same frozen reader and corrected evidence requests'),
      'C3':dict(parent='S12-C',arms=['whole_bundle','independent_marginals','new_query'],waiting='learned bundle interface; structural references opening'),
      'D1':dict(parent='S12-06',arms=['correct','random','shuffled','wrong_variable','noop','full_state'],waiting='shared owner, actual training roster, fitted capability'),
      'D2':dict(parent='S12-06',arms=['static_commuting','dependent_ordered'],waiting='admitted D1 fit and frozen transfer worlds'),
      'E1':dict(parent='S12-C',arms=['declarative','observation','practice','matched_replay'],waiting='Ghost task-objective and observation-quality export'),
    }
    freeze(raw/'LEAF_REGISTRY.json',dict(seed=SEED,leaves=leaves,source_candidate_policy='freeze exact additional IDs and hashes before each admitted expansion; never manufacture unavailable source hashes',
        unresolved_implementation='registry is not proof every later handler is assembled; finish setup-day B2/C2/C3/D1 consumer compilation'))
    return dict(cards=len(cards),source_files=len(pins),plan=str(raw/'OPENING_QUEUE.json'),capsule=str(capsule))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--raw',type=Path,default=RAW)
    print(prepare(parser.parse_args().raw))
