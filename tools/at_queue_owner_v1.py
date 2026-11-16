"""Owner-only counted metadata preparation, then separately reviewed AT launch.

DESIGN CHECK: LESSONS 3-5. Identical bounds under every scientific direction.
No new source/scorer choice. Unknown pins, identities, costs or classifications
refuse; resource/capacity holds are operational, never scientific outcomes.
Builder has not executed this candidate. Native/scientific runtime stays pinned.
"""
from pathlib import Path
from datetime import datetime, timezone
from types import FunctionType
import argparse, copy, json, math, os, sys, time

REPO = Path.cwd().resolve()
sys.path.insert(0,str(REPO))
for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[name]='2'
os.environ['CUDA_VISIBLE_DEVICES']='';os.environ['PYTHONDONTWRITEBYTECODE']='1'
from runners.stage14.common import read,freeze,filehash,now
from runners.stage9.process_identity import native_identity,is_same_live_process
from runners.drive.cards import batch_runtime_v8 as kernel,week5_policy_v3 as policy
from runners.drive.cards.batch_runtime import check_files,release_slot,resource_snapshot
from runners.drive.cards import week5_at_queue_v1 as queue
from runners.drive.cards.week5_at_queue_child_v2 import handshake
from runners.drive.cards.week5_historical_exit_v1 import stopped
from runners.drive import week5_launch_v10 as launcher
from tools import prepare_at_queue_v1 as freezer

MODULE='tools.at_queue_owner_v1'
PREP_TOTAL=600;PREP_PLAN=570;PREP_WALL=1800;PREP_RAM=1;PREP_OUTPUT=128*2**20
QUEUE_CHARGED=32000;QUEUE_PLAN=31970;MAINTENANCE=41000
PRIOR_SUPERVISION=90572.345264;BK_SUPERVISION=43200
TEMPLATE=REPO/'.agent-state/drive-20261115/full-run-build/worry/at-queue-collector-v1/OWNER_REQUEST_PROPOSED_32000_TOTAL.json'
TEMPLATE_SHA='9a4bdfa2e638093cbc674e72a053462b436db76227071a8b65b079f46626745d'
RESERVE=REPO/'.agent-state/drive-20261115/storage-recovery/SUPERVISION_RESERVE.json'
BK_PREFLIGHT=REPO/'.agent-state/drive-20261115/full-run-build/BK_LONG_PREFLIGHT.json'

class ResourceHeld(RuntimeError):pass
def need(value,message):
    if not value:raise ValueError(message)
def ref(path):return dict(path=str(Path(path).resolve()),sha256=filehash(path))
def bound(reference):
    need(filehash(reference['path'])==reference['sha256'],'Reviewed reference changed')
    return read(reference['path'])
def original_reserves():
    previous=read(RESERVE);bk=read(BK_PREFLIGHT)
    need(previous['existing_maintenance_reserve']==MAINTENANCE and
         previous['additional_supervision_reserve']+13600==PRIOR_SUPERVISION and
         bk['prior_supervision_reserve_retained']==PRIOR_SUPERVISION and
         bk['additional_supervision_reserve_cpu_seconds']==BK_SUPERVISION,
         'Original retained reservation evidence differs')
    return dict(maintenance_cpu_seconds=MAINTENANCE,prior_supervision_cpu_seconds=PRIOR_SUPERVISION,
                new_BK_supervision_cpu_seconds=BK_SUPERVISION,references=[ref(RESERVE),ref(BK_PREFLIGHT)])
def drain_wall(at=None):
    at=at or datetime.now(timezone.utc)
    if not policy.OPEN<=at<policy.FREEZE:raise ResourceHeld('Original no-new-start boundary')
    wall=min(43200,math.floor((policy.DRAIN-at).total_seconds())-120)
    if wall<=0:raise ResourceHeld('No positive original-drain wall remains')
    return wall

