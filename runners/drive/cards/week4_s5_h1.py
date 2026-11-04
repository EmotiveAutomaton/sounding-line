"""S5: stops before expert-labelled planning runs in released ScholaWrite edits.

DESIGN CHECK: LESSONS 2-5, DECISION_TRACES 6 and its afterword reread
2026-11-02. Positive/zero/reversed constructed effects must retain their sign.
The case requires >=30 planning starts in each of >=6 project-scoped authors.
Missing/ambiguous gaps and >30-minute breaks are counted, never imputed. The
primary is within author, with centered fixed covariates and author/project
random intercepts. Centered X is orthogonal to both intercept designs, so its
GLS coefficient equals OLS for every positive variance choice. Dense GLS and
the certified mixed solver check that identity before bootstrap shortcuts.
Smaller route: all ScholaWrite identities are required; otherwise cost hold.
"""
from collections import Counter,defaultdict
from pathlib import Path
import math,time
import numpy as np
from sklearn.mixture import GaussianMixture
from threadpoolctl import threadpool_limits
from .week3_pp3_inputs import load as load_rows,CONFIG as SOURCE_CONFIG,envelope,digest
from .week3_pause_model import full_fit
from .timing_p6 import write_equal,gzip_equal,gzread,progress
from .timing_census import read,filehash
from .states_v2 import contrast_state

# Classification tolerance is numerical, fixed before empirical outcomes.
# The original constructed zero had a spurious negative interval at 1e-15.
ZERO_ATOL=1e-12
def result_state(estimate,interval):
    values=[0.0 if abs(float(v))<=ZERO_ATOL else float(v) for v in (estimate,*interval)]
    return contrast_state(*values)

SEED=20261102
CONFIG=dict(card='S5',gap_ceiling_seconds=1800,bootstrap=2000,permutations=200,seed=SEED,
    planning_starts_per_author=30,min_authors=6,expected_rows=61504)

def extract(rows,ceiling=1800):
    groups=defaultdict(list)
    for i,r in enumerate(rows):groups[(r['project'],r['author'])].append((i,r))
    records=[];audit=Counter();distributions=defaultdict(list)
    for (project,author),stream in sorted(groups.items()):
        stream.sort(key=lambda x:(x[1]['timestamp'],x[0]));times=Counter(r['timestamp'] for _,r in stream)
        previous=None;session_start=None;candidate=[]
        for ordinal,r in stream:
            audit['released_rows']+=1
            gap=None if previous is None else (r['timestamp']-previous['timestamp'])/1000
            missing=('first released row' if previous is None else 'ambiguous timestamp block'
                if times[r['timestamp']]!=1 or times[previous['timestamp']]!=1 else 'nonpositive interval' if gap<=0 else None)
            if session_start is None or (gap is not None and gap>ceiling):session_start=r['timestamp']
            high_start=previous is None or r['high-level']!=previous['high-level'] or (gap is not None and gap>ceiling)
            fine_start=previous is None or r['label']!=previous['label'] or (gap is not None and gap>ceiling)
            if missing:audit['missing: '+missing]+=1
            else:
                _,deleted,inserted=envelope(r['before text'],r['after text'])
                item=dict(ordinal=ordinal,project=digest({'project':project}),author=digest({'project':project,'author':author}),
                    category=r['high-level'],label=r['label'],gap_seconds=gap,high_start=high_start,fine_start=fine_start,
                    break_gap=gap>ceiling,log_edit_size=math.log1p(deleted+inserted),
                    log_session_elapsed=math.log1p((r['timestamp']-session_start)/1000),
                    visible_continuity=previous['after text']==r['before text'])
                candidate.append(item);audit['long_gaps']+=gap>ceiling
                audit['discontinuous_visible_views']+=not item['visible_continuity']
                distributions[r['label']].append(gap)
            previous=r
        eligible=[r['gap_seconds'] for r in candidate if not r['break_gap']]
        median=float(np.median(eligible)) if eligible else None
        for row in candidate:
            row['own_median_gap_seconds']=median
            row['log_relative_gap']=math.log(row['gap_seconds']/median) if median else None
        records.extend(candidate)
    return sorted(records,key=lambda r:r['ordinal']),dict(audit)

