"""Manually translated final setup additions, not an automatic study generator.

DESIGN CHECK: LESSONS 3-5. NULL: an unavailable package or failed selector remains
held. ALTERNATIVE: three-seed stability and longer-dose tests interrogate variance
and undertraining. Same people and unchanged doses are not independent evidence.
"""
from .common import RAW,read,freeze,filehash,REPORTING
from .build_plan import card

def build():
    prior=read(RAW/'plans/local-week-v4.json');new=[];data='P01-chronology-corpora-v1'
    new.append(card('R01-derived-fields-v1','derived_fields','cpu',[],['PREDICTIONS.json','SUMMARY.json','ADMISSION.json'],'Do deterministic related-slot and span-state fields match the existing constructor?',wall_seconds=600))
    new.append(card('H05-gold-census-v1','aries_census','cpu',[],['PAPER_LEDGER.json','SOURCE_PINS.json','SUMMARY.json'],'What gold denominator and prior paper exposure are actually witnessed?',wall_seconds=3600))
    for name in ('llama3','llama8','qwen9'):
        c=read(RAW/'cards'/f'R04-natural-{name}-pilot-v2.json')
        new.append(card(f'R02-option-id-{name}-v1','option_ids','gpu',[],['SERVER.json','PREDICTIONS.json','SUMMARY.json','ADMISSION.json'],'Do raw generated-token numbered-option readouts preserve full legal support and coherence?',wall_seconds=7200,**{k:c[k] for k in ('model','model_digest','memory_MiB')}))
    for name in ('smol360','qwen500'):
        for corpus in ('human_typed','mixed_final','accepted_model'):
            for rank in (4,16):
                c=read(RAW/'cards'/f'P03-{name}-{corpus}-r{rank}-s141010-v2.json')
                extra={k:v for k,v in c.items() if k in ('gates','backbone','model_files','memory_MiB','rank','epochs','corpus','training_tokens','writer_limit','wall_seconds')}
                new.append(card(f'P03-{name}-{corpus}-r{rank}-s141012-v2','adaptive_v2','gpu',c['requires'],c['produces'],'Does optimization-seed stability persist in a third frozen seed, on the same historical writers?',seed=141012,**extra))
            for epochs in (4,8):
                for seed in (141010,141011):
                    c=read(RAW/'cards'/f'Q05-{name}-{corpus}-t32768-s{seed}-v1.json')
                    extra={k:v for k,v in c.items() if k in ('gates','selector','mode','backbone','model_files','memory_MiB','rank','corpus','writer_limit')}
                    new.append(card(f'Q05-{name}-{corpus}-e{epochs}-s{seed}-v1','continuation','gpu',c['requires'],c['produces'],'Does additional training on the same sparse past text help or overfit, after the frozen calibration gate?',training_tokens=16384,epochs=epochs,seed=seed,wall_seconds=43200,**extra))
    producers=list(new)
    for ident in producers:
        c=read(RAW/'cards'/f'{ident}.json')
        if c['handler']=='adaptive_v2' or c.get('mode')=='selected_adapter':
            new.append(card(ident+'-readouts','adapter_readouts','cpu',[ident,data],['PREDICTIONS.json','CALIBRATION.json','SUMMARY.json'],'Do normalized likelihood and adapted-minus-base readouts survive on this frozen training variant?',wall_seconds=7200))
    # New instrument checks precede long training without interrupting live workers.
    ids=new[:5]+prior['cards']+new[5:]
    plan=dict(id='local-week-v5',cards=ids,card_pins={i:filehash(RAW/'cards'/f'{i}.json') for i in ids},reporting=REPORTING,authority=prior['authority'],predecessor='local-week-v4',capacity_status='pilot-calibrated estimates; conditional work never counted as admitted',no_new_spend=True)
    freeze(RAW/'plans/local-week-v5.json',plan);return plan

if __name__=='__main__':print(len(build()['cards']))
