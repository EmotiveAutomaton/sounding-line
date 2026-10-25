"""FR1 fixed style distances, planted calibration and paired writer references.

DESIGN CHECK: LESSONS 3-5 and mid-run errata rules4-5, 2026-10-25.
Identical profiles cannot yield a person advantage; planted held-out writer text
must increase self-proximity at20% then40%. Primary and whole-profile fake
references retain identical rows. Writers are the bootstrap unit in both arms.
Within-writer arm swaps are a distinct reference whose nonzero mean flags bias.
"""
from collections import Counter,defaultdict

import numpy as np

from .timing_text import WORD


def style(tokens,dictionary):
    names=dictionary['words']+dictionary['punctuation']
    if len(set(names))!=len(names) or not names or not tokens:raise ValueError('invalid fixed style roster or empty text')
    counts=Counter(tokens)
    return np.asarray([counts[t]/len(tokens) for t in names],float)


def plant(neutral,heldout,words):
    boundaries=[i for i,t in enumerate(neutral) if WORD.fullmatch(t)]
    held=[i for i,t in enumerate(heldout) if WORD.fullmatch(t)]
    if len(boundaries)!=50 or len(held)<words:raise ValueError('plant requires50neutral words and enough held-out words')
    stop=held[words] if len(held)>words else len(heldout)
    return heldout[:stop]+neutral[boundaries[words]:]


def features(data,dictionary):
    writers=sorted(w for w,p in data['profiles'].items() if p['support'])
    profiles=np.asarray([style(data['profiles'][w]['tokens'],dictionary) for w in writers])
    rows=[]
    for pair in data['pairs']:
        writer=pair['event']['writer'];index=writers.index(writer);values={}
        for arm in ('event','control'):
            window=style(pair[arm]['window']['tokens'],dictionary)
            context=np.asarray([style(r['tokens'],dictionary) for r in pair['context'][arm]])
            reference=np.abs(context[:,None,:]-profiles[None,:,:]).sum(2).mean(0)
            values[arm]=reference-np.abs(profiles-window).sum(1)
        neutral=pair['context']['event'][0]['tokens'];held=data['profiles'][writer]['heldout_tokens']
        distances=[float(np.abs(style(t,dictionary)-profiles[index]).sum()) for t in
                   (neutral,plant(neutral,held,10),plant(neutral,held,20))]
        pauses=[pair[a]['window']['pause_seconds'] for a in ('event','control')]
        rows.append(dict(writer=writer,kind=pair['event']['kind'],id=pair['event']['id'],
            delta_by_profile=(values['event']-values['control']).tolist(),
            calibration20=distances[0]-distances[1],calibration40_increment=distances[1]-distances[2],
            pause_delta=None if any(v is None for v in pauses) else float(pauses[0]-pauses[1])))
    return dict(profile_writers=writers,rows=rows,source_summary=data['summary'],
        style_definition='L1 distance in fixed PMAP100 frequent-word and punctuation relative-frequency coordinates; denominator all produced word/punctuation tokens',
        calibration_definition='10 and20 held-out words replace first10/20 of a matched different-writer neutral50wordwindow; context baseline cancels')


def grouped(rows,key):
    groups=defaultdict(list)
    for row in rows:
        if row[key] is not None:groups[row['writer']].append(row[key])
    return {w:float(np.mean(v)) for w,v in sorted(groups.items())}


def interval(values,rng,n):
    values=np.asarray(values,float)
    if not len(values):return dict(mean=None,ci95=None,writers=0)
    means=np.mean(values[rng.integers(0,len(values),(n,len(values)))],axis=1)
    return dict(mean=float(values.mean()),ci95=np.quantile(means,[.025,.975]).tolist(),writers=len(values))


