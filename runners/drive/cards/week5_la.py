"""LA: laugh-safe dialogue features, matched conditional model and joining.

DESIGN CHECK: LESSONS3--5, CONTROLS1--6, 2026-11-07. Laugh marks never enter
predictors. Masked paired scoring uses identical old-token support in both
arms. Null/reversal plants, absent labels and exact identity cases must remain
reachable. No inference from incomplete source or selected-model banks.
"""
from collections import defaultdict
from bisect import bisect_right
from pathlib import Path
import math,re
import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp,softmax
from threadpoolctl import threadpool_limits
from .timing_census import read,filehash
from .timing_p6 import gzread,write_equal
from .week5_at_analysis import outcome
from .week5_at_scoring import SEED

LAUGH=re.compile(r'(laugh|laughter|breath[- ]laugh|while[- ]laughing)',re.I)


def safe_words(words):
    """Explicit annotation flags override lexical rendering; no tag survives."""
    return [w for w in words if w.get('kind')=='word' and not w.get('laugh',False)
            and not LAUGH.search(w.get('annotation',''))]


def labelled_acts(acts,laughs,window=2.,left=1.,others_only=False):
    out=[];by_meeting=defaultdict(list)
    for e in laughs:by_meeting[e['meeting']].append(e)
    for meeting in by_meeting:by_meeting[meeting].sort(key=lambda e:e['start'])
    starts={m:[e['start'] for e in events] for m,events in by_meeting.items()}
    maximum={m:max((e['end']-e['start'] for e in events),default=0) for m,events in by_meeting.items()}
    for act in sorted(acts,key=lambda a:(a['meeting'],a['start'],a['end'],a['speaker'])):
        m=act['meeting'];events=by_meeting[m];s=starts.get(m,[])
        lo=bisect_right(s,act['end']-left-maximum.get(m,0)-1e-9)
        hi=bisect_right(s,act['end']+window)
        hits=[e for e in events[lo:hi] if
              (not others_only or e['speaker']!=act['speaker']) and
              e['end']>=act['end']-left and e['start']<=act['end']+window]
        words=safe_words(act['words']);text=' '.join(w['text'] for w in words)
        out.append({k:v for k,v in act.items() if k!='words'}|dict(text=text,word_count=len(words),
                   laughed_after=bool(hits),own_laugh=any(e['speaker']==act['speaker'] for e in hits),
                   other_laugh=any(e['speaker']!=act['speaker'] for e in hits),removed_marks=len(act['words'])-len(words)))
    return out


def matched_sets(acts,ratio=.2):
    pools=defaultdict(list)
    for a in acts:
        if not a['laughed_after']:pools[(a['meeting'],a['speaker'],a['act_type'])].append(a)
    sets=[];unsupported=0
    for case in acts:
        if not case['laughed_after']:continue
        eligible=[a for a in pools[(case['meeting'],case['speaker'],case['act_type'])]
                  if abs(a['word_count']-case['word_count'])<=max(2,ratio*case['word_count'])]
        eligible.sort(key=lambda a:(abs(a['word_count']-case['word_count']),a['start'],a['id']))
        if not eligible:unsupported+=1;continue
        sets.append(dict(meeting=case['meeting'],case=case['id'],members=[case]+eligible[:5]))
    return sets,unsupported


