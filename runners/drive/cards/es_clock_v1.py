"""Additive source-semantic bridge; original ES delivery remains unchanged.

DESIGN CHECK: LESSONS2/3/5. Only explicit column whitelists materialize. Source
timestamps use official UTC conversion; original elapsed study days never reset
at a presumed wave. Calibrate before selecting adjacent pairs. Missing ordering
holds that person's carry panel and cannot bridge an unknown answered prompt.
"""
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pandas as pd
try:
    from . import es_core_v1 as core,es_source_v1 as original,es_carry_v1 as carry
except ImportError:
    import es_core_v1 as core
    import es_source_v1 as original
    import es_carry_v1 as carry

UTC_PROFILE='openesm_ryvkina_utc_created_day_v1'
CALIBRATION='all_complete_qualifying_prompts_by_context_before_pair_selection'


def whitelist(member,route):
    if route=='duration0045':
        core.need(member=='0045','duration member differs')
        return ('id','day','beep','emotion_chronometry')
    if route=='daily0062':
        core.need(member=='0062','daily member differs')
        return ('id','day','source')+original.DAILY_EVENTS+original.DAILY_FEELINGS
    core.need(route=='carry' and member in ('0056','0057'),'source route differs')
    emotions=tuple(dict.fromkeys(item for family in core.FAMILIES.values() for item in family
                                if member=='0057' or item not in ('lonely','excluded')))
    return ('id','day','created_esm','ended_esm','interaction')+tuple('status_'+n for n in core.NEGATIVE)+tuple('int_'+n for n in emotions)+tuple('occup_'+n for n in ('angry','sad','anxious'))


def selected_frames(path,pin,member,route,guard=lambda:None):
    path=Path(path);core.need(path.stat().st_size==pin['bytes'],'source size mismatch')
    core.need(original.sha256(path,guard)==pin['sha256'],'source digest differs')
    wanted=whitelist(member,route)
    for frame in pd.read_csv(path,sep='\t',usecols=list(wanted),dtype=str,
                             keep_default_na=False,na_filter=False,chunksize=20000):
        core.need(set(frame.columns)==set(wanted),'whitelist materialization differs')
        guard();yield frame.loc[:,list(wanted)]


def utc_seconds(text):
    try:value=datetime.fromisoformat(text.replace('Z','+00:00'))
    except (TypeError,ValueError):raise ValueError('documented UTC ISO timestamp required') from None
    core.need(value.utcoffset() is not None and value.utcoffset().total_seconds()==0,'documented UTC offset required')
    return value.timestamp()


