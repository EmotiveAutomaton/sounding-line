"""LGH7. Test who joins a laugh using documented meeting roles and annotations.

DESIGN CHECK (2026-11-27). Lessons read: LESSONS §§2–3 and CONTROLS §1.
Gates, null/alternative/direction: under the null, reassignment of an
exchangeable leader gives a rate difference centered at zero. Under the
alternative, a leader whose laughs always attract another speaker has a
positive difference above the within-meeting permutation band.
Equal rates give exactly zero. A missing role cannot be inferred from frequency.
Verdict bands per arm, exhaustive: unavailable roles are void. Fewer than
11 meetings yields no comparison, 11–19 is descriptive. At 20 or more,
a positive or negative interval excluding zero is read against the matching
tail of the permutation reference. Overlap of either bar is undecided.
"""
from bisect import bisect_left, bisect_right
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import numpy as np

from . import week8_lgh6 as source
from . import week7_ami_channels as ami, week7_icsi_recordings as icsi
from runners.stage14.common import filehash, freeze, read

UNIT = 'LGH7-registered-meeting-roles'
ROLES = ('PM','ID','ME','UI')
LEADER = 0


def design(unit):
    if unit != UNIT:
        raise ValueError('Unrecognized role study')
    expected = {}
    inputs = [Path(ami.__file__),Path(icsi.__file__),Path(source.__file__),source.ROOT/'docs/design/stage-15/week8/LGH7.md']
    for key in source.COHORTS:
        _, info, archive, _, _, _ = source.inputs(key)
        expected[str(archive)] = info['pins'][str(archive)]
        inputs.extend([archive,source.HIST/source.COHORTS[key][1]])
    return dict(inputs=inputs,expected=expected,peak=.6,cap=20000,operations=['execute','verify'],
                source='ICSI and AMI original timed annotations and meeting rosters')


def counts(marks):
    starts = [sorted(row) for row in marks]
    total = np.array([len(v) for v in starts],dtype=int)
    joined = np.zeros(4,dtype=int)
    pairs = np.zeros((4,4),dtype=int)
    for role, times in enumerate(starts):
        for t in times:
            found = [j for j,v in enumerate(starts) if j != role and bisect_right(v,t+1) > bisect_left(v,t)]
            joined[role] += bool(found)
            pairs[role,found] += 1
    return total,joined,pairs


def meeting_stat(total, joined, leader):
    others = total.sum()-total[leader]
    if total[leader] == 0 or others == 0:
        return np.nan
    return joined[leader]/total[leader] - (joined.sum()-joined[leader])/others


def summarize(meetings,seed=2026112707):
    if not meetings:
        return dict(status='void',reason='No meeting with bound roles')
    rng=np.random.default_rng(seed)
    totals,joined,pairs=(np.stack(x) for x in zip(*meetings))
    # Require all four roles to have an initiating laugh for the rank comparison,
    # so the roster is identical for every permissible within-meeting permutation.
    eligible=(totals>0).all(axis=1)
    choices=np.array([[meeting_stat(t,j,k) for k in range(4)] for t,j in zip(totals[eligible],joined[eligible])])
    result=dict(meetings_with_roles=len(meetings),rank_meetings=int(eligible.sum()),
                meetings_missing_an_initiating_role=int((~eligible).sum()),role_rates={},join_pairs={})
    role_rates=np.divide(joined,totals,out=np.full(totals.shape,np.nan),where=totals>0)
    pair_rates=np.divide(pairs,totals[:,:,None],out=np.full(pairs.shape,np.nan),where=totals[:,:,None]>0)
    for i,role in enumerate(ROLES):
        valid=totals[:,i]>0
        if valid.sum() < 11:
            continue
        result['role_rates'][role]=dict(meetings=int(valid.sum()),rate=float(role_rates[valid,i].mean()))
        for j,other in enumerate(ROLES):
            if i!=j:
                result['join_pairs'][role+' to '+other]=dict(meetings=int(valid.sum()),rate=float(pair_rates[valid,i,j].mean()))
    n=len(choices)
    if n<11:
        result['status']='insufficient meetings'
        return result
    obs=float(choices[:,LEADER].mean())
    people=np.arange(n)
    draws=choices[rng.integers(n,size=(2000,n)),LEADER].mean(axis=1)
    null=choices[people,rng.integers(4,size=(1000,n))].mean(axis=1)
    result.update(status='measured' if n>=20 else 'below floor descriptive',point=obs,
                  interval=np.quantile(draws,[.025,.975]).tolist(),
                  permutation_interval=np.quantile(null,[.025,.975]).tolist(),
                  permutation_at_or_above=int((null>=obs).sum()),permutations=len(null),draws=len(draws))
    return result


