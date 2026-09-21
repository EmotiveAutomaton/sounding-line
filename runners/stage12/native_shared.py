"""Consume the actual Ghost V19 packets without another sequence-model fit.

DESIGN CHECK: LESSONS 3-5; CONTROLS 3,6. NULL: exact saved outputs and
same-update practice/replay identities reproduce. ALTERNATIVE: schema drift,
corruption, failed capability or nonspecific edits cannot admit a successor.
Capability is separate from selective access and from production competence.
The numeric world port is shared source, not independent biological evidence.
"""
from itertools import product
from pathlib import Path
import gzip,json
import numpy as np
from .common import read,freeze,filehash
from . import native_math as N

TINY='G19-06-tiny-reader-1'
FIXTURE='G19-C1-fixtures-1'
SITES=('G19-C1-alignment-1','G19-C1-alternate-site-1')
PRACTICE='G19-E1-practice-1'
ARMS=('unchanged','learned','random','shuffled','wrong-factor','mean-direction','full-state')


def checked(path,expected,root):
    path=Path(path).resolve();root=Path(root).resolve()
    if not path.is_relative_to(root) or filehash(path)!=expected:
        raise ValueError('shared packet member escaped or changed')


def packet(card,name,pulse):
    manifest=read(card['snapshot']);root=Path(card['snapshot']).parent/name
    if manifest['schema']!='s12.ghost-native-snapshot.1':raise ValueError('unknown snapshot')
    record=manifest['packets'][name]
    for i,(filename,sha) in enumerate(record['files'].items()):
        checked(root/filename,sha,root)
        if i%100==0:pulse(phase='native-input-integrity',packet=name,files=i)
    complete=read(root/'COMPLETE.json');plan=read(root/'PLAN.json')
    checked(root/'PLAN.json',complete['plan_sha256'],root)
    checked(root/'SOURCE.zip',plan['source_archive_sha256'],root)
    for group in ('files','execution_measurements'):
        for filename,sha in complete[group].items():checked(root/filename,sha,root)
    for filename,sha in plan['design'].get('input_files',{}).items():checked(root/'inputs'/filename,sha,root)
    return root,plan['design']


def close(a,b,tol=1e-10):
    a=np.asarray(a);b=np.asarray(b)
    if a.shape!=b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('nonfinite or incompatible replay arrays')
    error=float(np.max(abs(a-b))) if a.size else 0.
    if error>tol:raise ValueError('native semantic replay differs: '+str(error))
    return error


def rows(path):return json.loads(gzip.decompress(Path(path).read_bytes()))


def public(path):
    r=N.arrays(path)
    if set(r)!={'codes','novel'}:raise ValueError('evaluator data at reader boundary')
    return r


def bound_fixture(snapshot,cfg):
    root=Path(snapshot).parent/FIXTURE
    if filehash(root/'COMPLETE.json')!=cfg['fixture_complete_sha256']:
        raise ValueError('alignment parent fixture differs')
    return root