def prepare_carry(frames,member,outcomes,missing_tokens,clock_profile,calibration_scope,guard=lambda:None):
    core.need(clock_profile==UTC_PROFILE and calibration_scope==CALIBRATION,'unreviewed clock/calibration scope')
    core.need(tuple(outcomes) in (('angry',),('angry','sad','anxious')),'carry outcome scope differs')
    grouped={};counts={'source_rows':0,'missing_id_rows':0,'source_people':0,
        'clock_held_people':0,'day_recipe_held_people':0,'under_ten_complete_interaction_people':0,
        'under_two_complete_activity_people':0,'missing_or_unknown_context_rows':0,
        'complete_interaction_calibration_rows':0,'complete_activity_calibration_rows':0,
        'candidate_adjacent_pairs':0,'missing_pair_outcome_rows':0,'complete_pairs':0}
    for frame in frames:
        guard()
        core.need(set(frame.columns)==set(whitelist(member,'carry')),'carry source whitelist differs')
        for row in frame.to_dict('records'):
            counts['source_rows']+=1
            if row['id'] in missing_tokens:counts['missing_id_rows']+=1;continue
            grouped.setdefault(row['id'],[]).append(row)
    counts['source_people']=len(grouped);prepared=[];keys=[];source_people={}
    for identity,rows in sorted(grouped.items()):
        guard()
        decoded=[];held=False
        for row in rows:
            if row['created_esm'] in missing_tokens or row['ended_esm'] in missing_tokens:
                held=True;break
            created=utc_seconds(row['created_esm']);ended=utc_seconds(row['ended_esm'])
            core.need(ended>=created,'prompt end precedes creation')
            day=original.study_day(row['day'],missing_tokens)
            if not np.isfinite(day):held=True;break
            if row['interaction'] in missing_tokens:context=None
            else:
                try:context=float(row['interaction'])
                except ValueError:raise ValueError('unknown interaction code') from None
                core.need(context in (1.,2.),'unknown interaction code')
            if context is None:counts['missing_or_unknown_context_rows']+=1
            values={name:original.rating(row['int_'+name],6,missing_tokens)
                    for name in dict.fromkeys(x for family in core.FAMILIES.values() for x in family)
                    if member=='0057' or name not in ('lonely','excluded')}
            after={name:original.rating(row['occup_'+name],6,missing_tokens) for name in ('angry','sad','anxious')}
            negative={name:original.rating(row['status_'+name],6,missing_tokens) for name in core.NEGATIVE}
            decoded.append({'created':created,'ended':ended,'day':int(day),'context':context,
                            'before':values,'after':after,'negative':negative})
        if held:
            counts['clock_held_people']+=1;continue
        core.need(len({r['ended'] for r in decoded})==len(decoded),'ambiguous tied answered timestamps')
        # Exact official cleaning recipe: elapsed UTC created-date from first
        # observed created prompt, across the complete person (no wave reset).
        first=min(datetime.fromtimestamp(r['created'],timezone.utc).date() for r in decoded)
        if any(r['day']!=(datetime.fromtimestamp(r['created'],timezone.utc).date()-first).days+1 for r in decoded):
            counts['day_recipe_held_people']+=1;continue
        decoded.sort(key=lambda r:r['ended'])
        interaction=[r['before']['angry'] for r in decoded if r['context']==1 and np.isfinite(r['before']['angry'])]
        activity=[tuple(r['after'][n] for n in outcomes) for r in decoded if r['context']==2 and all(np.isfinite(r['after'][n]) for n in outcomes)]
        if len(interaction)<10:counts['under_ten_complete_interaction_people']+=1;continue
        if len(activity)<2:counts['under_two_complete_activity_people']+=1;continue
        counts['complete_interaction_calibration_rows']+=len(interaction)
        counts['complete_activity_calibration_rows']+=len(activity)
        xcal=np.asarray(interaction);ycal=np.asarray(activity)
        calibration_ss=np.concatenate(([np.sum((xcal-xcal.mean())**2)],np.sum((ycal-ycal.mean(0))**2,0)))
        calibration_n=np.array([len(xcal)]+[len(ycal)]*len(outcomes))
        gaps=[];xs=[];ys=[]
        for previous,current in zip(decoded,decoded[1:]):
            if previous['day']!=current['day'] or previous['context']!=1 or current['context']!=2:continue
            counts['candidate_adjacent_pairs']+=1
            x=previous['before']['angry'];y=[current['after'][n] for n in outcomes]
            if not np.isfinite(x) or not np.all(np.isfinite(y)):
                counts['missing_pair_outcome_rows']+=1;continue
            gaps.append((current['ended']-previous['ended'])/60);xs.append(x);ys.append(y)
        counts['complete_pairs']+=len(gaps)
        prepared.append({'gap':np.asarray(gaps),'x':np.asarray(xs),'ys':np.asarray(ys).reshape((-1,len(outcomes))),
            'calibration_n':calibration_n,'calibration_ss':calibration_ss,'original_interactions':len(interaction)})
        keys.append((member,identity))
        interactions=[r for r in decoded if r['context']==1]
        names=tuple(interactions[0]['before']) if interactions else ()
        source_people[(member,identity)]={'days':[r['day'] for r in interactions],
            'ratings':{**{n:[r['negative'][n] for r in interactions] for n in core.NEGATIVE},
                       **{n:[r['before'][n] for r in interactions] for n in names}}}
    return {'stats':carry.stats(prepared,tuple(outcomes)),'source_counts':counts,'private_keys':keys,
            'private_es2_people':source_people,'private_pair_arrays':prepared}


def exact_person_join(first,second):
    """Only for the declared cross-card descriptive pairing; never silent loss."""
    a=set(first);b=set(second);common=sorted(a&b)
    return ([first[k] for k in common],[second[k] for k in common],
            {'first_people':len(a),'second_people':len(b),'common_people':len(common),
             'first_only_people':len(a-b),'second_only_people':len(b-a)})


def daily_frames(frames):
    """Source tags distinguish end-of-day rows; not a duplicate-column join."""
    for frame in frames:
        core.need(set(frame.columns)==set(whitelist('0062','daily0062')),'daily whitelist differs')
        core.need(set(frame['source'])<=set(('esm','daily')),'unknown source table tag')
        yield frame.loc[frame['source']=='daily'].drop(columns=['source'])


def duration_description(frames,missing_tokens):
    """0045 descriptive minutes only. No groups, traits, fit or effect test."""
    values=[];people=set();counts={'source_rows':0,'missing_id_rows':0,'missing_duration_rows':0}
    for frame in frames:
        core.need(set(frame.columns)==set(whitelist('0045','duration0045')),'duration whitelist differs')
        for row in frame.to_dict('records'):
            counts['source_rows']+=1
            if row['id'] in missing_tokens:counts['missing_id_rows']+=1;continue
            if row['emotion_chronometry'] in missing_tokens:counts['missing_duration_rows']+=1;continue
            try:value=float(row['emotion_chronometry'])
            except ValueError:raise ValueError('unrecognized minute encoding') from None
            core.need(np.isfinite(value) and value>=0,'duration must be finite nonnegative minutes')
            values.append(value);people.add(row['id'])
    if not values:return {'status':'UNSUPPORTED_NO_RECORDED_DURATION',**counts}
    v=np.asarray(values)
    return {'status':'DESCRIPTIVE_ONLY','unit':'self-estimated current-state minutes','eligible_rows':len(v),
            'people':len(people),'minimum':float(v.min()),'q25':float(np.quantile(v,.25)),
            'median':float(np.median(v)),'q75':float(np.quantile(v,.75)),'maximum':float(v.max()),
            'mean':float(v.mean()),'outlier_trimming':False,'diagnostic_groups_read':False,**counts}
