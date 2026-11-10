"""SP1 exact separable-group estimator repair; original resamples are retained.

DESIGN CHECK: LESSONS 2?5, CONTROLS 6?7. With separate group intercepts and
slopes, AC/NV estimates do not depend on a nuisance mixed-mode group's rank.
AC or NV rank loss still refuses; no resample is discarded or redrawn.
"""
from pathlib import Path
import json
from .week5_sp import *
from . import week5_sp as original


def estimate(table,card):
    if card!='SP1':raise ValueError('This repair admits only SP1')
    slopes={}
    for group in [AC,NV]:
        data=table.loc[table.cooling.eq(group)].dropna(subset=['weather'])
        x=np.column_stack([np.ones(len(data)),data.weather.to_numpy()])
        if len(data)<2 or np.linalg.matrix_rank(x)<2:return None
        slopes[group]=float(np.linalg.lstsq(x,data.neutral.to_numpy(),rcond=None)[0][1])
    return slopes[NV]-slopes[AC]

def analyse(data,config):
    card=config['phase'];table,exclusions=building_summaries(data,config)
    fallback=False
    if len(table)<20:
        table,exclusions=building_summaries(data,{**config,'allow_small':True});fallback=True
    if table.empty:return {'card':card,'status':'unsupported','exclusions':exclusions,'fallback':'no estimable buildings; descriptive source counts only'}
    if config.get('side')=='hot':table=table.loc[table.weather>=22]
    if config.get('side')=='cold':table=table.loc[table.weather<22]
    if config.get('range_matched'):table=range_match_bins(table) if card=='SP3' else range_match(table)
    point=estimate(table,card)
    record={'card':card,'buildings':len(table),'rows':int(table.n.sum()) if len(table) else 0,'exclusions':exclusions,
            'scope':'descriptive observational buildings; cooling type mixes thermal exposure with personal control',
            'ordinal_latent_units':bool(config.get('ordinal'))}
    if point is None:record['status']='unsupported';return record
    cluster='study' if config.get('cluster')=='study' else 'building'
    groups=[g for _,g in table.groupby(cluster,sort=True)];rng=np.random.default_rng(SEED);draws=config.get('draws',2000);samples=[];failed=0
    for _ in range(draws):
        frame=pd.concat([groups[i] for i in rng.integers(0,len(groups),len(groups))],ignore_index=True)
        value=estimate(frame,card)
        if value is None:failed+=1
        else:samples.append(value)
    record['clusters']=len(groups);record['draws']=draws;record['failed_draws']=failed;record['estimate']=point
    if failed:record['status']='bootstrap_support_failure';return record
    ci=np.quantile(samples,[.025,.975]).tolist();bar={'SP1':.1,'SP2':.05,'SP3':.01}[card];direction=-1 if card=='SP3' else 1
    lo,hi=sorted(direction*np.array(ci));outcome='supports' if lo>bar else 'against' if hi<0 or (lo>=-bar and hi<=bar) else 'inconclusive'
    if len(groups)<20 or fallback:outcome='below floor, descriptive'
    if config.get('ordinal'):outcome='descriptive latent-probit sensitivity; original practical bar not applicable'
    record.update(status='ok',interval=ci,bar=bar,outcome=outcome)
    record['cooling_counts']={str(k):int(v) for k,v in table.cooling.value_counts(dropna=False).items()}
    record['griffiths_buildings']=int(table.griffiths.sum())
    record['median_acceptability_width']={k:(float(g.acceptable_width.median()) if g.acceptable_width.notna().any() else None) for k,g in table.groupby('cooling')}
    return record


def execute(output:Path,inputs:dict,config:dict):
    result=analyse(pd.read_parquet(inputs['data']),config)
    result['implementation']='separate-group exact OLS; unchanged AC/NV contrast and bootstrap sequence'
    write(output/'RESULT.json',result);return result

def verify(output:Path,inputs:dict,config:dict):
    result=execute(output/'independent-replay',inputs,config)
    if result!=json.loads((output/'RESULT.json').read_text('utf8')):raise ValueError('SP1 exact repair full replay differs')
    return {'verified':True,'all_original_resamples_used':True,'complete_replay':True}