def fixture():
    t,j,p=counts([[0,3],[0,1],[1.01,7],[4.001]])
    assert t.tolist()==[2,2,2,1] and j[0]==1 and p[0,1]==1 and p[0,2]==0
    assert p[1,0]==1 and p[1,2]==1 and np.all(p.diagonal()==0)
    # A simultaneous second initiator and repeated starts by one joiner count once per target.
    _,j,p=counts([[5],[5,5.3,5.7],[],[]])
    assert j[0]==1 and p[0,1]==1
    rows=[counts([[0,10,40],[.2,20],[10.2,30],[40.1,50]]) for _ in range(24)]
    measured=summarize(rows)
    assert measured['interval']==[1.,1.] and measured['permutation_at_or_above']==0
    equal=summarize([counts([[0],[0],[0],[0]]) for _ in range(21)])
    assert equal['point']==0 and equal['permutation_interval']==[0.,0.]
    one_missing=summarize(rows+[counts([[0],[1],[2],[]])])
    assert one_missing['rank_meetings']==24 and one_missing['meetings_missing_an_initiating_role']==1
    return dict(roles=4,exact_window=True,tied_onsets=True,same_speaker_excluded=True,
                multiple_marks_once=True,planted_and_equal=True,stable_permutation_cohort=True)


def calculate():
    _,_,ip,_,expected_icsi,_ = source.inputs('LGH6-ICSI-prejoin')
    with ZipFile(ip) as bundle:
        originals=icsi.editions(bundle)
        if len(originals)!=expected_icsi:
            raise ValueError('Original ICSI edition roster changed')
        participant_fields=set()
        for member in originals.values():
            for speaker in ET.fromstring(bundle.read(member)).iter('Participant'):
                participant_fields.update(speaker.attrib)
        if any('rank' in k.lower() or 'role' in k.lower() or k.lower() in ('position','chair') for k in participant_fields):
            raise ValueError('ICSI has a new candidate role field')
    _,info,archive,_,expected_ami,_=source.inputs('LGH6-AMI-prejoin')
    registered=info['meetings']
    meetings=[]
    omitted=Counter()
    with ZipFile(archive) as bundle:
        roster=ET.fromstring(bundle.read('corpusResources/meetings.xml')).findall('meeting')
        if len(registered)!=expected_ami or {m.get('observation') for m in roster}!=set(registered):
            raise ValueError('Original AMI meeting roster differs')
        for m in sorted(roster,key=lambda m:m.get('observation')):
            if m.get('type')!='scenario':
                omitted['without_scenario_roles']+=1
                continue
            speakers=m.findall('speaker')
            by_role={s.get('role'):s.get('nxt_agent') for s in speakers}
            if len(speakers)!=4 or set(by_role)!=set(ROLES) or len(set(by_role.values()))!=4:
                omitted['incomplete_roles']+=1
                continue
            marks=[]
            for role in ROLES:
                times=ami.intervals(bundle,m.get('observation'),by_role[role])
                if times is None:
                    break
                laughs,_,untimed=times
                omitted['untimed_marks']+=untimed
                marks.append([a for a,_ in laughs])
            if len(marks)==4:
                meetings.append(counts(marks))
            else:
                omitted['incomplete_annotations']+=1
    return dict(ICSI=dict(status='void',reviewed_originals=expected_icsi,reason='No documented speaker role or rank'),
                AMI=summarize(meetings),AMI_exclusions=dict(omitted),AMI_handling='internal tests only')


def run(unit,d,mode):
    if unit != UNIT:
        raise ValueError('Unrecognized role study')
    freeze(d/(mode+'_INTERNAL.json'),calculate())


def check(unit,d):
    a=d/'execute_INTERNAL.json'
    b=d/'verify_INTERNAL.json'
    if read(a)!=read(b):
        raise ValueError('Independent role-study replay differs')
    return {p.name:filehash(p) for p in (a,b)}
