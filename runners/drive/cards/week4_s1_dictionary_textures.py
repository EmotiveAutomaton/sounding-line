"""Declared 100/300-word S1 dictionary variants; source preparation only.

DESIGN CHECK: LESSONS2-5 and Week4 S1/G read 2026-11-02. NULL and ALTERNATIVE
share frozen dictionary ranking, window membership, clocks and exclusions.
Known tied-frequency sources exercise the original implementation at both
sizes; source or output disagreement refuses. No scientific effect is computed.
"""
from pathlib import Path
from types import FunctionType
from . import week4_typed_windows as original
from .timing_p6 import write_equal,gzip_equal
from .timing_census import read,filehash


def configuration(size,mode):
    if type(size) is not int or size not in (100,300) or mode not in ('constructed','full'):
        raise ValueError('Only declared 100/300-word dictionary variants')
    return dict(original.CONFIG,card=f'S1-texture-dictionary-{size}',dictionary_words=size,
                expected_sessions=1 if mode=='constructed' else 1399,mode=mode,descriptive=True,descendants=False)


def fixture_inputs(output):
    output=Path(output);p6=output/'fixture/p6';timing=output/'fixture/timing'
    words=[dict(index=i,ordinal=2*i+1,completed_ordinal=2*i+2,is_word=True,token=f'w{i:03d}',
                previous_typed_token_index=i-1 if i else None,sentence_start=i%8==0,length=4,seconds=float(i),revised=False) for i in range(400)]
    intervals=[dict(ordinal=w['ordinal'],onset=True,stop=i%8==0,fast=.2 if i%8==0 else .95-(i//8)*.01,interval_seconds=1.) for i,w in enumerate(words)]
    record=dict(session='fixture',writer='fixture',prompt='constructed',timestamp=0.,end_at=1000.,words=words)
    gzip_equal(p6/'record.json.gz',record)
    write_equal(p6/'INDEX.json',[dict(session='fixture',writer='fixture',file='record.json.gz',sha256=filehash(p6/'record.json.gz'))])
    write_equal(p6/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,constructed_fixture=True,outputs={'INDEX.json':filehash(p6/'INDEX.json')}))
    write_equal(timing/'output/PRIVATE_ROSTER.json',[dict(session='fixture',writer='fixture',genre='constructed',session_order=0)])
    gzip_equal(timing/'output/INTERVALS.json.gz',{'fixture':intervals})
    write_equal(timing/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,constructed_fixture=True,
        outputs={n:filehash(timing/n) for n in ('output/PRIVATE_ROSTER.json','output/INTERVALS.json.gz')}))
    return dict(p6_index=str(p6/'INDEX.json'),p6_completion=str(p6/'COMPLETE.json'),timing_completion=str(timing/'COMPLETE.json'))


def run(output,inputs,config,verification=False):
    if config!=configuration(config['dictionary_words'],config['mode']):raise ValueError('Frozen dictionary variant required')
    if config['mode']=='constructed':
        if inputs:raise ValueError('No human input in known source')
        inputs=fixture_inputs(output)
    implementation=FunctionType(original.run.__code__,dict(original.__dict__,CONFIG=config),'run',original.run.__defaults__)
    result=implementation(output,inputs,config,verification)
    if config['mode']=='constructed':
        d=read(Path(output)/'FROZEN_DICTIONARY.json');s=read(Path(output)/'SUMMARY.json')
        if d['words']!=[f'w{i:03d}' for i in range(config['dictionary_words'])] or d['total_words']!=400:
            raise ValueError('Known frequency/tie dictionary differs')
        if s['census']['formed_windows']!=50:raise ValueError('Known unchanged window membership differs')
    return result


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
