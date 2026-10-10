"""Finite week continuation cards, manually commissioned from Q02/Q05.

DESIGN CHECK: LESSONS 5. NULL: gate failure closes its descendants; card counts
and maximum runtimes never establish capacity. ALTERNATIVE: predeclared distinct
doses and selected larger packages supply useful conditional work without repeats.
"""
from .common import RAW,read,freeze,filehash,REPORTING
from .build_plan import card
from runners.stage13.detectors import cached_model,model_pins

def build():
    old=read(RAW/'plans/local-week-v3.json');new=[];data='P01-chronology-corpora-v1'
    new.append(card('H01-event-exposure-v1','exposure','cpu',['H01-replay-census-v1'],['EVENT_LEDGER.json','SOURCE_PINS.json','EXCLUSIONS.json','SUMMARY.json'],
        'Which event exposures are positively witnessed in retained model/scorer outputs, and which remain unknown?',wall_seconds=7200))
    for name in ('smol360','qwen500'):
        parents=[f'P03-{name}-human_typed-r{r}-s141010-v2' for r in (4,16)];sel=f'Q02-select-{name}-v1'
        new.append(card(sel,'continuation','cpu',[data]+parents,['SUMMARY.json','ADMISSION.json'],
            'Which small-backbone rank remains a supported recipe for the predeclared dose and capacity continuation?',mode='select',parents=parents,data=data,wall_seconds=7200))
        proto=read(RAW/'cards'/f'P03-{name}-human_typed-r4-s141010-v2.json')
        for corpus in ('human_typed','mixed_final','accepted_model'):
            for dose in (4096,32768):
                for seed in (141010,141011):
                    i=f'Q05-{name}-{corpus}-t{dose}-s{seed}-v1'
                    new.append(card(i,'continuation','gpu',[data,sel],['RESOLVED_CARD.json','MODEL.json','PREDICTIONS.json','COSTS.json','EXCLUSIONS.json','SUMMARY.json','ADMISSION.json'],
                        'At the calibration-selected rank, does a genuinely different earlier-text dose change later choice prediction?',gates=[data,sel],selector=sel,mode='selected_adapter',backbone=proto['backbone'],model_files=proto['model_files'],memory_MiB=proto['memory_MiB'],rank=None,seed=seed,epochs=2,corpus=corpus,training_tokens=dose,writer_limit=999,wall_seconds=28800))
    for small,name,backbone,mem in [('smol360','smol1700','HuggingFaceTB/SmolLM2-1.7B',6500),('qwen500','qwen1500','Qwen/Qwen2.5-1.5B',6000)]:
        sel=f'Q02-select-{small}-v1';models=model_pins(cached_model(backbone));pilot=f'Q02-memory-{name}-v1'
        new.append(card(pilot,'continuation','gpu',[data,sel],['RESOLVED_CARD.json','MODEL.json','PREDICTIONS.json','COSTS.json','EXCLUSIONS.json','SUMMARY.json','ADMISSION.json'],
            'Does the next cached backbone complete the same four-arm fit and native choice score while fully resident?',gates=[data,sel],selector=sel,mode='selected_adapter',backbone=backbone,model_files=models,memory_MiB=mem,rank=None,seed=141010,epochs=1,corpus='human_typed',training_tokens=1024,writer_limit=3,wall_seconds=7200))
        for corpus in ('human_typed','mixed_final','accepted_model'):
            new.append(card(f'Q02-{name}-{corpus}-main-v1','continuation','gpu',[data,sel,pilot],['RESOLVED_CARD.json','MODEL.json','PREDICTIONS.json','COSTS.json','EXCLUSIONS.json','SUMMARY.json','ADMISSION.json'],
                'Does a selected capacity rung alter the source-separated personal-choice comparison?',gates=[data,sel,pilot],selector=sel,mode='selected_adapter',backbone=backbone,model_files=models,memory_MiB=mem,rank=None,seed=141010,epochs=2,corpus=corpus,training_tokens=16384,writer_limit=999,wall_seconds=43200))
    # Zero additional GPU work: mandated normalized and residual readouts of
    # every corrected complete adapter block, plus conditional continuations.
    adapter_ids=[]
    for i in old['cards']+new:
        c=read(RAW/'cards'/f'{i}.json')
        if c['handler']=='adaptive_v2' or c.get('mode')=='selected_adapter':adapter_ids.append(i)
    for parent in adapter_ids:
        new.append(card(parent+'-readouts','adapter_readouts','cpu',[parent,data],['PREDICTIONS.json','CALIBRATION.json','SUMMARY.json'],
            'Do length-normalized native likelihood and adapted-minus-base signals survive base, pooled, donor and uniform rivals?',wall_seconds=7200))
    ids=old['cards']+new;plan=dict(id='local-week-v4',cards=ids,card_pins={i:filehash(RAW/'cards'/f'{i}.json') for i in ids},reporting=REPORTING,
        authority=old['authority'],predecessor='local-week-v3',capacity_status='conditional forest; measure runnable and fast-depletion occupancy, never sum wall ceilings',
        expansion_questions=['native likelihood normalization without new GPU','real text-dose response','selected backbone-capacity rung'],no_new_spend=True)
    freeze(RAW/'plans/local-week-v4.json',plan);return plan

if __name__=='__main__':print(len(build()['cards']))
