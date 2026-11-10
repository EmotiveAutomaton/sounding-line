"""Actual raw event/P6 source handler fixture; no human data or fake receipt."""
import copy
from pathlib import Path
from . import week5_bk_outcome_source as card
from . import week3_outcome_blocks_inputs as old
from . import week4_record as record
from .timing_census import read
from .timing_p6 import write_equal,gzread
from tests.test_week3_outcome_blocks_inputs import fixture as wc_fixture,session
from tests.test_week3_frames_inputs import fixture as fr_fixture


def raw_cases():
    rows=wc_fixture()
    single=session('single','single',True)
    single['canonical']['events'][0]['options']=single['canonical']['events'][0]['options'][1:]
    # FR1 uses the same accepted record but also requires the canonical menu
    # resolution. Its deleted secondary must survive absence of unchosen text.
    single['timeline']['decisions']=[dict(ordinal=1,resolution_ordinal=3,handling='accept',latency_kind='observed')]
    rows.append(single)
    for row in rows:
        row['timeline'].setdefault('decisions',[dict(ordinal=1,resolution_ordinal=3,handling='accept',latency_kind='observed')])
    return rows+fr_fixture()


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('Constructed-only fixture')
    root=Path(output);root.mkdir(parents=True,exist_ok=True)
    rows=raw_cases();source=root/'CONSTRUCTED.json';write_equal(source,rows)
    data=dict(fixture=str(source));call=card.verify if verifying else card.execute
    checks=record.historical_checks()
    for kind in ('WC2-inputs','FR1-inputs'):
        dest=root/kind;cfg=dict(card=kind,mode='constructed',max_wall_seconds=1200)
        if not verifying:
            dest.mkdir(parents=True,exist_ok=True);write_equal(dest/'YIELD_REQUEST.json',dict(reason='preload'))
            if card.execute(dest,data,cfg).get('status')!='yielded':raise ValueError('Preload yield missing')
            (dest/'YIELD_REQUEST.json').unlink()
            previous=card.prepare;calls=0
            def pause(*args):
                nonlocal calls
                value=previous(*args);calls+=1
                if calls==1:write_equal(dest/'YIELD_REQUEST.json',dict(reason='first sealed session'))
                return value
            card.prepare=pause
            try:
                if card.execute(dest,data,cfg).get('status')!='yielded':raise ValueError('Session yield missing')
            finally:card.prepare=previous
            (dest/'YIELD_REQUEST.json').unlink()
        if not call(dest,data,cfg).get('verified' if verifying else 'status'):raise ValueError('Handler did not finish')
        result=gzread(dest/'EVENTS.json.gz');single=gzread(dest/'sessions/session-0006.json.gz')
        if result['summary']['sessions']!=len(rows):raise ValueError('Source census lost sessions')
        if kind=='WC2-inputs':
            if single['events'] or len(single['unsupported_comparator_events'])!=1:raise ValueError('Single-option WC2 contrast silently defined')
            if result['summary']['complete_deleted_with_context']!=3:raise ValueError('Known supported WC2 window count differs')
            # Every previously supported row is unchanged except its R1 physical
            # insertion identifier (the obsolete parser used a menu identifier).
            for n in range(6):
                expected=old.prepare_session(**rows[n]);actual=gzread(dest/f'sessions/session-{n:04d}.json.gz')
                for e in expected['events']:
                    e['id']=e['session']+':3';e['span']=card.r1.spans(rows[n]['events'],rows[n]['timeline'],rows[n]['canonical'])[0]
                if {k:actual[k] for k in expected if k!='audit'}!={k:v for k,v in expected.items() if k!='audit'}:raise ValueError('Original window coordinates changed')
        elif [e['kind'] for e in single['events']]!=['deleted']:raise ValueError('Single-option deletion history lost')
        if not verifying:
            seal=dest/'sessions/session-0000.json.seal.json';prior=seal.read_bytes();seal.write_text('{}',encoding='utf8')
            try:
                try:card.execute(dest,data,cfg)
                except ValueError as error:
                    if 'seal differs' not in str(error):raise
                else:raise ValueError('Tampered source seal accepted')
            finally:seal.write_bytes(prior)
    receipt=dict(fixture_only=True,raw_sessions=len(rows),both_complete_source_handlers=True,
        historical_parser_failures=checks,canonical_windows_unchanged=True,single_option_wc2_excluded_but_retained=True,
        single_option_fr1_deletion_preserved=True,preload_and_session_yield_resume=True,altered_checkpoint_refused=True)
    if verifying:
        if read(root/'FIXTURE.json')!=receipt:raise ValueError('Fixture replay differs')
    else:write_equal(root/'FIXTURE.json',receipt)
    return dict(verified=True,complete_raw_source_replay=True) if verifying else dict(status='complete',fixture_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)

if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,{},{})))
