"""Native full-handler raw-event proof for the AT covariate successor."""
from pathlib import Path
import json
from . import week5_at_covariates_v2 as producer
from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('Constructed fixture takes no human inputs')
    root=Path(output);root.mkdir(parents=True,exist_ok=True);source=root/'constructed-source';data=source/'output'
    events=[dict(eventName='system-initialize',eventTimestamp=0,currentDoc='prompt '),
        dict(eventName='suggestion-open',eventTimestamp=1,currentSuggestions=[dict(index=8,original='hidden',trimmed='shown')]),
        dict(eventName='suggestion-reopen',eventTimestamp=2,currentSuggestions=[]),
        dict(eventName='insert',eventTimestamp=3,eventSource='api',textDelta={'ops':[{'retain':7},{'insert':'accepted '}]}),
        dict(eventName='insert',eventTimestamp=4,eventSource='user',textDelta={'ops':[{'retain':16},{'insert':'future '}]}),
        dict(eventName='suggestion-open',eventTimestamp=5,currentSuggestions=[dict(index=1,original='later',trimmed='later')])]
    words=[dict(index=i,token=t,ordinal=4,population_probability=.05,context=[],is_word=True)
           for i,t in enumerate(['prompt','accepted','shown','future','later','hidden'])]
    raw=root/'constructed-events.jsonl';raw.write_text(''.join(json.dumps(e)+'\n' for e in events),encoding='utf8')
    gzip_equal(data/'session.json.gz',dict(words=words));write_equal(data/'P6_INDEX.json',[dict(session='constructed',file='session.json.gz',sha256=filehash(data/'session.json.gz'))])
    write_equal(root/'ROSTER.json',[dict(session='constructed',path=raw.name,source_sha256=filehash(raw))])
    args=dict(p6_root=str(source),raw_roster=str(root/'ROSTER.json'),repo_root=str(root))
    old=producer.authenticate;producer.authenticate=lambda p:source
    try:(producer.verify if verifying else producer.execute)(root/'produced',args,{})
    finally:producer.authenticate=old
    value=gzread(root/'produced/sessions/session-0000.json.gz')
    if [value[f'0000:{i}']['on_screen'] for i in range(6)]!=[1,1,1,0,0,0]:raise ValueError('Strict raw-event predictor clock failed')
    if read(root/'produced/AUDIT.json')!=[dict(session_ordinal=0,empty_reopen_ordinals=[2])]:raise ValueError('Empty reopen audit differs')
    receipt=dict(fixture_only=True,full_handler_execute_verify=True,raw_jsonl_and_p6_schema=True,
                 no_target_future_or_original_suggestion_leakage=True,empty_reopen_audited=True,no_fake_completion=True)
    if verifying:
        if read(root/'FIXTURE.json')!=receipt:raise ValueError('Native fixture differs')
        return dict(verified=True,complete_raw_event_handler_replay=True)
    write_equal(root/'FIXTURE.json',receipt);return dict(status='complete',fixture_only=True)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)

if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,{},{})))
