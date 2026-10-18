"""D12: session split reliability of selected raw producer scores.

DESIGN CHECK: LESSONS 3-5, TTI 6 and READER_HEURISTICS 9-10 read 2026-10-18.
NULL: independent uniform menu selections or shuffled even-half writer labels
have no persistent writer correlation. ALTERNATIVE: stable high/low raw-score
selection gives positive correlation; reversed halves give negative correlation.
Constant halves, insufficient writers and >5% undefined bootstrap draws are
invalid, never a null. Shared states_v2 supplies exhaustive directional bands.
The field named probability has UNKNOWN backend semantics. Standardization and
ranks are of the unchanged finite raw score, never probabilities or log losses.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import hashlib
import json
import math
import time
import numpy as np
from scipy.stats import rankdata

from .menus_io import read, write, sha256, input_hashes, assert_equal
from . import states_v2 as states

CONFIG = dict(seed=20261018, bootstrap=2000, permutations=1000,
              minimum_writers=4, maximum_undefined_fraction=.05)


def authenticate(inputs):
    complete = Path(inputs['p8_complete']); receipt = read(complete)
    if receipt.get('status') != 'COMPLETE':
        raise ValueError('P8 incomplete')
    for path in (Path(inputs['p8']), complete.parent/'PLAN.json'):
        relative = path.resolve().relative_to(complete.parent.resolve()).as_posix()
        if receipt['outputs'].get(relative) != sha256(path):
            raise ValueError('P8 output binding differs')
    plan = read(complete.parent/'PLAN.json')
    if plan['pins'].get(str(Path(inputs['sessions']).resolve())) != sha256(inputs['sessions']):
        raise ValueError('P8 session binding differs')


def load(inputs):
    authenticate(inputs)
    sessions = read(inputs['sessions'])
    with Path(inputs['p8']).open(encoding='utf8') as stream:
        producer = [json.loads(line) for line in stream]
    return sessions, producer


def prepare(sessions, producer):
    by_key = defaultdict(list)
    for row in producer:
        by_key[row['key']].append(row)
    ordered = defaultdict(list); seen_sessions = set(); seen_keys = set()
    for session in sessions:
        if session['session'] in seen_sessions:
            raise ValueError('duplicate session')
        seen_sessions.add(session['session']); ordered[session['writer']].append(session)
        for row in session['rows']:
            if row['key'] in seen_keys:
                raise ValueError('duplicate decision')
            seen_keys.add(row['key'])
            scores = sorted(by_key[row['key']], key=lambda p:p['position'])
            if (row['writer'] != session['writer'] or row['session'] != session['session']
                or [p['position'] for p in scores] != list(range(len(row['menu'])))
                or len({p['suggestion_index'] for p in scores}) != len(scores)
                or any(p['writer'] != row['writer'] or p['session'] != row['session']
                       or p['ordinal'] != row['ordinal'] for p in scores)):
                raise ValueError('P8 menu identity or coverage differs')
            for p in scores:
                value = p['logged_score']
                if value is not None and (isinstance(value, bool) or not math.isfinite(value)):
                    raise ValueError('nonfinite raw score')
    if seen_keys != set(by_key):
        raise ValueError('P8 decision coverage differs')
    return {w:sorted(v,key=lambda s:(s['timestamp'],s['session'])) for w,v in sorted(ordered.items())}, by_key


def writer_rows(writer, sessions, by_key, seed):
    result=[]; exclusions=Counter()
    for ordinal, session in enumerate(sessions):
        for row in sorted(session['rows'], key=lambda r:(r['ordinal'],r['key'])):
            record=dict(key=row['key'], writer=writer, session=session['session'],
                        session_ordinal=ordinal, half=ordinal%2, handling=row['handling'],
                        accepted=int(row['handling']=='accept'), selected=False)
            if row['handling'] not in ('accept','edit'):
                exclusions['no_observed_selection']+=1
            elif len(row['menu'])<2:
                exclusions['single_option']+=1
            else:
                matches=[i for i,text in enumerate(row['menu']) if text==row['inserted']]
                values=[p['logged_score'] for p in sorted(by_key[row['key']],key=lambda p:p['position'])]
                if len(matches)!=1:
                    exclusions['ambiguous_or_absent_selected_text']+=1
                elif any(v is None for v in values):
                    exclusions['menu_has_missing_score']+=1
                else:
                    values=np.asarray(values,float); scale=float(values.std(ddof=0))
                    if scale==0:
                        exclusions['constant_score_menu']+=1
                    else:
                        chosen=matches[0]; z=(values-values.mean())/scale
                        rank=rankdata(-values,method='average')
                        rng=np.random.default_rng(int.from_bytes(hashlib.sha256(
                            f'{seed}:{row["key"]}'.encode()).digest()[:8],'little'))
                        uniform=int(rng.integers(len(values)))
                        record.update(selected=True, size=len(values), chosen=chosen,
                            raw_scores=values.tolist(), standardized_selected=float(z[chosen]),
                            uniform_selected=float(z[uniform]), uniform_choice=uniform,
                            selected_rank=float(rank[chosen]), favorite=bool(values[chosen]==values.max()),
                            least=bool(values[chosen]==values.min()),
                            favorite_ties=int(np.sum(values==values.max())),
                            least_ties=int(np.sum(values==values.min())))
            result.append(record)
    return dict(writer=writer,rows=result,exclusions=dict(exclusions))


def correlation(x,y):
    x=np.asarray(x,float); y=np.asarray(y,float)
    x=x-x.mean();y=y-y.mean();den=float(np.linalg.norm(x)*np.linalg.norm(y))
    return float(np.clip(x@y/den,-1,1)) if den>1e-14 else None


def interval(point, draws, config):
    good=np.asarray([v for v in draws if v is not None],float)
    invalid=len(draws)-len(good)
    if point is None or invalid>config['maximum_undefined_fraction']*len(draws) or len(good)<2:
        return dict(effect=point,ci95=[None,None],standard_error=None,p_approx=None,
                    state='invalid',undefined_draws=invalid,draws=len(draws))
    low,high=map(float,np.quantile(good,[.025,.975]));se=float(good.std(ddof=1))
    return dict(effect=point,ci95=[low,high],standard_error=se,
        p_approx=math.erfc(abs(point/se)/math.sqrt(2)) if se>0 else None,
        state=states.contrast_state(point,low,high),undefined_draws=invalid,draws=len(draws))


def summarize(units,config):
    profiles=[]; excluded=Counter(); support=[]; census=Counter()
    for unit in sorted(units,key=lambda r:r['writer']):
        excluded.update(unit['exclusions']); halves=[]
        for h in (0,1):
            all_rows=[r for r in unit['rows'] if r['half']==h]
            chosen=[r for r in all_rows if r['selected']]
            halves.append(dict(decisions=len(all_rows),selections=len(chosen),
                score=float(np.mean([r['standardized_selected'] for r in chosen])) if chosen else None,
                uniform=float(np.mean([r['uniform_selected'] for r in chosen])) if chosen else None,
                accept=float(np.mean([r['accepted'] for r in all_rows])) if all_rows else None))
            for r in chosen:
                census['selected']+=1;census['favorite']+=r['favorite'];census['least']+=r['least']
                census['favorite_tied']+=r['favorite_ties']>1;census['least_tied']+=r['least_ties']>1
                if r['size']==5:
                    census['five_item_selected']+=1;census['five_item_favorite']+=r['favorite']
                    census['five_item_least']+=r['least']
        if any(h['score'] is None for h in halves):
            support.append(dict(writer=unit['writer'],reason='no eligible selection in one half'))
        else: profiles.append(dict(writer=unit['writer'],halves=halves))
    n=len(profiles)
    if n<config['minimum_writers']: raise ValueError('insufficient split-half writers')
    arrays={k:np.asarray([[p['halves'][h][k] for h in (0,1)] for p in profiles])
            for k in ('score','uniform','accept')}
    point={k:correlation(v[:,0],v[:,1]) for k,v in arrays.items()}
    rng=np.random.default_rng(config['seed']); draws={k:[] for k in point}; difference=[]
    for _ in range(config['bootstrap']):
        index=rng.integers(n,size=n); current={}
        for k,v in arrays.items():
            current[k]=correlation(v[index,0],v[index,1]);draws[k].append(current[k])
        difference.append(current['score']-current['accept']
                          if current['score'] is not None and current['accept'] is not None else None)
    reports={k:interval(point[k],draws[k],config) for k in point}
    diff=point['score']-point['accept'] if point['score'] is not None and point['accept'] is not None else None
    # Relabel complete even-session halves, retaining each writer's internal data.
    prng=np.random.default_rng(config['seed']+1); permutation=[]
    for _ in range(config['permutations']):
        permutation.append(correlation(arrays['score'][:,0],arrays['score'][prng.permutation(n),1]))
    p_perm=(1+sum(abs(v)>=abs(point['score']) for v in permutation))/(len(permutation)+1) if point['score'] is not None else None
    primary=reports['score']; above=primary.copy()
    above.update(effect=None if primary['effect'] is None else primary['effect']-.3,
                 ci95=[None if v is None else v-.3 for v in primary['ci95']])
    above['state']=states.contrast_state(above['effect'],*above['ci95'])
    above['p_approx']=math.erfc(abs(above['effect']/above['standard_error'])/math.sqrt(2)) if above['effect'] is not None and above['standard_error'] else None
    return dict(primary=primary,state=primary['state'],writers=n,profiles=profiles,
        accept_reliability=reports['accept'],uniform_control=reports['uniform'],
        reliability_minus_accept=interval(diff,difference,config),above_point_three=above,
        writer_label_permutation=dict(p_two_sided=p_perm,draws=permutation),
        excluded= dict(excluded),unsupported_writers=support,census=dict(census),
        semantics='Unchanged raw producer score, standardized within each menu; unknown backend semantics, no probability claim.',
        weighting='Equal writers in correlation; decision-weighted means within odd/even chronological sessions; acceptance comparator uses all decisions of the same eligible writers.',
        uncertainty='Writer-cluster percentile bootstrap; undefined correlations counted; no Spearman-Brown correction.')


def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);started=time.perf_counter()
    binding=dict(inputs=input_hashes(inputs),config=config)
    if (output/'BINDING.json').exists():assert_equal(read(output/'BINDING.json'),binding)
    else:write(output/'BINDING.json',binding)
    if (output/'SUMMARY.json').exists():verify(output,inputs,config);return read(output/'SUMMARY.json')
    sessions,producer=load(inputs);writers,by_key=prepare(sessions,producer);units=[];hashes={}
    for number,(writer,group) in enumerate(writers.items(),1):
        if (output/'YIELD_REQUEST.json').exists():return dict(status='yielded',completed=number-1)
        path=output/'writers'/(hashlib.sha256(writer.encode()).hexdigest()[:24]+'.json')
        if path.exists():
            if sha256(path)!=read(path.with_suffix('.seal.json'))['sha256']:raise ValueError('checkpoint changed')
            saved=read(path);assert_equal(saved['binding'],binding)
        else:
            saved=dict(binding=binding,unit=writer_rows(writer,group,by_key,config['seed']))
            write(path,saved);write(path.with_suffix('.seal.json'),dict(sha256=sha256(path)))
        units.append(saved['unit']);hashes[path.relative_to(output).as_posix()]=sha256(path)
        if number>=max(1,math.ceil(.1*len(writers))) and not (output/'FIRST_TENTH.json').exists():
            elapsed=time.perf_counter()-started
            write(output/'FIRST_TENTH.json',dict(completed_writers=number,total_writers=len(writers),
                elapsed_seconds=elapsed,projected_seconds=elapsed*len(writers)/number))
    if (output/'YIELD_REQUEST.json').exists():return dict(status='yielded',completed=len(writers))
    report=dict(card='D12',descriptive=True,scientific_admission=False,input_hashes=binding['inputs'],
                config=config,writer_hashes=hashes,extension_computed=False,**summarize(units,config))
    write(output/'SUMMARY.json',report);return report


def verify(output,inputs,config):
    output=Path(output);report=read(output/'SUMMARY.json')
    assert_equal(report['input_hashes'],input_hashes(inputs));assert_equal(report['config'],config)
    sessions,producer=load(inputs);writers,by_key=prepare(sessions,producer);units=[]
    expected_names=set()
    for writer,group in writers.items():
        name='writers/'+hashlib.sha256(writer.encode()).hexdigest()[:24]+'.json';expected_names.add(name)
        if report['writer_hashes'].get(name)!=sha256(output/name):raise ValueError('saved writer changed')
        saved=read(output/name);unit=writer_rows(writer,group,by_key,config['seed'])
        assert_equal(saved,dict(binding=dict(inputs=report['input_hashes'],config=config),unit=unit));units.append(unit)
    if expected_names!=set(report['writer_hashes']):raise ValueError('writer coverage differs')
    actual=summarize(units,config);assert_equal(actual,{k:report[k] for k in actual})
    return dict(verified=True,primary_recomputed=actual['primary'],state=actual['state'],source_replayed=True)
