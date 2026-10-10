"""Manual day-one recovery and independent branches; no prose-to-queue parser.

DESIGN CHECK: LESSONS 5. NULL: original attempted identities never change; failed
calibration support is excluded explicitly, not replaced with later targets.
ALTERNATIVE: frozen successors cover the same estimands with accountable rosters.
"""
from .common import RAW,read,freeze,filehash,REPORTING,now
from .build_plan import card,sources
from runners.stage13.detectors import cached_model,model_pins

def build():
    old=read(RAW/'plans/local-week-v2.json');ids=list(old['cards']);new=[];replacements={}
    for identifier in old['cards']:
        c=read(RAW/'cards'/f'{identifier}.json')
        if c['handler'] not in ('adaptive','personal_head','natural_reader'):continue
        nxt=identifier.removesuffix('-v1')+'-v2';replacements[identifier]=nxt
    for identifier,nxt in replacements.items():
        c=read(RAW/'cards'/f'{identifier}.json');c['id']=nxt;c['handler']+='_v2';c['source_pins']=sources(c['handler']);c['repair_identity']='engineering successor 1: explicit usable calibration support; one-writer inference unavailable; deduplicated text'
        c['requires']=[replacements.get(x,x) for x in c['requires']];c['gates']=[replacements.get(x,x) for x in c['gates']]
        if 'memory-pilot' in identifier:c['writer_limit']=3
        freeze(RAW/'cards'/f'{nxt}.json',c);new.append(nxt)
        out=RAW/'jobs'/identifier
        if not any((out/p).exists() for p in ('DISPATCH.json','COMPLETE.json','FAILED.json','BLOCKED.json')):
            freeze(out/'BLOCKED.json',dict(at=now(),status='blocked',reason='undispatched mechanical predecessor replaced by '+nxt,card_sha256=filehash(RAW/'cards'/f'{identifier}.json')))
    data='P01-chronology-corpora-v1'
    cpu=[];gpu=[]
    cpu.append(card('H03-public-document-intake-v1','public_git','cpu',[],['MANIFEST.json','EXCLUSIONS.json','SUMMARY.json','ADMISSION.json'],
        'Which bounded public document revisions have complete licensed parent and child records?',since='2025-01-01T00:00:00Z',until='2026-10-10T00:00:00Z',wall_seconds=7200))
    model='sentence-transformers/all-MiniLM-L6-v2'
    cpu.append(card('P04-frozen-embedding-features-v1','embedding_features','cpu',[data],['FEATURES.json','MODEL.json','SUMMARY.json','ADMISSION.json'],
        'Does a pinned frozen encoder yield finite candidate features without accessing future choices?',gates=[data],backbone=model,model_files=model_pins(cached_model(model)),wall_seconds=21600))
    for embedding in (False,True):
        name='embedding' if embedding else 'lexical';requires=[data]+(['P04-frozen-embedding-features-v1'] if embedding else [])
        for pilot in (True,False):
            identifier=f'P04-candidate-{name}-'+('pilot' if pilot else 'full')+'-v1';deps=requires+([] if pilot else [f'P04-candidate-{name}-pilot-v1'])
            cpu.append(card(identifier,'choice_model','cpu',deps,['PREDICTIONS.json','MODELS.json','EXCLUSIONS.json','SUMMARY.json','ADMISSION.json'],
                'Does a past-choice posterior over candidate coefficients improve later choices beyond population, donor and position?',gates=deps,writer_limit=3 if pilot else 999,
                embedding_job='P04-frozen-embedding-features-v1' if embedding else None,wall_seconds=14400 if pilot else 86400))
    for name,backbone,mem in [('smol360','HuggingFaceTB/SmolLM2-360M-Instruct',4500),('qwen500','Qwen/Qwen2.5-0.5B-Instruct',4500),('smol1700','HuggingFaceTB/SmolLM2-1.7B-Instruct',6500),('qwen1500','Qwen/Qwen2.5-1.5B-Instruct',6000)]:
        gpu.append(card(f'R02-native-readout-{name}-v1','likelihood_controls','gpu',[],['MODEL.json','PREDICTIONS.json','SUMMARY.json','ADMISSION.json'],
            'Do raw HF sequence and first-legal-token readouts survive exact truth, option order, negation and partition coherence?',backbone=backbone,model_files=model_pins(cached_model(backbone)),memory_MiB=mem,wall_seconds=7200))
    # Repairs precede main continuations; independent CPU branches launch beside
    # the GPU pilot. No worker source or original manifest is rewritten.
    pilots=[i for i in new if 'pilot' in i or 'personal-head' in i]
    mains=[i for i in new if i not in pilots]
    allids=ids+cpu+pilots+gpu+mains
    plan=dict(id='local-week-v3',cards=allids,card_pins={i:filehash(RAW/'cards'/f'{i}.json') for i in allids},reporting=REPORTING,
        authority=old['authority'],predecessor='local-week-v2',replacements=replacements,
        capacity_status='Measured main-block occupancy pending; wall ceilings do not establish runnable runway')
    freeze(RAW/'plans/local-week-v3.json',plan);return plan

if __name__=='__main__':print(len(build()['cards']))