def model_import(out,card,pulse,raw):
    tiny,cfg=packet(card,TINY,pulse);source,fc=packet(card,FIXTURE,pulse)
    owner=read(tiny/'inputs/shared/TINY_SETTINGS.json')
    if (owner['owner']!='Ghost' or owner['combined_allowance']!=2 or
            owner['reserved_settings']!=2 or cfg['tiny_setting_consumption']!=2):
        raise ValueError('shared setting ownership differs')
    child=read(tiny/'CHILD_ACCOUNTING.json')
    if child['exit_code']!=0 or not child['parent_waited'] or not child['native_handle']:
        raise ValueError('fit native accounting absent')
    if set(cfg['train_lineages'])&set(cfg['development_lineages']):raise ValueError('split crossover')
    if any(cfg[k]!=fc[k] for k in ('train_lineages','development_lineages','training_draws','fit_seeds','kinds')):
        raise ValueError('fixture/model roster differs')
    capability=[];max_p=max_h=0.;weights={}
    for draw,seed,kind in product(cfg['training_draws'],cfg['fit_seeds'],cfg['kinds']):
        pulse(phase='frozen-native-model',draw=draw,seed=seed,kind=kind)
        key=f'{draw}-{seed}-{kind}';path=tiny/'neural'/key/'PARAMETERS.npz';a=N.arrays(path)
        if filehash(path)!=filehash(source/'inputs/models'/f'{key}.npz'):raise ValueError('fixture uses different fit')
        weights[key]=filehash(path)
        train=[N.arrays(tiny/'data/reader'/f'train-{draw}-{c}.npz') for c in ('independent','copied')]
        mean=np.concatenate([r['target'][r['novel']] for r in train]).mean(0).reshape(4,8)
        for condition in ('independent','copied'):
            obs=public(tiny/'data/reader'/f'development-{draw}-{condition}.npz')
            ev=N.arrays(tiny/'inputs/evaluator'/f'development-{draw}-{condition}.npz')
            saved=N.arrays(tiny/'neural'/key/f'{condition}.npz')
            h,p=N.reconstruct(a,obs['codes'],obs['novel'],kind)
            max_h=max(max_h,close(h,saved['hidden'],2e-5));max_p=max(max_p,close(p,saved['probabilities'],2e-6))
            close(N.decode(a,h),p,2e-6)
            target=ev['target'].reshape(-1,32,4,8)
            for length in cfg['lengths']:
                t=target[:,length-1];pred=p[:,length-1]
                loss=float(N.loss(t,pred).mean());no=float(N.loss(t,np.broadcast_to(mean,t.shape)).mean());exact=float(N.loss(t,t).mean())
                spread=float(np.mean([pred[ev['ids'][:,0]==lineage].std(0).mean() for lineage in cfg['development_lineages']]))
                passed=no-exact>0 and no-loss>=.02 and no-loss>=.5*(no-exact) and spread>1e-5
                capability.append(dict(draw=draw,seed=seed,kind=kind,condition=condition,length=length,passed=bool(passed)))
    # Rebuild every public fixture forecast and every exact conditional target.
    fixture_cells=[];max_law=0.;forecast_arrays=0
    for split,lineages in [('train',fc['train_lineages']),('development',fc['development_lineages'])]:
        for lineage in lineages:
            pulse(phase='native-reference-and-fixtures',split=split,lineage=lineage)
            laws=N.arrays(source/'evaluator'/f'{split}-{lineage}-laws.npz')['laws']
            world=N.law(lineage)
            calculated=np.array([[N.endpoint_law(world,m,c) for c in N.CONTEXTS] for m in N.MAKERS])
            max_law=max(max_law,close(calculated,laws,1e-12))
            for draw in fc['training_draws']:
                stem=f'{split}-{lineage}-{draw}';obs=public(source/'reader'/f'{stem}.npz')
                ev=N.arrays(source/'evaluator'/f'{stem}.npz');posterior=np.full((16,16),1/16.)
                if sorted(ev['maker_indices'].tolist())!=list(range(16)):raise ValueError('maker roster differs')
                close(ev['maker'],np.array(N.MAKERS)[ev['maker_indices']],0)
                for j in range(32):
                    codes=obs['codes'][:,j];posterior*=laws[:,codes//8,codes%8].T
                    posterior/=posterior.sum(-1,keepdims=True)
                    close(posterior,ev['posteriors'][:,j]);close(np.einsum('ni,icv->ncv',posterior,laws),ev['conditional'][:,j])
                for seed,kind in product(fc['fit_seeds'],fc['kinds']):
                    key=f'{draw}-{seed}-{kind}';a=N.arrays(source/'inputs/models'/f'{key}.npz')
                    h,p=N.reconstruct(a,obs['codes'],obs['novel'],kind)
                    saved=N.arrays(source/'forecasts'/f'{stem}-{seed}-{kind}.npz')
                    max_h=max(max_h,close(h,saved['hidden']));max_p=max(max_p,close(p,saved['probabilities']));forecast_arrays+=1
                    if split=='development':
                        mean=N.arrays(source/'inputs/means'/f'{draw}.npz')['mean'].reshape(4,8)
                        for length in fc['lengths']:
                            t=ev['conditional'][:,length-1];pred=p[:,length-1]
                            fixture_cells.append(dict(draw=draw,seed=seed,kind=kind,length=length,lineage=lineage,
                                loss=float(N.loss(t,pred).mean()),mean=float(N.loss(t,np.broadcast_to(mean,t.shape)).mean()),
                                exact=float(N.loss(t,t).mean()),spread=float(pred.std(0).mean())))
    challenge=[]
    for draw,seed,kind,length in product(fc['training_draws'],fc['fit_seeds'],fc['kinds'],fc['lengths']):
        rr=[r for r in fixture_cells if (r['draw'],r['seed'],r['kind'],r['length'])==(draw,seed,kind,length)]
        values={k:float(np.mean([r[k] for r in rr])) for k in ('loss','mean','exact','spread')}
        v=values;passed=v['mean']-v['exact']>0 and v['mean']-v['loss']>=.02 and v['mean']-v['loss']>=.5*(v['mean']-v['exact']) and v['spread']>1e-5
        challenge.append(dict(draw=draw,seed=seed,kind=kind,length=length,passed=bool(passed),**values))
    admitted=all(r['passed'] for r in capability+challenge)
    freeze(out/'CAPABILITY.json',dict(original=capability,challenge=challenge,admitted=admitted))
    freeze(out/'MODEL.json',dict(architecture='native-token-GRU38-and-transformer32',weights=weights,fit_owner='Ghost',new_settings=0))
    if admitted:freeze(out/'MODEL_READY.json',dict(status='complete',snapshot_sha256=filehash(card['snapshot'])))
    return dict(status='complete',kind='infrastructure',admitted=admitted,models=len(weights),forecast_arrays=forecast_arrays,
        max_probability_error=max_p,max_hidden_error=max_h,max_reference_error=max_law,
        scope='native model and challenge replay; no new fit, selective access or human claim',
        controls=dict(source_bound=True,sole_fit_owner=True,ordinary_replay=True,reference_replay=True,reader_boundary=True),
        files={p.name:filehash(p) for p in out.glob('*.json') if p.name in ('CAPABILITY.json','MODEL.json','MODEL_READY.json')})


def swap(r,d,q):return r+np.outer((d-r)@q,q)


def composition_controls():
    # Static assignments differ from sequential edits with an undo buffer.
    count=0
    for maker,a,b in product(N.MAKERS,N.MAKERS,N.MAKERS):
        left=list(maker);left[0]=a[0];left[2]=b[2]
        right=list(maker);right[2]=b[2];right[0]=a[0]
        if left!=right:raise ValueError('static assignments do not commute')
        count+=1
    maker=(0,1,0,0);initial=(0,0,0)
    def ordered(ops):
        current=previous=initial
        for op in ops:current,previous=N.execute(current,previous,op,maker),current
        return current
    first=ordered(('edit-claim','repair-evidence'));second=ordered(('repair-evidence','edit-claim'))
    if first==second:raise ValueError('dependent operation control lost order')
    r=np.array([[-1.,-1.]]);d=np.array([[1.,1.]])
    close(swap(swap(r,d,np.array([1.,0.])),d,np.array([0.,1.])),d,0)
    return dict(static_assignments=count,dependent_orders=[first,second],passed=True)


def causal_review(out,card,pulse,raw):
    control=composition_controls();groups=[];scores=0;max_error=0.;probe_count=0
    # The original final-site export keeps cached states only; public histories
    # are in its immutable parent. Verify that parent before resolving them.
    packet(card,FIXTURE,pulse)
    for name in SITES:
        root,cfg=packet(card,name,pulse);site=cfg.get('site','final');source=root/'inputs'
        fixture=bound_fixture(card['snapshot'],cfg)
        raw_rows=rows(root/'raw/alignment_points.json.gz')
        index={(r['draw'],r['seed'],r['kind'],r['lineage'],r['length'],r['factor'],r['change'],r['arm'],r['recipient']):r for r in raw_rows}
        if len(index)!=len(raw_rows):raise ValueError('duplicate scientific row')
        for draw,seed,kind in product(cfg['training_draws'],cfg['fit_seeds'],cfg['kinds']):
            parameters=N.arrays(source/'inputs/models'/f'{draw}-{seed}-{kind}.npz')
            def output(h):return N.decode(parameters,N.final_normalize(parameters,h) if site!='final' else h)
            x=[];labels=[]
            for lineage in cfg['train_lineages']:
                stem=f'train-{lineage}-{draw}';obs=public(fixture/'reader'/f'{stem}.npz')
                h,_=N.reconstruct(parameters,obs['codes'],obs['novel'],kind,site)
                x.append(h[:,31]);labels.append(N.arrays(source/'evaluator'/f'{stem}.npz')['maker'])
            x=np.concatenate(x);labels=np.concatenate(labels);directions={}
            for factor in (0,2):
                saved=N.arrays(root/'models'/f'{draw}-{seed}-{kind}-{factor}.npz');y=2*labels[:,factor]-1
                close(saved['training_labels'],y,0)
                xc=x-x.mean(0);penalty=.001*np.mean(np.sum(xc*xc,axis=0)/len(x))+1e-8
                aug=np.vstack((xc,np.sqrt(len(x)*penalty)*np.eye(x.shape[1])))
                beta=np.linalg.lstsq(aug,np.r_[y-y.mean(),np.zeros(x.shape[1])],rcond=None)[0]
                close(beta,saved['beta'],1e-8);close(y.mean()-x.mean(0)@beta,saved['bias'],1e-8)
                close(beta/np.linalg.norm(beta),saved['learned'],1e-8)
                close((x[y==1].mean(0)-x[y==-1].mean(0))/np.linalg.norm(x[y==1].mean(0)-x[y==-1].mean(0)),saved['mean-direction'],1e-9)
                random=N.rng('v19-C1-probe-controls',draw,seed,kind,factor);shuffled=y.copy()
                for i,_ in enumerate(cfg['train_lineages']):shuffled[i*16:(i+1)*16]=random.permutation(y[i*16:(i+1)*16])
                close(shuffled,saved['shuffled_labels'],0)
                sb=np.linalg.lstsq(aug,np.r_[shuffled-shuffled.mean(),np.zeros(x.shape[1])],rcond=None)[0]
                close(sb,saved['shuffled_beta'],1e-8);close(sb/np.linalg.norm(sb),saved['shuffled'],1e-8)
                q=random.normal(size=x.shape[1]);close(q/np.linalg.norm(q),saved['random'],1e-10)
                directions[factor]=saved;probe_count+=1
            for lineage in cfg['development_lineages']:
                pulse(phase='native-causal-replay',site=site,draw=draw,seed=seed,kind=kind,lineage=lineage)
                stem=f'development-{lineage}-{draw}';obs=public(fixture/'reader'/f'{stem}.npz');ev=N.arrays(source/'evaluator'/f'{stem}.npz')
                h,_=N.reconstruct(parameters,obs['codes'],obs['novel'],kind,site);h=h[np.argsort(ev['maker_indices'])]
                makers=np.array(N.MAKERS);laws=N.arrays(source/'evaluator'/f'development-{lineage}-laws.npz')['laws']
                for length,factor,change in product(cfg['lengths'],(0,2),(False,True)):
                    state=h[:,length-1];donor=makers.copy();donor[:,1]=1-donor[:,1]
                    if change:donor[:,factor]=1-donor[:,factor]
                    hybrid=makers.copy();hybrid[:,factor]=donor[:,factor]
                    di=donor@np.array([8,4,2,1]);hi=hybrid@np.array([8,4,2,1]);target=laws[hi];original=output(state)
                    saved=N.arrays(root/'forecasts'/f'{lineage}-{draw}-{seed}-{kind}-{length}-{factor}-{int(change)}.npz')['probabilities']
                    for ai,arm in enumerate(ARMS):
                        q=directions[2-factor]['learned'] if arm=='wrong-factor' else directions[factor].get(arm)
                        altered=state if arm=='unchanged' else state[di] if arm=='full-state' else swap(state,state[di],q)
                        pred=output(altered);max_error=max(max_error,close(pred,saved[ai],1e-9))
                        values=dict(loss=N.loss(target,pred).mean(-1),oracle_loss=N.loss(target,target).mean(-1),
                                    target_tv=(abs(target-pred).sum(-1)/2).mean(-1),prediction_tv=(abs(original-pred).sum(-1)/2).mean(-1))
                        for ri in range(16):
                            r=index.pop((draw,seed,kind,lineage,length,factor,change,arm,ri))
                            if r['donor']!=int(di[ri]) or r['hybrid']!=int(hi[ri]):raise ValueError('counterfactual identity differs')
                            for k,v in values.items():max_error=max(max_error,close(v[ri],r[k],1e-9))
                            scores+=1
        if index:raise ValueError('incomplete causal roster replay')
        # Record complete groups for source review. This never selects a new site
        # or upgrades a peer's exploratory margin into our confirmation gate.
        for kind,factor,change,arm in product(cfg['kinds'],(0,2),(False,True),ARMS):
            rr=[r for r in raw_rows if (r['kind'],r['factor'],r['change'],r['arm'],r['length'])==(kind,factor,change,arm,32)]
            groups.append(dict(site=site,kind=kind,factor=factor,change=change,arm=arm,loss=float(np.mean([r['loss'] for r in rr]))))
    freeze(out/'GROUPS.json',groups);freeze(out/'COMPOSITION_CONTROLS.json',control)
    freeze(out/'SUCCESSOR.json',dict(status='awaiting_selection',joint_selective_admission=False,
        reason='Neither peer packet admits joint purpose/belief access; source replay does not override its scientific gate.',
        learned_composition='blocked',expertise='separate production/replay support only'))
    return dict(status='complete',kind='infrastructure',scores_replayed=scores,probes_replayed=probe_count,max_error=max_error,
        controls=dict(source_bound=True,probe_reconstruction=True,all_rivals_replayed=True,reference_composition=True),
        scope='complete external causal-source replay, not a new fit, confirmation or local-goal recovery',
        files={n:filehash(out/n) for n in ('GROUPS.json','COMPOSITION_CONTROLS.json','SUCCESSOR.json')})


ARTIFACTS=tuple(product(range(2),repeat=3))
INITIAL=(ARTIFACTS.index((0,1,0)),ARTIFACTS.index((1,0,1)))
SUCCESS=np.array([float(a[0]==a[1]==1) for a in ARTIFACTS])
SHAPE=(3,2,8,8,3,8)


def production_kernel(world):
    kernel=np.zeros(SHAPE);actor=(0,1,0,0)
    for step,ctx,ai,pi in product(range(3),range(2),range(8),range(8)):
        choices=list(N.choices(world,actor,ARTIFACTS[ai],step,N.CONTEXTS[ctx*2]))
        for gi,goal in enumerate(N.GOALS):
            pairs=[(op,w) for g,op,w in choices if g==goal];total=sum(w for _,w in pairs)
            for op,w in pairs:
                end=N.execute(ARTIFACTS[ai],ARTIFACTS[pi],op,actor)
                kernel[step,ctx,ai,pi,gi,ARTIFACTS.index(end)]+=w/total
    close(kernel.sum(-1),np.ones(SHAPE[:-1]))
    return kernel


def policy_values(kernel,pi):
    """Evaluate the saved policy unchanged; ties never select a new policy."""
    value=np.zeros((4,2,8,8));value[3]=SUCCESS[None,:,None]
    for step,ctx,ai,previous in product((2,1,0),range(2),range(8),range(8)):
        value[step,ctx,ai,previous]=kernel[step,ctx,ai,previous,pi[step,ctx,ai,previous]]@value[step+1,ctx,:,ai]
    occupancy=np.zeros(SHAPE[:-1]);success=[]
    for ctx,initial in enumerate(INITIAL):
        mass=np.zeros((8,8));mass[initial,initial]=1.;success.append(value[0,ctx,initial,initial])
        for step in range(3):
            after=np.zeros_like(mass)
            for ai,previous in product(range(8),repeat=2):
                goal=pi[step,ctx,ai,previous];occupancy[step,ctx,ai,previous,goal]+=mass[ai,previous]/2
                after[:,ai]+=mass[ai,previous]*kernel[step,ctx,ai,previous,goal]
            mass=after
    return np.array(success),value,occupancy


def check_optimal(kernel,pi,values):
    close(values[3],np.broadcast_to(SUCCESS[None,:,None],values[3].shape))
    for step,ctx,ai,previous in product((2,1,0),range(2),range(8),range(8)):
        action=kernel[step,ctx,ai,previous]@values[step+1,ctx,:,ai]
        close(action.max(),values[step,ctx,ai,previous],1e-12)
        close(action[int(pi[step,ctx,ai,previous])],action.max(),1e-12)


def practice_review(out,card,pulse,raw):
    root,cfg=packet(card,PRACTICE,pulse);records=rows(root/'raw/practice_points.json.gz')
    index={(r['lineage'],r['draw'],r['policy_seed'],r['condition'],r['episodes'],r['arm']):r for r in records}
    if len(index)!=len(records):raise ValueError('duplicate practice row')
    count=0;max_error=0.;transitions=0
    for lineage in cfg['lineages']:
        reference=N.arrays(root/'evaluator'/f'law-{lineage}.npz');kernel=production_kernel(N.law(lineage))
        max_error=max(max_error,close(kernel,reference['kernel'],1e-12))
        check_optimal(kernel,reference['oracle_policy'],reference['oracle_values'])
        oracle,_,oracle_occupancy=policy_values(kernel,reference['oracle_policy'])
        close(oracle,reference['oracle_success']);close(oracle_occupancy,reference['oracle_occupancy'])
        untrained=np.zeros(SHAPE[:-2],dtype=int);baseline,_,_=policy_values(kernel,untrained)
        uniform,_,_=policy_values(np.repeat(kernel.mean(-2,keepdims=True),3,axis=-2),untrained)
        close(baseline,reference['untrained_success']);close(uniform,reference['uniform_success'])
        for draw,seed,condition in product(cfg['training_draws'],cfg['policy_seeds'],('matched-start','restricted-start')):
            pulse(phase='native-practice-replay',lineage=lineage,draw=draw,seed=seed,condition=condition)
            logs={arm:N.arrays(root/'observed'/f'{lineage}-{draw}-{seed}-{condition}-{arm}.npz')['transitions'] for arm in ('active','replay','demonstration')}
            close(logs['active'],logs['replay'],0)
            for arm,log in logs.items():
                if log.shape!=(max(cfg['budgets'])*3,6) or log.dtype.kind not in 'iu':raise ValueError('practice log schema differs')
                counts=np.full(SHAPE,.5);previous_row=None
                for i,row in enumerate(log):
                    if any(v<0 or v>=lim for v,lim in zip(row,SHAPE)):raise ValueError('transition out of range')
                    step,ctx,a,previous,goal,end=map(int,row)
                    if step!=i%3 or ctx!=(0 if condition=='restricted-start' else (i//3)%2):raise ValueError('acquisition distribution differs')
                    if step==0:
                        if a!=INITIAL[ctx] or previous!=a:raise ValueError('initial state differs')
                    elif a!=previous_row[5] or previous!=previous_row[2]:raise ValueError('broken trajectory continuity')
                    if kernel[tuple(row)]<=0:raise ValueError('unsupported native transition')
                    counts[tuple(row)]+=1;previous_row=row;transitions+=1
                    episode=(i+1)//3
                    if step!=2 or episode not in cfg['budgets']:continue
                    stem=f'{lineage}-{draw}-{seed}-{condition}-{episode}-{arm}'
                    saved=N.arrays(root/'models'/f'{stem}.npz');ev=N.arrays(root/'evaluator'/f'{stem}.npz')
                    close(counts,saved['counts'],0)
                    check_optimal(counts/counts.sum(-1,keepdims=True),saved['policy'],saved['learned_values'])
                    success,values,occupancy=policy_values(kernel,saved['policy'])
                    close(values,ev['exact_values']);close(occupancy,ev['policy_occupancy'])
                    r=index.pop((lineage,draw,seed,condition,episode,arm))
                    visited=counts.sum(-1)>4
                    for key,v in dict(success=success.mean(),context_success=success,oracle_success=oracle.mean(),
                                      untrained_success=baseline.mean(),uniform_success=uniform.mean(),
                                      visited_state_goals=visited.sum(),oracle_occupancy_coverage=(oracle_occupancy*visited).sum()/3).items():
                        max_error=max(max_error,close(v,r[key],1e-10))
                    if r['feedback']!=episode*3:raise ValueError('feedback charge differs')
                    count+=1
    if index:raise ValueError('incomplete production review')
    freeze(out/'SOURCE_SCOPE.json',dict(production_and_replay_verified=True,inversion_admitted=False,
        reason='Fixed known actor and assigned production objective; this packet supplies no held-out inversion or observation-degradation cross.',
        scope='shared production support; not the full Stage12 expertise/inversion contrast'))
    return dict(status='complete',kind='infrastructure',tables_replayed=count,transitions=transitions,max_error=max_error,
        controls=dict(source_bound=True,native_kernel=True,exact_ordered_replay=True,full_update_reconstruction=True,
                      saved_policy_valid=True,full_score_replay=True),
        scope='actual shared practice/replay support audited; no new learning or full inversion claim',
        files={'SOURCE_SCOPE.json':filehash(out/'SOURCE_SCOPE.json')})
