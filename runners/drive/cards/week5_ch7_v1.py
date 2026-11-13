"""Counted CH7 consumer: complete original histories, player bootstrap and null.

DESIGN CHECK: preserve fixed source cohorts and every invalid fit/draw. A cached
execute unit needs an authenticated new-attempt copy; verification recomputes
the complete source and all 2,000/20 draws in a fresh private workspace.
"""
from pathlib import Path
from collections import Counter
import hashlib
import io
import json
import math
import sqlite3
import time
import numpy as np

from . import week5_ch7_math_v1 as m
from . import week5_ch7_source_v1 as source_adapter
from . import week5_ch_pipeline_checkpoint as ck
from . import week5_ch_models as legacy_math
from .week5_ch_history_index import HistoryStore
from .week5_ch_source import digest,write_json

KINDS=('recent','window_slope','new_best','pace','provisional_start')


def identity(inputs,config):
    allowed={'draws','null_draws','floor','constructed_fixture','max_new_draws'}
    if set(config)-allowed:raise ValueError('Unknown CH7 configuration')
    fixture=bool(config.get('constructed_fixture'))
    draws=config.get('draws',2000);null=config.get('null_draws',20);floor=config.get('floor',3000)
    if any(type(v) is not int or v<1 for v in (draws,null,floor)):
        raise ValueError('Integral positive CH7 bounds required')
    if null!=20 or (not fixture and (draws!=2000 or floor!=3000)):
        raise ValueError('Frozen CH7 resampling or case floor changed')
    if set(inputs)!=({'histories'} if fixture else {'histories','index','source_seal'}):
        raise ValueError('Complete independently verified CH7 history projection required')
    return ck.binding(inputs,config,dict(adapter=digest(__file__),math=digest(m.__file__),
        source=digest(source_adapter.__file__),legacy_math=digest(legacy_math.__file__)))


class Work:
    def __init__(self,output,request_root,inputs,config,operation):
        self.output=Path(output);self.output.mkdir(parents=True,exist_ok=True)
        self.root=Path(request_root);self.bound=identity(inputs,config);self.operation=operation
        self.path=self.output/'CH7_CHECKPOINT.json';self.values={};self.new=0;self.times={}
        self.quantum=config.get('max_new_draws') if operation=='execute' else None
        if self.path.exists():
            if operation!='execute':raise ValueError('Fresh verifier workspace must be empty')
            ck.copied(self.path,self.root,lambda:ck.require(self.root))
            record=json.loads(self.path.read_text())
            if record['binding']!=self.bound:raise ValueError('CH7 checkpoint controls changed')
            self.values=record['values']
        self.database=self.output/'PRIVATE_CH7_CACHE.sqlite'
        if self.database.exists():ck.copied(self.database,self.root,lambda:ck.require(self.root))
        self.con=sqlite3.connect(self.database)
        self.con.execute('CREATE TABLE IF NOT EXISTS players(player TEXT PRIMARY KEY,metadata TEXT,payload BLOB)')
        self.con.execute('CREATE TABLE IF NOT EXISTS null_parameters(player TEXT,controls TEXT,payload TEXT,PRIMARY KEY(player,controls))')
        self.con.commit()
    def check(self):
        ck.require(self.root)
        if self.quantum is not None and self.new>=self.quantum:
            self.save();raise ck.YieldRequested('Complete CH7 player/draw checkpoint quantum')
    def save(self):
        self.con.commit()
        write_json(self.path,dict(binding=self.bound,values=self.values),mutable=True)
    def progress(self,label,done,total):
        self.new+=1
        start,new=self.times.setdefault(label,[time.process_time(),0]);self.times[label][1]+=1
        record=dict(operation=self.operation,phase=label,completed=done,total=total,new_this_invocation=self.times[label][1],
            invocation_phase_cpu_seconds=time.process_time()-start,population_complete=False,
            five_percent_cpu_fraction_claim=False)
        write_json(self.output/'PROGRESS.json',record,mutable=True)
        if done>=math.ceil(total*.05):
            for name in ('PILOT.json','PILOT_'+label.upper()+'.json'):
                if not (self.output/name).exists():
                    write_json(self.output/name,dict(record,basis='First complete unit crossing 5% of this source/player or draw loop; setup/replay remain charged.'))
    def value(self,label,index,total,compute):
        self.check();series=self.values.setdefault(label,[])
        if index<len(series):return series[index]
        if index!=len(series):raise ValueError('Nonconsecutive CH7 draw')
        value=compute();series.append(value);self.progress(label,index+1,total);self.save()
        return value
    def player(self,name,games,done,total):
        self.check()
        existing=self.con.execute('SELECT metadata,payload FROM players WHERE player=?',(name,)).fetchone()
        if existing:return json.loads(existing[0])
        data=m.player_data(games())
        metadata={key:data[key] for key in ('sessions','counts')}
        binary=io.BytesIO();np.savez_compressed(binary,rows=data['rows'],trace=data['trace'])
        self.con.execute('INSERT INTO players VALUES(?,?,?)',(name,json.dumps(metadata,sort_keys=True),binary.getvalue()))
        self.con.commit();self.progress('source_players',done,total);self.save()
        return metadata
    def load(self,name):
        self.check()
        metadata,payload=self.con.execute('SELECT metadata,payload FROM players WHERE player=?',(name,)).fetchone()
        with np.load(io.BytesIO(payload),allow_pickle=False) as arrays:
            return dict(json.loads(metadata),rows=arrays['rows'],trace=arrays['trace'])
    def null_fit(self,name,data,controls,done,total):
        self.check();key=json.dumps(list(controls))
        prior=self.con.execute('SELECT payload FROM null_parameters WHERE player=? AND controls=?',(name,key)).fetchone()
        if prior:return json.loads(prior[0])
        try:result=dict(fit=m.fit_null(data,controls))
        except ValueError as exc:result=dict(unsupported=str(exc))
        self.con.execute('INSERT INTO null_parameters VALUES(?,?,?)',(name,key,json.dumps(result,sort_keys=True)))
        self.con.commit();self.progress('own_null_parameters',done,total);self.save()
        return result
    def close(self):self.con.close()


