"""AT1.s: chronological, recipient-excluded genre population adaptation.

This conditional branch is dispatched only after AT1's shared-history route.
It is a population reader with no target writer's history, not another donor
set selected for a favorable coefficient.
"""
from pathlib import Path
import math
import numpy as np
from .week5_at_history import load,probability
from .timing_d33 import cache,WEIGHTS
from .timing_d33_match import earlier
from .week5_at_analysis import prediction_folds,gaussian_predictions,cluster_indices,outcome
from .timing_census import read,filehash
from .timing_p6 import write_equal,progress


def population(bank,writer):
    parts=bank.roster['writers'][writer]
    calibration=parts['supported_sessions']['calibration'];evaluation=sorted({r['session'] for r in bank.rows[writer]})
    histories={}
    for sid in calibration+evaluation:
        target=bank.records[sid]
        available=[s for donor,ss in bank.by_writer.items() if donor!=writer
                   for s in earlier(ss,target,True) if s['genre']==target['genre']]
        histories[sid]=cache(available,target['timestamp'])
    losses={a:[] for a in WEIGHTS}
    for sid in calibration:
        for word in bank.records[sid]['words']:
            p=word['population_probability']
            if not word['is_word'] or p is None or p<=0:continue
            q=probability(word,histories[sid],p)
            for a in WEIGHTS:losses[a].append(-math.log((1-a)*p+a*q))
    if not losses[0]:raise ValueError('Genre population lacks calibration support')
    alpha=min(WEIGHTS,key=lambda a:(np.mean(losses[a]),a));rows=[]
    for row in bank.rows[writer]:
        word=bank.records[row['session']]['words'][row['index']];p=word['population_probability']
        q=(1-alpha)*p+alpha*probability(word,histories[row['session']],p)
        rows.append(dict(row,genre_population_surprisal=-math.log(q),genre_alpha=float(alpha)))
    return rows


def analyze(rows,draws):
    writers=np.array([r['writer'] for r in rows]);y=np.array([r['log_pause'] for r in rows])
    n=np.array([[r[k] for k in ('length','log_frequency','sentence_start','after_punctuation','on_screen','session_surprisal')] for r in rows])
    f=prediction_folds(writers);within=len(set(writers))>=20
    _,base=gaussian_predictions(np.c_[n,[r['population_surprisal'] for r in rows]],y,writers,f,within)
    _,adapted=gaussian_predictions(np.c_[n,[r['genre_population_surprisal'] for r in rows]],y,writers,f,within)
    delta=adapted-base;sample=[float(delta[ix].mean()) for ix in cluster_indices(writers,draws)]
    return dict(card='AT1.s',primary=outcome(float(delta.mean()),sample,.002),writers=len(set(writers)),words=len(rows),
                reader='Population plus same-genre earlier other-writer cache; calibration-selected mixture',
                practical_bar='0.002 nats/word, AT2 held-out fit scale',descriptive=True,
                scope='below floor, descriptive' if len(set(writers))<20 else 'descriptive')


def run(output,inputs,config,verifying=False):
    bank=load(inputs,config);rows=[];root=Path(output)
    for i,writer in enumerate(bank.writers):
        rows.extend(population(bank,writer));progress(root/'PROGRESS.json',dict(phase='verify' if verifying else 'source',writers=i+1,total=len(bank.writers)))
    draws=config.get('draws',200)
    if draws not in (200,2000):raise ValueError('Unregistered shared branch uncertainty')
    result=analyze(rows,draws);result['screening_only']=draws==200
    if verifying:
        if read(root/'RESULT.json')!=result:raise ValueError('Genre population full replay differs')
        return dict(verified=True,complete_genre_population_replay=True)
    write_equal(root/'RESULT.json',result);return dict(status='complete',card='AT1.s')
def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
