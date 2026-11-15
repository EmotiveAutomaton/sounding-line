"""Owner-only qualification harness candidate; preparation/launch/inspect split.

DESIGN CHECK: LESSONS 3-5. Review/pin/clock/slot/closure/cost gates are identical
under every scientific direction. Missing native proof refuses. No bypass of
the actual existing launcher, no standalone uncounted numerical test command.
The builder has not executed any action from this file.
"""
from pathlib import Path
import argparse,json


def prepare(request,destination):
    from runners.drive import week5_launch_v10 as launcher
    from runners.drive.cards.batch_runtime import REPO,filehash,freeze,read
    from runners.theory_days.launch import closure
    need(request.get('owner_reviewed') is True,'Explicit owner fixture review required')
    destination=Path(destination).resolve();destination.relative_to(REPO/'.agent-state')
    need(not destination.exists(),'Fresh private qualification proposal directory required')
    bootstrap=request['passed_bootstrap_fixture']
    need(filehash(bootstrap['path'])==bootstrap['sha256'],'Prior guard/child fixture changed')
    need(read(bootstrap['path']).get('status')=='COMPLETE','Bootstrap native fixture not complete')
    modules=['runners.drive.cards.week5_at_queue_v1_fixture',*launcher.MODULES]
    pins={str(p):filehash(p) for p in closure(modules)}
    tests=REPO/'tests/test_week5_at_queue_v1.py'
    pins[str(tests)]=filehash(tests);pins[bootstrap['path']]=bootstrap['sha256']
    design=Path(request['design']).resolve();pins[str(design)]=filehash(design)
    plan=dict(campaign='S15-WEEK5',family='AT',card='AT-queue-v1-counted-qualification',
        module=modules[0],inputs={},config={},pins=pins,owner_reviewed=True,
        design=str(design),reviewed_design_commit=request['reviewed_design_commit'],
        fixture_passed=True,fixture_scope='Existing original guard/child native bootstrap passed; this run qualifies the new queue',
        validation_receipts=[bootstrap['path']],gpu=False,paid=False,ollama=False,numerical_threads=2,
        accounting_runtime='week5-v11',max_cpu_seconds=2000,max_wall_seconds=3600,
        projected_peak_ram_GiB=4,max_output_bytes=512*2**20,pilot_fraction=.05,
        premortem=dict(case_and_check='Exact queue/child/containment against constructed known answers, including native refusal cases',
                       smaller_route='Sealed unchanged fixture continuation; never a human or substituted scoring run'))
    launcher.review(plan)
    destination.mkdir(parents=True);freeze(destination/'PLAN_CANDIDATE.json',plan)
    freeze(destination/'REQUEST_BINDING.json',request)
    return dict(prepared=True,nonlaunchable_until_owner_dispatch=True,path=str(destination/'PLAN_CANDIDATE.json'))


def need(value,message):
    if not value:raise ValueError(message)


def prepare_collector(request,destination):
    from runners.drive import week5_launch_v10 as launcher
    from runners.drive.cards.batch_runtime import REPO,filehash,freeze,read
    from runners.theory_days.launch import closure
    need(request.get('owner_reviewed') is True,'Explicit collector fixture review required')
    native=Path(request['native_queue_fixture_root']).resolve()
    need(filehash(native/'COMPLETE.json')==request['queue_fixture_complete_sha256'] and
         read(native/'COMPLETE.json').get('fresh_process_verified') is True and
         read(native/'PLAN.json')['module']=='runners.drive.cards.week5_at_queue_v1_fixture',
         'Complete actual constructed queue source required')
    owner_review=request['queue_qualification_inspection']
    need(filehash(owner_review['path'])==owner_review['sha256'] and
         read(owner_review['path'])['complete_sha256']==request['queue_fixture_complete_sha256'],
         'Exact queue native-accounting inspection required')
    module='runners.drive.cards.week5_at_queue_collect_v1_fixture'
    pins={str(p):filehash(p) for p in closure([module,*launcher.MODULES])}
    pins[str(native/'COMPLETE.json')]=filehash(native/'COMPLETE.json')
    pins[owner_review['path']]=owner_review['sha256']
    design=Path(request['design']).resolve();pins[str(design)]=filehash(design)
    plan=dict(campaign='S15-WEEK5',family='AT',card='AT-queue-collector-v1-counted-qualification',
        module=module,inputs=dict(native_queue_fixture_root=str(native)),config={},pins=pins,
        owner_reviewed=True,design=str(design),reviewed_design_commit=request['reviewed_design_commit'],
        fixture_passed=True,fixture_scope='Actual queue producer fixture passed; this run qualifies its collector consumer',
        validation_receipts=[str(native/'COMPLETE.json'),owner_review['path']],gpu=False,paid=False,ollama=False,
        numerical_threads=2,accounting_runtime='week5-v11',max_cpu_seconds=300,max_wall_seconds=600,
        projected_peak_ram_GiB=2,max_output_bytes=128*2**20,pilot_fraction=.05,
        premortem=dict(case_and_check='Consume actual constructed native chunks and refuse altered provenance plus incomplete original pilot scope',
                       smaller_route='No partial pilot admission; preserve all constructed failures and costs'))
    launcher.review(plan)
    destination=Path(destination).resolve();destination.relative_to(REPO/'.agent-state')
    need(not destination.exists(),'Fresh private collector qualification proposal required')
    destination.mkdir(parents=True);freeze(destination/'PLAN_CANDIDATE.json',plan)
    freeze(destination/'REQUEST_BINDING.json',request)
    return dict(prepared=True,nonlaunchable_until_owner_dispatch=True,path=str(destination/'PLAN_CANDIDATE.json'))