def authenticate(inputs,config,root):
    paths={key:ck.checked(value,lambda:ck.require(root)) for key,value in inputs.items()}
    if not config.get('constructed_fixture'):
        index=json.loads(paths['index'].read_text());seal=json.loads(paths['source_seal'].read_text())
        if (not index.get('complete') or index.get('constructed_fixture') or
            seal['files'].get('PRIVATE_PLAYER_HISTORY.sqlite')!=inputs['histories']['sha256'] or
            seal['files'].get('INDEX.json')!=inputs['index']['sha256'] or
            seal['binding']['config'].get('ch7_projection_sha256')!=digest(source_adapter.__file__)):
            raise ValueError('CH7 source projection is incomplete or differently bound')
    return paths['histories']


def estimate(statistics,weights=None):
    try:
        beta=m.coefficients(statistics,weights)
        return dict(coefficients=beta.tolist(),contrast=m.contrast(beta) if statistics['kind'] in ('recent','pace','provisional_start') else None)
    except ValueError as exc:return dict(invalid=True,reason=str(exc))


def intervals(values,kind,point):
    valid=[value[kind] for value in values if not value[kind].get('invalid')]
    invalid=len(values)-len(valid)
    result=dict(point=point,draws=len(values),invalid_draws=invalid,interval=None)
    if invalid or not values:return result
    betas=np.asarray([item['coefficients'] for item in valid])
    result['coefficient_intervals']=np.quantile(betas,[.025,.975],axis=0).T.tolist()
    if point.get('contrast') is not None:
        contrasts=np.asarray([item['contrast'] for item in valid]);result['interval']=np.quantile(contrasts,[.025,.975]).tolist()
        result['bootstrap_se']=float(np.std(contrasts,ddof=1)) if len(contrasts)>1 else None
    else:
        result['interval']=result['coefficient_intervals'][0]
        result['bootstrap_se']=float(np.std(betas[:,0],ddof=1)) if len(betas)>1 else None
    return result


