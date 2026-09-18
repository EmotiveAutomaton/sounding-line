"""Outcome-blind preparation for the commissioned continuation branches.

DESIGN CHECK: LESSONS 2-5; CONTROLS 6. NULL: private answers never enter
requests, identical visible twins receive identical query menus, future/donor
history fails temporal admission. ALTERNATIVE: executed observations discriminate
histories and strictly earlier records can be reused before target access.
Preparation freezes exclusions and recipes; it makes no scientific selection.
"""
import argparse
import copy
import hashlib
import json
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from .common import PRIVATE, read, freeze, digest, canonical
from .prepare import balanced
from .construct import twins
from . import models_v3 as model
from .branch_runtime import auxiliary_request, task_steps
from runners.stage11.replay import replay

MENU = [dict(id='before',description='The document immediately before the suggestion menu.',retrieval_cost=1),
        dict(id='alternatives',description='The complete displayed suggestion alternatives.',retrieval_cost=1),
        dict(id='insertion',description='The first text-delta event after the menu, including recorded source and position.',retrieval_cost=1)]


def forecast(row,condition,method='direct',profile='qwen',public=None,**extra):
    return dict(kind='forecast',id=digest([row['key'],condition,method,profile])[:20],
                method=method,profile=profile,condition=condition,public=copy.deepcopy(public or row['views']['artifact']),
                evaluator={k:row[k] for k in ('key','writer','session','prompt','domain','target')},**extra)


def plan(identifier,branch,tasks,pursuit,warrant,next_action,requires=(),**extra):
    if len({t['id'] for t in tasks})!=len(tasks): raise ValueError('duplicate task identity')
    for t in tasks:
        if t['kind']=='forecast':
            model.request_for(t['public'],'account' if t['method']=='account' else 'direct')
        else: auxiliary_request(t)
    return dict(id=identifier,branch=branch,tasks=tasks,pursuit=pursuit,warrant=warrant,
                next_action=next_action,requires=list(requires),maximum_calls=sum(len(task_steps(t)) for t in tasks),**extra)


def source_rows(root):
    source=read(root/'SOURCE.json'); out={}
    for item in source['audit']:
        path=Path(item['path'])
        if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']: raise ValueError('original source changed')
        lines=[json.loads(s) for s in path.read_text(encoding='utf-8').splitlines()]
        events={e['ordinal']:e for e in replay(lines)['events']}
        out[item['session']] = (lines,events)
    return out


def observations(row,sources):
    lines,events=sources[row['session']]; event=events[row['ordinal']]
    candidates=[r for r in lines[event['ordinal']:event['cutoff_ordinal']] if r.get('textDelta')]
    insertion={'event':r.get('eventName'),'source':r.get('eventSource'),'operations':r['textDelta'].get('ops',[])} if (r:=next(iter(candidates),None)) else {'unavailable':'no text-delta event in interval'}
    return dict(before=event['document'],alternatives=[s['original'] for s in event['options']],insertion=insertion)


def s2_plan(rows,methods,constructed=False):
    tasks=[]
    for row in rows:
        public=row['views']['artifact']
        if constructed:
            for condition in ('blind','true','irrelevant','misleading'):
                e=copy.deepcopy(public)
                if condition!='blind': e['context_cue']=row['cues'][condition]
                tasks += [forecast(row,'twins-'+condition,m,public=e) for m in methods]
        else:
            # One common direct query policy; its selected evidence is identical
            # across the paired readers. Policy performance is a separate contrast.
            query=dict(id=digest(['query',row['key']])[:20],kind='query',profile='qwen',
                       public=dict(evidence=public,menu=MENU))
            tasks.append(query)
            random_choice=MENU[int(digest(public)[:8],16)%len(MENU)]['id']
            for condition,selection in [('blind',None),('fixed',dict(choice='before')),('random',dict(choice=random_choice)),('chosen',dict(query=query['id']))]:
                extra={} if selection is None else dict(reveal=dict(observations=row['observations'],**selection))
                tasks += [forecast(row,'human-'+condition,m,**extra) for m in methods]
    return plan('S2-twins-v1' if constructed else 'S2-evidence-v1','S2',tasks,
                'Identify ambiguity and selective correction from additional evidence',
                'Constructed ambiguity; four construction families, no human prevalence claim' if constructed else 'Exposed human records; equal retrieval actions, actual token costs reported',
                'Choose the smallest useful evidence tier, preserving blind failure and misleading-cue susceptibility',
                ['QUERY_PILOT_PASSED-v1.json'] if not constructed else [])


