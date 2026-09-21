"""Raw, retrieved and frozen learned records on a separate development roster.

DESIGN CHECK: LESSONS 3-5. NULL: a bad compression or a repeated answer bank
does not create new evidence. ALTERNATIVE: retained representations may change
query access or cost. Acquisition and repeated-query calls are all charged.
Targets come only from the independent finite reference, never model agreement.
The answer bank has query-specific acquisition; report that access difference.
"""
import json
from .common import REPO,read,freeze,filehash,digest,distribution
from .local_api import request,call,service
from .canary import PROFILE
from .context_battery import text_for,independent,matched_timing_check


def compile(out,card,pulse,raw):
    from runners.stage11_2.world import enumerate_predict
    by={r['unit']:r for r in read(REPO/'results/phase_2_4_stage_11_2/raw/fixture/dev-public.json')}
    units=[by[k] for k in card['candidate_ids']];targets=[]
    for row in units:
        for q in (1,3):
            obs=row['queries'][q]['observation'];p=enumerate_predict(row['history'],obs)['probabilities']
            if max(abs(a-b) for a,b in zip(p,independent(row['history'],obs)))>1e-12:raise ValueError('retention target reference failed')
            targets.append(dict(unit=row['unit'],query=q,target=p))
    freeze(out/'PUBLIC_UNITS.json',units);freeze(out/'EVALUATOR_ONLY.json',targets)
    freeze(out/'MATRIX.json',dict(conditions=['raw_history','retrieval_last_four','frozen_account','predictive_bank'],queries=[1,3],
        acquisition=dict(account_query=0,bank_queries=[1,3]),calls_per_source=11,
        access='bank sees evaluation questions during acquisition, never their true answers; account sees separate query zero',
        state='frozen explicit records; no persistent KV-state or weight update'))
    pulse(phase='retention-matrix-compiled')
    return dict(status='complete',kind='infrastructure',sources=len(units),calls=len(units)*11,
        controls=dict(separate_development_roster=True,independent_reference=True,all_acquisition_charged=True),
        scope='descriptive controlled access/cost comparison; query-specific bank access identified',
        files={n:filehash(out/n) for n in ('PUBLIC_UNITS.json','EVALUATOR_ONLY.json','MATRIX.json')})


def run(out,card,pulse,raw):
    from .output_interface import adapt,profile_for_card
    from runners.stage11_2.world import render_observation,rules
    source=raw/'jobs'/card['compile_card'];units=read(source/'PUBLIC_UNITS.json')
    targets={(r['unit'],r['query']):r['target'] for r in read(source/'EVALUATOR_ONLY.json')};rows=[];recorded=[]
    admission=raw/'jobs'/card['canary_card']
    if read(admission/'ADMISSION.json').get('reader_admitted') is not True:raise ValueError('reader interface not admitted')
    reference=read(admission/'ROWS.json');timings={'forecast':[],'account':[]}
    def invoke(text,name,state,kind='forecast'):
        req=adapt(request(text,4,kind),card.get('output_interface'));path=out/'calls'/name;c=call(req,4,path,state,raw)
        timings[kind].append(c)
        if len(timings[kind])%5==0:
            check=matched_timing_check(timings[kind][-5:],[r['call'] for r in reference if r['call_class']==kind])
            freeze(out/('TIMING-'+name+'.json'),check)
            if check['degraded']:raise RuntimeError('matched throughput degraded; preserve incomplete retention unit')
        recorded.append((req,path,c));return c,read(path/'RAW.json')
    with service(out,profile_for_card(card,admission,PROFILE),raw) as state:
        for unit in units:
            key=unit['unit'];pulse(phase='retention-acquisition',unit=key)
            account,reply=invoke(text_for(unit,unit['history'],0),key+'-account',state,'account')
            if account['probabilities'] is None:raise ValueError('account acquisition invalid; full unit retained incomplete')
            hypothesis=json.loads(reply['message']['content'])['analysis'];bank={}
            for q in (1,3):
                prediction,_=invoke(text_for(unit,unit['history'],q),key+'-bank-'+str(q),state)
                if prediction['probabilities'] is None:raise ValueError('bank acquisition invalid; full unit retained incomplete')
                # JSON object keys are strings on disk. Preserve those native
                # types so handler reentry compares the same frozen record.
                bank[str(q)]=prediction['probabilities']
            freeze(out/(key+'-FROZEN.json'),dict(account=hypothesis,bank=bank,evidence_sha256=digest(unit['history']),
                status='model-generated hypotheses, not additional observed outcomes'))
            for q in (1,3):
                obs=unit['queries'][q]['observation'];query=rules(obs['world_family'])+'\nCurrent query: '+render_observation(obs,unit['rendering'])+'\nPredict action probabilities in label order A, B, C, D.'
                texts=dict(raw_history=text_for(unit,unit['history'],q),retrieval_last_four=text_for(unit,unit['history'][-4:],q),
                    frozen_account='Previously generated account, possibly mistaken:\n'+hypothesis+'\n'+query,
                    predictive_bank='Previously generated answers, possibly mistaken: '+json.dumps(bank)+'\nBank entry for this question: '+str(q)+'\n'+query)
                for condition,text in texts.items():
                    pulse(phase='retention-query',unit=key,query=q,condition=condition)
                    c,_=invoke(text,key+'-'+str(q)+'-'+condition,state)
                    rows.append(dict(unit=key,query=q,condition=condition,**distribution(c['probabilities'],targets[key,q])))
    for req,path,c in recorded:
        if call(req,4,path,{'uncertain':False},raw)!=c:raise ValueError('retention raw replay differs')
    freeze(out/'ROWS.json',rows)
    return dict(status='complete',kind='scientific',sources=len(units),rows=len(rows),calls=len(recorded),
        scope='same recorded evidence; acquisition differs by query access and all costs remain; no persistent neural state claim',
        controls=dict(all_arms=True,raw_replay=True,acquisition_charged=True,no_oracle_bank=True),files={'ROWS.json':filehash(out/'ROWS.json')})
