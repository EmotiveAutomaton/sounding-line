"""Complete-population Week 4 timing-control replay for AT2/AT3.

Kept separate from the already frozen production-context source. This adapter
uses the retained D33 raw-screen algorithm with no target/future insertion.
"""
from pathlib import Path
from types import FunctionType
import json
from .week5_at_source import authenticate
from . import timing_d33_supported_source as original
from . import timing_d33_supported_utf16 as fast
from runners.stage9.coauthor import suggestions
from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal,progress


def displayed_options(value):
    if type(value) is list and not value:return []
    return suggestions(value)


def screen_covariates(events,words):
    """An orphan literal-empty reopen adds no exposure, never a guessed menu."""
    audit=[];prior=False
    for ordinal,event in enumerate(events):
        if event['eventName'] not in ('suggestion-open','suggestion-reopen'):continue
        value=event.get('currentSuggestions')
        if type(value) is list and not value:
            if event['eventName']!='suggestion-reopen':raise ValueError('Empty new suggestion open remains unsupported')
            audit.append(dict(ordinal=ordinal,had_prior_display=prior,
                              correspondence_warning=None if prior else 'orphan empty reopen; no prior display',
                              displayed_words_added=0))
        else:
            suggestions(value);prior=True
    function=FunctionType(original.screen_covariates.__code__,dict(original.__dict__,
        suggestions=displayed_options,units=fast.units,text_of=fast.text_of,
        apply_delta=fast.apply_delta,visible_sequences=fast.visible_sequences))
    return function(events,words),audit


def produce(output,inputs,config,verifying=False):
    if set(inputs)!={'p6_root','raw_roster','repo_root'} or config!={}:raise ValueError('Exact timing-control inputs required')
    root=Path(output);root.mkdir(parents=True,exist_ok=True)
    source=authenticate(inputs['p6_root'])/'output';raw={r['session']:r for r in read(inputs['raw_roster'])}
    index=[];audits=[]
    for n,entry in enumerate(sorted(read(source/'P6_INDEX.json'),key=lambda r:r['session'])):
        path=source/entry['file']
        if filehash(path)!=entry['sha256']:raise ValueError('P6 covariate source changed')
        record=gzread(path);meta=raw[entry['session']];rawpath=(Path(inputs['repo_root'])/meta['path']).resolve()
        rawpath.relative_to(Path(inputs['repo_root']).resolve())
        if filehash(rawpath)!=meta['source_sha256']:raise ValueError('Raw timing-control source changed')
        events=[json.loads(line) for line in rawpath.read_text(encoding='utf8').splitlines() if line]
        covariates,empty_reopens=screen_covariates(events,record['words'])
        values={f'{n:04d}:{k}':v for k,v in covariates.items()}
        audits.append(dict(session_ordinal=n,empty_reopen_events=empty_reopens))
        name=f'sessions/session-{n:04d}.json.gz'
        if verifying:
            if gzread(root/name)!=values:raise ValueError('Complete timing-control replay differs')
        else:gzip_equal(root/name,values)
        index.append(dict(file=name,sha256=filehash(root/name),words=len(values)))
        progress(root/'PROGRESS.json',dict(phase='verify' if verifying else 'source',sessions=n+1))
    if verifying:
        if read(root/'INDEX.json')!=index or read(root/'AUDIT.json')!=audits:raise ValueError('Timing-control roster differs')
        return dict(verified=True,complete_raw_screen_replay=True)
    write_equal(root/'INDEX.json',index);write_equal(root/'AUDIT.json',audits)
    return dict(status='complete',sessions=len(index),scientific_admission=False)


def execute(output,inputs,config):return produce(output,inputs,config)
def verify(output,inputs,config):return produce(output,inputs,config,True)
