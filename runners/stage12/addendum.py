"""Approved finite Stage 12 evidence-revision and binding addendum.

DESIGN CHECK: LESSONS 3-5; CONTROLS 6-7. NULL: exact irrelevant updates
leave targets unchanged; wrong supplied answers separate fidelity from loss.
ALTERNATIVE: diagnostic records move an independently computed reference.
All arms, invalids, saved reply bytes and original charges persist. Empty
support, changed sources, dynamic request drift and absent rivals refuse.
No model fit, outcome-selected expansion or new human-mechanism claim.
"""
from collections import defaultdict
from copy import deepcopy
import json
from pathlib import Path
import statistics
import tarfile
from .common import REPO, read, freeze, filehash, digest, distribution
from . import local_api
from .output_interface import adapt, profile_for_card
from .context_battery import text_for, independent, TRUE_FRAME, FALSE_FRAME, matched_timing_check
from .execution_access import rounded_answer, fidelity

UPDATES = ('unchanged', 'diagnostic', 'irrelevant')
BINDING = ('canonical', 'repeat', 'entry_order', 'label_order', 'distractor', 'wrong_vector')
PERMUTATION = (2, 0, 3, 1)

def rank_concordance(positive,negative):
    return None if positive is None or negative is None else float(positive>negative)+.5*float(positive==negative)


def source_aries(root, excluded):
    """Source-only eligibility, no reader outcomes; original byte rule retained."""
    from .aries import jsonl, paragraph_text
    root = Path(root)
    for row in read(root/'FETCH.json'):
        if filehash(root/row['name']) != row['sha256']:
            raise ValueError('ARIES source changed')
    labels = jsonl(root/'edit_labels_test.jsonl')
    papers = {r['doc_id'] for r in labels}
    if len(labels) != 196 or len(papers) != 42:
        raise ValueError('released source denominator changed')
    edits = {r['doc_id']:r for r in jsonl(root/'paper_edits.jsonl') if r['doc_id'] in papers}
    comments = {(r['doc_id'],r['comment_id']):r for r in jsonl(root/'review_comments.jsonl') if r['doc_id'] in papers}
    needed = {r[k] for r in edits.values() for k in ('source_pdf_id','target_pdf_id')}
    documents = {}
    with tarfile.open(root/'s2orc.tar.gz','r:gz') as archive:
        for member in archive:
            name = Path(member.name).stem
            if name in needed and member.isfile():
                if member.size > 8*1024*1024 or name in documents:
                    raise ValueError('oversize or duplicate source parse')
                documents[name] = json.load(archive.extractfile(member))
    if set(documents) != needed:
        raise ValueError('missing source parse')
    eligible = defaultdict(list)
    for label in labels:
        if not label['positive_edits'] or not label['negative_edits']:
            continue
        doc = label['doc_id']; record = edits[doc]
        by = {r['edit_id']:r for r in record['edits']}
        comment = comments[doc,label['comment_id']]
        counts = []
        for key in ('positive_edits','negative_edits'):
            count = 0
            for eid in label[key]:
                edit = by[eid]
                public = dict(review_request=comment['comment'],request_context=comment['comment_context'],
                    before=paragraph_text(documents[record['source_pdf_id']],edit['source_idxs']),
                    after=paragraph_text(documents[record['target_pdf_id']],edit['target_idxs']))
                count += len(json.dumps(public,ensure_ascii=True).encode()) <= 4200
            counts.append(count)
        if min(counts)>0:
            eligible[doc].append(label['comment_id'])
    chosen = sorted(set(eligible)-set(excluded),key=lambda x:digest(['S12-addendum-B',120923,x]))[:16]
    if len(chosen)!=16:
        raise ValueError('sixteen additional eligible paper groups unavailable')
    selected = {doc:min(eligible[doc],key=lambda x:digest(['S12-addendum-comment',120923,doc,x])) for doc in chosen}
    return dict(paper_ids=chosen,selected_comments=selected,pairs_per_class=1,
        census=dict(papers=42,label_rows=196,length_eligible_papers=len(eligible),
            excluded_compiled_papers=len(excluded),remaining_eligible_papers=len(set(eligible)-set(excluded))),
        scope='Additional paper groups only; historical corpus/model exposure and author independence remain unknown')