def qualification(review):
    receipts=[];records={}
    for label,module,status in (
        ('queue','runners.drive.cards.week5_at_queue_v1_fixture','OWNER_REVIEWABLE_COMPLETE_NATIVE_QUALIFICATION'),
        ('collector','runners.drive.cards.week5_at_queue_collect_v1_fixture','OWNER_REVIEWABLE_COMPLETE_COLLECTOR_QUALIFICATION')):
        item=review['qualification'][label];root=Path(item['root']).resolve();root.relative_to(policy.ROOT)
        done=bound(item['complete']);inspection=bound(item['inspection']);plan=read(root/'PLAN.json')
        need(Path(item['complete']['path']).resolve()==root/'COMPLETE.json' and
             done.get('status')=='COMPLETE' and done.get('fresh_process_verified') is True and
             plan['module']==module and inspection['status']==status and
             inspection['complete_sha256']==item['complete']['sha256'] and
             inspection['plan_sha256']==filehash(root/'PLAN.json') and
             stopped(read(root/'OWNER.json')['native'],done['at']), 'Actual native qualification/inspection absent')
        check_files(plan['pins'])
        records[label]=plan
        receipts.extend([item['complete'],item['inspection'],ref(root/'PLAN.json')])
    # No new code gets qualified merely by this metadata helper.
    for relative,origin in [('runners/drive/cards/week5_at_queue_v1.py','queue'),
            ('runners/drive/cards/week5_at_queue_native_v2.py','queue'),
            ('runners/drive/cards/week5_at_queue_child_v2.py','queue'),
            ('runners/drive/cards/week5_at_queue_collect_v1.py','collector')]:
        path=(REPO/relative).resolve();need(records[origin]['pins'].get(str(path))==filehash(path),
            'Current producer/consumer is not the actually qualified source')
    return receipts

def capacity(review,production):
    paths=policy.lease_paths();snapshots=[];fillers=0
    extra=review.get('other_filler_natives',[]);short=review.get('other_short_lane_natives',[])
    for path in paths:
        value=read(path);identity=value['native']
        need(is_same_live_process(identity),'Lease identity unknown; reconcile without reclamation')
        if value.get('lane')=='short_metadata_preparation' or identity in short:pass
        elif value.get('family') in ('AT','BK','CH') or identity in extra:fillers+=1
        else:need(False,'Explicit owner classification required for additional lease')
        snapshots.append(dict(path=str(path),value=value))
    shared=policy.shared_reservation()
    if len(paths)>=8-int(shared['active']):raise ResourceHeld('Eight shared slots including ToM reservation occupied')
    if production and fillers>=6:raise ResourceHeld('Six filler slots occupied')
    return paths,dict(leases=snapshots,filler_count=fillers,shared_reservation=shared,
                      available_shared_slots=8-int(shared['active'])-len(paths))

def resource_and_budget(review,plan,production,prep_extra=0):
    drain_wall()
    paths,slots=capacity(review,production);snapshot=resource_snapshot()
    floors={'ram_available_GiB':20 if production else 6,
            'commit_headroom_GiB':26 if production else 8,'disk_free_GiB':20}
    if any(snapshot[k]<v for k,v in floors.items()):raise ResourceHeld('Unchanged native admission resource floor')
    if policy.memory_reserve(paths)+plan['projected_peak_ram_GiB']>snapshot['ram_available_GiB']-8:
        raise ResourceHeld('Projected concurrent peak leaves less than eight GiB')
    try:admission=policy.admission(plan,resources=snapshot,occupied=paths)
    except RuntimeError as error:
        if str(error) in ('Week 5 no-new-start boundary','CPU resource floor','Counted CPU slots occupied',
                          'Projected concurrent peak leaves less than eight GiB','Family or campaign CPU allowance exhausted'):
            raise ResourceHeld(str(error)) from error
        raise
    reserves=original_reserves();wall=plan['max_wall_seconds'] if production else drain_wall()
    held=MAINTENANCE+PRIOR_SUPERVISION+BK_SUPERVISION+2*wall
    # policy.admission already retains the next attempt's standard30 seconds.
    required=QUEUE_PLAN+held+prep_extra
    if admission['remaining_cpu_seconds']<required:raise ResourceHeld('Existing AT/campaign allowance cannot retain all declared reserves')
    return dict(admission=admission,capacity=slots,reserves=reserves,new_AT_supervision_cpu_seconds=2*wall,
                required_after_standard30_cpu_seconds=required,resource_floors=floors)

def immutable_inputs(review):
    need(review.get('owner_reviewed') is True,'Exact owner review required')
    need(Path(review['template']['path']).resolve()==TEMPLATE.resolve(),'Different original owner template refused')
    need(review['template']['sha256']==TEMPLATE_SHA,'Reviewed original template bytes changed')
    template=bound(review['template']);check_files(review['source_pins'])
    need(review['source_pins'].get(str(Path(__file__).resolve()))==filehash(__file__), 'Owner helper source unpinned')
    need(template['caps']==dict(chunk_cpu_seconds=7200,chunk_wall_seconds=1700,output_bytes=2**30,
          projected_peak_ram_GiB=20,queue_cpu_seconds=QUEUE_PLAN,queue_wall_seconds=43200), 'Original reviewed queue envelope changed')
    return template,qualification(review)

