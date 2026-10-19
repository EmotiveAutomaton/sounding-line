"""EV1: fixed-session within-writer pause slope from completed engine exports.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 6-7 reread October 19. A planted
within-session slope is recovered, its reversal reverses, and constant outcomes
give exactly zero. Session offsets cannot create a slope. Whole-writer resamples
retain all sessions; 200 within-session departure shuffles preserve every row.
Under null and alternative their slope reference is centered at zero; either-sign
bias above one quarter SD invalidates admission. Missing/changed evidence or
unidentifiable target fails closed. Exhaustive states: unsupported, invalid,
negative, null, marginal, positive. Association does not identify attention.
"""
from __future__ import annotations
from collections import Counter,defaultdict
import hashlib
import math
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from runners.stage14.common import read,atomic
from . import engine_export_full as reader,engine_d33_consumer as source
from . import timing_stats as stats,timing_pmap_stats as pmap,states_v2 as states
from .engine_signatures_guarded import boundary
from .timing_p6 import gzread,gzip_equal,write_equal

CONFIG=dict(mode='full-departure-pauses',permutations=200,draws=2000,seed=20261018)
CONSTRUCTED=dict(CONFIG,mode='constructed-departure-pauses')
COVARIATES=('population_surprisal','length','log_frequency','sentence_start','after_punctuation','personal_surprise')


def validate(inputs,config):
    expected={'reader_completion'} if config==CONFIG else {'fixture'} if config==CONSTRUCTED else None
    if expected is None or set(inputs)!=expected:raise ValueError('exact EV1 inputs/config required')


def load(inputs,config):
    validate(inputs,config)
    if config==CONSTRUCTED:return read(inputs['fixture'])
    root,plan=reader.authenticate(inputs['reader_completion'],'runners.drive.cards.engine_export_full')
    if plan['config']['mode']!='full-reader' or plan['config']['expected_sessions']!=1399:
        raise ValueError('complete fixed reader population required')
    joined=gzread(root/'output/JOINED.json.gz')
    original=source.original_rows(plan['inputs'],dict(mode='reader-pilot'))
    if [r['original'] for r in joined['rows']]!=original:raise ValueError('original D33 rows differ')
    if len(original)!=78602 or len({r['writer'] for r in original})!=41:
        raise ValueError('original D33 population changed')
    if not joined['engine_export_consumed'] or not joined['engine_scored']:
        raise ValueError('unscored join')
    return joined


def prepare(joined):
    original=[r['original'] for r in joined['rows']]
    identity=[(r['writer'],r['session'],r['index']) for r in original]
    if len(set(identity))!=len(identity):raise ValueError('duplicate original occurrence')
    dispositions=dict(Counter(r['disposition'] for r in joined['rows']))
    if dispositions!=joined['support']['dispositions'] or len(original)!=joined['support']['original_rows']:
        raise ValueError('support accounting differs')
    rows=[];session_writer={}
    for record in joined['rows']:
        r=record['original'];session=r['session'];writer=r['writer']
        if not isinstance(session,str) or not session or not isinstance(writer,str) or not writer:
            raise ValueError('missing identity')
        if session in session_writer and session_writer[session]!=writer:raise ValueError('session crosses writers')
        session_writer[session]=writer
        if record['disposition']!='engine-scored':
            if record.get('engine') is not None:raise ValueError('unsupported row has score')
            continue
        engine=record['engine']
        values=[engine['departure'],r['log_pause']]+[r[k] for k in COVARIATES]
        if any(type(x) not in (float,int) or not math.isfinite(x) for x in values):
            raise ValueError('nonfinite scored row')
        rows.append(dict(r,departure=engine['departure']))
    return sorted(rows,key=lambda r:(r['writer'],r['session'],r['index'])),dict(joined['support'])


def arrays(rows):
    x=np.asarray([[r['departure']]+[r[k] for k in COVARIATES] for r in rows],float)
    y=np.asarray([r['log_pause'] for r in rows],float)
    writers=np.asarray([r['writer'] for r in rows])
    positions=defaultdict(list)
    for i,r in enumerate(rows):positions[r['session']].append(i)
    cells=[np.array(positions[s],int) for s in sorted(positions)]
    # Session intercepts absorb the nested writer-intercept column space exactly.
    # Never drop a writer or session to remove this dummy-column redundancy.
    for ix in cells:x[ix]-=x[ix].mean(axis=0);y[ix]-=y[ix].mean()
    return x,y,writers,cells


