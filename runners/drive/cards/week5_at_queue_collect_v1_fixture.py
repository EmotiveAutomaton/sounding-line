"""UNRUN collector known-answer consumers of the actual constructed native queue.

DESIGN CHECK: LESSONS 3-5. Only the original queue fixture's constructed texts
are admitted. Actual native score/guard/exit proofs exercise the new consumer;
metadata scope controls prove that a two-chunk fixture cannot close a165-chunk
pilot. This fixture neither fabricates native evidence nor decodes human data.
"""
from pathlib import Path
import copy,json,shutil
from . import week5_at_queue_collect_v1 as collector
from .batch_runtime import read,freeze,filehash


def mutate_copy(base,destination,relative,change,call,wanted):
    shutil.copytree(base,destination)
    path=destination/relative;value=read(path);change(value)
    path.write_text(json.dumps(value),encoding='utf8')
    try:call(destination)
    except ValueError as error:
        collector.require(str(error)==wanted,'Wrong refusal reason: '+repr(error))
    else:raise ValueError('Constructed mutation accepted: '+relative)


def run(output,inputs,config,verifying=False):
    collector.require(set(inputs)=={'native_queue_fixture_root'} and not config,'Exact counted native fixture source required')
    native=Path(inputs['native_queue_fixture_root']).resolve()
    plan=read(native/'PLAN.json')
    collector.require(plan['module']=='runners.drive.cards.week5_at_queue_v1_fixture',
                      'Only constructed native queue may feed this fixture')
    collector.native_complete(native,read(native/'COMPLETE.json'))
    base=native/'output/execution'
    marker=read(base/'FIXTURE.json')
    collector.require(marker['fixture_only'] is True and marker['full_production_admission'] is False,
                      'Wrong fixture scope')
    output=Path(output)/('verify' if verifying else 'execute');output.mkdir(parents=True,exist_ok=True)
    counts=[];roots=[];batches=[];model_path=base/'constructed-sources/MODEL.json';model=read(model_path)
    collector.require(model==dict(model='constructed-gpt2',family='gpt2',revision='fixture-at-queue-v1'),
                      'Pretrained or human model source refused')
    for ordinal in (163,164):
        root=base/'queue/chunks'/f'{ordinal:04d}'/'a000'
        source=base/'constructed-sources'/f'fixture-{ordinal:04d}.json.gz'
        batch=dict(input_rows=str(source.resolve()),input_sha256=filehash(source),words=18)
        proof=collector.phase_proof(root,batch,True)
        rows=collector.score_rows(root,batch,model,filehash(model_path))
        collector.require(len(rows)==18 and all(x['row_key'].startswith(f'constructed-{ordinal}-') for x in rows),
                          'Constructed row identities differ')
        counts.append(len(rows));roots.append(root);batches.append(batch)
    collector.original_scope(list(range(165)),27007)
    for ordinals,words in [(list(range(164)),27007),(list(range(165)),27006),([*range(164),163],27007),([163,164],36)]:
        try:collector.original_scope(ordinals,words)
        except ValueError:pass
        else:raise ValueError('Incomplete or duplicated scope accepted')
    root=roots[0];batch=batches[0]
    score=lambda p:collector.score_rows(p,batch,model,filehash(model_path))
    phase=lambda p:collector.phase_proof(p,batch,True)
    mutate_copy(root,output/'wrong-context','output/SUMMARY.json',lambda x:x.update(context_length=64),score,'Changed score summary scope')
    mutate_copy(root,output/'wrong-revision','output/SUMMARY.json',lambda x:x.update(model_revision='different'),score,'Changed score summary scope')
    mutate_copy(root,output/'wrong-precision','output/SUMMARY.json',lambda x:x.update(numerical_spec={}),score,'Changed score summary scope')
    mutate_copy(root,output/'missing-fresh','VERIFIED.json',lambda x:x.update(fresh_forward_count=0),phase,'Original seeded fresh-forward verification missing')
    mutate_copy(root,output/'wrong-native','EXECUTE_OWNED.json',lambda x:x['native'].update(created_ticks=0),phase,'Exact nested native closure missing')
    mutate_copy(root,output/'wrong-row-order','output/INDEX.json',lambda x:x.reverse(),score,'Original word-row order differs')
    def drop_guard(value):
        value['pins']={p:h for p,h in value['pins'].items() if not p.endswith('week5_at_precision_guard.py')}
    mutate_copy(root,output/'missing-core','PLAN.json',drop_guard,score,'Original numerical/guard code pin missing')
    def corrupt_score(value):
        value['values'][0]['score']['surprisal_nats']=999.0
    mutate_copy(root,output/'corrupt-score','output/block-00000.json',corrupt_score,score,'Score block hash differs')
    incomplete=output/'queue-without-complete';incomplete.mkdir()
    freeze(incomplete/'PAUSED.json',dict(status='PAUSED',fixture_only=True,no_native_evidence_claimed=True))
    request=dict(queue_root=str(incomplete),queue_complete_sha256='0'*64,
                 pilot_source_root='never-read',pilot_source_complete_sha256='0'*64)
    try:collector.validate(request)
    except FileNotFoundError as error:
        collector.require(Path(error.filename).resolve()==(incomplete/'COMPLETE.json').resolve(),
                          'No-complete case failed at a different dependency')
    else:raise ValueError('Queue without COMPLETE was accepted')
    collector.require(not (incomplete/'output/MEASURED_ENVELOPE.json').exists(),
                      'Incomplete queue produced a complete-pilot envelope')
    result=dict(fixture_only=True,actual_constructed_native_rows=counts,original_numeric_kernel_used=True,
        exact_row_binding_and_native_guard_consumer_passed=True,
        incomplete_165_chunk_pilot_refused=True,corrupt_score_block_refused=True,missing_queue_complete_refused=True,
        changed_context_revision_precision_core_fresh_native_and_row_order_refused=True,
        complete_original_m00_pilot=False,whole_ten_reader_bank_ready=False,scientific_admission=False,
        fixture_source_complete_sha256=filehash(native/'COMPLETE.json'))
    freeze(output/'FIXTURE.json',result)
    if verifying:
        collector.require(result==read(output.parent/'execute/FIXTURE.json'),'Collector constructed replay differs')
        return dict(verified=True,fixture_only=True)
    return dict(status='complete',fixture_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