def center_by_author(x,authors):
    x=np.asarray(x,float).copy()
    for a in sorted(set(authors)):
        ix=np.flatnonzero(np.asarray(authors)==a);x[ix]-=x[ix].mean(0)
    return x

def solve(xx,xy):
    residual=xx[0,0]-xx[0,1:]@np.linalg.pinv(xx[1:,1:])@xx[1:,0]
    if not np.isfinite(residual) or residual<=1e-9:raise ValueError('Primary planning contrast not identifiable')
    return float((xy[0]-xx[0,1:]@np.linalg.pinv(xx[1:,1:])@xy[1:])/residual)

def fit_arrays(x,y,authors,projects,bootstrap=2000,permutations=200,seed=SEED,certify=True):
    x=center_by_author(x,authors);y=np.asarray(y,float)
    # Scaling is outcome-blind; zero nuisance columns remain explicit zeros.
    scales=x.std(0);scales[scales<1e-12]=1;x=x/scales
    xx=x.T@x;xy=x.T@y;effect=solve(xx,xy)/scales[0]
    mixed=None
    if certify:
        beta,mixed=full_fit(x,y,list(authors),list(projects))
        if not np.isclose(beta[0]/scales[0],effect,atol=1e-8,rtol=1e-7):raise ValueError('Certified random-intercept GLS/within-author identity failed')
    names=sorted(set(authors));indices=[np.flatnonzero(np.asarray(authors)==a) for a in names]
    blocks=[(x[ix].T@x[ix],x[ix].T@y[ix]) for ix in indices]
    rng=np.random.default_rng(seed);bank=[]
    for _ in range(bootstrap):
        weights=np.bincount(rng.integers(len(names),size=len(names)),minlength=len(names))
        # Each copy is a whole independent author; within-author centering stays exact.
        bank.append(solve(sum(w*b[0] for w,b in zip(weights,blocks)),sum(w*b[1] for w,b in zip(weights,blocks)))/scales[0])
    null=[]
    for _ in range(permutations):
        perm=x.copy()
        for ix in indices:perm[np.ix_(ix,[0,1])]=x[np.ix_(rng.permutation(ix),[0,1])]
        null.append(solve(perm.T@perm,perm.T@y)/scales[0])
    return dict(estimate=effect,interval=np.quantile(bank,[.025,.975]).tolist(),
        permutation_p=(1+sum(z>=effect for z in null))/(1+len(null)),bootstrap=bank,reference=null,
        authors=len(names),observations=len(y),mixed_model=mixed,
        estimand='Planning minus implementation in log gap / own median, among high-level run starts, within author.',
        random_effects='Project and project-scoped author random intercepts; fixed predictors centered within author.',
        bootstrap_method='Whole-author resampling; exact centered-GLS sufficient statistics; no successful-only filtering.')

def descriptive_mixtures(records):
    groups=defaultdict(list)
    for r in records:
        if not r['break_gap'] and r['log_relative_gap'] is not None:groups[r['author']].append(r)
    result={}
    for author,rows in sorted(groups.items()):
        z=np.array([r['log_relative_gap'] for r in rows])
        if len(z)<30 or len(np.unique(z))<3:
            result[author]=dict(state='unsupported',intervals=len(z));continue
        model=GaussianMixture(n_components=3,covariance_type='full',reg_covar=1e-6,tol=1e-4,max_iter=500,n_init=1,
            random_state=SEED,means_init=np.quantile(z,[.2,.65,.95]).reshape(3,1)).fit(z.reshape(-1,1))
        if not model.converged_:
            result[author]=dict(state='invalid',reason='nonconverged descriptive mixture',intervals=len(z));continue
        order=np.argsort(model.means_.ravel());posterior=model.predict_proba(z.reshape(-1,1))[:,order]
        if np.any(np.diff(model.means_.ravel()[order])<=1e-6) or np.any(model.weights_[order]<=1e-6):
            result[author]=dict(state='invalid',reason='collapsed descriptive mixture',intervals=len(z));continue
        summaries={}
        for category in ('PLANNING','IMPLEMENTATION','REVISION'):
            ix=[i for i,r in enumerate(rows) if r['category']==category]
            summaries[category]=dict(n=len(ix),posterior_means=posterior[ix].mean(0).tolist() if ix else None)
        labels={}
        for label in sorted({r['label'] for r in rows}):
            ix=[i for i,r in enumerate(rows) if r['label']==label]
            labels[label]=dict(n=len(ix),posterior_means=posterior[ix].mean(0).tolist())
        result[author]=dict(state='fitted descriptive mixture',intervals=len(z),log_means=model.means_.ravel()[order].tolist(),
            variances=model.covariances_.ravel()[order].tolist(),weights=model.weights_[order].tolist(),by_category=summaries,by_label=labels)
    return result

