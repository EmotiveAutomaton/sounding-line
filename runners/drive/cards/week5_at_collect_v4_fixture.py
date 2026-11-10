"""Actual tiny-reader v4/v5 complete collection, refusal and AT2 replay proof.

DESIGN CHECK: LESSONS3--5. Constructed inputs only. A compatible completed
producer joins unchanged numeric values; old, incomplete or unpinned producers
must fail. Full 2,000-draw original AT2 analysis and reader binding are retained.
"""
from pathlib import Path
import json
from threadpoolctl import threadpool_limits
from . import week5_at_collect_v4 as collector
from . import week5_at_analysis_v3 as analysis
from . import week5_at_analysis as original_analysis
from . import week5_at_scoring_v4 as v4
from . import week5_at_scoring_v5 as v5
from .week5_at_scoring import MODELS
from .week5_at_scoring_v4_fixture import loader
from .week5_at_fixture import rows
from .week5_at_selection import selected_reader
from .timing_census import read,filehash
from .timing_p6 import gzip_equal,gzread,write_equal


def seal(root,module,inputs,config):
    pins={str(Path(__file__).parent/name):sha for name,sha in collector.CORE.items()}
    for value in inputs.values():
        if Path(value).is_file():pins[str(Path(value).resolve())]=filehash(value)
    write_equal(root/'PLAN.json',dict(module=module,inputs=inputs,config=config,pins=pins))
    if not (root/'COMPLETE.json').exists():
        outputs={p.relative_to(root).as_posix():filehash(p) for p in root.rglob('*')
                 if p.is_file() and p.name not in ('COMPLETE.json','PROGRESS.json')}
        write_equal(root/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,outputs=outputs,
            constructed_dependency_fixture=True,not_a_production_runtime_admission=True))


