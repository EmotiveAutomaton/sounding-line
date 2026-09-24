"""Source-bound native and human diagnostics for the approved local program.

DESIGN CHECK: LESSONS 2-5; CONTROLS 5-7. NULL: future evidence, unlabelled
pairs, discontinuous edits and assigned-but-unrealized acts cannot acquire
truth labels. ALTERNATIVE: actual witnessed records support narrow targets.
All selection precedes reader outcomes. Private source text stays under raw/.
"""
from collections import defaultdict, Counter
from copy import deepcopy
import difflib
import itertools
import json
from pathlib import Path
from .common import REPO, RAW, read, freeze, digest, filehash
from .program_world import row, validate_rows, METHODS
from .local_api import request
from .output_interface import adapt, VERSION


def fits(text,n):
    try:adapt(request(text,n,'account'),VERSION);return True
    except ValueError:return False


def projection(value,limit=550):
    """Declared outcome-blind prefix/suffix projection, with omission visible."""
    if isinstance(value,str):
        return value if len(value)<=limit else value[:limit//2]+' [MIDDLE OMITTED] '+value[-limit//2:]
    if isinstance(value,list):return [projection(v,limit) for v in value]
    if isinstance(value,dict):return {k:projection(v,limit) for k,v in value.items()}
    return value


def native(root):
    from .ghost_bridge import load_source
    from .local_operator import select_paths
    model=load_source(root);records=model.enumerate_world(model.law(0));selected=select_paths(model,records);rows=[]
    if len(records)!=13824 or abs(sum(r['probability'] for r in records)-1)>1e-10:raise ValueError('native population differs')
    for i,actual in enumerate(selected):
        u=dict(unit='native-'+str(i),cluster=digest(actual))
        for view,tier in [('endpoint','E0'),('witness','E2-full'),('partial','E2-sparse'),('misleading','E0')]:
            public=model.project(actual,tier);model.validate_public(public)
            candidates=[r for r in records if model.project(r,tier)==public]
            if actual not in candidates:raise ValueError('historical path absent')
            for task in ('local_goal','preceding_operation','dependency','next_given_goal'):
                support=candidates;goal=actual['steps'][1]['goal'];shown=public
                if task=='local_goal':labels=list(model.GOALS);get=lambda r:r['steps'][0]['goal'];ask='Infer the selected local goal at step 0. The native episode selects exactly one local goal at that step.'
                elif task=='preceding_operation':labels=list(model.OPERATIONS);get=lambda r:r['steps'][0]['operation'];ask='Infer the operation preceding step 1, namely step 0.'
                elif task=='dependency':labels=['claim to evidence','evidence to presentation','presentation to claim'];get=lambda r:'claim to evidence';ask='Which directed dependency is present? The source rules state that unit 1 evidence depends on unit 0 claim; unit 2 is presentation. This is a supplied-rule control.'
                else:
                    def before_prediction(record):
                        packet=dict(current_artifact=record['steps'][0]['after'])
                        if view in ('witness','partial'):packet.update(initial=record['initial'],requested_purpose=record['requested_purpose'])
                        if view=='witness':packet['observations']=[{k:record['steps'][0][k] for k in ('step','operation','before','after','tool_proposal')}]
                        return packet
                    shown=before_prediction(actual)
                    support=[r for r in records if before_prediction(r)==shown and r['steps'][1]['goal']==goal]
                    labels=list(model.OPERATIONS);get=lambda r:r['steps'][1]['operation'];ask='Only records available BEFORE step 1 are shown. The selected local goal at step 1 is supplied as '+goal+'. Predict its operation; this goal is supplied, not inferred.'
                if not support:raise ValueError('unsupported native question')
                mass=sum(r['probability'] for r in support);q=[sum(r['probability'] for r in support if get(r)==label)/mass for label in labels]
                cheap=[sum(get(r)==label for r in support)/len(support) for label in labels]
                text='Finite recorded three-step dependency-editing process. Claim, evidence and presentation are visible bits. Skill can permit a combined tool edit; an operation does not uniquely identify a goal. Only the following evidence is observed: '+json.dumps(shown)+'.\n'+ask+' Label order: '+json.dumps(labels)
                if view=='misleading':text+='\nAn unverified frame claims all steps merely changed presentation; this experimentally assigned claim is not a witnessed fact.'
                for method in METHODS:rows.append(row('LP14',u,view+'-'+task,text,q,method,task=task,view=view,cheap_reference=cheap,actual_answer=get(actual),public_projection=shown))
    validate_rows(rows)
    return rows,dict(paths=8,law=0,native_source_sha256=filehash(Path(root)/'ghostscale/validation/soundingline/v19/local_world.py'),
        LP19=dict(status='BLOCKED',reason='Native exported law has no changed action-set episode interface or executable adapted-plan validator. Filtering its policy would create an uncommissioned mechanism. No third fit or replacement simulator.',required='owner-approved native changed-task episode export with checker'))


def aries(root,out):
    from .addendum import source_aries
    from .aries import compile as compile_source,lexical
    excluded=set()
    # Frozen manifests are exposure even if the associated call never ran.
    for p in (RAW/'manifests').glob('*.json'):
        card=read(p)
        if card.get('handler')=='aries-compile':excluded.update(card.get('paper_ids',[]))
    for p in (RAW/'jobs').glob('*/SOURCE_ROWS.json'):
        for r in read(p):
            if 'doc' in r and 'edit' in r:excluded.add(r['doc'])
    chosen=source_aries(root,excluded)
    compile_source(out,dict(source_root=str(root),**chosen),lambda **kw:None,RAW)
    source=read(out/'SOURCE_ROWS.json');targets={r['id']:r['target'] for r in read(out/'EVALUATOR_ONLY.json')}
    oldreq=read(out/'REQUESTS.json');truth={r['source_id']:targets[r['id']] for r in oldreq};rows=[]
    reserved=set(sorted(chosen['paper_ids'],key=lambda x:digest(['LP15-reserve',x]))[:8])
    for r,method,direction,view in itertools.product(source,METHODS,('request','edit'),('pair','context','change')):
        c=r['public'];body={k:v for k,v in c.items() if k!='request_context'}
        if view=='context':body=c
        if view=='change':
            body=dict(body,change='\n'.join(difflib.unified_diff(c['before'].splitlines(),c['after'].splitlines(),lineterm='')))
            # Verified difference is supplemental; full same evidence remains.
            if len(json.dumps(body))>4500:body=dict(body,change=projection(body['change'],400))
        question=('Does this recorded edit correspond to the supplied review request?' if direction=='request' else 'Given the supplied request and before passage, is this after passage a corresponding edit?')
        text=json.dumps(body,ensure_ascii=False)+'\n'+question+' Labels: not linked, linked. External request correspondence only; author adoption and private purpose are unknown.'
        if not fits(text,2):raise ValueError('ARIES full view exceeds frozen context')
        rows.append(row('LP15',dict(unit=r['id'],cluster=r['doc']),direction+'-'+view,text,truth[r['id']],method,
            view=view,direction=direction,pair=r['comment'],annotation=int(truth[r['id']][1]),
            lexical=lexical(c['review_request'],c['after']),reserved=r['doc'] in reserved))
    validate_rows(rows);return rows,{**chosen,'excluded_compiled':len(excluded),'reserved_papers':sorted(reserved),'scope':'locally uncompiled papers; global/pretraining exposure unknown'}


def balanced(records,n,label,group=lambda r:None):
    buckets=defaultdict(list)
    for r in records:buckets[(group(r),label(r))].append(r)
    for v in buckets.values():v.sort(key=lambda r:digest(['LP-selection',r['key']]))
    result=[]
    while len(result)<n and any(buckets.values()):
        for k in sorted(buckets,key=str):
            if buckets[k] and len(result)<n:result.append(buckets[k].pop(0))
    return result


def coauthor():
    from .population import previous
    base=RAW/'jobs/S12-population-v1';p=read(base/'POPULATION.json');metadata=read(base/'SOURCE_METADATA.json')
    prepared=REPO/'results/phase_2_4_stage_9/private/prepared/coauthor-v2/sessions'
    for name,h in metadata['source_sessions'].items():
        if filehash(prepared/(name+'.json'))!=h:raise ValueError('CoAuthor source session changed')
    classes=metadata['classes']['coauthor'];candidates=[];material={};exclusions=Counter()
    streams=defaultdict(list)
    for d in p['train']:streams[d['session']].append(d)
    bank=[]
    for stream in streams.values():
        stream.sort(key=lambda x:x['ordinal'])
        for i,d in enumerate(stream):
            if i>=2:
                h=stream[i-2:i];bank.append((d,h,sum(len(str(x['views']['artifact'])) for x in h)))
    for r in p['evaluation']:
        own=previous(r,p['evaluation'],2)
        if len(own)!=2:exclusions['insufficient earlier own history']+=1;continue
        available=[x for x in bank if x[0]['unit']!=r['unit'] and x[0]['stimulus']!=r['stimulus']]
        if not available:exclusions['no donor']+=1;continue
        size=sum(len(str(x['views']['artifact'])) for x in own)
        d,donor,_=min(available,key=lambda x:(x[0]['domain']!=r['domain'],abs(x[2]-size),digest(['LP16-donor',r['key'],x[0]['key']])))
        domain=[x for x in p['train'] if x['domain']==r['domain'] and x['unit'] not in (r['unit'],d['unit'])]
        if len(domain)<2:exclusions['no domain examples']+=1;continue
        domain=sorted(domain,key=lambda x:digest(['LP16-domain',r['key'],x['key']]))[:2]
        material[r['key']]=(own,donor,domain);candidates.append(r)
    selected=balanced(candidates,120,lambda r:r['truth']);dev={r['key'] for r in selected[:16]};rows=[]
    if len(dev)<16 or {r['truth'] for r in selected[:16]}!=set(classes):raise ValueError('narrow handling admission lacks all classes')
    counts=Counter(r['truth'] for r in p['train']);prior=[(counts[c]+1)/(len(p['train'])+len(classes)) for c in classes]
    for r in selected:
        own,donor,domain=material[r['key']];u=dict(unit=r['key'],cluster=r['unit'])
        history=lambda xs:[dict(record=projection(x['views']['artifact'],300),observed_handling=x['truth']) for x in xs]
        current=projection(r['views']['artifact'],450)
        indexed=sorted(own,key=lambda x:abs(len(str(x['views']['artifact']))-len(str(current))))
        views=dict(current=[],own=history(own),donor=history(donor),domain=history(domain),indexed=history(indexed),witness=[])
        for method,(view,h) in itertools.product(METHODS,views.items()):
            text='Predict recorded suggestion handling. Label order: '+json.dumps(classes)+'. Accept means retained without revision; edit means accepted then changed; dismiss means explicitly rejected; ignore means no acceptance. Private intention is not labeled. Current pre-decision record: '+json.dumps(current,ensure_ascii=False)+'. Earlier completed records ('+view+'): '+json.dumps(h,ensure_ascii=False)
            if view=='witness':text+='\nVerified subsequent handling from the strict event reconstruction: '+r['truth']+'. This is explicit assistance, not a forecast.'
            if not fits(text,4):raise ValueError('CoAuthor declared projection does not fit')
            rows.append(row('LP16',u,view,text,[float(c==r['truth']) for c in classes],method,view=view,development=r['key'] in dev,classes=classes,prior=prior,persistence=[.99*float(c==own[-1]['truth'])+.01/len(classes) for c in classes],donor_component=donor[0]['unit']))
    validate_rows(rows);return rows,dict(eligible=len(candidates),selected=len(selected),development=16,components=len({r['unit'] for r in selected}),exclusions=dict(exclusions),fresh_components=0,projection='each text first/last half, 450 characters current and 300 history; omissions explicit')


def scholawrite():
    from runners.stage9.scholawrite import raw_inputs,reconstruct,CATEGORIES,LOCATIONS
    source,identity=raw_inputs();projects,ledger,summary=reconstruct(source)
    baseline=REPO/'results/phase_2_4_stage_9/private/pilot-baseline/scholawrite-v1'
    predictions={(r['key'],r['target']):r['probabilities'] for r in read(baseline/'PREDICTIONS.json')};rows=[];selected=[];contexts={}
    labels=list(itertools.product(CATEGORIES,LOCATIONS))
    for project,payload in projects.items():
        records=payload['records'];by=defaultdict(list)
        for r in records:by[r['session']].append(r)
        eligible=[]
        for stream in by.values():
            stream.sort(key=lambda r:r['source_ordinal'])
            for i,r in enumerate(stream):
                if not r['usable'] or i<2 or (r['key'],'category') not in predictions:continue
                if any(stream[j]['next_source_ordinal']!=stream[j+1]['source_ordinal'] for j in range(i-2,i)):continue
                contexts[r['key']]=(payload,stream[i-2:i]);eligible.append(r)
        chosen=balanced(eligible,50,lambda r:(r['next_category'],r['next_location']))
        if len(chosen)<5:raise ValueError('project lacks narrow admission windows')
        for i,r in enumerate(chosen):selected.append((r,i<5))
    for r,dev in selected:
        payload,earlier=contexts[r['key']];texts=payload['texts'];current=projection(texts[r['after']],1000)
        donors=[(x,d) for x,d in selected if x['unit']!=r['unit'] and x['category']==r['category']]
        if not donors:raise ValueError('no task-matched project donor')
        donor=min((x for x,d in donors),key=lambda x:(abs(len(projects[x['unit']]['texts'][x['after']])-len(texts[r['after']])),digest([r['key'],x['key']])))
        old=lambda xs,p:[dict(before=projection(p['texts'][x['before']],200),after=projection(p['texts'][x['after']],200),completed_category=x['category'],completed_location=x['location']) for x in xs]
        views=dict(current=[],previous=old([r],payload),earlier=old(earlier+[r],payload),donor=old([donor],projects[donor['unit']]))
        q=[float(c==r['next_category'] and l==r['next_location']) for c,l in labels]
        base={name:[predictions[r['key'],'category'][name][c]*predictions[r['key'],'location'][name][l] for c,l in labels] for name in ('class_prior','persistence','previous_transition')}
        run=1
        for e in reversed(earlier):
            if e['category']!=r['category']:break
            run+=1
        base['duration_rule']=base['persistence'] if run>=2 else base['class_prior']
        for method,(view,h) in itertools.product(METHODS,views.items()):
            text='Predict the NEXT RELEASED edit annotation and location in this visible editor fragment. This is not writer-reported cognition or the next physical keystroke. Category meanings: planning, implementation, revision. Location is the quarter containing the first changed character in the before text, or no_change. Joint label order: '+json.dumps(labels)+'. Current fragment: '+current+'\nEarlier completed records ('+view+'): '+json.dumps(h,ensure_ascii=False)
            if dev:text+='\nDevelopment known-answer assistance: the strict successor has category '+r['next_category']+' and location '+r['next_location']+'. Return that joint label; this assisted probe is excluded from main science.'
            if not fits(text,15):raise ValueError('ScholaWrite declared projection does not fit')
            rows.append(row('LP17',dict(unit=r['key'],cluster=r['unit']),view,text,q,method,view=view,development=dev,classes=labels,cheap_references=base,annotation_transition=r['category']!=r['next_category'],prior_span_length=run))
    validate_rows(rows);return rows,dict(selected=len(selected),development=sum(d for r,d in selected),projects=len(projects),source_summary=summary,identity=identity,baseline_sha256=filehash(baseline/'PREDICTIONS.json'),duration_rule='fixed no-fit rival: persistence if two or more completed annotations agree, otherwise existing training prior',projection='current first/last 500 characters; historical text first/last 100; omissions explicit',scope='aggregate-only restricted human records; all five projects previously exposed')


def realization():
    from runners.run_g159_gen import mechanical_check,BUILD_SUFFIX
    root=REPO/'corpora/g159_rebuild';audit=read(root/'realization_audit.json');rows=[];counts=Counter()
    for a in audit['rows']:
        if a['grade']!='exact':continue
        record=read(root/a['family']/(a['artifact_id']+'.json'));ins=record['instructions'][a['instruction_index']]
        check=mechanical_check(BUILD_SUFFIX.sub('',ins),record['text'])
        if check!=('exact',a['passed']) or ins!=a['instruction']:raise ValueError('G159 realization differs from exact original audit')
        key=digest([a['family'],a['artifact_id'],a['instruction_index']]);u=dict(unit=key,cluster=record['lineage_id']);q=[float(not check[1]),float(check[1])]
        counts[(a['arm'],check[1])]+=1
        for method,view in itertools.product(METHODS,('artifact','instruction','trace')):
            text='Determine whether the artifact satisfies this mechanically checkable feature description: '+BUILD_SUFFIX.sub('',ins)+'. Label order: absent, present. Artifact:\n'+record['text']
            if view in ('instruction','trace'):text+='\nSource instruction role: '+record['instructions_role']+'. '+('This feature was requested from the maker.' if a['arm']=='plus' else 'This was a counterfactual instruction NEVER shown to the maker; do not call it an actual request.')
            if view=='trace':text+='\nCheckable execution record: the exact source feature checker returns '+('present' if check[1] else 'absent')+'. This is privileged verified assistance.'
            if not fits(text,2):raise ValueError('G159 full artifact exceeds context; do not silently truncate exact checker input')
            rows.append(row('LP18',u,view,text,q,method,view=view,instruction_sign=a['arm'],fulfilled=check[1],exact_check=check,artifact_sha256=digest(record['text'])))
    if len(rows)>384 or set(k[1] for k in counts)!={False,True}:raise ValueError('realization census or dynamic range')
    validate_rows(rows);return rows,dict(exact_items=len(rows)//6,realization_counts={str(k):v for k,v in counts.items()},counterfactual_not_requested=True,source_sha256=filehash(root/'realization_audit.json'))