def inverse_labels(values, order):
    if values is None:
        return None
    if sorted(order)!=list(range(4)) or len(values)!=4:
        raise ValueError('invalid label permutation')
    result = [0.]*4
    for j,i in enumerate(order):
        result[i] = values[j]
    return result


def compile(out, card, pulse, raw):
    from runners.stage11_2.world import enumerate_predict, rules, render_observation
    roster = read(card.get('public_source',REPO/'results/phase_2_4_stage_11_2/raw/fixture/dev-public.json'))
    by = {r['unit']:r for r in roster}
    units = [by[k] for k in card['candidate_ids']]
    if not units or len({r['cluster'] for r in units})!=len(units):
        raise ValueError('missing or repeated history content')
    requests, targets, references = [], [], []
    def add(unit, condition, text, target, **extra):
        ident = digest(['S12-addendum',card['family'],unit['unit'],condition,extra.get('query',1),extra.get('method')])
        row = dict(id=ident,unit=unit['unit'],cluster=unit['cluster'],condition=condition,
            text=text,**extra)
        if not row.get('saved_reply'):
            row['request'] = adapt(local_api.request(text,4,row.get('call_class','forecast')),card['output_interface'])
        requests.append(row)
        targets.append(dict(id=ident,target=target,**({'supplied_answer':extra['supplied_answer']} if 'supplied_answer' in extra else {})))
    for ordinal, unit in enumerate(units):
        if card['family']=='revision':
            q=1; obs=unit['queries'][q]['observation']; short=unit['history'][:1]; long=unit['history'][:8]
            before=enumerate_predict(short,obs)['probabilities']; after=enumerate_predict(long,obs)['probabilities']
            if any(abs(a-b)>1e-12 for h,t in ((short,before),(long,after)) for a,b in zip(independent(h,obs),t)):
                raise ValueError('independent correction reference differs')
            movement=sum(abs(a-b) for a,b in zip(before,after))/2
            if movement<.05 or obs['reader_only_notice']==obs['last_notice_seen_by_maker']:
                raise ValueError('correction lacks diagnostic movement or publicly contradicted frame')
            frame=TRUE_FRAME if ordinal%2==0 else FALSE_FRAME
            # Both assertions concern public task rules, never a hidden maker label.
            new_record_text=text_for(unit,long,q,frame)
            old_record_text=text_for(unit,short,q,frame)
            extra_bytes=len(new_record_text.encode())-len(old_record_text.encode())
            if extra_bytes<=0:raise ValueError('no additional public evidence')
            marker='\nExplicitly irrelevant margin text:\n'
            filler=('Decorative page margin; not a maker observation. '*((extra_bytes//47)+2)).encode()[:extra_bytes-len(marker.encode())].decode('ascii')
            texts=dict(unchanged=old_record_text,diagnostic=new_record_text,
                irrelevant=old_record_text+marker+filler)
            if len(texts['irrelevant'].encode())!=len(texts['diagnostic'].encode()):raise ValueError('irrelevant length mismatch')
            references.append(dict(unit=unit['unit'],cluster=unit['cluster'],before=before,after=after,
                frame='true' if ordinal%2==0 else 'false',total_variation=movement,
                prefix_lengths=[1,8],irrelevant_bytes=extra_bytes,diagnostic_bytes=extra_bytes,
                irrelevant_target=before,query=q))
            for method, call_class in (('direct','forecast'),('account','account')):
                add(unit,'initial',old_record_text,before,method=method,call_class=call_class,update='initial',mode='initial',query=q)
                initial=requests[-1]['id']
                for update in UPDATES:
                    order=('saved','fresh') if int(digest([unit['unit'],method,update])[:2],16)%2 else ('fresh','saved')
                    for mode in order:
                        add(unit,update+'-'+mode,texts[update],after if update=='diagnostic' else before,
                            method=method,call_class=call_class,update=update,mode=mode,query=q,
                            saved_reply=initial if mode=='saved' else None)
        elif card['family']=='binding':
            bank={}
            for q in (1,3):
                obs=unit['queries'][q]['observation']; target=enumerate_predict(unit['history'],obs)['probabilities']
                if any(abs(a-b)>1e-12 for a,b in zip(target,independent(unit['history'],obs))):
                    raise ValueError('independent binding reference differs')
                bank[str(q)]=rounded_answer(target)
            if bank['1']==bank['3']:raise ValueError('lookup entries are constant')
            references.append(dict(unit=unit['unit'],cluster=unit['cluster'],bank=bank))
            for q in (1,3):
                obs=unit['queries'][q]['observation']; target=enumerate_predict(unit['history'],obs)['probabilities']
                for condition in BINDING:
                    order=list(PERMUTATION) if condition=='label_order' else list(range(4))
                    supplied={k:[v[i] for i in order] for k,v in bank.items()}
                    if condition=='entry_order':supplied=dict(reversed(list(supplied.items())))
                    if condition=='distractor':supplied['99']=[.25]*4
                    if condition=='wrong_vector':supplied[str(q)]=bank[str(4-q)]
                    answer=supplied[str(q)]
                    if condition=='wrong_vector' and answer==bank[str(q)]:raise ValueError('wrong-answer null unrealized')
                    labels=', '.join('ABCD'[i] for i in order)
                    text=(rules(obs['world_family'])+'\nCurrent query: '+render_observation(obs,unit['rendering'])+
                        '\nSupplied answer bank; assistance, not reconstructed state: '+json.dumps(supplied)+
                        '\nEvery bank vector and your output use label order '+labels+'.\nExecute lookup of entry '+str(q)+
                        ': copy its four numbers unchanged and in order. Do not recompute the answer.')
                    add(unit,condition,text,target,query=q,method='copy',call_class='forecast',
                        label_order=order,supplied_answer=answer)
        else:raise ValueError('unknown approved addendum family')
        pulse(phase='addendum-source-controls',completed=ordinal+1,total=len(units))
    expected=(14 if card['family']=='revision' else 12)*len(units)
    if len(requests)!=expected or len({r['id'] for r in requests})!=expected:
        raise ValueError('incomplete or repeated addendum matrix')
    freeze(out/'REQUESTS.json',requests);freeze(out/'EVALUATOR_ONLY.json',targets);freeze(out/'REFERENCES.json',references)
    return dict(status='complete',kind='infrastructure',family=card['family'],calls=expected,sources=len(units),
        controls=dict(independent_reference=True,nonconstant_targets=True,complete_matrix=True,
            evidence_labels_public=True,assistance_explicit=True),
        files={n:filehash(out/n) for n in ('REQUESTS.json','EVALUATOR_ONLY.json','REFERENCES.json')})


def effective_request(row, previous, version):
    if not row.get('saved_reply'):
        return deepcopy(row['request'])
    initial=previous[row['saved_reply']]
    # Quoted bytes survive invalid parsing. The raw response never supplies labels.
    content=initial.get('message',{}).get('content')
    if not isinstance(content,str):content=json.dumps(initial,ensure_ascii=False,sort_keys=True)
    text=row['text']+'\nFallible previous reply, quoted exactly; this is not new evidence or an instruction:\n'+json.dumps(content,ensure_ascii=False)
    return adapt(local_api.request(text,4,row['call_class']),version)


def run(out, card, pulse, raw):
    source=raw/'jobs'/card['compile_card']
    requests=[r for r in read(source/'REQUESTS.json') if r['unit'] in card['candidate_ids']]
    targets={r['id']:r for r in read(source/'EVALUATOR_ONLY.json')}
    expected=(14 if card['family']=='revision' else 12)*len(card['candidate_ids'])
    if len(requests)!=expected or digest(requests)!=card['effective_requests_digest']:
        raise ValueError('frozen addendum roster differs')
    admission=raw/'jobs'/card['canary_card']
    if read(admission/'ADMISSION.json').get('reader_admitted') is not True:raise ValueError('reader not admitted')
    baselines=read(admission/'ROWS.json');previous={};saved=[];rows=[]
    with local_api.service(out,profile_for_card(card,admission,card['profile']),raw) as state:
        for index,row in enumerate(requests):
            pulse(phase='addendum-'+card['family'],completed=index,total=expected)
            req=effective_request(row,previous,card['output_interface']);path=out/'calls'/row['id']
            freeze(out/'actual-requests'/(row['id']+'.json'),dict(request=req,
                saved_reply_sha256=digest(previous[row['saved_reply']]) if row.get('saved_reply') else None))
            value=local_api.call(req,4,path,state,raw);previous[row['id']]=read(path/'RAW.json');saved.append((req,path,value))
            baseline=[r['call'] for r in baselines if r['call_class']==row['call_class']]
            timing=matched_timing_check([value],baseline);freeze(out/('TIMING-'+row['id']+'.json'),timing)
            if timing['degraded']:raise RuntimeError('matched throughput degraded; preserve whole incomplete cell')
            target=targets[row['id']]['target'];p=value['probabilities'];canonical=inverse_labels(p,row.get('label_order',list(range(4))))
            score=distribution(canonical,target);floor=distribution(target,target)
            result=dict(id=row['id'],unit=row['unit'],cluster=row['cluster'],condition=row['condition'],
                method=row['method'],query=row['query'],probabilities=canonical,target=target,score=score,
                exact_reference=floor,uniform_reference=distribution([.25]*4,target),
                excess_half_brier=score['half_brier']-floor['half_brier'])
            if card['family']=='revision':result.update(update=row['update'],mode=row['mode'])
            else:result.update(fidelity=fidelity(p,targets[row['id']]['supplied_answer']))
            rows.append(result)
    for req,path,value in saved:
        if local_api.call(req,4,path,{'uncertain':False},raw)!=value:raise ValueError('addendum raw replay differs')
    freeze(out/'ROWS.json',rows)
    return dict(status='complete',kind='scientific',family=card['family'],calls=expected,
        scope='Paired constructed diagnostic; no hidden persistent state, human mechanism or independent world claim',
        controls=dict(all_rivals=True,saved_reply_binding=True,invalids_retained=True,raw_replay=True),
        files={'ROWS.json':filehash(out/'ROWS.json')})


def summarize_pairs(rows):
    """Same-snapshot comparison; invalids stay in the primary denominator."""
    by=defaultdict(dict);initials={(r['unit'],r['method']):r for r in rows if r.get('mode')=='initial'}
    for row in rows:
        if row.get('mode')=='initial':continue
        key=(row['unit'],row['method'],row['update'])
        if row['mode'] in by[key]:raise ValueError('duplicate revision result')
        by[key][row['mode']]=row
    result=[]
    for key,pair in sorted(by.items()):
        if set(pair)!={'fresh','saved'}:raise ValueError('incomplete saved/fresh pair')
        f,s=pair['fresh'],pair['saved']
        if f['exact_reference']!=s['exact_reference']:raise ValueError('different later target floor')
        initial=initials[key[:2]];target=f['target']
        def movement(later):
            a,b=initial['probabilities'],later['probabilities']
            if a is None or b is None:return dict(available=False,reason='invalid initial or later distribution retained')
            modal=lambda v:max(range(len(v)),key=v.__getitem__)
            before=modal(a)==modal(target);after=modal(b)==modal(target)
            return dict(available=True,total_variation_improvement=(sum(abs(x-y) for x,y in zip(a,target))-sum(abs(x-y) for x,y in zip(b,target)))/2,
                modal_correction=not before and after,modal_damage=before and not after,
                initial_loss_at_later_target=distribution(a,target)['half_brier'],later_loss=later['score']['half_brier'])
        result.append(dict(unit=key[0],method=key[1],update=key[2],
            fresh_minus_saved_loss=f['score']['half_brier']-s['score']['half_brier'],
            both_valid=f['score']['valid'] and s['score']['valid'],
            fresh_excess=f['excess_half_brier'],saved_excess=s['excess_half_brier'],
            fresh_movement=movement(f),saved_movement=movement(s)))
    return result


def summary(out,card,pulse,raw):
    rows=[]
    for job in card['source_jobs']:
        directory=raw/'jobs'/job;terminal=read(directory/'COMPLETE.json')
        for name,h in terminal['output_files'].items():
            if filehash(directory/name)!=h:raise ValueError('source result changed')
        rows.extend(read(directory/'ROWS.json'))
    if card['family']=='revision':
        comparisons=summarize_pairs(rows)
        if len(comparisons)!=48:raise ValueError('revision family incomplete')
    elif card['family']=='binding':
        if len(rows)!=48:raise ValueError('binding family incomplete')
        comparisons={condition:dict(attempted=len(own),valid=sum(r['score']['valid'] for r in own),
            copied_exactly=sum(r['fidelity']['copied_exactly'] for r in own),
            half_brier=statistics.mean(r['score']['half_brier'] for r in own))
            for condition in BINDING for own in [[r for r in rows if r['condition']==condition]]}
    elif card['family']=='aries':
        from .output_interface import rows_for_card
        source=raw/'jobs'/card['compile_card'];inputs=read(source/'SOURCE_ROWS.json');public={r['id']:r for r in inputs}
        truth={r['id']:r for r in read(source/'EVALUATOR_ONLY.json')};probabilities={}
        for job in card['source_jobs']:
            manifest=read(raw/'manifests'/(job+'.json'))
            expected=rows_for_card([r for r in read(source/'REQUESTS.json') if r['id'] in manifest['request_ids']],manifest)
            for r in expected:
                path=raw/'jobs'/job/'calls'/r['id']
                if not (path/'COMPLETE.json').exists():raise ValueError('missing completed raw call')
                probabilities[r['id']]=local_api.call(r['request'],2,path,{'uncertain':False},raw)['probabilities']
        if len(rows)!=128 or len(probabilities)!=128:raise ValueError('ARIES family incomplete')
        groups=defaultdict(list)
        for row in rows:
            p=public[row['source_id']];groups[p['doc'],row['method'],row['direction']].append(row)
        comparisons=[]
        for (doc,method,direction),pair in sorted(groups.items()):
            if len(pair)!=2:raise ValueError('ranking pair incomplete')
            positive=next(r for r in pair if truth[r['id']]['target']==[0.,1.]);negative=next(r for r in pair if truth[r['id']]['target']==[1.,0.])
            pp=probabilities[positive['id']];pn=probabilities[negative['id']]
            comparisons.append(dict(paper=doc,method=method,direction=direction,
                model_concordance=rank_concordance(pp[1] if pp else None,pn[1] if pn else None),
                lexical_concordance=rank_concordance(public[positive['source_id']]['lexical_overlap'],public[negative['source_id']]['lexical_overlap']),
                model_half_brier=statistics.mean(r['half_brier'] for r in pair),
                valid=sum(r['valid'] for r in pair),attempted=2))
        if card.get('earlier_jobs'):
            earlier_public={r['id']:r for r in read(raw/'jobs'/card['earlier_compile_card']/'SOURCE_ROWS.json')}
            earlier=[]
            for job in card['earlier_jobs']:
                directory=raw/'jobs'/job
                for name,h in read(directory/'COMPLETE.json')['output_files'].items():
                    if filehash(directory/name)!=h:raise ValueError('earlier paper result changed')
                earlier.extend(read(directory/'ROWS.json'))
            populations={'new':[(public[r['source_id']]['doc'],r) for r in rows],
                         'earlier_exposed':[(earlier_public[r['source_id']]['doc'],r) for r in earlier]}
            if {p for p,r in populations['new']}&{p for p,r in populations['earlier_exposed']}:raise ValueError('additional papers overlap earlier support')
            populations['combined_descriptive']=populations['new']+populations['earlier_exposed'];weighted=[]
            for population,records in populations.items():
                for method,direction in sorted({(r['method'],r['direction']) for p,r in records}):
                    own=[(p,r) for p,r in records if (r['method'],r['direction'])==(method,direction)]
                    papers=sorted({p for p,r in own})
                    weighted.append(dict(population=population,method=method,direction=direction,papers=len(papers),
                        paper_weighted_half_brier=statistics.mean(statistics.mean(r['half_brier'] for p,r in own if p==paper) for paper in papers),
                        pair_weighted_half_brier=statistics.mean(r['half_brier'] for p,r in own),
                        valid=sum(r['valid'] for p,r in own),attempted=len(own),
                        scope='Descriptive paper weighting; earlier records exposed; unknown author dependence; invalid penalties retained'))
            freeze(out/'PAPER_WEIGHTING.json',weighted)
    else:raise ValueError('unknown addendum consumer')
    freeze(out/'COMPARISONS.json',comparisons);pulse(phase='whole-addendum-family-consumed')
    return dict(status='complete',kind='scientific',family=card['family'],rows=len(rows),
        scope='Complete descriptive paired comparison; every original score and failure preserved; no population p-values',
        controls=dict(whole_roster=True,source_replay=True,complete_pairs=True,invalids_retained=True),
        files={p.name:filehash(p) for p in (out/'COMPARISONS.json',out/'PAPER_WEIGHTING.json') if p.exists()})


def audit(out,card,pulse,raw):
    """Zero-call provenance/denominator consumer; source scores stay untouched."""
    inventory=[];cases=[];failure_records=[];human_pairs=[]
    for source in card['sources']:
        directory=raw/'jobs'/source['job'];terminal=read(directory/'COMPLETE.json')
        if filehash(directory/'COMPLETE.json')!=source['terminal_sha256']:raise ValueError('audit source changed')
        manifest=read(raw/'manifests'/(source['job']+'.json'))
        if filehash(raw/'manifests'/(source['job']+'.json'))!=terminal['manifest_sha256']:raise ValueError('audit manifest changed')
        for name,h in manifest.get('inputs',{}).items():
            if filehash(name)!=h:raise ValueError('audit input changed')
        for name,h in {**terminal['output_files'],**read(directory/'SUMMARY.json').get('files',{})}.items():
            if filehash(directory/name)!=h:raise ValueError('audit output changed')
        states=defaultdict(int)
        for call in (directory/'calls').glob('*/COMPLETE.json'):
            saved=read(call);response=read(call.with_name('RAW.json'))
            if saved.get('raw_sha256')!=digest(response):raise ValueError('audit raw binding changed')
            states['returned']+=1;states['literal_valid']+=saved.get('probabilities') is not None
        states['attempted']=len(list((directory/'calls').glob('*/REQUEST.json')))
        inventory.append(dict(job=source['job'],terminal_sha256=source['terminal_sha256'],handler=manifest['handler'],
            planned_requests=len(manifest['request_ids']) if 'request_ids' in manifest else manifest.get('planned_calls'),
            planned_candidates=len(manifest.get('candidate_ids',[])),whole_comparison_complete=True,
            scored_rows=len(read(directory/'ROWS.json')) if (directory/'ROWS.json').exists() else None,
            request_counts=dict(states),support=manifest.get('independent_unit',manifest.get('claim_scope','see original source protocol')),
            source_score_files={n:filehash(directory/n) for n in ('ROWS.json','METRICS.json','COMPARISONS.json') if (directory/n).exists()},
            original_scores_unchanged=True))
        if manifest['handler']=='process-context':
            from runners.stage11_1.score import summarize
            original=read(directory/'ROWS.json');grouped=defaultdict(list)
            for row in original:grouped[row['key'],row['view']].append(row)
            methods={r['method'] for r in original}
            if any({r['method'] for r in pair}!=methods or len(pair)!=len(methods) for pair in grouped.values()):
                raise ValueError('human replay missing paired rival')
            eligible={key for key,pair in grouped.items() if not any(r['invalid'] for r in pair)}
            for view in sorted({r['view'] for r in original}):
                for method in sorted(methods):
                    all_rows=[r for r in original if r['view']==view and r['method']==method]
                    paired=[r for r in all_rows if (r['key'],view) in eligible]
                    human_pairs.append(dict(job=source['job'],view=view,method=method,attempted=len(all_rows),
                        complete_pairs=len(paired),all_attempt=summarize(all_rows),
                        secondary_complete_pair=summarize(paired) if paired else None,
                        interpretation='Secondary conditional view only; original all-attempt estimand retained'))
        pulse(phase='audit-completed-sources',completed=len(inventory),total=len(card['sources']))
    for source in card['failures']:
        if filehash(REPO/source['path'])!=source['sha256']:raise ValueError('retained failure changed')
        directory=(REPO/source['path']).parent
        failure_records.append(dict(source,attempted_requests=len(list((directory/'calls').glob('*/REQUEST.json'))),
            returned_raw=len(list((directory/'calls').glob('*/RAW.json'))),
            complete_calls=len(list((directory/'calls').glob('*/COMPLETE.json'))),
            whole_comparison_complete=False,scope='Historical failure retained; selected replacement status comes from frozen support map'))
    for slot in card['case_slots']:
        path=Path(slot['path']);data=read(path)
        if filehash(path)!=slot['sha256']:raise ValueError('case source changed')
        selected=data[slot['ordinal']] if isinstance(data,list) else data
        cases.append(dict(role=slot['role'],source=slot,record=selected,
            interpretation='Source-bound illustration; no new truth label, independence or calibrated mental probability'))
    if len(cases)!=8 or len({r['role'] for r in cases})!=8:raise ValueError('eight case roles required')
    freeze(out/'INVENTORY.json',inventory);freeze(out/'FAILURES.json',failure_records);freeze(out/'CASES.json',cases)
    freeze(out/'CHARGE_SNAPSHOT.json',card['charge_snapshot'])
    freeze(out/'SUPPORT_MAP.json',card['support_map'])
    freeze(out/'HUMAN_COMPLETE_PAIRS.json',human_pairs)
    return dict(status='complete',kind='scientific',sources=len(inventory),failures=len(failure_records),cases=8,
        scope='Immutable source/denominator and case audit; complete-pair scientific consumers retain original all-attempt scores',
        controls=dict(source_bindings=True,raw_hashes=True,prior_failures_retained=True,case_roles=True,no_model_calls=True),
        files={n:filehash(out/n) for n in ('INVENTORY.json','FAILURES.json','CASES.json','CHARGE_SNAPSHOT.json','HUMAN_COMPLETE_PAIRS.json','SUPPORT_MAP.json')})


def warm(out,card,pulse,raw):
    """One retained warm-up; previous canary admission remains authoritative."""
    from .output_interface import adapt
    admission=raw/'jobs'/card['canary_card']
    if read(admission/'ADMISSION.json').get('reader_admitted') is not True:raise ValueError('reader not admitted')
    req=adapt(local_api.request('Operational warm-up only. Copy the supplied distribution [0.25, 0.25, 0.25, 0.25] in A, B, C, D order.',4),card['output_interface'])
    pulse(phase='one-bounded-warm-up')
    with local_api.service(out,profile_for_card(card,admission,card['profile']),raw,diagnostic=True) as state:
        result=local_api.call(req,4,out/'calls/warm',state,raw,diagnostic=True)
    if result['probabilities'] is None:raise ValueError('warm-up literal response invalid; no retry')
    if local_api.call(req,4,out/'calls/warm',{'uncertain':False},raw,diagnostic=True)!=result:raise ValueError('warm-up replay differs')
    freeze(out/'WARM.json',dict(literal_valid=True,call_sha256=filehash(out/'calls/warm/COMPLETE.json'),
        scope='Operational load only; no renewed capability or scientific result'))
    return dict(status='complete',kind='infrastructure',calls=1,controls=dict(retained_raw=True,literal_valid=True),
        files={'WARM.json':filehash(out/'WARM.json')})
