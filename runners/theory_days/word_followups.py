"""Registered TD4.s/.m word-list diagnostics; original parent remains unchanged.

DESIGN CHECK: LESSONS 2-5, CONTROLS 6-7. Monotone and reverse constructions,
constant axes, ties, deletion adjacency and coverage floors have known answers.
Missing norms never become zero scores. No causal or population inference.
"""
from pathlib import Path
import io,zipfile
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from runners.stage14.common import read,filehash,freeze
from .emotions import SCALES,scale_stats,td4

def deletion_curve(x,a,d):
    x,a,d=map(lambda v:np.asarray(v,dtype=float),(x,a,d))
    if not (len(x)==len(a)==len(d)) or len(x)<5:raise ValueError('Five covered words required')
    variants=[]
    for i in range(len(x)):
        keep=np.arange(len(x))!=i
        variants.append(dict(omitted_covered_position=i,**scale_stats(x[keep],a[keep],d[keep])))
    counts={k:sum(v['verdict']==k for v in variants) for k in ('supports','against','inconclusive','design cannot test')}
    ranges={}
    for k in ('inversions','spearman','off_line_ratio'):
        vals=[v[k] for v in variants if v[k] is not None]
        ranges[k]=[min(vals),max(vals)] if vals else None
    return dict(baseline=scale_stats(x,a,d),variants=variants,counts=counts,ranges=ranges,against_fraction=counts['against']/len(variants))

def rho(x,y):
    return float(spearmanr(x,y).statistic) if np.ptp(x)>0 and np.ptp(y)>0 else None

def axes_diagnostic(x,a,d):
    data=np.column_stack([x,a,d]);data=data[np.isfinite(data).all(axis=1)]
    if len(data)<4:return dict(status='design cannot test',joint_covered=len(data))
    names=('joy','arousal','dominance');axes={}
    for k,name in enumerate(names):
        v=data[:,k]
        axes[name]=dict(inversions=int((np.diff(v)<0).sum()),ties=int((np.diff(v)==0).sum()),order_rho=rho(np.arange(len(v)),v))
    pairs={}
    for i in range(3):
        for j in range(i+1,3):
            counts=dict(concordant=0,discordant=0,tied=0)
            for l in range(len(data)):
                for r in range(l+1,len(data)):
                    product=np.sign(data[r,i]-data[l,i])*np.sign(data[r,j]-data[l,j])
                    counts['concordant' if product>0 else 'discordant' if product<0 else 'tied']+=1
            pairs[names[i]+'__'+names[j]]=dict(rho=rho(data[:,i],data[:,j]),**counts)
    j=axes['joy']['order_rho'];a=axes['arousal']['order_rho']
    return dict(status='complete',joint_covered=len(data),axes=axes,pairs=pairs,arousal_minus_joy_order_rho=None if j is None or a is None else a-j)

def play_source(eil_path,vad_path):
    with zipfile.ZipFile(eil_path) as z:
        e=pd.read_csv(io.BytesIO(z.read('NRC-Emotion-Intensity-Lexicon/NRC-Emotion-Intensity-Lexicon-v1.txt')),sep='\t')
    with zipfile.ZipFile(vad_path) as z:
        v=pd.read_csv(io.BytesIO(z.read('NRC-VAD-Lexicon-v2.1/NRC-VAD-Lexicon-v2.1.txt')),sep='\t')
    e.columns=['word','emotion','score'];v.columns=['word','valence','arousal','dominance']
    assert not e.duplicated(['word','emotion']).any() and not v.word.duplicated().any()
    joy={r.word:float(r.score) for r in e.itertuples() if r.emotion=='joy'}
    vad={r.word:(float(r.arousal),float(r.dominance)) for r in v.itertuples()}
    words=[w for w in SCALES['PLAY'][1].split() if w in joy]
    if len(words)!=5 or not all(w in vad for w in words):raise ValueError('Parent support changed')
    return [joy[w] for w in words],[vad[w][0] for w in words],[vad[w][1] for w in words]

def fixtures():
    v=np.arange(6,dtype=float)
    inc=deletion_curve(v,v,2*v);rev=deletion_curve(v[::-1],v,2*v)
    assert inc['counts']['supports']==6 and rev['counts']['against']==6
    same=axes_diagnostic(v,v,2*v);opposite=axes_diagnostic(v,v[::-1],2*v)
    assert same['pairs']['joy__arousal']['discordant']==0
    assert opposite['pairs']['joy__arousal']['discordant']==15
    return dict(increasing=inc,reversed=rev,same=same,opposite=opposite,constant=axes_diagnostic(v,np.ones(6),2*v))

def calculate(inputs,config):
    if config.get('constructed'):return fixtures()
    for item in inputs.values():assert filehash(item['path'])==item['sha256']
    baseline=td4(inputs['eil']['path'],inputs['vad']['path'])
    assert baseline==read(inputs['parent']['path']),'Full parent reproduction'
    x,a,d=play_source(inputs['eil']['path'],inputs['vad']['path'])
    assert scale_stats(x,a,d)=={k:baseline['scales']['PLAY'][k] for k in scale_stats(x,a,d)}
    if config.get('cost_only'):return dict(parent_reproduced=True,covered=len(x),source_rows_valid=True)
    assert config['kind'] in ('s','m')
    return dict(status='complete',kind=config['kind'],parent_reproduced=True,descriptive=True,
                diagnostic=deletion_curve(x,a,d) if config['kind']=='s' else axes_diagnostic(x,a,d))

def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    freeze(output/'DIAGNOSTIC.json',calculate(inputs,config));return dict(status='complete')

def verify(output,inputs,config):
    assert calculate(inputs,config)==read(Path(output)/'DIAGNOSTIC.json')
    return dict(verified=True,complete_recalculation=True)
