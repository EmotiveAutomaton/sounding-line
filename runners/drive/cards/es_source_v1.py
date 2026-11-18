"""Prospective whitelist adapter; no source is opened at import.

DESIGN CHECK: collection availability is not scientific admission. The caller
must already own a counted native runtime lease. Authenticate source bytes,
parse only named columns, preserve missingness and reject unexplained coding.
No static table, trait or demographic column is admitted here. Production
missing-token/clock/daily-layout declarations need owner review before rows.
"""
from datetime import datetime
from pathlib import Path
import hashlib
import numpy as np
import pandas as pd
if __package__:
    from .es_core_v1 import EVENTS, FEELINGS, need
else:
    from es_core_v1 import EVENTS, FEELINGS, need

DAILY_EVENTS=('failure','pressure','unappreciated','disagreements_conflicts')
DAILY_FEELINGS=('angry_daily','afraid_daily','worried_daily')


def sha256(path, guard=lambda:None):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block:=stream.read(1024*1024):
            digest.update(block);guard()
    return digest.hexdigest()


def fields(member, card):
    need(member in ('0056','0057','0062'), 'unreviewed member')
    need(card in ('ES1','ES2','ES3'),'unreviewed card')
    if member=='0062':
        need(card=='ES2','0062 only supports the approved daily ES2 replication')
        return ('id','day')+DAILY_EVENTS+DAILY_FEELINGS
    feelings=tuple(n for n in FEELINGS if member=='0057' or n not in ('lonely','excluded'))
    base=('id','day','interaction')
    if card=='ES3':return base+('ended_esm',)+tuple('int_'+n for n in ('angry','sad','anxious'))+tuple('occup_'+n for n in ('angry','sad','anxious'))
    return base+tuple('status_'+n for n in EVENTS)+tuple('int_'+n for n in feelings)


def selected_frames(path, pin, member, card, missing_tokens, guard=lambda:None):
    """Only callable inside counted source/replay phases, never during intake.

    No pandas default NA vocabulary: an exact reviewed token list is mandatory.
    The parser materializes only this member/card's whitelist. Every source byte
    is nevertheless authenticated once per fresh source phase before parsing.
    """
    need(type(missing_tokens) is list and all(type(v) is str for v in missing_tokens),
         'explicit reviewed missing-token list required')
    path=Path(path)
    need(path.is_file() and path.stat().st_size==pin['bytes'],'source size mismatch')
    need(sha256(path,guard)==pin['sha256'],'source hash mismatch')
    wanted=fields(member,card)
    for frame in pd.read_csv(path,sep='\t',usecols=list(wanted),dtype=str,
                             keep_default_na=False,na_filter=False,chunksize=20000):
        need(set(frame.columns)==set(wanted),'source whitelist mismatch')
        guard();yield frame.loc[:,list(wanted)]


def rating(value, maximum, missing_tokens):
    if value in missing_tokens:return np.nan
    try:number=float(value)
    except (ValueError,TypeError):raise ValueError('unrecognized rating encoding') from None
    need(np.isfinite(number) and 1<=number<=maximum,'rating outside documented scale')
    return number


def study_day(value, missing_tokens):
    if value in missing_tokens:return np.nan
    try:number=float(value)
    except (ValueError,TypeError):raise ValueError('unrecognized study-day encoding') from None
    need(np.isfinite(number) and number>=1 and number==int(number),'invalid original study day')
    return number


def interaction_people(frames, member, missing_tokens):
    """All interaction prompts retained; panel-specific missingness is later.

    IDs group records in memory only and are omitted from every returned person
    and aggregate output. No rating threshold substitutes for interaction==1.
    """
    need(member in ('0056','0057'),'interaction source member differs')
    mapping={n:'status_'+n for n in EVENTS}
    mapping.update({n:'int_'+n for n in FEELINGS if member=='0057' or n not in ('lonely','excluded')})
    grouped={};answered={};counts={'source_rows':0,'interaction_rows':0,'noninteraction_rows':0,
                       'missing_interaction_rows':0,'missing_id_rows':0,'missing_day_answered_rows':0}
    for frame in frames:
        need(set(frame.columns)==set(fields(member,'ES1')),'unexpected source columns')
        for row in frame.to_dict('records'):
            counts['source_rows']+=1
            identity=row['id']
            if identity in missing_tokens:
                counts['missing_id_rows']+=1;continue
            day=study_day(row['day'],missing_tokens)
            if np.isfinite(day):
                table=answered.setdefault(identity,{})
                table[int(day)]=table.get(int(day),0)+1
            else:counts['missing_day_answered_rows']+=1
            status=row['interaction']
            if status in missing_tokens:
                counts['missing_interaction_rows']+=1;continue
            try:status=float(status)
            except (ValueError,TypeError):raise ValueError('unknown interaction code') from None
            need(status in (1.,2.),'unknown interaction code')
            if status==2.:
                counts['noninteraction_rows']+=1;continue
            counts['interaction_rows']+=1
            person=grouped.setdefault(identity,{'days':[],'ratings':{n:[] for n in mapping}})
            person['days'].append(day)
            for canonical,source in mapping.items():
                person['ratings'][canonical].append(rating(row[source],6,missing_tokens))
    people=[dict(grouped[k],answered_counts_by_day=answered.get(k,{})) for k in sorted(grouped)]
    return people,dict(counts,source_people=len(people),identity_fields_exported=False)


