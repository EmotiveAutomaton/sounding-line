"""EV3 fixed-gallery identification from authenticated pinned engine habits.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 6-7 reread 2026-10-19. Identical
profiles tie at exact chance and yield zero paired gain; distinct duplicated
fingerprints identify perfectly. Reversed matching must fail. Both hypotheses
retain the same fixed gallery; whole-session fake labels preserve counts and
never redraw. Missing fixed support invalidates the original; S1's separately
labelled common-support variant leaves it open. Chance-centered fake bias above
one quarter SD flags either sign. Changed sources, nonfinite features, stops
and failed fresh replay refuse completion. Exhaustive states are unsupported,
invalid, negative, null, marginal and positive. No private-preference inference.
"""
from __future__ import annotations
import math
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from runners.stage14.common import read,atomic
from runners.drive.engine_habits_child import project
from . import engine_habits_input as source, engine_export_full as reader
from . import timing_pmap_stats as pmap
from .engine_signatures_guarded import boundary
from .timing_p6 import gzread,gzip_equal,write_equal
from .timing_stats import bind,check_binding

CONNECTIVES=('and','but','because','however','therefore','although','yet','so')
PUNCTUATION=(',',';',':','\u2014','?','!')
FEATURES=CONNECTIVES+PUNCTUATION+('sentenceMean','sentenceSpread','quotedWordShare')
VARIANTS=('final','typed')
CONFIG=dict(mode='full-habit-identification',permutations=200,draws=2000,seed=20261018)
CONSTRUCTED=dict(CONFIG,mode='constructed-habit-identification')


def validate(inputs,config):
    expected={'habit_completion'} if config==CONFIG else {'fixture'} if config==CONSTRUCTED else None
    if expected is None or set(inputs)!=expected:raise ValueError('exact EV3 scope/config required')


def vector(value):
    if value is None:return [None]*len(FEATURES)
    raw=value['raw']
    for key in ('words','quotedWords','sentenceCount'):
        if type(raw[key]) is not int or raw[key]<0:raise ValueError('invalid habit denominator')
    for key in ('connectives','punctuation'):
        if any(type(x) is not int or x<0 for x in raw[key].values()):raise ValueError('invalid count')
    if value!=project(raw,CONNECTIVES):raise ValueError('habit projection differs from frozen engine')
    out=[value['ratesPer1000UnquotedWords'][k] for k in CONNECTIVES+PUNCTUATION]+[value[k] for k in FEATURES[-3:]]
    if any(x is not None and (type(x) not in (float,int) or not math.isfinite(x)) for x in out):raise ValueError('nonfinite habit')
    return out


def population(habits,chronology):
    result=[]
    for value in habits:
        keys=value['keys'];sid=keys['session'];meta=chronology[sid]
        if keys!=meta['keys']:raise ValueError('chronology and habit identities differ')
        if any(not isinstance(keys[k],str) or not keys[k] for k in ('writer','session','prompt')):raise ValueError('missing identity')
        timestamp=meta['timestamp']
        if type(timestamp) not in (int,float) or not math.isfinite(timestamp):raise ValueError('invalid chronology')
        result.append(dict(**keys,timestamp=timestamp,**{k:vector(value[k]) for k in VARIANTS}))
    result.sort(key=lambda r:r['session'])
    if not result or len({r['session'] for r in result})!=len(result) or set(chronology)!={r['session'] for r in result}:
        raise ValueError('incomplete or duplicate population')
    return result


def load(inputs,config):
    validate(inputs,config)
    if config==CONSTRUCTED:
        f=read(inputs['fixture']);return population(f['habits'],f['chronology'])
    root,plan=reader.authenticate(inputs['habit_completion'],'runners.drive.cards.engine_habits_input')
    if plan['config']!=source.CONFIG:raise ValueError('full completed habit population required')
    summary=read(root/'output/SUMMARY.json')
    if not summary['final_export_parity'] or summary['documents']!=1399:raise ValueError('input parity/population not admitted')
    records,_=source.load(plan['inputs'],plan['config'])
    chronology={r['document']['keys']['session']:dict(keys=r['document']['keys'],timestamp=r['chronology']['timestamp']) for r in records}
    rows=population(gzread(root/'output/HABITS.json.gz'),chronology)
    if len(rows)!=1399:raise ValueError('full session population changed')
    return rows


def profiles(rows,assignment=None):
    halves,excluded=pmap.split_sessions(rows,assignment);values={};support={}
    for writer,parts in halves.items():
        values[writer]={};support[writer]={}
        for variant in VARIANTS:
            vv=[];nn=[]
            for part in parts:
                a=np.asarray([r[variant] for r in part],float);n=np.isfinite(a).sum(axis=0)
                means=np.divide(np.nansum(a,axis=0),n,out=np.full(len(FEATURES),np.nan),where=n>0)
                vv.append([float(x) if math.isfinite(x) else None for x in means]);nn.append(n.tolist())
            values[writer][variant]=vv;support[writer][variant]=nn
    return values,excluded,{w:[[r['session'] for r in part] for part in parts] for w,parts in halves.items()},support


def supported(values,writer,variant):
    return writer in values and all(any(x is not None for x in part) for part in values[writer][variant])


def paired_interval(scores,config):
    value=pmap.interval(scores,config['draws'],config['seed'])
    # The packet asks for intervals. Do not emit additional approximate p-values.
    for key in ('z','approximate_two_sided_wald_p'):value.pop(key,None)
    return value


def score(values,variant,roster):
    if len(roster)<3 or any(not supported(values,w,variant) for w in roster):return None
    a=[values[w][variant][0] for w in roster];b=[values[w][variant][1] for w in roster]
    return pmap.identify(a,b)


