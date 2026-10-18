"""D33 single source-schema recovery for native empty suggestion reopens.

DESIGN CHECK: LESSONS3-5. Literal[] on reopen contributes zero new displayed
words and preserves all earlier exposure, deltas, occurrences and contrasts.
Empty new opens, encoded-empty/missing/malformed values still refuse. Every
saved covariate is checked against full raw/P6 replay before reuse. Failed
original sources remain immutable. Controller OWNER-to-FAILED wall time is
charged once under the original1800s cumulative ceiling.
"""
from __future__ import annotations

from datetime import datetime
import json
import math
from pathlib import Path
import time
from types import FunctionType

from . import timing_d33_supported as original
from . import timing_d33_supported_source as source
from .timing_census import read,write,filehash
from .timing_p6 import write_equal,progress
from .timing_pmap_source import bound_record
from .timing_stats import bind
from runners.stage9.coauthor import suggestions,replay as canonical_replay

EXTRA={'failed_plan','failed_record','failed_owner'}
INPUTS=original.INPUTS|EXTRA


def validate(inputs,config):
    if set(inputs)!=INPUTS or config!=original.configuration('pair'):
        raise ValueError('exact single D33 pair recovery inputs/config required')
    base={k:inputs[k] for k in original.INPUTS};original.validate(base,config)
    paths=[Path(inputs[k]).resolve() for k in ('failed_plan','failed_record','failed_owner')]
    if len({p.parent for p in paths})!=1:raise ValueError('failed attempt roots differ')
    plan,failed,owner=map(read,paths)
    if plan['module']!='runners.drive.cards.timing_d33_supported' or plan['inputs']!=base or plan['config']!=config:
        raise ValueError('failed source population or contrast differs')
    if failed.get('status')!='FAILED' or owner['plan_sha256']!=filehash(paths[0]):
        raise ValueError('failed attempt ownership differs')
    for path,expected in plan['pins'].items():
        if filehash(path)!=expected:raise ValueError('original failed pinned source changed')
    prior=(datetime.fromisoformat(failed['at'])-datetime.fromisoformat(owner['at'])).total_seconds()
    if not math.isfinite(prior) or not 0<prior<original.CUMULATIVE_CAP_SECONDS:
        raise ValueError('original controller wall time invalid')
    old=paths[0].parent/'output'
    if read(old/'INPUTS.json')!=original.binding(base,config):raise ValueError('failed source binding differs')
    checkpoint=read(old/'PROGRESS.json')
    if checkpoint['phase']!='screen-source' or not 0<=checkpoint['seconds']<=prior:
        raise ValueError('failed attempt is not a valid source checkpoint')
    files=sorted((old/'sessions').glob('*.json.gz'))
    if len(files)!=checkpoint['done'] or len(files)>=checkpoint['total']:
        raise ValueError('failed checkpoint inventory differs')
    return base,old,prior,files


def displayed_options(value):
    # The caller first requires literal[] to belong to a reopen, never an open.
    if type(value) is list and not value:return []
    return suggestions(value)


def screen_covariates(events,words):
    empty=[];prior_display=False
    for ordinal,event in enumerate(events):
        if event['eventName'] not in ('suggestion-open','suggestion-reopen'):continue
        value=event.get('currentSuggestions')
        if type(value) is list and not value:
            if event['eventName']!='suggestion-reopen' or not prior_display:
                raise ValueError('empty display is not a reopen after a known display')
            empty.append(ordinal)
        else:
            suggestions(value);prior_display=True
    # Copy the immutable implementation's globals, not its source or globals.
    # The sole replacement accepts the prevalidated zero-option reopen. Raw
    # events are passed unchanged; no event renaming or invented option text.
    function=FunctionType(source.screen_covariates.__code__,dict(source.__dict__,suggestions=displayed_options))
    return function(events,words),empty


class Sources(source.Sources):
    def __init__(self,inputs,output,verifying):
        super().__init__({k:inputs[k] for k in original.INPUTS})
        self.output=Path(output);self.verifying=verifying;self.audits={}
        old=Path(inputs['failed_plan']).parent/'output';checkpoint=read(old/'PROGRESS.json')
        ids=sorted({sid for sid,_ in self.roster_for('pair')['retained_keys']})
        names=sorted(p.name for p in (old/'sessions').glob('*.json.gz'))
        if checkpoint['total']!=len(ids) or names!=[sid+'.json.gz' for sid in ids[:checkpoint['done']]]:
            raise ValueError('saved covariate population is not the exact supported prefix')

    def covariates(self,sid):
        receipt=self.raw.session(sid) # unchanged complete raw/P6 occurrence replay
        path=(self.raw.root/self.raw.raw[sid]['path']).resolve()
        with path.open(encoding='utf8') as stream:events=[json.loads(line) for line in stream]
        words,empty=screen_covariates(events,self.lookup[sid]['words'])
        canonical=None
        if empty:
            checked=canonical_replay(events)
            timeline=bound_record(self.inputs['session_index'],self.raw.p2[sid])
            if checked['errors'] or checked['final_document']!=timeline['final_document']:
                raise ValueError('empty-reopen canonical document proof failed')
            canonical=dict(errors=checked['errors'],final_document_matches_p2=True)
        audit=dict(session=sid,source_hashes=receipt['source_hashes'],literal_empty_reopen_ordinals=empty,
            new_shown_tokens_from_empty_reopens=0,canonical=canonical)
        dest=self.output/'schema-audit'/(sid+'.json')
        if self.verifying:
            if read(dest)!=audit:raise ValueError('empty-reopen audit differs from original source')
        else:write_equal(dest,audit)
        self.audits[sid]=audit
        return dict(session=sid,writer=self.lookup[sid]['writer'],source_hashes=receipt['source_hashes'],
            words={str(k):v for k,v in words.items()})


