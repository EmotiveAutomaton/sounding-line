"""Complete AT2 precision provenance and actual paired LA1 inheritance proof."""
from pathlib import Path
import json,time
import numpy as np
from . import week5_at_analysis_v2 as analysis
from . import week5_at_collect_v3 as collector
from . import week5_at_selection as selection
from . import week5_la_pipeline_v3 as la
from .week5_at_scoring import MODELS,digest
from .week5_at_scoring_v4 import NUMERICAL_SPEC,score_binding
from .week5_at_fixture import rows,fixture_loader
from .week5_la_score_fixture import masked_loader
from .timing_census import read,filehash
from .timing_p6 import gzip_equal,write_equal


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('Constructed provenance fixture only')
    root=Path(output);data=rows()
    for i,row in enumerate(data):
        value=next(iter(row['scores'].values()));row['scores']={m:dict(value) for m in MODELS}
        row.update(row_key=str(i),after_punctuation=int(i%7==0),on_screen=int(i%3==0),session_surprisal=float(np.sin(i)))
    source=root/'source';chunk=source/'output/batches/final-0000.json.gz';gzip_equal(chunk,data)
    write_equal(source/'output/BATCHES.json',[dict(file='batches/final-0000.json.gz',sha256=filehash(chunk),context='final')])
    bank={};manifests={}
    for i,model in enumerate(MODELS):
        manifest=dict(model=model,revision='constructed-'+str(i),files={});manifests[model]=manifest
        mp=root/f'model-{i}.json';write_equal(mp,manifest);score_root=root/f'bank-{i}';bank[model]={'batches/final-0000.json.gz':str(score_root)}
        write_equal(score_root/'PLAN.json',dict(module='runners.drive.cards.week5_at_scoring_v4',inputs=dict(rows=str(chunk),model_manifest=str(mp)),config=dict(context='final',context_length=1024)))
        write_equal(score_root/'output/SUMMARY.json',dict(model=model,model_revision=manifest['revision'],context='final',context_length=1024,numerical_spec=NUMERICAL_SPEC))
        write_equal(score_root/'output/BINDING.json',dict(sha256=score_binding(data,manifest,'final',1024)))
    write_equal(root/'BANK.json',bank);collection=root/'collection';collection_inputs=dict(source_root=str(source),bank_manifest=str(root/'BANK.json'))
    write_equal(collection/'PLAN.json',dict(module='runners.drive.cards.week5_at_collect_v3',inputs=collection_inputs,config=dict(context='final',context_length=1024)))
    write_equal(collection/'output/SUMMARY.json',dict(models=sorted(MODELS)));write_equal(collection/'output/NUMERICAL_SPEC.json',NUMERICAL_SPEC)
    gzip_equal(collection/'output/ROWS.json.gz',data)
    originals=(analysis.authenticate,analysis.filehash,collector.authenticate,selection.authenticate,la.authenticate,la.filehash,la.load_model,la.load_masked,la.progress)
    def fixture_auth(path):
        path=Path(path)
        if not path.resolve().is_relative_to(root.resolve()):raise ValueError('Constructed paths only')
        return path
    def fixture_hash(path):return 'constructed-no-completion' if Path(path).name=='COMPLETE.json' else filehash(path)
    def causal_loader(manifest):
        model,tok,torch=fixture_loader(manifest);return model.double(),tok,torch
    analysis.authenticate=collector.authenticate=selection.authenticate=la.authenticate=fixture_auth
    analysis.filehash=la.filehash=fixture_hash;la.load_model=causal_loader;la.load_masked=masked_loader
    try:
        selected_root=root/'selection';cfg=dict(card='AT2',models=list(MODELS),draws=2000)
        (analysis.verify if verifying else analysis.execute)(selected_root/'output',dict(collection_root=str(collection)),cfg)
        result=read(selected_root/'output/RESULT.json');manifest=manifests[result['selected_model']]
        if result['primary']['draws']!=2000 or len(result['secondary'])!=10:raise ValueError('Complete original AT2 statistics missing')
        selected=selection.selected_reader(selected_root,manifest)
        if selected['numerical_spec']!=NUMERICAL_SPEC:raise ValueError('Selected numerical inheritance differs')
        try:selection.selected_reader(selected_root,dict(manifest,revision='wrong'))
        except ValueError:pass
        else:raise ValueError('Changed selected revision accepted')
        p=selected_root/'output/READER_BINDING.json';saved=p.read_bytes();changed=read(p);changed['numerical_spec']=dict(NUMERICAL_SPEC,model_computation='float32');p.write_text(json.dumps(changed)+'\n')
        try:
            try:selection.selected_reader(selected_root,manifest)
            except ValueError:pass
            else:raise ValueError('Legacy selected precision accepted')
        finally:p.write_bytes(saved)
        source_rows=[dict(id=str(i),causal_prefix='a ',target='b',previous='old',word_count=1,meeting='constructed') for i in range(2)]
        prepared=root/'la-source';rows_path=prepared/'output/batches/acts-000000.json.gz';gzip_equal(rows_path,source_rows)
        write_equal(prepared/'output/BATCHES.json',[dict(file='batches/acts-000000.json.gz',sha256=filehash(rows_path),rows=2)])
        write_equal(root/'causal.json',manifest);write_equal(root/'masked.json',dict(model='constructed-masked',revision='fixture'))
        args=dict(rows=str(rows_path),causal_manifest=str(root/'causal.json'),masked_manifest=str(root/'masked.json'),selection_root=str(selected_root))
        score_root=root/'la-scores';score_cfg=dict(operation='score');marker=score_root/'output/YIELD_REQUEST.json'
        write_equal(score_root/'PLAN.json',dict(module='runners.drive.cards.week5_la_pipeline_v3',inputs=args,config=score_cfg))
        def progress(path,value):
            originals[-1](path,value)
            if value['acts']==1:write_equal(marker,dict(reason='constructed yield'))
        if not verifying:
            la.progress=progress;value=la.execute(score_root/'output',args,score_cfg)
            if value.get('status')!='yielded' or value['completed']!=1:raise ValueError('LA selected-precision yield failed')
            marker.unlink();la.progress=originals[-1]
        (la.verify if verifying else la.execute)(score_root/'output',args,score_cfg)
        write_equal(root/'LA_BANK.json',{'batches/acts-000000.json.gz':str(score_root)})
        collect_args=dict(prepared_root=str(prepared),score_bank=str(root/'LA_BANK.json'))
        (la.verify if verifying else la.execute)(root/'la-collected',collect_args,dict(operation='collect'))
        p=score_root/'output/SUMMARY.json';saved=p.read_bytes();changed=read(p);changed['numerical_spec']={};p.write_text(json.dumps(changed)+'\n')
        try:
            try:la.collect(root/'invalid-la-bank',collect_args,dict(operation='collect'))
            except ValueError as error:
                if 'numerical specification' not in str(error):raise
            else:raise ValueError('Mixed LA precision accepted')
        finally:p.write_bytes(saved)
    finally:
        analysis.authenticate,analysis.filehash,collector.authenticate,selection.authenticate,la.authenticate,la.filehash,la.load_model,la.load_masked,la.progress=originals
    receipt=dict(fixture_only=True,full_original_at2_2000_draws=True,all_ten_models=True,actual_collection_binding_validation=True,
                 selected_exact_manifest_revision_precision=True,changed_revision_and_legacy_precision_refused=True,
                 actual_paired_causal_fp64_masked_fp32=True,la_yield_resume=True,complete_la_collection=True,mixed_la_precision_refused=True)
    if verifying:
        if read(root/'FIXTURE.json')!=receipt:raise ValueError('Selected-reader proof changed')
        return dict(verified=True,complete_selection_and_paired_reader_replay=True)
    write_equal(root/'FIXTURE.json',receipt);return dict(status='complete',fixture_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
if __name__=='__main__':
    import argparse
    from threadpoolctl import threadpool_limits
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--verify',action='store_true');a=p.parse_args();began=time.process_time()
    with threadpool_limits(limits=2):value=(verify if a.verify else execute)(a.output,{}, {})
    write_equal(Path(a.output)/('NATIVE_VERIFY_CPU.json' if a.verify else 'NATIVE_EXECUTE_CPU.json'),dict(cpu_seconds=time.process_time()-began))
    print(json.dumps(value))
