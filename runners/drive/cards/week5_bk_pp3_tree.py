"""Frozen PP3.p1 whole-project tree with authenticated fit checkpoints.

DESIGN CHECK: LESSONS 1d/2/3/4/5; BK_PP3.md. Same trees, source rows,
three-project sample, seeds, banks and bootstrap as the validated cost design.
Known constant/separable cases and fresh full refitting are mandatory. Saved
confusions are private checkpoints, never prefix scientific results.
"""
from pathlib import Path
import json,time
import numpy as np
from threadpoolctl import threadpool_limits
from . import week3_pp3_followups as old
from . import week3_pp3_analysis as model
from .week4_pp3_project_cost import subset,configuration as cost_config
from .week5_bk_klicke_intake import read,write,digest
from .timing_pmap_source import completed
from .timing_p6 import progress


def source(inputs,mode):
    if mode=='constructed':
        if inputs:raise ValueError('Constructed fixture cannot consume human source')
        return subset(old.wide_fixture())
    if set(inputs)!={'cost_complete'}:raise ValueError('Reviewed source cost completion required')
    c=Path(inputs['cost_complete']).resolve();root=c.parent
    for name in ('PLAN.json','VERIFIED.json','output/PROBE.json','output/FORECAST.json'):completed(c,root/name)
    plan=read(root/'PLAN.json');probe=read(root/'output/PROBE.json')
    if plan['module']!='runners.drive.cards.week4_pp3_project_cost' or plan['config']!=cost_config('cost'):
        raise ValueError('Wrong whole-project source cost contract')
    if not read(root/'VERIFIED.json').get('complete_source_and_timing_replay'):raise ValueError('Independent cost-source replay required')
    if probe['empirical_scores_reported'] or not probe['complete_project_selection']:raise ValueError('Invalid source cost role')
    arrays,_=old.source(plan['inputs'],'main');selected,census=subset(arrays)
    if census!=probe['census']:raise ValueError('Frozen project sample/source membership changed')
    return selected,census


def serialized(record):return {k:v.tolist() for k,v in record.items()}
def restored(record):return {k:np.asarray(v,dtype=float if k=='loss' else np.int64) for k,v in record.items()}


def summarize(real,banks,p,a):
    refs={k:np.array([[r[k] for r in bank] for bank in banks]) for k in real}
    rng=np.random.default_rng(model.CONTRACT['seed']+97);summaries={};primary={};counts=np.bincount(a)
    for kind in ('author','project'):
        weights=model.resample_weights(a,p,kind,rng,2000)
        summaries[kind],null=model.summarize(real,refs,weights,counts)
        draws=old.primary_draws(real,refs,weights,'p');ci=np.quantile(draws,[.025,.975]).tolist()
        point=float(old.primary_draws(real,refs,np.ones((1,len(counts))),'p')[0])
        primary[kind]=dict(effect=point,ci95=ci,state=model.states.contrast_state(point,*ci))
    references=[]
    for bank in range(2):
        for arm in range(2):
            values=null[bank,:,arm];actual=model.f1(real['cm3'][arm].sum(axis=0))
            references.append(dict(bank=bank,arm=arm,mean=float(values.mean()),ci95=np.quantile(values,[.025,.975]).tolist(),
                                   p=float((1+(values>=actual).sum())/(len(values)+1))))
    fifteen=model.f1(refs['cm15'].sum(axis=2));actual15=model.f1(real['cm15'].sum(axis=0))
    return dict(summaries=summaries,primary=primary,references=references,
                fifteen_references=[dict(mean=float(v.mean()),ci95=np.quantile(v,[.025,.975]).tolist(),
                                         p=float((1+(v>=actual15).sum())/(len(v)+1))) for v in fifteen],
                confusion_matrices={k:v.sum(axis=1 if k=='cm3' else 0).tolist() for k,v in real.items() if k!='loss'},
                classes=list(model.CLASSES),categories=list(model.CATEGORIES))


def run(output,inputs,config,verification=False):
    if set(config)!={'card','mode','max_new_draws'} or config['card']!='BK-PP3.p1' or config['mode'] not in ('constructed','corpus') or type(config['max_new_draws']) is not int or config['max_new_draws']<1:
        raise ValueError('Frozen whole-project tree config required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);start=time.process_time()
    with threadpool_limits(limits=1):
        known=old.known_answers('p');(x,c,y,p,a),census=source(inputs,config['mode'])
        binding=dict(mode=config['mode'],census=census,input_sha256={k:digest(v) for k,v in inputs.items()},
                     seed=model.CONTRACT['seed'],permutations_per_bank=200,bootstrap=2000,tree='entropy_depth5_leaf25_seed20261026')
        if (output/'BINDING.json').exists() and read(output/'BINDING.json')!=binding:raise ValueError('Saved scientific contract changed')
        if not verification:write(output/'BINDING.json',binding)
        designs=old.designs(x,c,p,'p',1.);new=0;done=0
        def fit(name,labels):
            nonlocal new,done
            path=output/'fits'/(name+'.json.gz')
            if verification or not path.exists():
                record=old.evaluate(designs,labels,p,a,True);new+=1
                if verification:
                    if read(path)!=serialized(record):raise ValueError('Independent complete tree fit mismatch')
                else:write(path,serialized(record))
            else:record=restored(read(path))
            done+=1
            progress(output/'PROGRESS.json',dict(phase='verify' if verification else 'execute',done=done,total=401,new_fits=new,cpu_seconds=time.process_time()-start))
            if not verification and done==21 and not (output/'PILOT.json').exists():
                write(output/'PILOT.json',dict(completed_fits=21,total_fits=401,fraction=21/401,cpu_seconds=time.process_time()-start,
                                             scope='first five percent fit-cost checkpoint; no empirical summary'))
            if done<401 and ((output/'YIELD_REQUEST.json').exists() or (not verification and new>=config['max_new_draws'])):
                raise InterruptedError('fit_boundary')
            return record
        try:
            real=fit('real',y);banks=[]
            for bank,groups in enumerate((p,a)):
                rng=np.random.default_rng(model.CONTRACT['seed']+bank);records=[]
                for draw in range(200):records.append(fit(f'bank{bank}-{draw:03d}',model.permute(y,groups,rng)))
                banks.append(records)
        except InterruptedError:
            return dict(status='yielded',reason='completed_tree_fit_boundary',completed_units=done,new_fits=new,
                        verification_restarts_all=verification)
        result=summarize(real,banks,p,a)
        result.update(card='PP3.p1',mode=config['mode'],census=census,known_answers=known,source_rows_complete=True,
                      sample_scoped=True,whole_projects=3,source_projects=5,permutations_per_reference=200,bootstrap=2000,
                      descriptive=True,followup_generation=1,scope='Fixed seed-selected three complete ScholaWrite projects; annotations, not unrestricted goals. Few project clusters limit uncertainty.',
                      references_names=['within_project','within_project_author'])
        if verification:
            if read(output/'SUMMARY.json')!=result:raise ValueError('Independent complete tree summary mismatch')
            return dict(verified=True,whole_source_all401fits_and4000bootstrap_replayed=True,new_fits=new)
        write(output/'SUMMARY.json',result)
        return dict(status='complete',new_fits=new,complete_fits=done)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
