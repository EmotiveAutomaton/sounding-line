"""D11 recent-own-fit coefficient on menu acceptance, with partial pooling.

DESIGN CHECK: LESSONS 3-5 and DECISION_TRACES AI/choice discussion read October18.
Predecision all-option mean similarity avoids selected-option leakage. Fixed
regularization defines a descriptive population coefficient, not a held-out
forecast claim. Entire writer clusters are refitted in every bootstrap; copied
writer likelihoods and penalties both multiply. Noise, planted and reversed
worlds must recover their signs. Constant own-fit, empty history and insufficient
writer support cannot become scientific nulls. Later-text comparison is separate.
"""
from collections import Counter,defaultdict
from pathlib import Path
import copy
import math
import time
import numpy as np
from sklearn.decomposition import PCA
from . import states_v2 as states
from . import menus_d11_sources as source
from . import menus_d11_stats as stats
from . import menus_d12 as intervals
from . import menus_p4 as d1
from .events_p5 import Encoder
from .menus_io import read,write,sha256,input_hashes,assert_equal

CONFIG=dict(seed=20261018,bootstrap=2000,minimum_writers=4,maximum_undefined_fraction=.05,
            threads=2,batch_size=16,pca_dimensions=16,fixed_ridge=.01,intercept_ridge=.25,slope_ridge=1.,
            max_iterations=100,gradient_tolerance=1e-7,checkpoint_draws=25)


def seal(path,value):
    write(path,value);write(path.with_suffix('.seal.json'),dict(sha256=sha256(path)))


def sealed(path):
    if sha256(path)!=read(path.with_suffix('.seal.json'))['sha256']:raise ValueError('changed D11 checkpoint')
    return read(path)


def encode_rows(rows,encoder):
    texts=sorted({text for r in rows for text in (r['history'],r['prompt_text'],r['later_sentence']) if text})
    vectors,scope=encoder.encode(texts);lookup={text:(v,s) for text,v,s in zip(texts,vectors,scope)}
    for r in rows:
        mean=np.asarray(r['menu_mean_vector']);prompt=lookup[r['prompt_text']][0]
        r['prompt_fit']=float(mean@prompt)
        r['own_fit']=float(mean@lookup[r['history']][0]) if r['history'] else None
        r['embedding_visibility']={name:lookup[r[name]][1] for name in ('history','prompt_text','later_sentence') if r[name]}
        r['later_fit']=None
        if r['later_sentence'] and (r['handling']=='dismiss' or r['accepted_vector'] is not None):
            option=mean if r['handling']=='dismiss' else np.asarray(r['accepted_vector'])
            r['later_fit']=float(option@lookup[r['later_sentence']][0])
    return rows