def history_plan(cohort,sources):
    pool=cohort['discovery']+cohort['breadth']; by={}; excluded=[]
    for row in pool:
        lines,_=sources[row['session']]
        timestamps=[e.get('eventTimestamp') for e in lines[row['ordinal']:row['cutoff_ordinal']]]
        start=timestamps[0];end=timestamps[-1]
        if any(not isinstance(t,int) for t in timestamps) or timestamps!=sorted(timestamps):
            excluded.append(dict(key=row['key'],reason='missing or nonmonotone episode times')); continue
        by.setdefault(row['writer'],[]).append((start,end,row))
    histories={}
    for writer,own in by.items():
        own.sort(key=lambda x:(x[0],x[2]['key']))
        first=own[0]; targets=[r for start,end,r in own[1:] if start>first[1]][-2:]
        if len(targets)<2:
            excluded.append(dict(writer=writer,reason='fewer than two targets strictly after separate history episode')); continue
        lines,events=sources[first[2]['session']];e=events[first[2]['ordinal']]
        # A declared byte-bounded excerpt of actual earlier source observations,
        # with no projection labels and no current/future target text.
        observed=[{k:r.get(k) for k in ('eventName','eventSource','textDelta','currentSuggestionIndex')}
                  for r in lines[e['ordinal']:e['cutoff_ordinal']]
                  if r.get('textDelta') or r.get('eventName') in ('suggestion-select','suggestion-close')]
        if not observed:
            excluded.append(dict(writer=writer,reason='earlier interval has no recorded production choice'));continue
        text='EARLIER OBSERVED CHOICES (excerpt): '+canonical(observed)+'\nEARLIER BEFORE TEXT: '+e['document']
        histories[writer]=dict(text=text,cutoff=first[1],targets=targets,
                               start=min(sources[r['session']][0][r['ordinal']]['eventTimestamp'] for r in targets),source=first[2]['key'])
    tasks=[]; admission=[]
    for writer,h in sorted(histories.items(),key=lambda x:digest(x[0])):
        donors=[(w,v) for w,v in histories.items() if w!=writer and v['cutoff']<h['start']]
        if not donors:
            excluded.append(dict(writer=writer,reason='no different-writer history earlier than both targets')); continue
        donor,dh=min(donors,key=lambda x:digest([writer,x[0]]))
        length=min(1200,len(h['text']),len(dh['text']))
        own_text=h['text'][:length]; donor_text=dh['text'][:length]
        hypothesis=dict(id=digest(['history',writer])[:20],kind='history',profile='qwen',public={'earlier_history':own_text})
        candidate=[hypothesis]
        for row in h['targets']:
            for condition in ('none','own-raw','donor-raw','own-hypothesis'):
                evidence=copy.deepcopy(row['views']['alternatives']); extra={}
                if condition in ('own-raw','donor-raw'): evidence['history']={'record_excerpt':own_text if condition=='own-raw' else donor_text,'excerpt_characters':length}
                if condition=='own-hypothesis': extra['history_ref']=hypothesis['id']
                candidate.append(forecast(row,'history-'+condition,public=evidence,**extra))
        try:
            for t in candidate:
                if t['kind']=='forecast':
                    e=copy.deepcopy(t['public'])
                    if 'history_ref' in t: e['history_hypothesis']={'reserved':'x'*3072}
                    model.request_for(e)
                else: auxiliary_request(t)
        except ValueError as exc:
            excluded.append(dict(writer=writer,reason='whole matched history set context screen: '+str(exc))); continue
        tasks+=candidate;admission.append(dict(writer=writer,donor=donor,history_cutoff=h['cutoff'],donor_cutoff=dh['cutoff'],first_target=h['start'],characters=length,history_source=h['source'],targets=[r['key'] for r in h['targets']]))
        if len(admission)==8: break
    result=plan('S4-history-v1','S4',tasks,'Test a reusable earlier-choice hypothesis against exactly the same raw history',
                'Descriptive, temporally earlier human process excerpts; matched characters, measured tokens; no values ruler',
                'Compare own hypothesis, own raw, donor raw and none with amortized construction costs',
                ['HISTORY_PILOT_PASSED-v1.json']) if tasks else None
    return result,dict(admission=admission,exclusions=excluded)


def intervention_plan(cohort):
    rows=cohort['discovery'][:16]; initial=cohort['discovery'][:32]; tasks=[]
    for row in rows:
        donor=next(r for r in initial if r['writer']!=row['writer'])
        for view in ('artifact','alternatives'):
            for mode in ('remove','replace'):
                ref=dict(job='S1-account-initial-v3b',key=(row if mode=='remove' else donor)['key'],view=view,mode=mode)
                tasks.append(forecast(row,'account-'+mode+'-'+view,'account',public=row['views'][view],account_ref=ref))
    return plan('S1-account-interventions-v1','S1',tasks,'Test whether the explicit account is used and whether that use helps',
                'Separate intervention; held public evidence, original full-account forecast retained; never infer benefit from movement alone',
                'Report accuracy changes beside susceptibility and invalid donor accounts', ['ACCOUNT_PILOT_PASSED-v3.json'])


