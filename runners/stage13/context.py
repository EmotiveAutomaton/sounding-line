"""Readout, evidence and memory interventions on the same retrospective targets.

DESIGN CHECK: LESSONS 3-5. NULL: duplicated evidence is not independent support;
missing true candidates are charged, not dropped. ALTERNATIVE: declared context
and memory improve held-out process decisions without increasing wrong-context
harm. This CPU conditional-likelihood arm is GPT-2 medium, not the primary Qwen.
"""
from __future__ import annotations
import json
import time
from copy import deepcopy
import numpy as np
from .common import freeze,digest,atomic,now
from .scoring import proper_loss,interval
from .detectors import Detector
from .reconstruction import ACTIONS

_MEMORY={}
MODES=('none','raw-retrieval','linked-memory','old-answer','irrelevant','misleading','duplicated','independent','missing-candidate','wrong-location')


def evidence(row,view):
    original=row['views'][view]
    # Frozen bounded textual projection; exact locations are scored in the separate
    # full-endpoint contribution task, never on these clipped likelihood prompts.
    e=dict(endpoint_tail=original['endpoint'][-900:],endpoint_start=max(0,len(original['endpoint'])-900),menu_was_available=True)
    if view in ('C','D'):
        e['before_tail']=original['before'][-450:];e['alternatives']=[s[:160] for s in original['alternatives'][:5]]
    if view=='D':e['observed_operations']=original['observed_operations']
    return e


def intervention(row,training,mode):
    if mode not in MODES:raise ValueError('unknown memory/context treatment')
    from sklearn.feature_extraction.text import TfidfVectorizer
    cache_key=digest([x['key'] for x in training])
    if cache_key not in _MEMORY:
        vector=TfidfVectorizer(analyzer='char',ngram_range=(3,5),max_features=12000)
        matrix=vector.fit_transform([x['views']['A']['endpoint'] for x in training]);_MEMORY[cache_key]=(vector,matrix)
    vector,matrix=_MEMORY[cache_key]
    sim=(matrix@vector.transform([row['views']['A']['endpoint']]).T).toarray().ravel()
    ordered=[training[i] for i in sorted(range(len(training)),key=lambda i:(-float(sim[i]),training[i]['key']))]
    if any(x['unit']==row['unit'] for x in ordered):raise ValueError('memory crosses source split')
    chosen=ordered[:1]
    chosen+=next(([x] for x in ordered if x['unit']!=chosen[0]['unit']),[]) if chosen else []
    if mode=='independent' and len(chosen)<2:return None,[]
    # These are fixed prior source episodes, never evaluation outcome retrieval.
    raw=[dict(endpoint=x['views']['A']['endpoint'][-500:],recorded_handling=x['target']['handling']) for x in chosen]
    linked=[dict(endpoint=x['views']['A']['endpoint'][-500:],recorded_operations=x['target']['facts']) for x in chosen]
    data={'none':None,'raw-retrieval':raw[:1],'linked-memory':linked[:1],
        'old-answer':('Prior stored answer: '+chosen[0]['target']['handling']) if chosen else None,
        'irrelevant':'Unrelated context: the weather station was repainted last year.',
        'misleading':'Unverified contextual claim: the writer always accepts every offered suggestion without changing it.',
        'duplicated':raw[:1]*2,'independent':raw,'missing-candidate':None,
        'wrong-location':'Unverified contextual claim: the offered text was inserted at the very beginning of the document.'}[mode]
    serialized=json.dumps(data,ensure_ascii=False)
    return serialized[:700] if data is not None else '',[x['key'] for x in chosen] if mode in ('raw-retrieval','linked-memory','old-answer','duplicated','independent') else []