def contrast(rows,profile_writers,rng,bootstraps,permutations):
    names=sorted({r['writer'] for r in rows})
    if not names:return dict(state='unsupported',rows=0,writers=0)
    ownership={w:i for i,w in enumerate(profile_writers)}
    matrix=np.asarray([r['delta_by_profile'] for r in rows],float)
    if matrix.shape!=(len(rows),len(profile_writers)) or not np.isfinite(matrix).all():raise ValueError('invalid same-row profile matrix')
    ids=np.asarray([names.index(r['writer']) for r in rows]);own_columns=np.asarray([ownership[r['writer']] for r in rows])
    own=matrix[np.arange(len(rows)),own_columns]
    avg=lambda x:np.asarray([x[ids==i].mean() for i in range(len(names))])
    writer_own=avg(own);observed=float(writer_own.mean())
    fake_bank=[];arm_bank=[]
    for _ in range(permutations):
        assignment=rng.permutation(len(profile_writers))
        fake_bank.append(avg(matrix[np.arange(len(rows)),assignment[own_columns]]))
        arm_bank.append(float(avg(own*rng.choice([-1,1],len(rows))).mean()))
    fake_bank=np.asarray(fake_bank);arms=np.asarray(arm_bank)
    own_minus_fake=writer_own-fake_bank.mean(0)
    sd=float(np.std(arms,ddof=1));mean=float(arms.mean())
    biased=abs(mean)>.25*sd if sd else mean!=0
    result=dict(rows=len(rows),writers=len(names),primary=interval(writer_own,rng,bootstraps),
                own_minus_fake=interval(own_minus_fake,rng,bootstraps),fake_primary_mean=float(fake_bank.mean()),
                arm_label_reference=dict(mean=mean,sd=sd,ci95=np.quantile(arms,[.025,.975]).tolist(),
                  one_sided_p=float((1+np.sum(arms>=observed))/(permutations+1)),biased_reference=bool(biased)),
                full_profile_fake_draws=permutations,arm_label_draws=permutations)
    return result


def analyze(value,seed=20261026,bootstraps=2000,permutations=200):
    if seed!=20261026 or bootstraps<1 or permutations<2:raise ValueError('fixed seed and positive reference sizes required')
    rng=np.random.default_rng(seed);rows=value['rows']
    primary=[r for r in rows if r['kind']=='frustration'];secondary=[r for r in rows if r['kind']=='deleted']
    calibration={key:interval(list(grouped(primary,key).values()),rng,bootstraps) for key in ('calibration20','calibration40_increment')}
    calibrated=all(v['ci95'] is not None and v['ci95'][0]>0 for v in calibration.values())
    if not value['source_summary']['support'] or not calibrated:
        return dict(card='FR1',state='unsupported' if not value['source_summary']['support'] else 'invalid_calibration',
                    source_summary=value['source_summary'],calibration=calibration,calibration_pass=calibrated,
                    scientific_admission=False,descriptive_probabilities_only=True,
                    primary=dict(state='not_run_gate_closed'),secondary_deleted=dict(state='not_run_gate_closed'))
    result=dict(card='FR1',calibration=calibration,calibration_pass=calibrated,
                source_summary=value['source_summary'],primary=contrast(primary,value['profile_writers'],rng,bootstraps,permutations),
                secondary_deleted=contrast(secondary,value['profile_writers'],rng,bootstraps,permutations),
                secondary_pause=interval(list(grouped(primary,'pause_delta').values()),rng,bootstraps),
                control_contract='same occurrence rows; whole-profile labels reassigned including fixed points; writer-paired own-minus-mean-fake bootstrap; independent within-writer arm-label swaps',
                sensitivity='plant validates distance ruler, not primary contrast power; null effect-size sensitivity remains unquantified')
    p=result['primary'];supported=value['source_summary']['support']
    if not supported:state='unsupported'
    elif not calibrated:state='invalid_calibration'
    elif p['arm_label_reference']['biased_reference']:state='descriptive_only_biased_reference'
    elif p['primary']['ci95'][0]>0 and p['own_minus_fake']['ci95'][0]>0 and p['arm_label_reference']['one_sided_p']<.05:state='positive'
    elif p['primary']['ci95'][1]<0 and p['own_minus_fake']['ci95'][1]<0:state='negative'
    else:state='not_detected_sensitivity_unquantified'
    result.update(state=state,scientific_admission=state in ('positive','negative'),descriptive_probabilities_only=True)
    return result