def auxiliary_pilots():
    pair=twins()[:2]; tasks=[]
    query=[dict(id='query-'+str(i),kind='query',profile='qwen',public=dict(evidence=r['views']['artifact'],menu=MENU)) for i,r in enumerate(pair)]
    history=[dict(id='history-'+str(i),kind='history',profile='qwen',public=dict(earlier_history=canonical(r['trace']))) for i,r in enumerate(pair)]
    revision=[dict(id='revision-'+str(i),kind='revision',profile='qwen',public=dict(before=a,after=b,differences=[dict(before=a,after=b)],categories={'PLANNING':'organizing ideas','IMPLEMENTATION':'producing text','REVISION':'changing existing text'})) for i,(a,b) in enumerate([('A red boat.','A blue boat.'),('','A new sentence.')])]
    for kind,own in [('query',query),('history',history),('revision',revision)]:
        tasks.append(plan(kind+'-pilot-v1','integration',own,'Validate literal '+kind+' interface','Discarded constructed instrument check; no accuracy admission',
                          'Admit only this auxiliary interface or retire it visibly',pilot=True,pilot_gate=kind.upper()+'_PILOT_PASSED-v1.json'))
    for method in ('direct','review','account'):
        tasks.append(plan('llama-'+method+'-pilot-v1','integration',[forecast(r,'pilot',method,'llama') for r in pair],
                          'Validate the installed second reader on '+method,'Discarded constructed interface only',
                          'Admit this reader/method only; a failure does not block other methods',
                          pilot=True,pilot_gate='LLAMA_'+method.upper()+'_PILOT_PASSED-v1.json'))
    return tasks


def revision_plan():
    # Reuse and verify the cached source adapter; no scrape or new ingestion.
    from runners.stage9.schola_cases import inputs
    from runners.stage9.common import ROOT as OLD
    root=OLD/'private/prepared/scholawrite-v2'; ledger=read(root/'LEDGER.json')
    projects={r['unit']:read(root/r['path']) for r in ledger}; tasks=[]; sources=[]; excluded=[]
    descriptions={'PLANNING':'generating or organizing ideas or sections',
                  'IMPLEMENTATION':'producing text, manuscript objects, citations or references',
                  'REVISION':'changing clarity, coherence, structure, style, formatting, fluency or scientific accuracy'}
    for fold in range(5):
        partitions,source=inputs('scientific',fold); sources.append(digest(source))
        candidates={r['source_key']:r for r in partitions['evaluation']}
        used=0
        for key,row in sorted(candidates.items(),key=lambda x:digest(['stage11.1-revision',x[0]])):
            project=projects[row['unit']]; native=next(r for r in project['records'] if r['source_ordinal']==row['source_ordinal'])
            before=project['texts'][native['before']];after=project['texts'][native['after']]
            diff=[dict(operation=t,before=before[i:j],after=after[k:l]) for t,i,j,k,l in SequenceMatcher(None,before,after,autojunk=False).get_opcodes() if t!='equal']
            own=[]
            for view in ('endpoint','revision'):
                public=dict(before=before if view=='revision' else '',after=after,differences=diff if view=='revision' else [],categories=descriptions)
                t=dict(id=digest([key,view])[:20],kind='revision',condition=view,profile='qwen',public=public,
                       evaluator=dict(unit=row['unit'],truth=native['category'],source_ordinal=row['source_ordinal'],source_key=key))
                own.append(t)
            try:
                for t in own: auxiliary_request(t)
            except ValueError as exc:
                excluded.append(dict(key=key,reason=str(exc)));continue
            tasks+=own;used+=1
            if used==5:break
    return plan('S3-revision-v1','S3',tasks,'Recover released human revision annotations from observed before/after changes',
                'Historically exposed ScholaWrite, five project folds; annotator categories, no AI-involvement or private-purpose claim',
                'Compare endpoint and revision evidence by whole project; retain unavailable source/context cases',
                ['REVISION_PILOT_PASSED-v1.json']),dict(source_bindings=sources,excluded=excluded,projects=len({t['evaluator']['unit'] for t in tasks}))


