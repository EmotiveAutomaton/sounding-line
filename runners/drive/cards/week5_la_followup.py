"""Prespecified LA1 next-act surprise branch with arithmetic coupling control."""
from collections import defaultdict
from pathlib import Path
import numpy as np
from .week5_la import matched_sets
from .week5_at_analysis import outcome
from .week5_at_scoring import SEED
from .timing_p6 import gzread,write_equal
from .timing_census import read,filehash


def analyze(rows,draws=200):
    meetings=defaultdict(list)
    for r in rows:meetings[r['meeting']].append(r)
    values=[];missing=0
    for meeting,acts in sorted(meetings.items()):
        acts.sort(key=lambda a:(a['start'],a['end'],a['id']))
        for i,act in enumerate(acts):
            following=next((n for n in acts[i+1:] if n['start']>=act['end']),None)
            if following is None:missing+=1;continue
            values.append(dict(act,next_surprise=following['surprise'],surprise_drop=act['surprise']-following['surprise']))
    groups,unmatched=matched_sets(values);units=sorted({g['meeting'] for g in groups})
    if not groups:return dict(card='LA1.next',state='unsupported',reason='No matched next-act support',missing_next=missing)
    sufficient=defaultdict(lambda:[np.zeros((2,2)),np.zeros(2)])
    for group in groups:
        members=group['members'];x=np.array([[float(i==0),r['surprise']] for i,r in enumerate(members)])
        y=np.array([r['surprise_drop'] for r in members]);x-=x.mean(0);y-=y.mean()
        sufficient[group['meeting']][0]+=x.T@x;sufficient[group['meeting']][1]+=x.T@y
    def fit(sample):
        xx=sum(sufficient[m][0] for m in sample);xy=sum(sufficient[m][1] for m in sample)
        if np.linalg.matrix_rank(xx)<2:raise ValueError('Current-surprise-adjusted next-act contrast unidentifiable')
        return float(np.linalg.solve(xx,xy)[0])
    point=fit(units);rng=np.random.default_rng(SEED);samples=[fit(rng.choice(units,len(units),replace=True)) for _ in range(draws)]
    return dict(card='LA1.next',primary=outcome(point,samples,.01),meetings=len(units),matched_sets=len(groups),
                missing_next=missing,unmatched=unmatched,descriptive=True,
                estimand='Laugh minus matched nonlaugh next-act surprisal drop, controlling current surprisal and matched strata',
                practical_bar='Analyst-declared 0.01 nats/word; this follow-up cannot promote the parent claim')


def run(output,inputs,config,verifying=False):
    draws=config.get('draws',200)
    if draws not in (200,2000):raise ValueError('Unregistered follow-up uncertainty')
    result=analyze(gzread(inputs['rows']),draws);result['screening_only']=draws==200
    binding=dict(rows_sha256=filehash(inputs['rows']),config=config)
    root=Path(output)
    if verifying:
        if read(root/'RESULT.json')!=result or read(root/'BINDING.json')!=binding:raise ValueError('Next-act complete refit differs')
        return dict(verified=True,complete_followup_refit=True)
    write_equal(root/'RESULT.json',result);write_equal(root/'BINDING.json',binding);return dict(status='complete')
def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