def conditional(model,prompt,labels):
    torch=model.torch;tok=model.tokenizer
    prefix=tok.encode(prompt,add_special_tokens=False)
    if len(prefix)>512:raise ValueError('native prefix token budget exceeded')
    scores=[];tokens=[]
    for label in labels:
        suffix=tok.encode(' '+label,add_special_tokens=False)
        if not suffix or len(suffix)>32:raise ValueError('candidate token admission failed')
        ids=torch.tensor([prefix+suffix],dtype=torch.long)
        with torch.inference_mode():logits=model.model(input_ids=ids).logits[0].float()
        positions=logits[len(prefix)-1:len(prefix)+len(suffix)-1]
        target=ids[0,len(prefix):]
        score=(positions.gather(1,target[:,None]).squeeze(1)-torch.logsumexp(positions,-1)).sum().item()
        scores.append(score);tokens.append(suffix)
    p=np.exp(np.array(scores)-max(scores));p/=p.sum()
    return p.tolist(),dict(raw_log_likelihoods=scores,candidate_token_ids=tokens,prefix_tokens=len(prefix),readout='total candidate-sequence likelihood, normalized only by the declared likelihood model; not repaired elicited probabilities')


def run(rows,training,out,raw,modes=MODES,views=('A','C'),tick=None):
    model=Detector('gpt2-medium-logrank',raw);records=[];start=time.perf_counter()
    for row in rows:
        for view in views:
            e=evidence(row,view)
            for mode in modes:
                if tick:tick()
                memory,ids=intervention(row,training,mode)
                if memory is None:
                    records.append(dict(key=row['key'],unit=row['unit'],partition=row['partition'],view=view,mode=mode,unavailable='fewer than two independent training components',scores=None));continue
                call_start=time.perf_counter()
                labels=list(ACTIONS)+['unknown'];omitted=None
                if mode=='missing-candidate':
                    omitted=int(digest(row['key'])[:8],16)%4;labels.pop(omitted)
                base=model.tokenizer.decode(model.tokenizer.encode(json.dumps(e,ensure_ascii=False),add_special_tokens=False)[:260])
                memory=model.tokenizer.decode(model.tokenizer.encode(memory,add_special_tokens=False)[:100])
                prompt='Evidence from a completed writing episode: '+base+'\nContext/memory: '+memory+'\nPossible recorded actions: '+', '.join(labels)+'.\nRecorded action:'
                p,trace=conditional(model,prompt,labels)
                expanded=[0.]*5
                for label,value in zip(labels,p):expanded[(list(ACTIONS)+['unknown']).index(label)]=value
                truth=ACTIONS.index(row['target']['handling'])
                score=proper_loss(expanded,truth,5)
                record=dict(key=row['key'],unit=row['unit'],partition=row['partition'],view=view,mode=mode,probabilities=expanded,
                    truth=truth,omitted_candidate=omitted,true_candidate_omitted=omitted==truth,memory_source_ids=ids,
                    prompt_sha256=digest(prompt),trace=trace,scores=score,elapsed_seconds=time.perf_counter()-call_start,source_projection='bounded retrospective tails; no complete-span claim')
                records.append(record)
                freeze(out/'rows'/f"{row['key']}-{view}-{mode}.json",record)
                atomic(out/'PROGRESS.json',dict(at=now(),rows=len(records),elapsed_seconds=time.perf_counter()-start))
    result=dict(rows=records,identity=model.identity,scope='historically exposed human records; controlled analyst memory/context; conditional likelihood named model variant')
    freeze(out/'PREDICTIONS.json',result);return result


def summarize(records):
    grouped={}
    unavailable=[r for r in records if r.get('scores') is None]
    for r in records:
        if r.get('scores') is None:continue
        grouped.setdefault((r['partition'],r['view'],r['mode']),[]).append(r)
    results={}
    for (partition,view,mode),rows in sorted(grouped.items()):
        results[partition+'/'+view+'/'+mode]={metric:interval([r['scores'][metric] for r in rows],[r['unit'] for r in rows]) for metric in ('brier','log_loss','correct')}
        results[partition+'/'+view+'/'+mode]['omitted_truth_attempts']=sum(r['true_candidate_omitted'] for r in rows)
    return dict(status='complete',comparisons=results,unavailable=unavailable,scope='same model and bounded evidence projection; context effects include potentially useful and harmful controls',
        unknowns=['synthetic controlled context is not naturally occurring public context','cross-model elicited confidence is not a within-model readout contrast'])
