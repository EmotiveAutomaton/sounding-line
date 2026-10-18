"""Original D4 predictions and200 exact candidate-loss outcome permutations.

DESIGN CHECK: LESSONS3-5. No new fit/threshold; permutations change selected
positions within writer and menu size separately in calibration/test and
reselect penalties. Same candidate losses are independently checked against
original scalar scoring. Pure contradictory votes give exact uniform/null;
aligned and reversed targets retain opposite signs. Biased nulls flag openly.
"""
import numpy as np
from . import events_d4_stats as original
from .menus_io import assert_equal


def loss_table(models,rows,vectors):
    maximum=max(len(r['options']) for r in rows);table=np.full((len(rows),maximum,len(models)),np.nan)
    for i,row in enumerate(rows):
        for j,model in enumerate(models):
            p=original.probabilities(vectors[row['options']],model['coefficients'])
            table[i,:len(p),j]=[original.half_brier(p,k) for k in range(len(p))]
    return table


def session_average(rows,values):
    # values: permutations x rows x candidates. Preserve original equal-session
    # means and sorted session traversal, rather than changing row weights.
    keys=sorted({r['session'] for r in rows})
    return np.mean([values[:,[i for i,r in enumerate(rows) if r['session']==key]].mean(axis=1) for key in keys],axis=0)


def permutation_scores(models,calibration,test,vectors,writer,seed=20261018,permutations=200):
    chosen={};audits={}
    for phase,rows in (('calibration',calibration),('test',test)):
        chosen[phase]=[];audits[phase]=[]
        for index in range(permutations):
            shuffled,audit=original.permuted_choices(rows,original.stable_seed(seed,f'{writer}:{phase}:{index}'))
            chosen[phase].append([r['chosen'] for r in shuffled]);audits[phase].append(audit)
        chosen[phase]=np.asarray(chosen[phase],int)
    losses={};selected={};components={}
    uniform=np.asarray([original.half_brier([1/len(r['options'])]*len(r['options']),0) for r in test])
    uniform_mean=original.session_mean(test,uniform)
    for kind in ('content','housekeeping'):
        calibration_table=loss_table(models[kind],calibration,vectors)
        test_table=loss_table(models[kind],test,vectors)
        values=calibration_table[np.arange(len(calibration))[None,:],chosen['calibration'],:]
        loss=session_average(calibration,values);choice=np.argmin(loss,axis=1)
        all_test=test_table[np.arange(len(test))[None,:],chosen['test'],:]
        mean=session_average(test,all_test)
        components[kind]=uniform_mean-mean[np.arange(permutations),choice]
        selected[kind]=choice.tolist();losses[kind]=loss.tolist()
    contrast=components['content']-components['housekeeping']
    return dict(primary=contrast.tolist(),content_gain=components['content'].tolist(),housekeeping_gain=components['housekeeping'].tolist(),
        selected=selected,calibration_losses=losses,choice_positions={k:v.tolist() for k,v in chosen.items()},audit=audits)


def fit_writer(data,units,vectors,config):
    result=dict(writer=data['writer'],exclusion=data['exclusion'],arms={},models={},cohesion={})
    if data['exclusion']:return result
    for origin in ('model','own'):
        if not all(v['eligible'] for v in data['support'][origin].values()):continue
        models={}
        for kind in ('content','housekeeping'):
            indices=data['support'][origin][kind]['indices'];votes=units[indices]
            models[kind]=[original.fit_votes(votes,p) for p in original.PENALTIES]
            result['cohesion'][origin+'_'+kind]=original.cross_session_cohesion([data['corrections'][i] for i in indices],votes)
        result['models'][origin]=models
        result['arms'][origin]=original.score_pair(models,data['calibration'],data['test'],vectors)
        if origin=='model':result['permutations']=permutation_scores(models,data['calibration'],data['test'],vectors,data['writer'],config['seed'],config['permutations'])
        else:result['arms']['model_on_own_support']=result['arms']['model']
    return result


def summarize(writers,data,config):
    # Original deterministic summary including own-text specification/cohesion;
    # its obsolete one-shuffle slot is replaced explicitly by the200 reference.
    result=original.summarize(writers,config);result['comparisons'].pop('model_outcome_shuffle')
    eligible=[w for w in writers if 'model' in w['arms']]
    if len(eligible)<2:
        control=dict(state='invalid',reason='fewer than two supported writers',p_one_sided=None)
    else:
        values=np.mean([w['permutations']['primary'] for w in eligible],axis=0)
        if len(values)!=200 or not np.isfinite(values).all():raise ValueError('incomplete D4 permutation reference')
        mean=float(values.mean());sd=float(values.std(ddof=1));point=result['primary']['effect']
        control=dict(state='valid_reference',draws=200,values=values.tolist(),mean=mean,sd=sd,
            quantiles95=np.quantile(values,[.025,.975]).tolist(),p_one_sided=float((1+np.sum(values>=point))/201),
            biased_pipeline_flag=abs(mean)>.25*sd)
    result.update(outcome_permutation=control,card='D4-predictive-canonical',config=config,
        original_D4_unchanged_and_held=True,eligible_writers=len(eligible),writers=len(writers),scientific_admission=False,
        support={r['writer']:r['support'] for r in data},
        exclusions=[dict(writer=w['writer'],reason=w['exclusion']) for w in writers if w['exclusion']],
        source_caveat='P5 sentence-window before/after vectors may include unchanged context. Exact accepted-owner eligibility retained; canonical labels repair later-choice identity, not causal preference identification.',
        shuffle='200 phase-separated within-writer/menu-size permutations seed20261018; same supported choices and correction models, calibration penalty selected again; no redraw or subset selection',
        bootstrap_scope='Original equal-writer bootstrap of fixed held-out scores; independent writer-specific fits, intervals condition on those fits and support.',
        original_warning='Original D4 output remains source-held; prior null and single-shuffle results are preserved, not replaced in place.')
    return result