def dispatch(candidate,target):
    # This is the only dispatch route; clock/resource/lease checks and durable
    # native watcher handshake remain in the original qualified launcher.
    from runners.drive import week5_launch_v10 as launcher
    from runners.drive.cards.batch_runtime import read
    plan=read(candidate);launcher.freeze_plan(Path(target),plan)
    return launcher.launch(Path(target))


def inspect(root,receipt):
    from runners.drive.cards.batch_runtime import read,filehash,freeze
    from runners.drive.cards.week5_historical_exit_v1 import stopped
    root=Path(root).resolve();done=read(root/'COMPLETE.json');plan=read(root/'PLAN.json')
    need(done.get('status')=='COMPLETE' and done.get('fresh_process_verified') is True and
         plan['module']=='runners.drive.cards.week5_at_queue_v1_fixture','Wrong or incomplete qualification')
    need(not any((root/n).exists() for n in ('FAILED.json','PAUSED.json','MONITOR_FAILED.json')),'Ambiguous qualification terminal')
    need(stopped(read(root/'OWNER.json')['native'],done['at']),'Outer qualification owner exit unknown')
    for name,digest in done['outputs'].items():
        path=(root/name).resolve();path.relative_to(root)
        need(filehash(path)==digest,'Qualification output changed')
    native_totals={};pairs={};outer_total=0.0
    for operation,branch in [('EXECUTE','execution'),('VERIFY','verification')]:
        outer=read(root/(operation+'_JOB_USAGE.json'))
        need(outer['exit_code']==0 and outer['includes_all_descendants_and_exited_processes'] is True,'Outer all-descendant cost missing')
        outer_total+=outer['cpu_seconds'];work=root/'output'/branch
        fixture=read(work/'FIXTURE.json');targeted=read(work/'TARGETED_CHECKS.json')
        need(targeted['passed'] is True and targeted['tests']>0,'Counted targeted checks not passed')
        for key in ('serial_fresh_native_pairs','authenticated_pause_copy_and_resume','prior_evidence_unchanged',
                    'tampered_chunk_refused','fast_exit_output_cap_refused','forced_native_deadline_refused',
                    'refused_attempt_native_costs_retained','changed_summary_context_refused',
                    'actual_scorer_membership_verified','launcher_and_scorer_exits_verified',
                    'owned_job_empty_before_close','foreign_process_membership_refused','changed_membership_proof_refused'):
            need(fixture.get(key) is True,'Required native case absent: '+key)
        # Count only the fixture's three actual native execution trees.
        # Deliberately corrupted scratch copies are negative controls, not jobs.
        unique={};native_paths=[]
        for native_tree in ('queue','pause-queue','constructed-native-cases'):
            native_paths.extend((work/native_tree).rglob('*_OWNED.json'))
        for path in native_paths:
            prefix=path.name[:-len('_OWNED.json')];identity=read(path)['native']
            key=(identity['pid'],identity['created_ticks'])
            usage=read(path.parent/(prefix+'_JOB_USAGE.json'))
            from runners.drive.cards.week5_at_queue_native_v2 import require_phase_proof
            roles=require_phase_proof(path.parent,prefix,allow_forced=True)
            closed=read(path.parent/(prefix+'_CLOSED.json'))
            if closed['forced']:
                forced=read(path.parent/(prefix+'_FORCED_STOP.json'))
                need(forced['reason']=='chunk_or_queue_wall_boundary','Wrong forced refusal')
            need(usage['includes_all_descendants_and_exited_processes'] is True,'Nested exited CPU omitted')
            value=dict(identity=identity,actual_scorer=roles['native'],measured_cpu_seconds=usage['measured_cpu_seconds'],
                       cpu_seconds=usage['cpu_seconds'],forced=closed['forced'])
            need(key not in unique or unique[key]==value,'Conflicting copied native cost evidence')
            unique[key]=value
        measured=sum(x['measured_cpu_seconds'] for x in unique.values())
        need(len(unique)>=10 and outer['cpu_seconds']+1e-6>=measured,'Outer Job CPU omits nested descendants or native cases')
        native_totals[operation]=dict(outer_cpu_seconds=outer['cpu_seconds'],nested_measured_cpu_seconds=measured,
              nested_native_processes=len(unique),conservative_inner_termination_margin=sum(x['cpu_seconds']-x['measured_cpu_seconds'] for x in unique.values()))
        pairs[operation]=list(unique.values())
    need(done['cpu_seconds']+1e-6>=outer_total,'Terminal undercounts complete outer phases')
    result=dict(status='OWNER_REVIEWABLE_COMPLETE_NATIVE_QUALIFICATION',complete_sha256=filehash(root/'COMPLETE.json'),
        plan_sha256=filehash(root/'PLAN.json'),actual_launcher='runners.drive.week5_launch_v10',
        native_totals=native_totals,native_identities=pairs,outer_cpu_seconds=done['cpu_seconds'],
        supervisor_envelope_cpu_seconds=30,production_admission=False,
        limitation='Constructed tiny models and synthetic guard snapshots; real model memory gates remain unchanged')
    freeze(Path(receipt),result);return result