def analyze(data,work,config):
    floor=config.get('floor',3000);draws=config.get('draws',2000)
    blitz=[name for name,meta in data.items() if meta['sessions'].get('blitz',0)>=5]
    controls=(0,) if len(blitz)>=floor else (0,1)
    selected=blitz if len(blitz)>=floor else [name for name,meta in data.items() if sum(meta['sessions'].get(tc,0) for tc in m.CONTROLS)>=5]
    counts=Counter()
    for value in data.values():counts.update(value['counts'])
    counts.update(source_players=len(data),blitz_five_session_players=len(blitz),selected_players=len(selected))
    above=len(selected)>=floor
    if len(selected)<2:
        return dict(card='CH7',status='unsupported',reason='Fewer than two eligible five-session players',counts=dict(counts),verdict='inconclusive')
    blocks=[];datasets=[];null_fits=[];null_errors=Counter()
    for index,name in enumerate(selected):
        datum=work.load(name);allowed=np.isin(datum['rows'][:,m.TC],controls)
        blocks.append(datum['rows'][allowed]);datasets.append(datum)
        fitted=work.null_fit(name,datum,controls,index+1,len(selected))
        if 'fit' in fitted:null_fits.append(fitted['fit'])
        else:null_fits.append(None);null_errors[fitted['unsupported']]+=1
    statistics={};unsupported={};point={}
    for kind in KINDS:
        try:
            statistics[kind]=dict(m.sufficient_blocks(blocks,kind),kind=kind)
            point[kind]=estimate(statistics[kind])
            if point[kind].get('invalid'):unsupported[kind]=point[kind]['reason'];statistics.pop(kind)
        except ValueError as exc:unsupported[kind]=str(exc)
    if 'recent' not in statistics:
        return dict(card='CH7',status='unsupported',reason=unsupported.get('recent'),counts=dict(counts),verdict='inconclusive',secondary_support=unsupported)
    rng=np.random.default_rng(m.SEED);bootstrap=[]
    for index in range(draws):
        weights=np.bincount(rng.integers(0,len(blocks),len(blocks)),minlength=len(blocks))
        bootstrap.append(work.value('player_bootstrap',index,draws,
            lambda: {kind:estimate(stats,weights) for kind,stats in statistics.items()}))
    null=[]
    if not null_errors:
        for index in range(20):
            def compute(index=index):
                simulated=[]
                for player,(datum,fit) in enumerate(zip(datasets,null_fits)):
                    work.check()
                    seed=np.random.SeedSequence([m.SEED,811,index,player])
                    simulated.append(m.simulate(datum,fit,seed))
                try:
                    stats=m.sufficient_blocks(simulated,'recent')
                    return dict(contrast=m.contrast(m.coefficients(stats)))
                except ValueError as exc:return dict(invalid=True,reason=str(exc))
            null.append(work.value('whole_history_null',index,20,compute))
    stop=float(np.mean(np.concatenate([1-block[:,m.PLAY] for block in blocks])))
    valid_null=[value['contrast'] for value in null if not value.get('invalid')]
    bar=m.working_bar(stop,valid_null)
    estimates={kind:intervals(bootstrap,kind,point[kind]) for kind in statistics}
    for kind,estimate_ in estimates.items():
        stats=statistics[kind]
        estimate_.update(rows=stats['rows'],players_with_rows=stats['players_with_rows'],
                         exact_shared_gain_strata=len(stats['gain_levels']) if stats['gain_levels'] is not None else None)
    primary=estimates['recent'];ci=primary['interval'];slope_ci=primary.get('coefficient_intervals')
    shape=m.pattern(ci,slope_ci[0] if slope_ci else None,slope_ci[1] if slope_ci else None,bar) if above else 'mixed'
    verdict='inconclusive'
    if above and bar is not None and ci is not None:
        if ci[0]>bar:verdict='supports'
        elif ci[1]<0 or (ci[0]>=-bar and ci[1]<=bar):verdict='against'
    se=primary.get('bootstrap_se')
    own_summary=Counter()
    update_scales=[];update_rmse=[]
    for fit in null_fits:
        if fit is None:continue
        for parameters in fit.values():
            update_scales.append(parameters['update_scale']);update_rmse.append(parameters['update_rmse'])
            own_summary['draw_fraction_boundary']+=parameters['draw']['boundary']
            own_summary['constant_playing_on']+='constant' in parameters['play']
    return dict(card='CH7',status='complete' if above and bar is not None else 'below floor, descriptive' if not above else 'null unqualified, descriptive',
        counts=dict(counts),time_control_scope='blitz' if controls==(0,) else 'rapid pooled with blitz; separate control-class sessions/references',
        primary=primary,secondary={k:v for k,v in estimates.items() if k!='recent'},secondary_unsupported=unsupported,
        observed_stop_probability=stop,base_bar=.1*stop,working_bar=bar,pattern=shape,verdict=verdict,
        null=dict(simulations=20,completed=len(null),invalid=20-len(valid_null),own_player_fit_failures=dict(null_errors),
            mean_absolute_contrast=float(np.mean(np.abs(valid_null))) if valid_null else None,
            standard_deviation=float(np.std(valid_null,ddof=1)) if len(valid_null)>1 else None,
            diagnostics=dict(own_summary),positive_update_scale_range=[min(update_scales),max(update_scales)] if update_scales else None,
            median_update_rmse=float(np.median(update_rmse)) if update_rmse else None),
        precision=dict(sees=None if se is None else 2.8*se,supports_at=None if se is None or bar is None else bar+2.8*se,
                       normal_approximation_optimistic=True),
        by_construction=['Rating below session start requires unfavorable rating updates; result/streak terms are included.',
                         'New-best comparison is wins only and shares exact rating-gain strata.',
                         'Window best and first-30-game eligibility carry over months within time-control class.'],
        limitations=['Playing on is not risk-taking itself.','Start-to-start sessions and month-tail censoring preserve CH6 scope.',
                     'Own-player expected-score/draw/positive-update null is approximate, not Glicko-2 or an exact skill-regression null.',
                     'First-observed provisional-size change is a proxy, not authentication of account creation or true lifetime best.',
                     'Pace conditions on an observed next game and measurable positive clock use.','Standing remains under review; no theory is built on this card.'],
        record_kind='claim',theory_tags=['H12-T6'],constructed_fixture=bool(config.get('constructed_fixture')))