def rejected(root,path,value,call):
    saved=path.read_bytes();done=root/'COMPLETE.json';saved_done=done.read_bytes()
    try:
        path.write_text(json.dumps(value)+'\n',encoding='utf8')
        evidence=read(done);evidence['outputs'][path.relative_to(root).as_posix()]=filehash(path)
        done.write_text(json.dumps(evidence)+'\n',encoding='utf8')
        try:call()
        except (ValueError,KeyError):pass
        else:raise ValueError('Changed producer condition accepted')
    finally:path.write_bytes(saved);done.write_bytes(saved_done)


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('No human or external fixture input')
    root=Path(output);root.mkdir(parents=True,exist_ok=True);data=rows()
    if (root/'YIELD_REQUEST.json').exists():return dict(status='yielded',reason='constructed fixture boundary')
    for i,row in enumerate(data):
        row.pop('scores')
        row.update(row_key=str(i),session='constructed-'+row['writer'],target=' b',
            final_prefix='a '*(i%20),at_typing_prefix='a '*(i%20),timing_supported=True,
            after_punctuation=int(i%7==0),on_screen=int(i%3==0),session_surprisal=float(i%11))
    source=root/'source';batches=[]
    for j in range(2):
        name=f'batches/final-{j:04d}.json.gz';p=source/'output'/name
        gzip_equal(p,data[j*180:(j+1)*180]);batches.append(dict(file=name,context='final',words=180,sha256=filehash(p)))
    gzip_equal(source/'output/sessions/session-0000.json.gz',dict(rows=data))
    write_equal(source/'output/INDEX.json',[dict(file='sessions/session-0000.json.gz',sha256=filehash(source/'output/sessions/session-0000.json.gz'))])
    write_equal(source/'output/BATCHES.json',batches)
    seal(source,'constructed_source_fixture',{},{});bank={};original_loaders=(v4.load_model,v5.load_model)
    v4.load_model=v5.load_model=loader
    try:
        for m,model in enumerate(MODELS):
            manifest=dict(model=model,family='neox',revision='constructed-exact-'+str(m));mp=root/f'model-{m}.json';write_equal(mp,manifest)
            bank[model]={}
            for j,batch in enumerate(batches):
                if (root/'YIELD_REQUEST.json').exists():return dict(status='yielded',reason='sealed constructed score boundary')
                module=v4 if j==0 else v5;score_root=root/f'scores-{m}-{j}'
                args=dict(rows=str(source/'output'/batch['file']),model_manifest=str(mp))
                cfg=dict(context='final',context_length=1024,max_wall_seconds=1200)
                if verifying or (score_root/'COMPLETE.json').exists():
                    if module.verify(score_root/'output',args,cfg).get('verified') is not True:raise ValueError('Fresh score replay missing')
                else:
                    if module.execute(score_root/'output',args,cfg).get('status')!='complete':raise ValueError('Score execution incomplete')
                    if module.verify(score_root/'output',args,cfg).get('verified') is not True:raise ValueError('Score replay incomplete')
                    if module is v5:
                        oldcost=filehash(score_root/'output/COST.json')
                        module.execute(score_root/'output',args,cfg)
                        if filehash(score_root/'output/COST.json')!=oldcost:raise ValueError('Completed cost replaced')
                seal(score_root,module.__name__,args,cfg);bank[model][batch['file']]=str(score_root)
        # Same exact rows/model/context, separately executed by each producer.
        if (root/'YIELD_REQUEST.json').exists():return dict(status='yielded',reason='complete constructed score-bank boundary')
        original=root/'scores-0-0';oldplan=read(original/'PLAN.json');mirror=root/'same-input-v5'
        (v5.verify if verifying else v5.execute)(mirror/'output',oldplan['inputs'],oldplan['config'])
        if not verifying:v5.verify(mirror/'output',oldplan['inputs'],oldplan['config'])
        for entry in read(original/'output/INDEX.json'):
            if filehash(original/'output'/entry['file'])!=filehash(mirror/'output'/entry['file']):
                raise ValueError('v4/v5 numerical bytes differ on identical inputs')
    finally:v4.load_model,v5.load_model=original_loaders
    write_equal(root/'BANK.json',bank);args=dict(source_root=str(source),bank_manifest=str(root/'BANK.json'))
    cfg=dict(context='final',context_length=1024);collected=root/'collection'
    (collector.verify if verifying else collector.execute)(collected/'output',args,cfg)
    if not verifying:collector.verify(collected/'output',args,cfg)
    seal(collected,collector.__name__,args,cfg)
    if len(gzread(collected/'output/ROWS.json.gz'))!=360:raise ValueError('Whole constructed population lost')
    first=root/'scores-0-0';pp=first/'PLAN.json';summary=first/'output/SUMMARY.json'
    rejected(first,pp,dict(read(pp),module='runners.drive.cards.week5_at_scoring_v3'),lambda:collector.validate(args,cfg))
    missing=read(pp);missing['pins']={k:v for k,v in missing['pins'].items() if not k.endswith('week5_at_scoring_v4.py')}
    rejected(first,pp,missing,lambda:collector.validate(args,cfg))
    rejected(first,summary,dict(read(summary),numerical_spec=dict(v4.NUMERICAL_SPEC,model_computation='float32')),lambda:collector.validate(args,cfg))
    rejected(first,summary,dict(read(summary),context_length=64),lambda:collector.validate(args,cfg))
    rejected(first,summary,dict(read(summary),model_revision='changed'),lambda:collector.validate(args,cfg))
    rejected(first,first/'output/BINDING.json',dict(sha256='wrong'),lambda:collector.validate(args,cfg))
    bp=root/'BANK.json';saved=bp.read_bytes();incomplete=read(bp);incomplete[MODELS[0]].pop(batches[-1]['file'])
    try:
        bp.write_text(json.dumps(incomplete)+'\n',encoding='utf8')
        try:collector.validate(args,cfg)
        except ValueError:pass
        else:raise ValueError('Partial bank accepted')
    finally:bp.write_bytes(saved)
    selection=root/'selection';acfg=dict(card='AT2',models=list(MODELS),draws=2000)
    if (root/'YIELD_REQUEST.json').exists():return dict(status='yielded',reason='constructed complete-statistic boundary')
    (analysis.verify if verifying else analysis.execute)(selection/'output',dict(collection_root=str(collected)),acfg)
    if not verifying:analysis.verify(selection/'output',dict(collection_root=str(collected)),acfg)
    seal(selection,analysis.__name__,dict(collection_root=str(collected)),acfg)
    oracle=root/'original-analysis'
    (original_analysis.verify if verifying else original_analysis.execute)(oracle,dict(rows=str(collected/'output/ROWS.json.gz')),acfg)
    if read(oracle/'RESULT.json')!=read(selection/'output/RESULT.json'):raise ValueError('AT2 statistics changed')
    chosen=read(selection/'output/RESULT.json')['selected_model'];manifest=read(root/f'model-{list(MODELS).index(chosen)}.json')
    selected_reader(selection,manifest)
    result=dict(fixture_only=True,constructed_receipts_not_production_admission=True,
        actual_v4_and_v5_scoring=True,identical_input_score_bytes_equal=True,
        all_ten_complete_banks=True,all_360_constructed_rows=True,original_2000_draw_analysis_equal=True,
        exact_selected_manifest=True,old_precision_missing_pin_changed_binding_context_revision_and_incomplete_bank_refused=True)
    if verifying:
        if read(root/'FIXTURE.json')!=result:raise ValueError('Complete provenance fixture differs')
        return dict(verified=True,complete_numeric_collection_and_analysis=True)
    write_equal(root/'FIXTURE.json',result);return dict(status='complete',fixture_only=True)


def execute(output,inputs,config):
    with threadpool_limits(limits=2):return run(output,inputs,config)
def verify(output,inputs,config):
    with threadpool_limits(limits=2):return run(output,inputs,config,True)
