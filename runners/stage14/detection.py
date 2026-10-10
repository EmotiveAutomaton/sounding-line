"""D01 bounded typed-stream versus accepted-offer detector, writer-held transfer.

DESIGN CHECK: LESSONS 2-5; SL2. NULL: shuffled source labels do not retain real
classification; length-only rival exposes easy rendering confounds. ALTERNATIVE:
features generalize to held writers with separate human-only calibration. Chunk
counts never substitute for independent writers at the low false-positive tail.
"""
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from .common import read,freeze,digest
from .adaptive import proper

def run(card,out,raw,tick):
    data=read(raw/'jobs'/card['requires'][0]/'TEXT_CORPORA.json');writers=sorted(data,key=lambda w:digest(['detector-split',w]))
    a=int(len(writers)*.6);b=int(len(writers)*.8);split={w:'train' if i<a else 'calibration' if i<b else 'evaluation' for i,w in enumerate(writers)}
    rows=[];seen={};duplicates=set()
    for w in writers:
        for label,kind in [(0,'human_typed'),(1,'accepted_model')]:
            text=data[w][kind]
            for i in range(0,len(text)-255,256):
                piece=text[i:i+256];h=digest(piece)
                if h in seen:duplicates.add(h)
                seen[h]=w
                rows.append(dict(writer=w,partition=split[w],label=label,text=piece,key=h))
    rows=[r for r in rows if r['key'] not in duplicates]
    parts={p:[r for r in rows if r['partition']==p] for p in ('train','calibration','evaluation')}
    if any(len({r['label'] for r in rs})!=2 for rs in parts.values()):raise ValueError('incomplete detector comparison')
    vector=TfidfVectorizer(analyzer='char',ngram_range=(3,5),min_df=2,max_features=12000)
    x=vector.fit_transform([r['text'] for r in parts['train']]);y=np.array([r['label'] for r in parts['train']]);models={}
    for arm in ('source_labels','shuffled_labels'):
        target=y if arm=='source_labels' else np.random.default_rng(141010).permutation(y)
        models[arm]=LogisticRegression(C=1.,max_iter=500,random_state=141010,n_jobs=1).fit(x,target)
    outputs={}
    for part,rs in parts.items():
        xx=vector.transform([r['text'] for r in rs]);values={k:m.predict_proba(xx)[:,1] for k,m in models.items()}
        outputs[part]=[dict(key=r['key'],writer=r['writer'],label=r['label'],scores={k:float(v[i]) for k,v in values.items()},length_only=float(y.mean())) for i,r in enumerate(rs)]
        tick(dict(partition=part,rows=len(rs)))
    cal=outputs['calibration'];ev=outputs['evaluation'];summary={}
    humans=len({r['writer'] for r in cal if r['label']==0})
    for arm in models:
        human=np.array([r['scores'][arm] for r in cal if r['label']==0]);threshold=float(np.max(human))
        summary[arm]=dict(auc=float(roc_auc_score([r['label'] for r in ev],[r['scores'][arm] for r in ev])),
            empirical_zero_calibration_error_threshold=threshold,calibration_independent_human_writers=humans,
            false_positive_1_percent='UNDERPOWERED' if humans<300 else 'not estimated by this pilot',false_positive_5_percent='UNDERPOWERED' if humans<60 else 'not estimated by this pilot',
            evaluation_human_error=float(np.mean([r['scores'][arm]>threshold for r in ev if r['label']==0])),evaluation_model_recall=float(np.mean([r['scores'][arm]>threshold for r in ev if r['label']==1])))
    freeze(out/'SPLITS.json',dict(writer_partition=split,counts={p:len(rs) for p,rs in parts.items()},duplicates_excluded=len(duplicates)))
    freeze(out/'PREDICTIONS.json',outputs);freeze(out/'SUMMARY.json',dict(comparisons=summary,scope='historically exposed typed-fragment versus accepted-model-stream chunks, not general human/AI provenance; writer selection and concatenation remain confounds',length_control='fixed 256-character chunks; constant-prior length rival retained'))
    freeze(out/'MODELS.json',dict(vocabulary={k:int(v) for k,v in vector.vocabulary_.items()},idf=vector.idf_.tolist(),models={k:dict(weights=m.coef_.tolist(),intercept=m.intercept_.tolist()) for k,m in models.items()}))