def comparison(all_profiles,variant,roster,config):
    metrics=[score(v,variant,roster) for v in all_profiles]
    invalid=[i for i,v in enumerate(metrics) if v is None]
    result=dict(writers=len(roster),attempted_fake=config['permutations'],invalid_assignments=invalid)
    if metrics[0] is not None:
        result['real']={k:v for k,v in metrics[0].items() if k!='scores'}
        a=[all_profiles[0][w][variant][0] for w in roster];b=[all_profiles[0][w][variant][1] for w in roster]
        result['reliability']=pmap.reliability(a,b,FEATURES)
        valid=[r['spearman_brown'] for r in result['reliability'] if r['spearman_brown'] is not None]
        result['median_reliability']=pmap.median(valid)
    detail=dict(roster=roster,probe_scores=[v['scores'] if v else None for v in metrics])
    if invalid:
        result.update(state='unsupported' if 0 in invalid else 'invalid',reason='fixed gallery lacks support; no successful-only inference or redraw')
        return result,detail
    matrix=np.asarray(detail['probe_scores']);fake=matrix[1:].mean(axis=1)
    # Algebraically identical paired estimand, without subtracting independently
    # accumulated levels: identical real/fake scores retain an exact zero.
    contrast=paired_interval((matrix[0]-matrix[1:]).mean(axis=0),config)
    reference=pmap.distribution(fake-1/len(roster));reference.pop('one_sided_p',None)
    result.update(primary=contrast,fake_mean_accuracy=float(fake.mean()),fake_chance_centered=reference,
        state='invalid' if reference['bias_flag'] else contrast['state'],
        validity='chance-centered fake reference biased' if reference['bias_flag'] else 'fixed-support control complete')
    return result,detail


def analyze(rows,config,progress=lambda value:None):
    rows=sorted(rows,key=lambda r:r['session'])
    original,excluded,halves,counts=profiles(rows)
    all_profiles=[original];labels=np.array([r['writer'] for r in rows],dtype=object)
    rng=np.random.default_rng(config['seed']);permutations=[];fake_exclusions=[]
    for i in range(config['permutations']):
        fake=rng.permutation(labels);assignment={r['session']:str(w) for r,w in zip(rows,fake,strict=True)}
        value,exclusion,_,_=profiles(rows,assignment);all_profiles.append(value)
        permutations.append(fake.tolist());fake_exclusions.append(exclusion)
        if (i+1)%10==0:progress(dict(phase='fake-writers',completed=i+1,total=config['permutations']))
    variants={};details={}
    for variant in VARIANTS:
        roster=sorted(w for w in original if supported(original,w,variant))
        common=[w for w in roster if all(supported(v,w,variant) for v in all_profiles)]
        result,detail=comparison(all_profiles,variant,roster,config)
        variants[variant]=dict(original=result,selected_population='original-fixed-gallery',
            real_eligible_writers=len(roster),common_supported_writers=len(common),
            excluded_real_writers=len(set(original)-set(roster)),dropped_for_common_support=len(roster)-len(common))
        details[variant]=dict(original=detail,common_roster=common)
        if common!=roster:
            sr,sd=comparison(all_profiles,variant,common,config)
            variants[variant].update(supported_gallery=sr,selected_population='S1-common-supported-gallery',original_question_open=True)
            details[variant]['supported_gallery']=sd
    primary=variants['final'].get('supported_gallery',variants['final']['original'])
    summary=dict(card='EV3',state=primary['state'],primary_population=variants['final']['selected_population'],
        primary=primary.get('primary'),variants=variants,documents=len(rows),writers=len(set(labels)),
        split_ineligible_writers=len(excluded),seed=config['seed'],permutations=config['permutations'],
        bootstrap_draws=config['draws'],features=list(FEATURES),
        method='Unweighted per-session engine-vector averages; PMAP prompt-alternating halves, B-only scaling and fixed gallery; paired real-probe bootstrap; whole-session fake labels preserve counts',
        typed_limit='Surviving typed fragments with synthetic gap boundaries, not historical continuous prose',
        scientific_admission=False,instrument=True)
    detail=dict(rows=rows,halves=halves,profiles=original,feature_session_support=counts,
        split_excluded=excluded,session_order=[r['session'] for r in rows],
        assignments=permutations,fake_split_exclusions=fake_exclusions,variants=details)
    return summary,detail


def run(output,inputs,config,operation):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);boundary(output)
    if operation=='verify' or (output/'TIMING_BINDINGS.json').exists():check_binding(output,inputs,config)
    def progress(value):boundary(output);atomic(output/'PROGRESS.json',value)
    with threadpool_limits(limits=1):
        rows=load(inputs,config);boundary(output)
        summary,detail=analyze(rows,config,progress);boundary(output)
    if operation=='execute':
        write_equal(output/'SUMMARY.json',summary);gzip_equal(output/'DETAIL.json.gz',detail)
        if not (output/'TIMING_BINDINGS.json').exists():bind(output,inputs,config,['SUMMARY.json','DETAIL.json.gz'])
        return summary
    if summary!=read(output/'SUMMARY.json') or detail!=gzread(output/'DETAIL.json.gz'):raise ValueError('fresh complete habit comparison differs')
    return dict(verified=True,summary=summary,fresh_source_authentication=True,full_statistic_replay=True,full_control_replay=True)


def execute(output,inputs,config):return run(output,inputs,config,'execute')
def verify(output,inputs,config):return run(output,inputs,config,'verify')