def run(output,request_root,inputs,config,operation):
    path=authenticate(inputs,config,request_root)
    work=Work(output,request_root,inputs,config,operation)
    store=HistoryStore(path,bool(config.get('constructed_fixture')))
    try:
        players=list(store);metadata={}
        for index,name in enumerate(players):
            metadata[name]=work.player(name,lambda name=name:store[name],index+1,len(players))
        result=analyze(metadata,work,config)
        write_json(Path(output)/'SCIENCE.json',result);work.save()
        return dict(status='complete',card='CH7',scientific_result_complete=True)
    except ck.YieldRequested as exc:
        work.save();return dict(status='yielded',reason=str(exc),card='CH7')
    finally:store.close();work.close()


def _execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    bound=identity(inputs,config)
    if ck.sealed(output,bound,lambda:ck.require(output)):
        return dict(status='complete',sealed_science_reused=True)
    result=run(output,output,inputs,config,'execute')
    if result['status']=='complete':ck.seal(output,bound,['SCIENCE.json'],lambda:ck.require(output))
    return result


def _verify(output,inputs,config):
    output=Path(output);bound=identity(inputs,config)
    if not ck.sealed(output,bound,lambda:ck.require(output)):raise ValueError('Complete CH7 output required')
    ordinal=1
    while (output/f'independent-{ordinal:04}').exists():ordinal+=1
    independent=output/f'independent-{ordinal:04}'
    result=run(independent,output,inputs,config,'verify')
    if result['status']=='yielded':return result
    if digest(output/'SCIENCE.json')!=digest(independent/'SCIENCE.json'):
        raise ValueError('Full CH7 source/model/null/bootstrap replay differs')
    return dict(verified=True,complete_recalculation=True,source_and_all_null_and_bootstrap_draws_recomputed=True)


def execute(output,inputs,config):
    return ck.guarded(_execute,output,inputs,config)


def verify(output,inputs,config):
    return ck.guarded(_verify,output,inputs,config)
