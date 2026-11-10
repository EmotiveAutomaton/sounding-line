"""Constructed generic-guard lifecycle, complete collection and AT2 proof.

DESIGN CHECK: LESSONS 3-5. No human/model-cache inputs. Actual tiny CPU models
exercise the production handlers. Synthetic resource snapshots test guard
control flow only; they never establish an admission peak for pretrained models.
Every original collection refusal and complete 2,000-draw statistic is retained.
"""
from pathlib import Path
from types import FunctionType
import time
from threadpoolctl import threadpool_limits
from . import week5_at_scoring_guard_v1 as guarded
from . import week5_at_scoring_v5 as scorer
from . import week5_at_collect_v5 as collector
from . import week5_at_analysis_v4 as analysis
from . import week5_at_collect_v4_fixture as original_fixture
from .week5_at_scoring_v4_fixture import loader
from .timing_census import read, filehash
from .timing_p6 import gzip_equal, write_equal


def resource_controls(root):
    g = 2**30
    high = dict(commit_headroom_bytes=30*g, ram_available_bytes=30*g)
    state = [dict(high, commit_headroom_bytes=25*g)]
    data = [dict(row_key=str(i),final_prefix='a '*i,target=' b') for i in range(18)]
    rows = root/'rows.json.gz'
    manifest = root/'model.json'
    gzip_equal(rows,data)
    write_equal(manifest,dict(model='constructed-gpt2',family='gpt2',revision='fixture'))
    inputs = dict(rows=str(rows),model_manifest=str(manifest))
    config = dict(context='final',context_length=64,max_wall_seconds=1200)
    old_memory,old_loader,old_progress = guarded.memory,guarded.load_model,scorer.progress
    calls=[]
    guarded.memory=lambda:state[0]
    def counted_loader(m):
        calls.append('model-load')
        return loader(m)
    guarded.load_model=counted_loader
    try:
        result=guarded.execute(root/'refused',inputs,config)
        if result.get('status')!='yielded' or result.get('model_loads')!=0 or calls:
            raise ValueError('Generic guard reached model load below its start floor')
        state[0]=high
        def progress(path,value):
            old_progress(path,value)
            if value['words']==8:
                state[0]=dict(high,commit_headroom_bytes=int(6.5*g))
                until=time.monotonic()+3
                while not (Path(path).parent/'YIELD_REQUEST.json').exists():
                    if time.monotonic()>until:raise ValueError('Generic native guard failed to signal sealed yield')
                    time.sleep(.01)
        scorer.progress=progress
        interrupted=root/'interrupted'
        result=guarded.execute(interrupted,inputs,config)
        if result.get('status')!='yielded' or result.get('completed')!=8 or calls!=['model-load']:
            raise ValueError('Generic guarded checkpoint did not retain the first exact block')
        original={p.relative_to(interrupted).as_posix():filehash(p) for p in interrupted.rglob('*') if p.is_file()}
        resumed=root/'resumed';resumed.mkdir(parents=True,exist_ok=True)
        # This is a same-process numerical-copy control, not a claim of native
        # runtime continuation. All original guard evidence remains in place
        # and is copied into an explicitly separate predecessor namespace.
        for name,digest in original.items():
            if Path(name).name in {'YIELD_REQUEST.json','PROGRESS.json'}:continue
            dest=resumed/name
            if Path(name).name.startswith('GUARD_'):dest=resumed/'predecessor-guard'/name
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes((interrupted/name).read_bytes())
            if filehash(dest)!=digest:raise ValueError('Constructed checkpoint copy changed bytes')
        state[0]=high;scorer.progress=old_progress
        if guarded.execute(resumed,inputs,config).get('status')!='complete':raise ValueError('Generic guarded resume incomplete')
        if guarded.verify(resumed,inputs,config).get('verified') is not True:raise ValueError('Generic guarded fresh forwards absent')
        if any(filehash(interrupted/name)!=digest for name,digest in original.items()):
            raise ValueError('Original resource-yield evidence changed')
        if filehash(interrupted/'block-00000.json')!=filehash(resumed/'block-00000.json'):
            raise ValueError('Guarded continuation replaced numerical checkpoint')
    finally:
        guarded.memory,guarded.load_model,scorer.progress=old_memory,old_loader,old_progress
    return dict(actual_native_guard_identity=True,refusal_before_load=True,actual_guard_thread_yield=True,
                exact_eight_word_checkpoint=True,original_evidence_unchanged=True,
                explicit_same_process_copy_control=True,full_native_resume_not_claimed=True,
                synthetic_resource_snapshots_only=True,guard_limits=guarded.LIMITS)


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('Constructed proof has no external or human input')
    root=Path(output);root.mkdir(parents=True,exist_ok=True)
    if (root/'YIELD_REQUEST.json').exists():return dict(status='yielded',reason='guarded-bank fixture boundary')
    controls=resource_controls(root/('verify-controls' if verifying else 'execute-controls'))
    original_memory=guarded.memory
    guarded.memory=lambda:dict(commit_headroom_bytes=30*2**30,ram_available_bytes=30*2**30)
    # Reuse the full existing actual handler proof with only the explicit
    # producer/collector/consumer successor bindings replaced.
    seal=FunctionType(original_fixture.seal.__code__,
                      dict(original_fixture.seal.__globals__,collector=collector),
                      original_fixture.seal.__name__,original_fixture.seal.__defaults__,
                      original_fixture.seal.__closure__)
    fn=FunctionType(original_fixture.run.__code__,
                    dict(original_fixture.run.__globals__,collector=collector,analysis=analysis,
                         v4=guarded,v5=scorer,seal=seal),
                    original_fixture.run.__name__,original_fixture.run.__defaults__,
                    original_fixture.run.__closure__)
    try:result=fn(root/'complete-bank',{}, {},verifying)
    finally:guarded.memory=original_memory
    if result.get('status')=='yielded':return result
    if verifying and result.get('verified') is not True:raise ValueError('Complete guarded-bank replay absent')
    # The inherited proof exercises old precision, missing original pins,
    # changed binding/context/revision, and incomplete model-bank refusals.
    bank=root/'complete-bank';first=bank/'scores-0-0';pp=first/'PLAN.json'
    args=dict(source_root=str(bank/'source'),bank_manifest=str(bank/'BANK.json'))
    cfg=dict(context='final',context_length=1024)
    dropped=read(pp);dropped['pins']={p:s for p,s in dropped['pins'].items() if not p.endswith('week5_at_scoring_guard_v1.py')}
    original_fixture.rejected(first,pp,dropped,lambda:collector.validate(args,cfg))
    original_fixture.rejected(first,pp,dict(read(pp),module='runners.drive.cards.unknown_guard'),lambda:collector.validate(args,cfg))
    sealed=read(first/'COMPLETE.json')
    verify_name=next(n for n in sealed['outputs'] if n.startswith('output/GUARD_VERIFY_'))
    path=first/verify_name;bad=read(path);bad['limits']=dict(bad['limits'],start_commit_bytes=1)
    original_fixture.rejected(first,path,bad,lambda:collector.validate(args,cfg))
    # Appended operational receipts do not rewrite a completed producer's
    # immutable provenance. Both outer phases reproduce the same sidecar.
    collector.verify(bank/'collection/output',args,cfg)
    receipt=dict(fixture_only=True,resource_controls=controls,
                 actual_guarded_v5_and_unguarded_v5_numeric_bytes_equal=True,
                 complete_ten_reader_360_row_bank=True,original_2000_draw_AT2_equal=True,
                 exact_reader_binding=True,unknown_guard_missing_pin_changed_limits_refused=True,
                 original_collection_refusals_retained=True,
                 completed_guard_provenance_stable_under_later_replay=True,
                 native_human_model_admission=False)
    if verifying:
        if read(root/'FIXTURE.json')!=receipt:raise ValueError('Guarded bank fixture receipt differs')
        return dict(verified=True,complete_guarded_bank_and_statistics=True)
    write_equal(root/'FIXTURE.json',receipt)
    return dict(status='complete',fixture_only=True)


def execute(output,inputs,config):
    with threadpool_limits(limits=2):return run(output,inputs,config)


def verify(output,inputs,config):
    with threadpool_limits(limits=2):return run(output,inputs,config,True)