def analyze(joined,config,progress=lambda value:None):
    rows,support=prepare(joined)
    if len({r['writer'] for r in rows})<3:
        return dict(card='EV1',state='unsupported',reason='fewer than three scored writers',support=support),dict(rows=rows)
    x,y,writers,cells=arrays(rows);groups=stats.sufficient(x,y,writers)
    effect,_=stats.fit(groups);rng=np.random.default_rng(config['seed']);boot=[]
    for draw in range(config['draws']):
        choice=rng.integers(len(groups),size=len(groups))
        boot.append(stats.fit([groups[i] for i in choice])[0])
        if (draw+1)%100==0:progress(dict(phase='writer-bootstrap',completed=draw+1,total=config['draws']))
    low,high=map(float,np.quantile(boot,[.025,.975]));se=float(np.std(boot,ddof=1))
    primary=dict(effect=effect,ci_low=low,ci_high=high,bootstrap_se=se,state=states.contrast_state(effect,low,high),
        writers=len(groups),observations=len(rows),sessions=len(cells),draws=config['draws'],
        interval='Whole-writer percentile bootstrap; refit session fixed effects in each resample')
    rng=np.random.default_rng(config['seed']);null=[];digests=[]
    for draw in range(config['permutations']):
        changed=x.copy()
        for ix in cells:changed[ix,0]=rng.permutation(x[ix,0])
        null.append(stats.fit(stats.sufficient(changed,y,writers))[0])
        digests.append(hashlib.sha256(changed[:,0].astype('<f8').tobytes()).hexdigest())
        if (draw+1)%10==0:progress(dict(phase='within-session-reference',completed=draw+1,total=config['permutations']))
    reference=pmap.distribution(null);reference.pop('one_sided_p',None)
    state='invalid' if reference['bias_flag'] else primary['state']
    summary=dict(card='EV1',state=state,primary=primary,within_session_reference=reference,
        support=support,scored_rows=len(rows),scored_writers=len(groups),scored_sessions=len(cells),
        constant_departure_sessions=int(sum(np.ptp(x[ix,0])==0 for ix in cells)),
        seed=config['seed'],bootstrap_draws=config['draws'],permutations=config['permutations'],
        intercepts='Fixed session intercepts span the nested writer and session intercept space',
        covariates=list(COVARIATES),weighting='Each eligible original word contributes once; uncertainty clusters whole writers',
        fake_writer_control='Not applicable: departure is computed per document, not from writer assignment',
        method='Log pre-word pause on page-normalized departure, session-demeaned with the exact original D33 nuisance/history terms',
        instrument=True,scientific_admission=False,
        badge='tested on human writing logs: flagged words came after longer pauses' if state=='positive' else 'tested: no pause association' if state=='null' else None)
    return summary,dict(rows=rows,bootstrap_slopes=boot,permutation_slopes=null,permutation_departure_sha256=digests)


def run(output,inputs,config,operation):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);boundary(output)
    if operation=='verify' or (output/'TIMING_BINDINGS.json').exists():stats.check_binding(output,inputs,config)
    def progress(value):boundary(output);atomic(output/'PROGRESS.json',value)
    with threadpool_limits(limits=1):
        joined=load(inputs,config);boundary(output)
        summary,detail=analyze(joined,config,progress);boundary(output)
    if operation=='execute':
        write_equal(output/'SUMMARY.json',summary);gzip_equal(output/'DETAIL.json.gz',detail)
        if not (output/'TIMING_BINDINGS.json').exists():stats.bind(output,inputs,config,['SUMMARY.json','DETAIL.json.gz'])
        return summary
    if read(output/'SUMMARY.json')!=summary or gzread(output/'DETAIL.json.gz')!=detail:
        raise ValueError('fresh complete pause comparison differs')
    return dict(verified=True,summary=summary,fresh_source_authentication=True,full_statistic_replay=True,full_control_replay=True)


def execute(output,inputs,config):return run(output,inputs,config,'execute')
def verify(output,inputs,config):return run(output,inputs,config,'verify')
