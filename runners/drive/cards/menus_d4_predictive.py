"""Canonical D4 prediction with immutable source checkpoints and fresh replay.

DESIGN CHECK: LESSONS3-5. Original unsupported writers remain excluded before
fit. Any required objective/source failure fails the card, never drops a writer.
Known-answer controls exercise positive/reversed/null outcomes and200 complete
permutations. No new encoder, raw replay or extension is launched here.
"""
import hashlib
import math
from pathlib import Path
import time
import numpy as np
from . import events_d4 as storage
from . import menus_d4_predictive_source as source
from . import menus_d4_predictive_stats as stats
from .menus_io import read,write,sha256,assert_equal

CONFIG=dict(threads=1,bootstrap=2000,seed=20261018,permutations=200,
            minimum_corrections=5,minimum_training_sessions=2,penalties=list(stats.original.PENALTIES))


def load(inputs,config):
    if config!=CONFIG:raise ValueError('canonical D4 frozen configuration differs')
    return source.load(inputs)


def name(writer):return hashlib.sha256(writer.encode()).hexdigest()[:24]


def result(data,units):
    report=stats.summarize([r['result'] for r in units],[r['data'] for r in units],CONFIG)
    report.update(input_hashes=data['identity'],chronology_exclusions=data['excluded'],
        source_choice_audit=dict(decisions=len(data['choice_proofs']),changed=sum(p['choice_changed'] for p in data['choice_proofs']),
        supported={phase:dict(rows=sum(len(r['data'][phase]) for r in units if not r['data']['exclusion']),
            changed=sum(p['choice_changed'] for r in units if not r['data']['exclusion'] for p in r['data']['canonical_choice_audit'][phase])) for phase in ('calibration','test')}))
    return report


def execute(output:Path,inputs:dict,config:dict)->dict:
    output=Path(output);output.mkdir(parents=True,exist_ok=True);start=time.perf_counter()
    data=load(inputs,config);bind=dict(inputs=data['identity'],config=config)
    storage.save(output/'BINDING.json',bind);storage.save(output/'SOURCE_CHOICE_AUDIT.json',data['choice_proofs'])
    storage.save(output/'ROSTER.json',sorted(data['splits']));units=[];times=[]
    for i,writer in enumerate(sorted(data['splits']),1):
        folder=output/'writers'/name(writer);path=folder/'RESULT.json'
        if storage.sealed(path):
            saved=storage.read_sealed(path);metadata=storage.read_sealed(folder/'DATA.json');storage.read_sealed(folder/'UNITS.npy')
            for original,digest in metadata['source_pins'].items():
                if sha256(original)!=digest:raise ValueError('D4 saved correction source changed')
        else:
            if (output/'YIELD_REQUEST.json').exists():return dict(status='yielded',completed_writers=len(units))
            clock=time.perf_counter();metadata,vectors=source.writer_data(writer,data,config)
            storage.save(folder/'DATA.json',metadata);storage.save(folder/'UNITS.npy',vectors)
            fitted=stats.fit_writer(metadata,vectors,data['vectors'],config)
            saved=dict(writer=writer,result=fitted,elapsed_seconds=time.perf_counter()-clock)
            storage.save(path,saved)
        units.append(dict(data=metadata,result=saved['result']));times.append(saved['elapsed_seconds'])
        if i>=max(1,math.ceil(.1*len(data['splits']))) and not (output/'FIRST_TENTH.json').exists():
            write(output/'FIRST_TENTH.json',dict(completed_writers=i,total_writers=len(data['splits']),
                projected_seconds=2*(time.perf_counter()-start)*len(data['splits'])/i,
                includes_fresh_source_and_refit=True))
    if (output/'YIELD_REQUEST.json').exists():return dict(status='yielded',completed_writers=len(units))
    report=result(data,units)
    report['writer_hashes']={w:sha256(output/'writers'/name(w)/'RESULT.json') for w in sorted(data['splits'])}
    storage.save(output/'SUMMARY.json',report);return report


def verify(output:Path,inputs:dict,config:dict)->dict:
    output=Path(output);data=load(inputs,config);bind=dict(inputs=data['identity'],config=config)
    assert_equal(storage.read_sealed(output/'BINDING.json'),bind)
    assert_equal(storage.read_sealed(output/'SOURCE_CHOICE_AUDIT.json'),data['choice_proofs'])
    assert_equal(storage.read_sealed(output/'ROSTER.json'),sorted(data['splits']))
    units=[]
    for writer in sorted(data['splits']):
        folder=output/'writers'/name(writer)
        metadata,vectors=source.writer_data(writer,data,config)
        assert_equal(storage.read_sealed(folder/'DATA.json'),metadata)
        if not np.array_equal(storage.read_sealed(folder/'UNITS.npy'),vectors):raise ValueError('D4 fresh correction vectors differ')
        rebuilt=stats.fit_writer(metadata,vectors,data['vectors'],config)
        saved=storage.read_sealed(folder/'RESULT.json')
        if saved['writer']!=writer:raise ValueError('D4 saved writer differs')
        assert_equal(saved['result'],rebuilt);units.append(dict(data=metadata,result=rebuilt))
    actual=result(data,units)
    actual['writer_hashes']={w:sha256(output/'writers'/name(w)/'RESULT.json') for w in sorted(data['splits'])}
    assert_equal(storage.read_sealed(output/'SUMMARY.json'),actual)
    return dict(verified=True,canonical_source_replayed=True,corrections_reextracted=True,
        fresh_models_and_200_permutations=True,primary_recomputed=actual['primary'])