def prepare(root=PRIVATE):
    cohort=read(root/'COHORT-v3.json'); native=source_rows(root); recipes={}; exclusions=[]
    human=[]
    for row in balanced(cohort['discovery'],99,8,'stage11.1-evidence'):
        own=copy.deepcopy(row); own['observations']=observations(row,native)
        try:
            for value in own['observations'].values():
                for method in ('direct','account'):
                    e=dict(row['views']['artifact'],observation=value)
                    model.request_for(e,'account' if method=='account' else 'review',{'reserved':'x'*3050})
        except ValueError as exc:
            exclusions.append(dict(key=row['key'],reason=str(exc)));continue
        human.append(own)
        if len(human)==16:break
    freeze(root/'continuation/S2-HUMAN.json',human);freeze(root/'continuation/S2-EXCLUSIONS.json',exclusions)
    for p in auxiliary_pilots(): recipes[p['id']]=p
    history,admission=history_plan(cohort,native);freeze(root/'continuation/S4-ADMISSION.json',admission)
    if history:recipes[history['id']]=history
    try:
        revision,audit=revision_plan();recipes[revision['id']]=revision
        freeze(root/'continuation/S3-REVISION-SOURCE.json',audit)
    except (OSError,ValueError,KeyError) as exc:
        freeze(root/'continuation/S3-REVISION-BLOCKER.json',dict(status='BLOCKED',reason=str(exc),next_action='Continue CoAuthor evidence and history branches'))
    recipes['S1-account-interventions-v1']=intervention_plan(cohort)
    # Candidate comparisons are frozen before outcomes. Activation remains an
    # explicit operator selection, after complete S1 comparison/write-through.
    for label,rows in [('initial',balanced(cohort['breadth'],32,8,'stage11.1-breadth-first'))]:
        selected={r['key'] for r in rows};extension=[r for r in cohort['breadth'] if r['key'] not in selected]
        for tranche,own in [(label,rows),('extension',extension),('second-reader',rows[:16])]:
            for method in ('direct','review','account'):
                profile='llama' if tranche=='second-reader' else 'qwen'
                gate=('LLAMA_'+method.upper()+'_PILOT_PASSED-v1.json') if profile=='llama' else (method.upper()+'_PILOT_PASSED-v3.json')
                identifier='S3-'+tranche+'-'+method+'-v1'
                recipes[identifier]=plan(identifier,'S3',[forecast(r,'breadth-alternatives',method,profile,public=r['views']['alternatives']) for r in own],
                    'Replicate leading production-relation contrasts across sources and an installed reader',
                    'Descriptive separate breadth; inherited writer/session/prompt exclusions and actual attainable support',
                    'Retain source, model and target heterogeneity; expand the finite remaining breadth if useful', [gate])
    for name,p in recipes.items(): freeze(root/'branch_plans'/f'{name}.json',p)
    summary=dict(status='PREPARED',cohort_digest=digest(cohort),plans={name:dict(digest=digest(p),calls=p['maximum_calls'],tasks=len(p['tasks'])) for name,p in recipes.items()},
                 human_evidence_episodes=len(human),constructed_pairs=24,history_writers=len(admission['admission']),
                 history_targets=sum(len(r['targets']) for r in admission['admission']),
                 scientific_selection='S2 methods and S3 leading contrasts await complete S1 disposition; no interim scores read',
                 next_action='Validate and freeze coordinator, then run independently gated S1, history and revision work')
    freeze(root/'continuation/PREPARED.json',summary);return summary


def select(methods,root=PRIVATE):
    if not methods or len(methods)>2 or len(set(methods))!=len(methods) or set(methods)-{'direct','review','account'}:
        raise ValueError('one or two explicitly selected viable methods required')
    for name,rows,constructed in [('human',read(root/'continuation/S2-HUMAN.json'),False),('twins',read(root/'S2/CONSTRUCTED.json'),True)]:
        p=s2_plan(rows,methods,constructed);freeze(root/'branch_plans'/f"{p['id']}.json",p)
    return methods


def candidates(root=PRIVATE):
    result={}
    for methods in [('direct','review'),('direct','account'),('review','account'),('direct',)]:
        for rows,constructed in [(read(root/'continuation/S2-HUMAN.json'),False),(read(root/'S2/CONSTRUCTED.json'),True)]:
            p=s2_plan(rows,list(methods),constructed)
            p['id']=p['id'].replace('-v1','-'+'-'.join(methods)+'-v1')
            freeze(root/'branch_plans'/f"{p['id']}.json",p)
            result[p['id']]=dict(digest=digest(p),calls=p['maximum_calls'],methods=list(methods))
    freeze(root/'continuation/S2-CANDIDATES.json',dict(status='PREPARED',plans=result,
        activation='Choose one pair (or one remaining viable model plus CPU) after complete S1 write-through; never run every candidate'))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=PRIVATE);parser.add_argument('--select',nargs='+');parser.add_argument('--candidates',action='store_true')
    args=parser.parse_args();print(canonical(candidates(args.root) if args.candidates else select(args.select,args.root) if args.select else prepare(args.root)))
