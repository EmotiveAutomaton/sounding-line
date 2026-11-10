"""Native orphan-empty-reopen source-handler fixture, preserving predictor clock."""
from copy import deepcopy
from pathlib import Path
import json
from . import week5_at_covariates_v3 as producer
from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal


def events():
    return [dict(eventName='system-initialize',eventTimestamp=0,currentDoc='prompt '),
        dict(eventName='suggestion-reopen',eventTimestamp=1,currentSuggestions=[],eventSource='user',textDelta={'ops':[{'retain':7},{'insert':'same '}]}),
        dict(eventName='text-insert',eventTimestamp=2,eventSource='user',textDelta={'ops':[{'retain':12},{'insert':'later '}]}),
        dict(eventName='suggestion-open',eventTimestamp=3,currentSuggestions=[dict(index=8,original='hidden',trimmed='shown')]),
        dict(eventName='suggestion-close',eventTimestamp=4),
        dict(eventName='suggestion-reopen',eventTimestamp=5,currentSuggestions=[])]


def words():
    return [dict(index=i,token=t,ordinal=o,population_probability=.05,context=[],is_word=True)
            for i,(t,o) in enumerate([('same',1),('shown',1),('prompt',1),('same',2),('later',2),('shown',5),('hidden',5)])]


def checks():
    source=events();value,audit=producer.screen_covariates(source,words())
    if [value[i]['on_screen'] for i in range(7)]!=[0,0,1,1,0,1,0]:raise ValueError('Empty reopen clock/exposure changed')
    if audit[0]['had_prior_display'] or not audit[1]['had_prior_display']:raise ValueError('Orphan vs previous exposure audit differs')
    # Exposure oracle: the literal-empty display contributes no words, while
    # its original delta and ordinal remain. Only this constructed comparison
    # labels the no-op; actual source event bytes are never rewritten.
    oracle=deepcopy(source)
    for e in oracle:
        if e['eventName']=='suggestion-reopen' and e.get('currentSuggestions')==[]:e['eventName']='constructed-no-display'
    expected=producer.original.screen_covariates(oracle,words())
    if value!=expected:raise ValueError('Zero-display oracle differs')
    for bad in (None,'[]',{},[{}]):
        changed=deepcopy(source);changed[1]['currentSuggestions']=bad
        try:producer.screen_covariates(changed,words())
        except (ValueError,TypeError):pass
        else:raise ValueError('Malformed or encoded-empty display accepted')
    changed=deepcopy(source);changed[1]['eventName']='suggestion-open'
    try:producer.screen_covariates(changed,words())
    except ValueError:pass
    else:raise ValueError('Empty new open accepted')
    return dict(no_current_or_future_exposure=True,orphan_and_prior_audits=True,delta_and_ordinal_preserved=True,
                encoded_empty_missing_malformed_refused=True,empty_new_open_refused=True)


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('Fixture takes no human inputs')
    root=Path(output);root.mkdir(parents=True,exist_ok=True);source=root/'constructed-source';data=source/'output'
    raw=root/'constructed-events.jsonl';raw.write_text(''.join(json.dumps(e)+'\n' for e in events()),encoding='utf8')
    gzip_equal(data/'session.json.gz',dict(words=words()))
    write_equal(data/'P6_INDEX.json',[dict(session='constructed',file='session.json.gz',sha256=filehash(data/'session.json.gz'))])
    write_equal(root/'ROSTER.json',[dict(session='constructed',path=raw.name,source_sha256=filehash(raw))])
    args=dict(p6_root=str(source),raw_roster=str(root/'ROSTER.json'),repo_root=str(root))
    old=producer.authenticate;producer.authenticate=lambda p:source
    try:(producer.verify if verifying else producer.execute)(root/'produced',args,{})
    finally:producer.authenticate=old
    expected,audit=producer.screen_covariates(events(),words())
    if gzread(root/'produced/sessions/session-0000.json.gz')!={f'0000:{k}':v for k,v in expected.items()}:raise ValueError('Full raw handler projection differs')
    if read(root/'produced/AUDIT.json')!=[dict(session_ordinal=0,empty_reopen_events=audit)]:raise ValueError('Full raw audit differs')
    receipt=dict(fixture_only=True,actual_raw_jsonl_p6_handler=True,checks=checks(),no_fake_completion=True)
    if verifying:
        if read(root/'FIXTURE.json')!=receipt:raise ValueError('Full raw handler replay differs')
        return dict(verified=True,complete_orphan_empty_raw_handler_replay=True)
    write_equal(root/'FIXTURE.json',receipt);return dict(status='complete',fixture_only=True)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)

if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,{},{})))
