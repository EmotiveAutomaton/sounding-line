"""Separate D32 timing repair: pilot and full-main projections use their own scopes.

DESIGN CHECK: LESSONS3-5. Preserve source-defined support, clustering, covariates,
objective, original bootstrap draws and negative direction. Refit leave-writer-out
appeal for each resampled writer population. Missing choices or changed support
fail closed; fit failures stay invalid. Pilot reports timing only, never a verdict.
Known null/reversed/planted controls and complete fresh replay precede production.
"""
import copy
import math
import time
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

from . import events_d32 as original
from . import menus_canonical_selection as canonical
from .events_d4 import save, read_sealed, sealed, assert_close
from .events_d4_sources import bind_completed
from .menus_io import read, sha256, input_hashes, write

CONFIG = dict(bootstrap=2000, seed=20261017, permutations=200, permutation_seed=20261018,
              threads=1, mode='main')
PILOT_CONFIG = dict(CONFIG, mode='pilot')
INPUTS = {'sessions','selection_reader','selection_complete','original_complete'}


def correct_rows(rows, sessions, audit):
    by_key = {r['key']:r for s in sessions for r in s['rows']}
    if len(by_key) != sum(len(s['rows']) for s in sessions):
        raise ValueError('D32 duplicate source menu')
    proofs = {key:audit.join(row) for key,row in by_key.items()}
    corrected=[];seen=set();changed=0
    for row in rows:
        key=(row['key'],row['position'])
        if key in seen:raise ValueError('D32 duplicate eligible offer')
        seen.add(key);menu=by_key[row['key']];proof=proofs[row['key']]
        selected=menu['handling'] in ('accept','edit')
        actual=proof['canonical_positions'];old=proof['prepared_positions']
        if selected and (len(actual)!=1 or len(old)!=1 or not proof['verified_insertion'] or not proof['canonical_usable']):
            raise ValueError('D32 choice support differs')
        if not selected and actual:raise ValueError('D32 unselected menu has a choice')
        if row['writer']!=menu['writer'] or row['session']!=menu['session']:
            raise ValueError('D32 menu identity differs')
        position=row['position']
        if not 0<=position<len(menu['menu']) or row['length']!=len(menu['menu'][position]):
            raise ValueError('D32 offer identity differs')
        if row['accepted']!=int(selected and position==old[0]):
            raise ValueError('D32 original outcome disagrees with prepared source')
        updated=dict(row,accepted=int(selected and position==actual[0]))
        changed+=updated['accepted']!=row['accepted'];corrected.append(updated)
    return corrected,dict(rows=len(rows),changed_offer_labels=changed,menus=len({r['key'] for r in rows}),
        corpus_menus=len(proofs),corpus_changed_choices=sum(p['index_status']=='proven_disjoint_choice' for p in proofs.values()))


def load(inputs, config):
    if set(inputs)!=INPUTS or config not in (CONFIG,PILOT_CONFIG):
        raise ValueError('D32 canonical frozen contract differs')
    root=Path(inputs['original_complete']).parent/'output'
    for name in ('INPUTS.json','SOURCE_PINS.json','ROWS_k50.json','CENTERS_k50.json','SUPPORT_k50.json'):
        bind_completed(inputs['original_complete'],root/name)
    binding=read(root/'INPUTS.json')
    if Path(binding['paths']['sessions']).resolve()!=Path(inputs['sessions']).resolve():
        raise ValueError('D32 original prepared source differs')
    for path,h in read(root/'SOURCE_PINS.json').items():
        if sha256(path)!=h:raise ValueError('D32 immutable extraction source changed')
    original.checkpoint_read(root/'CENTERS_k50.json')
    support=original.checkpoint_read(root/'SUPPORT_k50.json')
    rows=original.checkpoint_read(root/'ROWS_k50.json')
    corrected,proof=correct_rows(rows,read(inputs['sessions']),canonical.load(inputs))
    return corrected,proof,support


def fit_draw(arrays, index, selections, beta):
    m=np.bincount(selections[index],minlength=len(arrays['writers']))
    try:
        estimate,_,certificate=original.fitted_contrast(arrays,m,beta)
        return dict(index=index,effect=estimate,certificate=certificate,error=None)
    except ValueError as exc:
        return dict(index=index,effect=None,certificate=None,error=str(exc))


def control_draw(arrays,index,beta,config):
    y=original.within_writer_shuffle(arrays['y'],arrays['groups'],config['permutation_seed']+index)
    try:
        estimate,_,certificate=original.fitted_contrast(arrays,initial=beta,y=y)
        return dict(index=index,effect=estimate,certificate=certificate,error=None)
    except ValueError as exc:
        return dict(index=index,effect=None,certificate=None,error=str(exc))


