"""Manual October 10 card-to-runner translation; never reads TODO as executable work.

DESIGN CHECK: LESSONS 5. NULL: omitted imported helpers or mutable cards refuse;
unmeasured budgets never become capacity claims. ALTERNATIVE: finite variants
preserve comparisons, dependencies and per-family gate isolation.
"""
import ast,importlib.util
from pathlib import Path
from .common import REPO,RAW,REPORTING,freeze,read,pins,filehash

def sources(handler):
    pending=['runners.stage14.worker','runners.stage14.'+handler];seen=set();paths=set()
    while pending:
        name=pending.pop()
        if name in seen or not name.startswith(('runners.','soundingline.')):continue
        seen.add(name);p=REPO/Path(*name.split('.')).with_suffix('.py')
        if not p.exists():p=REPO/Path(*name.split('.'))/'__init__.py'
        if not p.exists():continue
        paths.add(p);package=name if p.name=='__init__.py' else name.rsplit('.',1)[0]
        for node in ast.walk(ast.parse(p.read_text(encoding='utf8'))):
            if isinstance(node,ast.Import):pending.extend(x.name for x in node.names)
            elif isinstance(node,ast.ImportFrom):
                mod=importlib.util.resolve_name('.'*node.level+(node.module or ''),package) if node.level else node.module
                if mod:
                    pending.append(mod);pending.extend(mod+'.'+n.name for n in node.names)
    return pins(sorted(paths))

def card(identifier,handler,resource,requires,produces,question,**extra):
    c=dict(id=identifier,handler=handler,resource=resource,requires=requires,gates=[],produces=produces,source_pins=sources(handler),input_pins={},
        question=question,target='declared in the handler and detailed program branch',substrate='constructed controls or exposed human process records, explicitly separated',
        unit='writer for human comparisons; constructed record for ruler controls',split='strict past-only per recipient; no fresh human confirmation',
        view='declared per card; source truth kept outside reader prompt unless V4 extraction',score='half-Brier; invalid=1; zero target mass retains infinite logarithmic loss',
        status='PILOT',wall_seconds=14400,repair_budget=2,continuation='only listed whole comparison blocks; separate successor for semantic repair',
        design_check={'lessons':'2-5, CONTROLS and October errata read','null':'invalid instrument or failed dependence/chronology control refuses promotion','alternative':'complete source-bound control survives; performance evaluated separately','failure_direction':'all failures preserve evidence and block only their dependents'},**{})
    c.update(extra);freeze(RAW/'cards'/f'{identifier}.json',c);return identifier