def design(data,rows,config,projection=None):
    sessions=copy.deepcopy(list(data['sessions'].values()))
    for s in sessions:
        for r in s['rows']:r['session_end']=s['end_at']
    ordered,base,scalar,embedding=d1.prefix_features(sessions,list(data['features'].values()),data['vectors'])
    by_key={r['key']:r for r in rows};selected=np.array([i for i,r in enumerate(ordered) if by_key[r['key']]['history_count']>0],int)
    observations=[by_key[ordered[i]['key']] for i in selected]
    if len(observations)<3:raise ValueError('insufficient prior-text observations')
    if projection is None:
        k=min(config['pca_dimensions'],len(selected)-1,embedding.shape[1])
        pca=PCA(n_components=k,svd_solver='randomized',random_state=config['seed']).fit(embedding[selected])
        projection=dict(pca_mean=pca.mean_.tolist(),pca_components=pca.components_.tolist())
    transformed=(embedding-np.asarray(projection['pca_mean']))@np.asarray(projection['pca_components']).T
    own=np.asarray([r['own_fit'] for r in observations]);center=float(own.mean())
    extras=np.array([[r['prompt_fit'],math.log1p(r['history_count'])] for r in observations])
    covariates=np.c_[base[selected,1:],scalar[selected],transformed[selected],extras]
    mean=covariates.mean(axis=0);sd=covariates.std(axis=0);keep=np.flatnonzero(sd>1e-10)
    covariates=(covariates[:,keep]-mean[keep])/sd[keep]
    if own.std()<1e-8:raise ValueError('own-fit is constant')
    # A ridge must not manufacture identification when own-fit is a duplicate.
    rival=np.c_[np.ones(len(own)),covariates]
    if np.linalg.norm(own-rival@np.linalg.lstsq(rival,own,rcond=1e-10)[0])<1e-8*np.linalg.norm(own-center):
        raise ValueError('own-fit is aliased with frozen nuisance features')
    x=np.c_[np.ones(len(own)),own-center,covariates]
    writer_names=sorted({r['writer'] for r in observations});lookup={w:i for i,w in enumerate(writer_names)}
    group=np.asarray([lookup[r['writer']] for r in observations]);y=np.asarray([r['handling']=='accept' for r in observations],float)
    rng=np.random.default_rng(config['seed']+701)
    for session in sorted(sessions,key=lambda s:s['session']):
        labels=rng.permutation([r['handling'] for r in session['rows']])
        for r,label in zip(session['rows'],labels):r['handling']=str(label)
    shuffled,sb,ss,_=d1.prefix_features(sessions,list(data['features'].values()),data['vectors'])
    if [r['key'] for r in shuffled]!=[r['key'] for r in ordered]:raise ValueError('shuffle changed feature ordering')
    sc=np.c_[sb[selected,1:],ss[selected],transformed[selected],extras]
    sx=np.c_[np.ones(len(own)),own-center,(sc[:,keep]-mean[keep])/sd[keep]]
    sy=np.asarray([shuffled[i]['handling']=='accept' for i in selected],float)
    return dict(x=x,y=y,control_x=sx,control_y=sy,group=group,own=own-center,weights=stats.observation_weights(observations),
        writers=writer_names,rows=observations,projection=projection,scaling=dict(own_center=center,nuisance_mean=mean.tolist(),
        nuisance_sd=sd.tolist(),retained_nuisance_columns=keep.tolist()),excluded_no_history=len(rows)-len(observations))


def later_comparison(rows,config):
    sessions=defaultdict(lambda:defaultdict(list))
    for r in rows:
        if r['later_fit'] is not None and r['handling'] in ('accept','dismiss'):
            sessions[(r['writer'],r['session'])][r['handling']].append(r['later_fit'])
    writers=defaultdict(list)
    for (writer,_),classes in sorted(sessions.items()):
        if classes['accept'] and classes['dismiss']:writers[writer].append(float(np.mean(classes['accept'])-np.mean(classes['dismiss'])))
    values=np.asarray([np.mean(v) for _,v in sorted(writers.items())]);rng=np.random.default_rng(config['seed']+2)
    draws=[float(np.mean(values[rng.integers(len(values),size=len(values))])) for _ in range(config['bootstrap'])] if len(values) else []
    point=float(values.mean()) if len(values)>=config['minimum_writers'] else None
    return dict(contrast=intervals.interval(point,draws,config),writers=len(values),
        scope='Explicitly later-text descriptive: uniquely accepted original suggestion vs mean dismissed menu cosine with the next complete newly self-typed sentence; paired within session, then equal writers. Not a causal or predecision feature.')


def fit_one(data,config,arm,copies=None,start=None):
    x,y=(data['x'],data['y']) if arm=='primary' else (data['control_x'],data['control_y'])
    return stats.fit(x,y,data['group'],data['own'],data['weights'],config,copies,start)


