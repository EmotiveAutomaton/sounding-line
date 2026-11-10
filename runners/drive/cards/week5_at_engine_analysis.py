"""Paired AT2.e/AT4 exact-product-mark analyses on complete engine exports."""
from pathlib import Path
import numpy as np
from sklearn.metrics import roc_auc_score
from .week5_at_source import authenticate
from .week5_at_analysis import nuisance,prediction_folds,gaussian_predictions,classifier_predictions,cluster_indices,outcome
from .week5_at_engine import COMMIT
from .timing_census import read,filehash
from .timing_p6 import gzread,write_equal


def analyze(rows,card,draws=2000):
    w=np.array([r['writer'] for r in rows]);assignment=prediction_folds(w);x=nuisance(rows,card=='AT2.e')
    if card=='AT2.e':
        y=np.log([r['pause_seconds'] for r in rows]);within=len(set(w))>=40
        _,base=gaussian_predictions(np.c_[x,[r['population_surprisal'] for r in rows]],y,w,assignment,within)
        _,full=gaussian_predictions(np.c_[x,[r['engine']['mark_departure'] for r in rows]],y,w,assignment,within)
        delta=full-base;point=float(delta.mean());samples=[float(delta[ix].mean()) for ix in cluster_indices(w,draws)];bar=.002
    elif card=='AT4.engine':
        y=np.array([r['fast']<.5 for r in rows],int);base=classifier_predictions(x,y,assignment)
        marks=np.array([r['engine']['marked'] for r in rows],float)
        point=float(roc_auc_score(y,marks)-roc_auc_score(y,base));bar=.02;samples=[]
        for ix in cluster_indices(w,draws):
            if len(set(y[ix]))<2:raise ValueError('Exact-mark AUC bootstrap has one class')
            samples.append(float(roc_auc_score(y[ix],marks[ix])-roc_auc_score(y[ix],base[ix])))
    else:raise ValueError('Unknown exact-engine analysis')
    return dict(card=card,primary=outcome(point,samples,bar),words=len(rows),writers=len(set(w)),
                engine_commit=COMMIT,descriptive=True,mark_rule='Exact certified product-selected span contains word')


def run(output,inputs,config,verifying=False):
    rows=gzread(inputs['rows']);exports=read(inputs['engine_bank']);marks={};readers=set()
    for path in exports:
        root=authenticate(path);value=read(root/'output/SCORES.json')
        if value['engine_commit']!=COMMIT:raise ValueError('Wrong product function commit')
        readers.add(value['reader']['id'])
        for row in value['rows']:
            if row['row_key'] in marks:raise ValueError('Duplicate exact-engine word')
            marks[row['row_key']]=row
    if len(readers)!=1:raise ValueError('Mixed engine reader exports')
    absent=[r['row_key'] for r in rows if r['row_key'] not in marks]
    if absent:raise ValueError('Exact-engine exports incomplete for analysis rows')
    selected=[dict(r,engine=marks[r['row_key']]) for r in rows if marks[r['row_key']]['supported']]
    result=analyze(selected,config['card'],config.get('draws',2000));result['unsupported_words']=len(rows)-len(selected)
    result['reader']=next(iter(readers));result['screening_only']=config.get('draws',2000)==200
    root=Path(output);binding=dict(rows_sha256=filehash(inputs['rows']),bank_sha256=filehash(inputs['engine_bank']),config=config)
    if verifying:
        if read(root/'RESULT.json')!=result or read(root/'BINDING.json')!=binding:raise ValueError('Exact-engine analysis replay differs')
        return dict(verified=True,complete_exact_mark_refit=True)
    write_equal(root/'RESULT.json',result);write_equal(root/'BINDING.json',binding);return dict(status='complete',card=config['card'])
def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