def build():
    from runners.stage13.detectors import cached_model,model_pins
    ids=['H01-replay-census-v1','R01-contract-pilot-llama8-v1']
    ids.append(card('H04-missingness-ruler-v1','source_controls','cpu',[],['CONTROLS.json','PREDICTIONS.json','SUMMARY.json','ADMISSION.json'],
        'Does withholding source evidence preserve all supplied compatible histories?',wall_seconds=600))
    data='P01-chronology-corpora-v1'
    ids.append(card(data,'personal_data','cpu',['H01-replay-census-v1'],['READER.json','EVALUATOR.json','SPLITS.json','TEXT_CORPORA.json','SESSION_CORPORA.json','EXCLUSIONS.json','SUMMARY.json','ADMISSION.json'],
        'Which writers have strict earlier training, later calibration and prompt-novel future episodes?',wall_seconds=10800))
    ids.append(card('P04-personal-head-v1','personal_head','cpu',[data],['PREDICTIONS.json','MODELS.json','EXCLUSIONS.json','SUMMARY.json'],
        'Do maker residuals or earlier handling frequencies improve future handling beyond pooled and donor controls?',gates=[data],wall_seconds=21600))
    ids.append(card('D01-typed-offer-transfer-v1','detection','cpu',[data],['PREDICTIONS.json','MODELS.json','SPLITS.json','SUMMARY.json'],
        'Can a lexical detector transfer typed-stream versus accepted-offer distinction to held writers above length and shuffled-label controls?',gates=[data],wall_seconds=7200))
    packages=[('llama8','llama3.1:8b','46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e',6000),
              ('llama3','llama3.2:3b','a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72',3500),
              ('qwen9','qwen3.5:9b','6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7',7000)]
    for name,model,dg,mem in packages:
        ids.append(card(f'R01-factorized-{name}-v1','factorized','gpu',[],['CONTROL_MANIFEST.json','PREDICTIONS.json','SUMMARY.json','ADMISSION.json'],
            'Does one witnessed free quantity per request remove the diagnosed extraction burden?',cases=64,model=model,model_digest=dg,memory_MiB=mem,wall_seconds=21600,repair_identity='factorized semantic successor 1'))
    backbones=[('smol360','HuggingFaceTB/SmolLM2-360M',4500),('qwen500','Qwen/Qwen2.5-0.5B',4500)]
    modeldata={name:dict(backbone=model,model_files=model_pins(cached_model(model)),memory_MiB=mem) for name,model,mem in backbones}
    for name,_,_ in backbones:
        ids.append(card(f'P03-memory-pilot-{name}-v1','adaptive','gpu',[data],['MODEL.json','PREDICTIONS.json','COSTS.json','EXCLUSIONS.json','SUMMARY.json','ADMISSION.json'],
            'Can all four text-only adaptation arms complete with exact memory, token and future-choice accounting?',gates=[data],rank=4,seed=141010,epochs=1,corpus='human_typed',training_tokens=1024,writer_limit=1,wall_seconds=7200,**modeldata[name]))
    # Independent natural handling diagnostics do not inherit a failed graph gate.
    for name,model,dg,mem in packages:
        ids.append(card(f'R04-natural-{name}-pilot-v1','natural_reader','gpu',[data,'H01-replay-census-v1'],['MANIFEST.json','PREDICTIONS.json','EXCLUSIONS.json','SUMMARY.json','ADMISSION.json'],
            'Does the local reader predict natural handling above a past-only cheap prior, with own/donor/repeated history controls?',
            model=model,model_digest=dg,memory_MiB=mem,view='prospective',calibration_cases=32,evaluation_cases=64,wall_seconds=21600,gates=[data]))
    # Full finite learning-curve blocks: three provenance corpora, two ranks and
    # two seeds in each of two existing small backbones. Same-writer comparisons
    # are paired; these recipe variants are not independent human replications.
    for corpus in ('human_typed','mixed_final','accepted_model'):
        for rank in (4,16):
            for seed in (141010,141011):
                for name,_,_ in backbones:
                    ids.append(card(f'P03-{name}-{corpus}-r{rank}-s{seed}-v1','adaptive','gpu',[data,f'P03-memory-pilot-{name}-v1'],['MODEL.json','PREDICTIONS.json','COSTS.json','EXCLUSIONS.json','SUMMARY.json','ADMISSION.json'],
                        'Does strictly earlier text-only maker adaptation improve later offered choices beyond base, matched pool and donor?',
                        gates=[data,f'P03-memory-pilot-{name}-v1'],rank=rank,seed=seed,epochs=2,corpus=corpus,training_tokens=16384,writer_limit=999,wall_seconds=28800,**modeldata[name]))
    for name,model,dg,mem in packages:
        for view in ('prospective','V1','V3'):
            pilot=f'R04-natural-{name}-pilot-v1'
            ids.append(card(f'P02-natural-{name}-{view}-v1','natural_reader','gpu',[data,'H01-replay-census-v1',pilot],['MANIFEST.json','PREDICTIONS.json','EXCLUSIONS.json','SUMMARY.json','ADMISSION.json'],
                'Does earlier own history help an admitted local handling reader across evidence views and donor/duplicate controls?',
                model=model,model_digest=dg,memory_MiB=mem,view=view,calibration_cases=128,evaluation_cases=256,wall_seconds=43200,gates=[data,pilot]))
    plan=dict(id='local-week-v1',cards=ids,card_pins={i:filehash(RAW/'cards'/f'{i}.json') for i in ids},reporting=REPORTING,
        authority='October 10 local Gear 2 commission and strict-memory/residency exception',source='manual reviewed card translation, no TODO parser',
        capacity_status='CAPACITY_SHORTFALL until admitted measurements justify lane occupancy; wall budgets are ceilings, not forecasts')
    freeze(RAW/'plans/local-week-v1.json',plan);return plan

if __name__=='__main__':
    p=build();print('Frozen manually reviewed cards:',len(p['cards']))
