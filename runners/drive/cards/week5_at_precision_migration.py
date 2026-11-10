"""Narrow authenticated completed-v4 precision checkpoint adoption into v5.

This is a new engineering attempt, not a change to general resume contracts.
All predecessor bytes and pins survive; fresh guarded verification is mandatory.
"""
from pathlib import Path
import math
import shutil
from . import week5_at_scoring_v4 as old_scorer
from . import week5_at_scoring_v5 as scorer
from . import week5_at_precision_guard_v2 as guard
from .timing_census import read,filehash
from .timing_p6 import gzread,write_equal
from .batch_runtime import check_files
from .week5_resume import output_manifest
from runners.stage9.process_identity import is_same_live_process

OLD_MODULE='runners.drive.cards.week5_at_precision_guard'


def validate_scores(output,failed_root):
    root=Path(output);failed=Path(failed_root);plan=read(failed/'PLAN.json')
    if plan['module']!='runners.drive.cards.week5_at_scoring_v3' or not (failed/'FAILED.json').is_file():
        raise ValueError('Exact retained original-v3 failure required')
    rows=gzread(plan['inputs']['rows']);manifest=read(plan['inputs']['model_manifest']);cfg=plan['config']
    context=cfg.get('context','final');length=cfg.get('context_length',1024)
    binding=old_scorer.score_binding(rows,manifest,context,length);scores=root/'scores'
    if read(scores/'BINDING.json')!={'sha256':binding}:raise ValueError('Original scoring binding changed')
    expected=dict(status='complete',words=len(rows),context=context,context_length=length,
                  model=manifest['model'],model_revision=manifest['revision'],scientific_admission=False,
                  storage='sealed_blocks_v2',numerical_spec=scorer.NUMERICAL_SPEC)
    if not rows or read(scores/'SUMMARY.json')!=expected:raise ValueError('Complete original score reduction required')
    index=[];names=[]
    for offset in range(0,len(rows),8):
        path=scores/f'block-{offset//8:05d}.json';names.append(path.name);sha=filehash(path)
        if read(path.with_suffix('.receipt.json'))!={'sha256':sha}:raise ValueError('Original score seal changed')
        block=read(path);wanted=rows[offset:offset+8]
        if set(block)!={'binding','offset','values'} or block['binding']!=binding or block['offset']!=offset or len(block['values'])!=len(wanted):
            raise ValueError('Original score block shape or identity changed')
        for slot,(row,value) in enumerate(zip(wanted,block['values'])):
            if value['row_key']!=row['row_key']:raise ValueError('Original scored row identity changed')
            score=value['score'];losses=score['native_token_nll'];ids=score['native_token_ids']
            if not losses or len(losses)!=len(ids) or any(type(i) is not int or i<0 for i in ids):
                raise ValueError('Invalid complete original target scores')
            if any(not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) or v<0 for v in losses+[score['entropy_nats']]):
                raise ValueError('Invalid original predictive quantity')
            if score['surprisal_nats']!=sum(losses) or type(score['prefix_tokens_dropped']) is not int or score['prefix_tokens_dropped']<0:
                raise ValueError('Original score reconstruction differs')
            index.append(dict(row_key=row['row_key'],file=path.name,slot=slot,sha256=sha))
    if sorted(p.name for p in scores.glob('block-*.json') if not p.name.endswith('.receipt.json'))!=names or read(scores/'INDEX.json')!=index:
        raise ValueError('Incomplete, extra or reordered score blocks')
    scorer.retained_cost(scores/'COST.json')
    case=dict(original_plan_sha256=filehash(failed/'PLAN.json'),original_failure_sha256=filehash(failed/'FAILED.json'),
              original_rows_sha256=filehash(plan['inputs']['rows']),original_model_manifest_sha256=filehash(plan['inputs']['model_manifest']),
              numerical_spec=scorer.NUMERICAL_SPEC)
    if read(root/'CASE_BINDING.json')!=case:raise ValueError('Original failed-case binding changed')
    receipt=dict(engineering_replay_only=True,entire_original_chunk=True,unchanged_seeded_fresh_sample=True,
                 model=manifest['model'],words=len(rows),numerical_spec=scorer.NUMERICAL_SPEC,original_failure_preserved=True)
    if read(root/'FIXTURE.json')!=receipt:raise ValueError('Original execution did not finish the entire case')
    return dict(words=len(rows),score_binding=binding,cost_sha256=filehash(scores/'COST.json'))