def inspect_collector(root,receipt):
    from runners.drive.cards.batch_runtime import read,filehash,freeze
    from runners.drive.cards.week5_at_queue_collect_v1 import native_complete
    root=Path(root).resolve();plan=read(root/'PLAN.json');done=read(root/'COMPLETE.json')
    need(plan['module']=='runners.drive.cards.week5_at_queue_collect_v1_fixture','Wrong consumer qualification module')
    native_complete(root,done)
    required=('exact_row_binding_and_native_guard_consumer_passed','incomplete_165_chunk_pilot_refused',
              'corrupt_score_block_refused','missing_queue_complete_refused',
              'exact_job_membership_and_both_exits_required',
              'changed_context_revision_precision_core_fresh_native_and_row_order_refused')
    branches={}
    for phase in ('execute','verify'):
        value=read(root/'output'/phase/'FIXTURE.json')
        for key in required:need(value.get(key) is True,'Missing consumer refusal proof: '+key)
        need(value['complete_original_m00_pilot'] is False and value['scientific_admission'] is False,
             'Constructed consumer fixture falsely claims complete original pilot')
        branches[phase]=filehash(root/'output'/phase/'FIXTURE.json')
    result=dict(status='OWNER_REVIEWABLE_COMPLETE_COLLECTOR_QUALIFICATION',
        complete_sha256=filehash(root/'COMPLETE.json'),plan_sha256=filehash(root/'PLAN.json'),
        fixture_phases=branches,native_cpu_seconds=done['cpu_seconds'],supervisor_envelope_cpu_seconds=30,
        consumer_corruption_and_no_complete_refusals_required=True,
        production_admission=False,complete_original_m00_pilot=False)
    freeze(Path(receipt),result);return result


if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='action',required=True)
    a=sub.add_parser('prepare');a.add_argument('request',type=Path);a.add_argument('destination',type=Path)
    a=sub.add_parser('prepare-collector');a.add_argument('request',type=Path);a.add_argument('destination',type=Path)
    a=sub.add_parser('launch');a.add_argument('candidate',type=Path);a.add_argument('target',type=Path)
    a=sub.add_parser('inspect');a.add_argument('root',type=Path);a.add_argument('receipt',type=Path)
    a=sub.add_parser('inspect-collector');a.add_argument('root',type=Path);a.add_argument('receipt',type=Path)
    args=p.parse_args()
    if args.action=='prepare':result=prepare(json.loads(args.request.read_text()),args.destination)
    elif args.action=='prepare-collector':result=prepare_collector(json.loads(args.request.read_text()),args.destination)
    elif args.action=='launch':result=dispatch(args.candidate,args.target)
    elif args.action=='inspect-collector':result=inspect_collector(args.root,args.receipt)
    else:result=inspect(args.root,args.receipt)
    print(json.dumps(result,indent=2))