def daily_people(frames, missing_tokens, layout):
    """Approved daily perceived adversity. Never average conflicting records.

    `one_nonempty_daily_record_per_person_day` is the conservative candidate.
    `collapse_identical_daily_records` is an explicit alternative requiring a
    prospective source-layout review; it is not a silently enabled fallback.
    Entirely blank daily rows are counted as non-daily prompts, not reported days.
    Missing items within a recorded day stay NaN and fail complete-case support.
    """
    need(layout in ('one_nonempty_daily_record_per_person_day','collapse_identical_daily_records'),
         'reviewed daily layout required')
    names=DAILY_EVENTS+DAILY_FEELINGS;days={}
    counts={'source_rows':0,'non_daily_blank_rows':0,'missing_key_rows':0,'identical_daily_duplicates':0}
    for frame in frames:
        need(set(frame.columns)==set(fields('0062','ES2')),'unexpected daily source columns')
        for row in frame.to_dict('records'):
            counts['source_rows']+=1
            values=tuple(rating(row[n],7,missing_tokens) for n in names)
            if all(np.isnan(x) for x in values):counts['non_daily_blank_rows']+=1;continue
            if row['id'] in missing_tokens or row['day'] in missing_tokens:
                counts['missing_key_rows']+=1;continue
            day=study_day(row['day'],missing_tokens);key=(row['id'],int(day))
            if key in days:
                need(layout=='collapse_identical_daily_records','duplicate daily record needs reviewed layout')
                need(np.array_equal(days[key],values,equal_nan=True),'conflicting daily records')
                counts['identical_daily_duplicates']+=1
            else:days[key]=values
    grouped={}
    for (identity,day),values in sorted(days.items()):
        person=grouped.setdefault(identity,{'days':[],'ratings':{n:[] for n in names}})
        person['days'].append(day)
        for name,value in zip(names,values):person['ratings'][name].append(value)
    return list(grouped.values()),dict(counts,recorded_person_days=len(days),source_people=len(grouped),
        measure='mean daily perceived-adversity agreement; daily feeling ratings',identity_fields_exported=False)


def aware_seconds(text):
    """Accept explicit-offset ISO strings only; no timezone/default wave guess."""
    try:value=datetime.fromisoformat(text.replace('Z','+00:00'))
    except (ValueError,TypeError):raise ValueError('timestamp requires reviewed ISO offset encoding') from None
    need(value.tzinfo is not None and value.utcoffset() is not None,'timezone absent')
    return value.timestamp()


def consecutive_pairs(rows, source_clock, outcomes=('angry',)):
    """Constructed/canonical adapter only until actual clock mapping is bound.

    Rows hold id/day/timestamp/interaction and three interaction/activity ratings.
    Adjacent means previous answered row BEFORE outcome exclusions. Same-day
    identity uses the source's day token; repeated wave days are not reset here.
    Each row's timestamp must be unique within person. Returned identities remain
    private until later person-grouping removes them; never write these records.
    """
    need(source_clock=='explicit_offset_iso8601','reviewed source clock required')
    need(bool(outcomes) and set(outcomes)<=set(('angry','sad','anxious')),'unreviewed carry outcomes')
    groups={};counts={'answered_rows':len(rows),'candidate_pairs':0,'missing_pair_outcome':0}
    for row in rows:
        seconds=aware_seconds(row['timestamp'])
        groups.setdefault(row['id'],[]).append((seconds,row))
    result=[]
    for identity,records in groups.items():
        records.sort(key=lambda z:z[0])
        need(len({t for t,_ in records})==len(records),'ambiguous tied answered timestamps')
        for (ta,a),(tb,b) in zip(records,records[1:]):
            if a['day']!=b['day'] or a['interaction']!=1 or b['interaction']!=2:continue
            counts['candidate_pairs']+=1
            values=[a['int_angry']]+[b['occup_'+n] for n in outcomes]
            # Each declared comparison uses shared complete rows; no bridging.
            if not all(np.isfinite(x) for x in values):counts['missing_pair_outcome']+=1;continue
            result.append({'id':identity,'day':a['day'],'gap':(tb-ta)/60,
                           'angry_before':values[0],**{n+'_after':b['occup_'+n] for n in outcomes}})
    return result,counts