def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);started=time.perf_counter()
    binding=dict(inputs=input_hashes(inputs),config=config)
    if (output/'BINDING.json').exists():assert_equal(read(output/'BINDING.json'),binding)
    else:write(output/'BINDING.json',binding)
    if (output/'SUMMARY.json').exists():verify(output,inputs,config);return read(output/'SUMMARY.json')
    sources=source.common.load(inputs);rows=[];session_hashes={};encoder=None
    for sid in sorted(sources['sessions']):
        if (output/'YIELD_REQUEST.json').exists():return dict(status='yielded',saved_sessions=len(session_hashes))
        path=output/'sessions'/(sid+'.json')
        if path.exists():saved=sealed(path);assert_equal(saved['binding'],binding)
        else:
            extracted,pins=source.extract(sources,sid)
            if encoder is None:encoder=Encoder(inputs['content_model'],config['threads'],config['batch_size'])
            saved=dict(binding=binding,rows=encode_rows(extracted,encoder),source_pins=pins);seal(path,saved)
        rows.extend(saved['rows']);session_hashes[path.relative_to(output).as_posix()]=sha256(path)
    projection=read(output/'PROJECTION.json') if (output/'PROJECTION.json').exists() else None
    try:data=design(sources,rows,config,projection)
    except ValueError as exc:
        report=dict(card='D11',descriptive=True,scientific_admission=False,state='invalid',primary=intervals.interval(None,[],config),
            invalid_design=str(exc),config=config,input_hashes=binding['inputs'],session_hashes=session_hashes)
        write(output/'SUMMARY.json',report);return report
    if projection is None:write(output/'PROJECTION.json',data['projection'])
    if len(data['writers'])<config['minimum_writers'] or len(set(data['y']))<2:raise ValueError('insufficient coefficient support')
    design_info=dict(keys=[r['key'] for r in data['rows']],writers=data['writers'],scaling=data['scaling'],
                     excluded_no_history=data['excluded_no_history'])
    if (output/'DESIGN.json').exists():assert_equal(read(output/'DESIGN.json'),design_info)
    else:write(output/'DESIGN.json',design_info)
    arms={};hashes={};completed=0
    for arm in ('primary','outcome_control'):
        path=output/(arm+'-fit.json')
        if path.exists():point=sealed(path)
        else:point=fit_one(data,config,arm);seal(path,point)
        draws=[]
        for start in range(0,config['bootstrap'],config['checkpoint_draws']):
            if (output/'YIELD_REQUEST.json').exists():return dict(status='yielded',completed_draws=completed)
            path=output/'draws'/f'{arm}-{start:04d}.json';stop=min(start+config['checkpoint_draws'],config['bootstrap'])
            if path.exists():saved=sealed(path);assert_equal(saved['binding'],binding)
            else:
                batch=[]
                for number in range(start,stop):
                    rng=np.random.default_rng(config['seed']+10000+number);index=rng.integers(len(data['writers']),size=len(data['writers']))
                    copies=np.bincount(index,minlength=len(data['writers']))
                    try:
                        fitted=fit_one(data,config,arm,copies,point)
                        batch.append(dict(coefficient=fitted['beta'][1],gap=fitted['gradient_gap'],iterations=fitted['iterations'],valid=True))
                    except ValueError as exc:batch.append(dict(coefficient=None,valid=False,reason=str(exc)))
                saved=dict(binding=binding,arm=arm,start=start,stop=stop,draws=batch);seal(path,saved)
            if (saved['arm'],saved['start'],saved['stop'],len(saved['draws']))!=(arm,start,stop,stop-start):raise ValueError('D11 draw coverage differs')
            draws.extend(saved['draws']);hashes[path.relative_to(output).as_posix()]=sha256(path);completed+=stop-start
            if completed>=math.ceil(.1*2*config['bootstrap']) and not (output/'FIRST_TENTH.json').exists():
                elapsed=time.perf_counter()-started;write(output/'FIRST_TENTH.json',dict(completed_draws=completed,total_draws=2*config['bootstrap'],
                    elapsed_seconds=elapsed,projected_seconds=elapsed*2*config['bootstrap']/completed))
        arms[arm]=dict(primary=intervals.interval(point['beta'][1],[r['coefficient'] for r in draws],config),
            point=point,fit_failures=dict(Counter(r.get('reason') for r in draws if not r['valid'])))
    if (output/'YIELD_REQUEST.json').exists():return dict(status='yielded',completed_draws=completed)
    primary=arms['primary']['primary']
    report=dict(card='D11',descriptive=True,scientific_admission=False,primary=primary,state=primary['state'],arms=arms,
        input_hashes=binding['inputs'],config=config,session_hashes=session_hashes,draw_hashes=hashes,design=design_info,
        projection_hash=sha256(output/'PROJECTION.json'),later_text=later_comparison(rows,config),
        estimand='Population log-odds coefficient per unit mean own-fit cosine in an all-record descriptive partial-pooling logistic model; accept class versus the other handling classes. No held-out forecast claim.',
        method='Frozen D1 predecision feature recipe; sixteen unsupervised embedding PCs; mean prompt-fit and log1p prior-word count. Own-fit uses last50 completed produced words strictly before menu opening, all available if fewer, zero-history excluded. All offered options averaged.',
        objective='Equal writers then sessions then decisions, likelihood weights sum to number of observations. Population ridge .01 except intercept; writer-intercept ridge .25 and centered-own-fit slope ridge1. Own-fit only centered, nuisance columns centered/scaled; constants dropped before outcomes.',
        uncertainty='Full writer-node bootstrap refits population and writer conditional modes. Both likelihood and writer penalty multiplied for duplicate copies. Fixed-design permutation control rebuilds D1 handling-history covariates.',
        extension='Between-writer slope spread remains a separately gated/null-calibrated extension; no spread statistic or specificity claim from this primary.')
    write(output/'SUMMARY.json',report);return report