def audit_summary(instances):
    audits=instances[0].audits
    return dict(sessions=len(audits),affected_sessions=sum(bool(v['literal_empty_reopen_ordinals']) for v in audits.values()),
        literal_empty_reopens=sum(len(v['literal_empty_reopen_ordinals']) for v in audits.values()),
        policy='Native literal[] on reopen adds zero shown words; prior exposure, source events and every scoring row retained. All other display schemas remain strict.')


def recovery_record(inputs,config,old,prior,files):
    names=['SUPPORTED_ROSTER.json','CALIBRATION.json']+[p.relative_to(old).as_posix() for p in files]
    return dict(original_plan_sha256=filehash(inputs['failed_plan']),original_failed_sha256=filehash(inputs['failed_record']),
        original_owner_sha256=filehash(inputs['failed_owner']),prior_controller_seconds=prior,cumulative_cap_seconds=original.CUMULATIVE_CAP_SECONDS,
        preserved_old_outputs={name:filehash(old/name) for name in names},config=config)


def copy_equal(source_path,dest):
    if dest.exists():
        if filehash(source_path)!=filehash(dest):raise ValueError('original checkpoint bytes changed')
    else:
        dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('xb') as stream:stream.write(source_path.read_bytes())


def execute(output:Path,inputs:dict,config:dict)->dict:
    started=time.monotonic();output=Path(output);_,old,prior,files=validate(inputs,config)
    receipt=recovery_record(inputs,config,old,prior,files);write_equal(output/'RECOVERY.json',receipt)
    for name in receipt['preserved_old_outputs']:copy_equal(old/name,output/name)
    previous=read(output/'ACTIVE_TIME.json')['seconds'] if (output/'ACTIVE_TIME.json').exists() else prior
    if not math.isfinite(previous) or previous<prior:raise ValueError('original wall charge missing')
    previous+=time.monotonic()-started;progress(output/'ACTIVE_TIME.json',dict(seconds=previous))
    instances=[]
    def factory(values):
        value=Sources(values,output,False);instances.append(value);return value
    def bound(dest,values,cfg,names):
        write_equal(output/'SCHEMA_AUDIT.json',audit_summary(instances))
        extra=['RECOVERY.json','SCHEMA_AUDIT.json']+[p.relative_to(output).as_posix() for p in sorted((output/'schema-audit').glob('*.json'))]
        return bind(dest,values,cfg,names+extra)
    def write_corrected(path,value):
        if Path(path).name=='FIRST_TENTH.json':
            value=dict(value,projected_cpu_seconds=value['projected_cpu_seconds']-previous,
                prior_cumulative_seconds=previous,method='Prior cumulative cost charged once; current source plus both inference/control arms doubled for complete fresh verification.')
        return write_equal(path,value)
    function=FunctionType(original.execute.__code__,dict(original.__dict__,validate=validate,Sources=factory,bind=bound,write_equal=write_corrected))
    result=function(output,inputs,config)
    if result.get('status')!='yielded' and read(output/'SCHEMA_AUDIT.json')!=audit_summary(instances):
        raise ValueError('source schema summary differs')
    return result


def verify(output:Path,inputs:dict,config:dict)->dict:
    started=time.monotonic();output=Path(output);_,old,prior,files=validate(inputs,config)
    if read(output/'RECOVERY.json')!=recovery_record(inputs,config,old,prior,files):raise ValueError('recovery metadata changed')
    for name in read(output/'RECOVERY.json')['preserved_old_outputs']:
        if filehash(output/name)!=filehash(old/name):raise ValueError('old saved covariates not byte-identical')
    instances=[]
    def factory(values):
        value=Sources(values,output,True);instances.append(value);return value
    function=FunctionType(original.verify.__code__,dict(original.__dict__,validate=validate,Sources=factory))
    result=function(output,inputs,config)
    if read(output/'SCHEMA_AUDIT.json')!=audit_summary(instances):raise ValueError('source schema summary differs on fresh replay')
    seconds=read(output/'ACTIVE_TIME.json')['seconds']+time.monotonic()-started
    if seconds>original.CUMULATIVE_CAP_SECONDS:raise RuntimeError('original D33 cumulative cap exceeded in full verification')
    return dict(result,cumulative_seconds=seconds,prior_controller_seconds=prior)