def summarize(point,draws,controls,proof,support):
    good=[d['effect'] for d in draws if d['error'] is None]
    result=original.summarize_bootstrap(point,good,len(draws)-len(good))
    values=[d['effect'] for d in controls if d['error'] is None]
    reference=dict(total=len(controls),finite=len(values),invalid=len(controls)-len(values),
                   state='valid_reference' if len(values)==len(controls) else 'invalid_reference')
    if len(values)==len(controls):
        mean,sd=float(np.mean(values)),float(np.std(values,ddof=1))
        reference.update(mean=mean,sd=sd,bias_flag=abs(mean)>.25*sd)
    return dict(card='D32-canonical',primary=result,repeated_outcome_control=reference,
        source_audit=proof,support=support,original_cluster_count=50,original_primary_seed=20261017,
        scope='Descriptive acceptance association conditional on fixed source-defined clusters and repertoire',
        controls_scope='Outcome permutation within writer; full appeal refit; not a person-identification test',
        original_preserved=True,scientific_admission=False,extension_run=False)


def compute(output,inputs,config,verify=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    started=time.monotonic();rows,proof,support=load(inputs,config)
    def record(name,value):
        if verify:assert_close(read_sealed(output/name),value)
        else:save(output/name,value)
    record('BINDING.json',dict(inputs=input_hashes(inputs),config=config))
    record('SOURCE_AUDIT.json',proof);record('ROWS.json',rows)
    arrays=original.prepare_arrays(rows);point,beta,certificate=original.fitted_contrast(arrays)
    record('FIT.json',dict(effect=point,beta=beta.tolist(),certificate=certificate))
    selections=np.random.default_rng(config['seed']).integers(len(arrays['writers']),size=(2000,len(arrays['writers'])))
    counts=(20,20) if config['mode']=='pilot' else (2000,200)
    setup_seconds=time.monotonic()-started
    saved=[];control=[];times={'bootstrap':[],'controls':[]}
    for phase,count,collection in [('bootstrap',counts[0],saved),('controls',counts[1],control)]:
        for index in range(count):
            name=f'{phase}/{index:04d}.json';path=output/name
            if not verify and (output/'YIELD_REQUEST.json').exists():
                return dict(status='yielded',phase=phase,index=index)
            if not verify and sealed(path):value=read_sealed(path)
            else:
                clock=time.monotonic()
                value=fit_draw(arrays,index,selections,beta) if phase=='bootstrap' else control_draw(arrays,index,beta,config)
                elapsed=time.monotonic()-clock
                times[phase].append(elapsed)
                record(name,value)
            collection.append(value)
            if not verify and phase=='bootstrap' and index==19:
                elapsed=time.monotonic()-started
                write(output/'FIRST_TENTH.json',dict(completed_bootstrap=20,total_bootstrap=2000,
                    projected_seconds=2*(elapsed+max(times['bootstrap'],default=elapsed/20)*(20 if config['mode']=='pilot' else 2180)),
                    projected_full_main_seconds=2*(elapsed+max(times['bootstrap'],default=elapsed/20)*2180),
                    projection_scope='Conservative slowest measured bootstrap fit; execution plus full replay; controls measured separately in timing pilot'))
    if config['mode']=='pilot':
        # No primary result or gate from a partial bootstrap. Saved values remain private.
        report=dict(card='D32-canonical-cost-pilot',timing_only=True,bootstrap_fits=len(saved),control_fits=len(control),
                    source_rows=len(rows),source_writers=len(arrays['writers']),scientific_admission=False,
                    bootstrap_fit_failures=sum(d['error'] is not None for d in saved),
                    control_fit_failures=sum(d['error'] is not None for d in control))
    else:report=summarize(point,saved,control,proof,support)
    record('SUMMARY.json',report)
    if not verify:
        write(output/'TIMING.json',dict(elapsed_seconds=time.monotonic()-started,setup_seconds=setup_seconds,
            fresh_fit_seconds=times,
            conservative_full_execution_and_replay_seconds=3*(setup_seconds+
                max(times['bootstrap'],default=0)*2000+max(times['controls'],default=0)*200)))
    return report


def execute(output,inputs,config):
    if (Path(output)/'SUMMARY.json').exists():raise ValueError('Completed D32 successor is immutable')
    with threadpool_limits(limits=1):return compute(output,inputs,config)


def verify(output,inputs,config):
    with threadpool_limits(limits=1):compute(output,inputs,config,verify=True)
    return dict(verified=True,fresh_source_and_every_fit_replayed=True,timing_only=config['mode']=='pilot',scientific_admission=False)