def verify(output,inputs,config):
    output=Path(output);report=read(output/'SUMMARY.json');binding=dict(inputs=input_hashes(inputs),config=config)
    assert_equal(report['input_hashes'],binding['inputs']);assert_equal(report['config'],config);sources=source.common.load(inputs);rows=[]
    for sid in sorted(sources['sessions']):
        path=output/'sessions'/(sid+'.json')
        if sha256(path)!=report['session_hashes'][path.relative_to(output).as_posix()]:raise ValueError('changed D11 session')
        saved=read(path);extracted,pins=source.extract(sources,sid)
        actual=[{k:v for k,v in r.items() if k not in ('own_fit','prompt_fit','later_fit','embedding_visibility')} for r in saved['rows']]
        assert_equal(actual,extracted);assert_equal(pins,saved['source_pins']);rows.extend(saved['rows'])
    if 'invalid_design' in report:
        try:design(sources,rows,config)
        except ValueError as exc:assert_equal(str(exc),report['invalid_design'])
        else:raise ValueError('invalid D11 design no longer fails')
        return dict(verified=True,primary_recomputed=report['primary'],state='invalid')
    if sha256(output/'PROJECTION.json')!=report['projection_hash']:raise ValueError('changed D11 projection')
    data=design(sources,rows,config,read(output/'PROJECTION.json'))
    assert_equal(dict(keys=[r['key'] for r in data['rows']],writers=data['writers'],scaling=data['scaling'],excluded_no_history=data['excluded_no_history']),report['design'])
    for arm in ('primary','outcome_control'):
        point=sealed(output/(arm+'-fit.json'));certified=fit_one(data,config,arm,start=point)
        if certified['beta']!=point['beta']:raise ValueError('saved point is not at certified mode')
        draws=[]
        for start in range(0,config['bootstrap'],config['checkpoint_draws']):
            name=f'draws/{arm}-{start:04d}.json'
            if sha256(output/name)!=report['draw_hashes'][name]:raise ValueError('changed D11 draw')
            saved=read(output/name);assert_equal(saved['binding'],binding);draws.extend(saved['draws'])
        assert_equal(intervals.interval(point['beta'][1],[r['coefficient'] for r in draws],config),report['arms'][arm]['primary'])
    assert_equal(later_comparison(rows,config),report['later_text']);assert_equal(report['primary'],report['arms']['primary']['primary'])
    return dict(verified=True,primary_recomputed=report['primary'],state=report['state'],source_histories_replayed=True,point_certified=True)