class ResolutionScorer:
    def __init__(self,model,tokenizer,torch,max_tokens=512,mask_batch=16):
        self.model,self.tokenizer,self.torch=model,tokenizer,torch
        self.max_tokens,self.mask_batch=max_tokens,mask_batch

    def _pll(self,ids,positions):
        torch=self.torch;values=[]
        for offset in range(0,len(positions),self.mask_batch):
            selected=positions[offset:offset+self.mask_batch]
            batch=torch.tensor([ids]*len(selected),dtype=torch.long,device='cpu')
            truth=batch[torch.arange(len(selected)),selected].clone()
            batch[torch.arange(len(selected)),selected]=self.tokenizer.mask_token_id
            with torch.inference_mode():
                logits=self.model(input_ids=batch).logits[torch.arange(len(selected)),selected].float()
                nll=torch.nn.functional.cross_entropy(logits,truth,reduction='none')
            values.extend((-nll).tolist())
        if not values or not np.isfinite(values).all():raise ValueError('Unsupported masked target')
        return values

    def score(self,previous,current):
        """Mask only old tokens; the same old support is scored in both arms."""
        past=self.tokenizer(previous,add_special_tokens=False)['input_ids']
        future=self.tokenizer(' '+current,add_special_tokens=False)['input_ids']
        capacity=self.max_tokens-2-len(future)
        if capacity<1 or not past:raise ValueError('Current act leaves no masked old support')
        dropped=max(0,len(past)-capacity);past=past[-capacity:]
        before=self.tokenizer.build_inputs_with_special_tokens(past)
        after=self.tokenizer.build_inputs_with_special_tokens(past+future)
        # Require a single leading special token and exact retained old IDs.
        if before[1:1+len(past)]!=past or after[1:1+len(past)]!=past:
            raise ValueError('Masked tokenizer special-token layout differs')
        positions=list(range(1,len(past)+1))
        old=self._pll(before,positions);new=self._pll(after,positions)
        return dict(resolution_nats_per_token=float(np.mean(np.array(new)-np.array(old))),
                    old_tokens=len(past),old_tokens_dropped=dropped,current_tokens=len(future),
                    before_logprobs=old,after_logprobs=new)


def conditional_fit(groups):
    arrays=[np.asarray(g,float) for g in groups]
    if not arrays or any(len(x)<2 or x.shape[1]!=2 or not np.isfinite(x).all() for x in arrays):
        raise ValueError('Conditional model lacks complete matched sets')
    differences=np.concatenate([x-x[0] for x in arrays])
    if np.linalg.matrix_rank(differences)<2:raise ValueError('Resolution/surprise not separately identifiable')
    def objective(beta):
        value=0.;gradient=np.zeros(2)
        for x in arrays:
            logits=x@beta;p=softmax(logits)
            value+=logsumexp(logits)-logits[0]
            gradient+=x.T@p-x[0]
        return value,gradient
    fitted=minimize(lambda b:objective(b),np.zeros(2),jac=True,method='BFGS',options={'gtol':1e-7,'maxiter':1000})
    if not np.isfinite(fitted.x).all() or np.max(np.abs(objective(fitted.x)[1]))>1e-5:
        raise ValueError('Conditional likelihood lacks optimality certificate')
    return fitted.x


def la1(acts,draws=2000):
    sets,unsupported=matched_sets(acts)
    if not sets:return dict(card='LA1',state='unsupported',reason='No matched laugh/non-laugh acts',unmatched=unsupported)
    raw=np.array([[r['resolution'],r['surprise']] for g in sets for r in g['members']],float)
    center=raw.mean(0);scale=raw.std(0)
    if np.any(scale<=1e-12):raise ValueError('Constant predictor')
    groups=[(np.array([[r['resolution'],r['surprise']] for r in g['members']])-center)/scale for g in sets]
    meetings=sorted({g['meeting'] for g in sets})
    if len(meetings)<2:
        point=conditional_fit(groups)
        return dict(card='LA1',state='below floor, descriptive',pooled_coefficients=point.tolist(),
                    primary=dict(state='invalid',reason='One meeting cannot supply meeting-cluster uncertainty'),meetings=len(meetings))
    lookup={m:[i for i,g in enumerate(sets) if g['meeting']==m] for m in meetings}
    point=conditional_fit(groups);rng=np.random.default_rng(SEED);samples=[]
    for _ in range(draws):
        selected=rng.choice(meetings,size=len(meetings),replace=True)
        samples.append(conditional_fit([groups[i] for m in selected for i in lookup[m]]))
    samples=np.asarray(samples)
    return dict(card='LA1',primary=outcome(point[0],samples[:,0],math.log(1.10)),
                secondary_surprise=outcome(point[1],samples[:,1],math.log(1.10)),
                matched_sets=len(sets),unmatched_laughed_acts=unsupported,meetings=len(meetings),
                scope='below floor, descriptive' if len(meetings)<20 else 'descriptive',
                coefficient_scale='log odds per full-bank predictor SD',resolution_sd=float(scale[0]),surprise_sd=float(scale[1]))