def label_contrasts(records,config):
    """The packet's fifteen-label companion; descriptive, no claim upgrade.

    Each label's fine-run starts versus other implementation fine-run starts.
    Both groups must occur within author; no arbitrary change of primary floor.
    These subsidiary summaries retain all unsupported labels explicitly.
    """
    result={}
    for label in sorted({r['label'] for r in records}):
        candidates=[r for r in records if not r['break_gap'] and r['fine_start'] and
                    (r['label']==label or r['category']=='IMPLEMENTATION')]
        counts=defaultdict(Counter)
        for r in candidates:counts[r['author']][r['label']==label]+=1
        eligible={a for a,c in counts.items() if c[True]>=2 and c[False]>=2}
        entry=dict(scope='Descriptive fine-label starts versus other implementation-label starts; no scientific claim upgrade.',
                   authors=len(eligible))
        if len(eligible)<2:
            entry.update(state='unsupported',reason='Fewer than two authors with two starts in both arms')
        else:
            rows=[r for r in candidates if r['author'] in eligible]
            x=np.array([[r['label']==label,0,r['log_edit_size'],r['log_session_elapsed']] for r in rows],float)
            try:
                fit=fit_arrays(x,[r['log_relative_gap'] for r in rows],[r['author'] for r in rows],
                    [r['project'] for r in rows],config['bootstrap'],config['permutations'],config['seed'])
                entry.update({k:v for k,v in fit.items() if k not in ('bootstrap','reference','permutation_p')})
                entry.update(state='descriptive',estimand='Named fine-label starts minus other implementation fine-label starts in log gap / own median.')
            except ValueError as error:
                entry.update(state='invalid',reason=str(error))
        result[label]=entry
    return result