def child(operation,root):
    root=Path(root).resolve();root.relative_to(REPO/'.agent-state')
    plan=read(root/'PLAN.json');check_files(plan['pins'])
    identity=handshake(root,operation);freeze(root/(operation.upper()+'_NATIVE.json'),dict(at=now(),native=identity))
    request=read(plan['inputs']['owner_request']);destination=Path(plan['inputs']['destination'])
    if operation=='execute':
        freezer.build(request,destination)
        files={name:filehash(destination/name) for name in ('QUEUE_MANIFEST.json','PLAN_CANDIDATE.json','PREPARATION_RECEIPT.json')}
        freeze(root/'PREPARED_FILES.json',files)
        result=dict(status='complete',metadata_only=True,human_rows_decoded=False)
    else:
        for name,digest in read(root/'PREPARED_FILES.json').items():need(filehash(destination/name)==digest,'Prepared metadata changed')
        spec=read(destination/'QUEUE_MANIFEST.json');candidate=read(destination/'PLAN_CANDIDATE.json')
        queue.validate_manifest(spec)
        need(spec['start_ordinal']==133 and spec['end_ordinal_exclusive']==165 and
             spec['caps']==request['caps'] and spec['prefix']['owner_review']==request['prefix_review'] and
             candidate['max_cpu_seconds']==QUEUE_PLAN and candidate['owner_reviewed'] is False and
             candidate['template_only'] is True, 'Metadata replay changed original queue identity')
        result=dict(verified=True,metadata_only=True,human_rows_decoded=False)
    check_files(plan['pins']);freeze(root/('RESULT.json' if operation=='execute' else 'VERIFIED.json'),result)