def joining_pairs(laughs,metadata,background='native_language'):
    by_meeting=defaultdict(lambda:defaultdict(list));out=[]
    for e in laughs:by_meeting[e['meeting']][e['speaker']].append(e['start'])
    for meeting,speakers in sorted(by_meeting.items()):
        ids=sorted(metadata[meeting]['speakers'])
        duration=metadata[meeting]['duration']
        for i,a in enumerate(ids):
            for b in ids[i+1:]:
                ba=metadata[meeting]['speakers'].get(a,{}).get(background)
                bb=metadata[meeting]['speakers'].get(b,{}).get(background)
                if not ba or not bb:continue
                sa=np.asarray(speakers.get(a,[]));sb=np.asarray(speakers.get(b,[]))
                # A participant with no laugh has no defined fraction of their
                # events joined; do not manufacture zero-valued observations.
                if not len(sa) or not len(sb):continue
                joined=(np.mean([np.any(np.abs(sb-t)<=1.) for t in sa])+
                        np.mean([np.any(np.abs(sa-t)<=1.) for t in sb]))/2
                out.append(dict(meeting=meeting,joined=float(joined),same=int(ba==bb),
                                rate_a=len(sa)/duration,rate_b=len(sb)/duration))
    return out


def la2(rows,draws=2000):
    if not rows:return dict(card='LA2',state='unsupported',reason='No labelled participant pairs')
    meetings=sorted({r['meeting'] for r in rows})
    def fit(selected):
        x=[];y=[]
        for m in selected:
            rr=[r for r in rows if r['meeting']==m]
            a=np.array([[r['same'],r['rate_a'],r['rate_b']] for r in rr]);b=np.array([r['joined'] for r in rr])
            if len(meetings)>=20:x.extend(a-a.mean(0));y.extend(b-b.mean())
            else:x.extend(np.c_[a,np.ones(len(a))]);y.extend(b)
        x=np.asarray(x);y=np.asarray(y)
        if np.std(x[:,0])<=1e-12:raise ValueError('No within-meeting background contrast')
        if np.linalg.matrix_rank(x)<=np.linalg.matrix_rank(x[:,1:]):raise ValueError('Background and base rates are not separately identifiable')
        return float(np.linalg.lstsq(x,y,rcond=1e-10)[0][0])
    try:point=fit(meetings)
    except ValueError as error:return dict(card='LA2',state='unsupported',reason=str(error),meetings=len(meetings),pairs=len(rows))
    if len(meetings)<2:return dict(card='LA2',state='below floor, descriptive',pooled_effect=point,
                                  primary=dict(state='invalid',reason='One meeting cannot supply meeting-cluster uncertainty'),meetings=len(meetings))
    rng=np.random.default_rng(SEED);samples=[];failed=[]
    for i in range(draws):
        try:samples.append(fit(rng.choice(meetings,len(meetings),replace=True)))
        except ValueError:samples.append(None);failed.append(i)
    if failed:return dict(card='LA2',primary=dict(state='invalid',reason='Undefined cluster refits retained',failed_draws=failed),
                          meetings=len(meetings),pairs=len(rows))
    return dict(card='LA2',primary=outcome(point,samples,.02),meetings=len(meetings),pairs=len(rows),
                scope='below floor, descriptive' if len(meetings)<20 else 'descriptive',
                estimator='pooled with intercept' if len(meetings)<20 else 'within meeting')


def run(output,inputs,config,verifying=False):
    rows=gzread(inputs['rows']);draws=config.get('draws',2000)
    if draws not in (200,2000):raise ValueError('Unregistered uncertainty count')
    with threadpool_limits(limits=2):
        result=la1(rows,draws) if config['card']=='LA1' else la2(rows,draws) if config['card']=='LA2' else None
    if result is None:raise ValueError('Unregistered LA card')
    result['descriptive']=True
    if draws==200:result['screening_only']=True
    binding=dict(rows_sha256=filehash(inputs['rows']),config=config);root=Path(output)
    if verifying:
        if read(root/'RESULT.json')!=result or read(root/'BINDING.json')!=binding:
            raise ValueError('Complete laughter refit differs')
        return dict(verified=True,complete_refit=True)
    write_equal(root/'RESULT.json',result);write_equal(root/'BINDING.json',binding)
    return dict(status='complete',card=config['card'])


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