def summarize(records,audit,config):
    usable=[r for r in records if not r['break_gap'] and r['high_start'] and r['log_relative_gap'] is not None]
    counts=defaultdict(Counter)
    for r in usable:counts[r['author']][r['category']]+=1
    eligible=sorted(a for a,c in counts.items() if c['PLANNING']>=config['planning_starts_per_author'] and c['IMPLEMENTATION']>0)
    summary=dict(card='S5',audit=audit,case_supported=len(eligible)>=config['min_authors'],
        qualifying_author_ids=len(eligible),required_authors=config['min_authors'],
        minimum_planning_starts=config['planning_starts_per_author'],source_scope='Filtered released change timestamps; project-scoped authors, not authenticated cross-project persons.',
        analysis_scope='Expert annotation, not self-reported planning; observational timing association, not an identified psychological cause.')
    if not summary['case_supported']:
        summary.update(state='design cannot test',reason='Insufficient planning-run starts across project-scoped author identities')
        return summary,dict(run_support={a:dict(c) for a,c in counts.items()})
    selected=[r for r in usable if r['author'] in eligible]
    x=np.array([[r['category']=='PLANNING',r['category']=='REVISION',r['log_edit_size'],r['log_session_elapsed']] for r in selected],float)
    y=[r['log_relative_gap'] for r in selected];authors=[r['author'] for r in selected];projects=[r['project'] for r in selected]
    fit=fit_arrays(x,y,authors,projects,config['bootstrap'],config['permutations'],config['seed'])
    summary['primary']={k:v for k,v in fit.items() if k not in ('bootstrap','reference')}
    summary['state']=result_state(fit['estimate'],fit['interval'])
    summary['sensitivity']='untested on the released population; known-answer instrument checks passed'
    distributions={}
    for label in sorted({r['label'] for r in records}):
        by={}
        for category,filtered in [('run_starts',[r for r in records if r['label']==label and r['fine_start'] and not r['break_gap']]),
            ('inside_runs',[r for r in records if r['label']==label and not r['fine_start'] and not r['break_gap']]),
            ('long_breaks',[r for r in records if r['label']==label and r['break_gap']])]:
            values=[r['gap_seconds'] for r in filtered]
            relative=[r['log_relative_gap'] for r in filtered if r['log_relative_gap'] is not None]
            by[category]=dict(n=len(values),quantiles=np.quantile(values,[0,.25,.5,.75,1]).tolist() if values else None,
                mean_log_relative_gap=float(np.mean(relative)) if relative else None)
        distributions[label]=by
    summary['label_gap_distributions']=distributions
    summary['fine_label_contrasts']=label_contrasts(records,config)
    mixtures=descriptive_mixtures(records)
    aggregate={}
    for category in ('PLANNING','IMPLEMENTATION','REVISION'):
        values=[v['by_category'][category]['posterior_means'] for v in mixtures.values()
                if v['state']=='fitted descriptive mixture' and v['by_category'][category]['n']]
        aggregate[category]=dict(author_ids=len(values),equal_author_posterior_mean=np.mean(values,axis=0).tolist() if values else None)
    summary['descriptive_mixture_summary']=dict(by_category=aggregate,fit_states=dict(Counter(v['state'] for v in mixtures.values())),
        normalization='Each project-scoped author own median eligible released gap; no physical-keypress or PP1 mechanical correction claim.')
    summary['descriptive_mixture_summary']['by_label']={}
    for label in sorted({r['label'] for r in records}):
        values=[v['by_label'][label]['posterior_means'] for v in mixtures.values() if v['state']=='fitted descriptive mixture' and label in v['by_label']]
        summary['descriptive_mixture_summary']['by_label'][label]=dict(author_ids=len(values),equal_author_posterior_mean=np.mean(values,axis=0).tolist() if values else None)
    private=dict(run_support={a:dict(c) for a,c in counts.items()},bootstrap=fit['bootstrap'],reference=fit['reference'],
        descriptive_author_mixtures=mixtures)
    return summary,private

def run(output,inputs,config,verification=False):
    if config!=CONFIG:raise ValueError('Frozen S5 configuration required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);started=time.process_time()
    rows=load_rows(inputs,SOURCE_CONFIG);records,audit=extract(rows,config['gap_ceiling_seconds'])
    with threadpool_limits(limits=1):summary,private=summarize(records,audit,config)
    summary['source_bindings']={k:filehash(v) for k,v in inputs.items()}
    if verification:
        if read(output/'SUMMARY.json')!=summary or read(output/'PRIVATE.json')!=private or gzread(output/'GAPS.json.gz')!=records:
            raise ValueError('S5 full source and model replay differs')
        return dict(verified=True,full_source_and_model_replay=True)
    write_equal(output/'SUMMARY.json',summary);write_equal(output/'PRIVATE.json',private);gzip_equal(output/'GAPS.json.gz',records)
    write_equal(output/'TIMING.json',dict(cpu_seconds=time.process_time()-started))
    return dict(status='complete',scientific_admission=False)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)

def known_arrays(effect=.7):
    rng=np.random.default_rng(SEED);authors=np.repeat(np.arange(8),36);projects=authors//2
    category=np.tile(np.repeat(np.arange(3),12),8)
    x=np.column_stack([category==0,category==2,rng.normal(size=len(authors)),rng.uniform(size=len(authors))])
    x=center_by_author(x,authors);noise=rng.normal(size=len(authors))
    for author in range(8):
        ix=np.flatnonzero(authors==author);z=np.column_stack([np.ones(len(ix)),x[ix]])
        noise[ix]-=z@np.linalg.lstsq(z,noise[ix],rcond=None)[0]
    y=x@np.array([effect,-.2,.3,.1])+authors*.3+projects*.7+noise
    return x,y,authors,projects