def adopt(output,inputs):
    if set(inputs)!={'failed_root','predecessor_root'}:raise ValueError('Exact retained source and predecessor required')
    root=Path(output).resolve();old=Path(inputs['predecessor_root']).resolve()
    if root==old/'output':raise ValueError('Never modify the predecessor')
    prior=read(old/'PLAN.json');paused=read(old/'PAUSED.json');owner=read(old/'OWNER.json')
    current=read(root.parent/'PLAN.json')
    if prior['module']!=OLD_MODULE or prior['config']!={} or prior['inputs']!={'failed_root':inputs['failed_root']}:
        raise ValueError('Only the exact guarded original-v4 case is migratable')
    if current['module']!=__name__ or current['inputs']!=inputs or current['config']!={}:
        raise ValueError('Exact declared successor plan required')
    if prior.get('family')!=current.get('family') or prior.get('campaign')!=current.get('campaign'):
        raise ValueError('Migration cannot change the charged family or campaign')
    if any((old/name).exists() for name in ('COMPLETE.json','FAILED.json')):
        raise ValueError('Only the unambiguous guarded pause is migratable')
    if paused.get('status')!='PAUSED' or not paused.get('checkpoint_validation_required'):
        raise ValueError('Authenticated resource pause required')
    if owner['plan_sha256']!=filehash(old/'PLAN.json') or is_same_live_process(owner['native']):
        raise ValueError('Wrong or still-live predecessor native identity')
    if any(current['pins'].get(path)!=sha for path,sha in prior['pins'].items()):
        raise ValueError('Successor dropped or changed a predecessor pin')
    prior_paths={str(Path(path).resolve()):sha for path,sha in prior['pins'].items()}
    failed=Path(inputs['failed_root']);failed_plan=read(failed/'PLAN.json')
    required=[failed/'PLAN.json',failed/'FAILED.json',Path(failed_plan['inputs']['rows']),Path(failed_plan['inputs']['model_manifest'])]
    required += [Path(__file__).parent/name for name in ('week5_at_precision_guard.py','week5_at_precision_case.py','week5_at_scoring_v4.py','week5_at_scoring.py')]
    if any(prior_paths.get(str(path.resolve()))!=filehash(path) for path in required):
        raise ValueError('Original source or scoring closure was not pinned')
    check_files(prior['pins']);check_files(current['pins'])
    for filename in ('PLAN.json','PAUSED.json'):
        path=old/filename
        if current['pins'].get(str(path))!=filehash(path):
            raise ValueError('Successor must explicitly pin predecessor plan and pause')
    expected=paused.get('checkpoint_outputs')
    if not expected or output_manifest(old/'output')!=expected:
        raise ValueError('Predecessor output manifest changed or is incomplete')
    proof=validate_scores(old/'output',inputs['failed_root'])
    receipt=dict(predecessor=str(old),plan_sha256=filehash(old/'PLAN.json'),paused_sha256=filehash(old/'PAUSED.json'),
                 old_module=OLD_MODULE,new_module=__name__,copied=expected,proof=proof,
                 numerical_spec=scorer.NUMERICAL_SPEC,prior_and_failed_continuation_costs_retained=True)
    root.mkdir(parents=True,exist_ok=True);receipt_path=root/'MIGRATED_FROM_V4.json'
    if receipt_path.exists():
        if read(receipt_path)!=receipt:raise ValueError('Migration receipt changed')
        if any(filehash(root/name)!=sha for name,sha in expected.items()):
            raise ValueError('Inherited immutable output changed on successor reentry')
    else:
        if output_manifest(root):raise ValueError('New migration target must have no existing immutable outputs')
        for name,sha in expected.items():
            src=(old/'output'/name).resolve();src.relative_to((old/'output').resolve())
            dest=(root/name).resolve();dest.relative_to(root)
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
            if filehash(dest)!=sha:raise ValueError('Exact predecessor copy failed')
        if output_manifest(root)!=expected:raise ValueError('Incomplete immutable migration copy')
        write_equal(receipt_path,receipt)
    validate_scores(root,inputs['failed_root'])
    return receipt


def run(output,inputs,config,verifying=False):
    if config:raise ValueError('No scoring or resource changes in migration')
    adopt(output,inputs)
    return guard.run(output,{'failed_root':inputs['failed_root']},{},verifying)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