def prepare(review_path,budget_root,work):
    started=time.monotonic();cpu0=time.process_time();review=read(review_path)
    need(review.get('status')=='OWNER_REVIEWED_AT_QUEUE_PREPARATION_V1' and review.get('owner_reviewed') is True,
         'Distinct reviewed preparation request required')
    budget_root=Path(budget_root).resolve();budget_root.relative_to(policy.ROOT)
    work=Path(work).resolve();work.relative_to(REPO/'.agent-state')
    need(not budget_root.exists() and not work.exists(),'Fresh preparation roots required')
    # Existing policy can account this operational preparation without adding a
    # new family or touching any running PLAN. Unknown interrupted use retains570.
    plan=dict(campaign='S15-WEEK5',family='AT',card=budget_root.name,module=MODULE,
        accounting_runtime='week5-v11',owner_reviewed=True,fixture_passed=True,gpu=False,paid=False,ollama=False,
        numerical_threads=2,max_cpu_seconds=PREP_PLAN,max_wall_seconds=PREP_WALL,projected_peak_ram_GiB=PREP_RAM,
        max_output_bytes=PREP_OUTPUT,reviewed_design_commit=review['reviewed_design_commit'],
        design=str(REPO/'docs/design/stage-15/week5/AT_QUEUE_V1.md'),attempt_root=str(budget_root),
        pins=dict(review['source_pins'],**{str(Path(review_path).resolve()):filehash(review_path)}),
        premortem=dict(case_and_check='Metadata-only original-prefix assembly and independent metadata replay',
                       smaller_route='Preserve interrupted preparation; no source or roster substitution'),
        operation_kind='owner_metadata_preparation',scientific_admission=False)
    budget_root.mkdir();freeze(budget_root/'PLAN.json',plan)
    (budget_root/'ATTEMPT.claim').write_text(now(),encoding='utf8')
    freeze(budget_root/'OWNER.json',dict(native=native_identity(),at=now(),plan_sha256=filehash(budget_root/'PLAN.json')))
    work.mkdir();freeze(work/'OWNER_REVIEW.json',review)
    lease=None;error=None;held=False;launched=[];native=work/'native';destination=work/'candidate'
    try:
        with kernel.admission_lock(policy.OLD_SLOTS):
            preflight=resource_and_budget(review,plan,False,PREP_TOTAL)
            value=dict(native=native_identity(),card=budget_root.name,family='AT',runtime='at-owner-metadata-v1',
                 lane='short_metadata_preparation',at=now(),attempt_root=str(budget_root),projected_peak_ram_GiB=PREP_RAM)
            for index in (4,5,6,7,0,1,2,3):
                bank=policy.NEW_SLOTS if index>=4 else policy.OLD_SLOTS;path=bank/f'slot-{index}.json'
                try:
                    with path.open('x',encoding='utf8',newline='\n') as stream:json.dump(value,stream)
                    lease=(path,value);break
                except FileExistsError:continue
            if lease is None:raise ResourceHeld('No exclusive preparation slot')
        freeze(work/'ADMISSION.json',dict(preflight,lease=str(lease[0]),lease_value=lease[1]))
        template,receipts=immutable_inputs(review)
        # Original launcher still verifies the committed design independently.
        import subprocess
        design=Path(plan['design']);committed=subprocess.run(['git','show',review['reviewed_design_commit']+':'+design.relative_to(REPO).as_posix()],
            cwd=REPO,capture_output=True,check=True).stdout
        need(committed==design.read_bytes(),'Preparation design is not the reviewed committed bytes')
        request=copy.deepcopy(template);request.update(owner_reviewed=True,reviewed_design_commit=review['reviewed_design_commit'])
        request['caps']['queue_wall_seconds']=drain_wall()
        request['qualification']=dict(native_fixture_and_actual_launcher_reviewed=True,receipts=receipts)
        request['preparation_charge_receipt']=str(budget_root/'COMPLETE.json')
        freeze(work/'BOUND_REQUEST.json',request)
        native.mkdir();pins=dict(review['source_pins']);pins[str(work/'BOUND_REQUEST.json')]=filehash(work/'BOUND_REQUEST.json')
        for receipt in receipts:pins[receipt['path']]=receipt['sha256']
        freeze(native/'PLAN.json',dict(module=MODULE,inputs=dict(owner_request=str(work/'BOUND_REQUEST.json'),destination=str(destination)),
                                       config={},pins=pins,metadata_only=True))
        def guarded_bytes(path):
            snapshot=resource_snapshot()
            if any(snapshot[k]<v for k,v in [('ram_available_GiB',4),('commit_headroom_GiB',6),('disk_free_GiB',20)]):
                raise ResourceHeld('Runtime metadata preparation resource hold')
            return kernel.output_bytes(path)
        phase=FunctionType(queue.native_phase.__code__,dict(queue.native_phase.__globals__,CHILD=MODULE,output_bytes=guarded_bytes),
                           queue.native_phase.__name__,queue.native_phase.__defaults__,queue.native_phase.__closure__)
        charged_native=0.0
        deadline=min(started+PREP_WALL,time.monotonic()+max(0,(policy.DRAIN-datetime.now(timezone.utc)).total_seconds()-60))
        for operation in ('execute','verify'):
            left=PREP_PLAN-charged_native-(time.process_time()-cpu0)-2
            need(left>0,'Preparation inclusive CPU exhausted before next phase')
            launched.append(operation)
            result,charge=phase(native,operation,work,deadline,left,PREP_OUTPUT);charged_native+=charge
            queue.native_proof.require_phase_proof(native,operation.upper(),read(native/(operation.upper()+'_NATIVE.json'))['native'])
        check_files(review['source_pins'])
        need(time.monotonic()<=deadline,'Final preparation wall exceeded')
    except ResourceHeld as exc:held=True;error=repr(exc)
    except BaseException as exc:error=repr(exc)
    finally:
        if lease:
            with kernel.admission_lock(policy.OLD_SLOTS):release_slot(*lease)
        usages=[];unknown=False
        for operation in launched:
            path=native/(operation.upper()+'_JOB_USAGE.json')
            if path.is_file():usages.append(read(path))
            else:unknown=True
        total=sum(v['cpu_seconds'] for v in usages)+(time.process_time()-cpu0)+2
        if unknown:total=max(PREP_PLAN,total)
        if total>PREP_PLAN:error=error or 'Final inclusive preparation CPU cap exceeded'
        status='PAUSED' if held else 'FAILED' if error else 'COMPLETE'
        terminal=dict(at=now(),status=status,cpu_seconds=total,standard_policy_supervisor_cpu_seconds=30,
            charged_upper_bound_cpu_seconds=total+30,max_charged_cpu_seconds=PREP_TOTAL,
            metadata_only=True,human_rows_decoded=False,scientific_admission=False,error=error,
            operational_hold=held,accounting_reconciliation_required=unknown,owned_lease_released=lease is not None,
            work=str(work),native_usage=usages,wall_seconds=time.monotonic()-started,
            fresh_process_verified=error is None,full_write_through_required=True)
        if not error:terminal['prepared_files']=read(native/'PREPARED_FILES.json')
        freeze(budget_root/(status+'.json'),terminal);freeze(work/'PREPARATION_ACCOUNTING.json',terminal)
    return dict(status=status,budget_root=str(budget_root),work=str(work),error=error,
                next='Separate owner launch review; preparation never launches science')

def launch(review_path):
    review=read(review_path)
    need(review.get('status')=='OWNER_REVIEWED_AT_QUEUE_LAUNCH_V1' and review.get('owner_reviewed') is True,
         'Distinct exact owner launch review required')
    template,receipts=immutable_inputs(review)
    prepared=bound(review['preparation_complete']);budget_root=Path(review['preparation_complete']['path']).parent
    need(prepared['status']=='COMPLETE' and prepared['fresh_process_verified'] is True and
         prepared['metadata_only'] is True and not prepared['accounting_reconciliation_required'] and
         stopped(read(budget_root/'OWNER.json')['native'],prepared['at']), 'Counted preparation not completely closed')
    work=Path(prepared['work']);candidate=work/'candidate'
    for name,digest in prepared['prepared_files'].items():need(filehash(candidate/name)==digest,'Prepared candidate changed')
    need(review['candidate_sha256']==filehash(candidate/'PLAN_CANDIDATE.json'),'Owner did not review exact candidate')
    spec=read(candidate/'QUEUE_MANIFEST.json');plan=read(candidate/'PLAN_CANDIDATE.json')
    wall=min(spec['caps']['queue_wall_seconds'],drain_wall());spec['caps']['queue_wall_seconds']=wall
    queue.validate_manifest(spec)
    need(plan['max_cpu_seconds']==QUEUE_PLAN and spec['caps']['queue_cpu_seconds']==QUEUE_PLAN and
         spec['start_ordinal']==133 and spec['end_ordinal_exclusive']==165, 'Original32000 charged cap or ordinals changed')
    staging=Path(review['launch_staging']).resolve();staging.relative_to(REPO/'.agent-state')
    root=Path(review['target_root']).resolve();root.relative_to(policy.ROOT)
    need(not staging.exists() and not root.exists(),'Fresh launch staging and attempt required')
    staging.mkdir();freeze(staging/'OWNER_REVIEW.json',review);freeze(staging/'QUEUE_MANIFEST.json',spec)
    old_manifest=plan['inputs']['queue_manifest'];plan['pins'].pop(old_manifest)
    plan['inputs']['queue_manifest']=str(staging/'QUEUE_MANIFEST.json')
    plan['pins'][str(staging/'QUEUE_MANIFEST.json')]=filehash(staging/'QUEUE_MANIFEST.json')
    for reference in [review['preparation_complete'],*receipts]:plan['pins'][reference['path']]=reference['sha256']
    plan.update(card=root.name,owner_reviewed=True,template_only=False,max_wall_seconds=wall,operating_gear=2)
    plan['owner_preparation_proof']=review['preparation_complete']
    plan['new_AT_supervision_reservation_cpu_seconds']=2*wall
    launcher.review(plan)
    with kernel.admission_lock(policy.OLD_SLOTS):preflight=resource_and_budget(review,plan,True)
    freeze(staging/'PREFLIGHT.json',dict(at=now(),**preflight,original_charged_queue_cpu_cap=QUEUE_CHARGED,
           launch_clock_wall_seconds=wall,retained_preparation_receipt=review['preparation_complete']))
    # The supported original writer and launcher retain their own fresh admission
    # and native monitor handshake. The single owner serializes filler dispatches.
    launcher.freeze_plan(root,plan)
    with kernel.admission_lock(policy.OLD_SLOTS):resource_and_budget(review,plan,True)
    result=launcher.launch(root)
    freeze(staging/'LAUNCH.json',dict(at=now(),**result,additional_AT_supervision_reserve_cpu_seconds=2*wall,
                                   prior_reservations_retained=original_reserves()))
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='action',required=True)
    p=sub.add_parser('prepare');p.add_argument('review',type=Path);p.add_argument('budget_root',type=Path);p.add_argument('work',type=Path)
    p=sub.add_parser('launch');p.add_argument('review',type=Path)
    for operation in ('execute','verify'):
        p=sub.add_parser(operation);p.add_argument('root',type=Path)
    args=parser.parse_args()
    if args.action in ('execute','verify'):child(args.action,args.root)
    else:
        result=prepare(args.review,args.budget_root,args.work) if args.action=='prepare' else launch(args.review)
        print(json.dumps(result,indent=2),flush=True)
