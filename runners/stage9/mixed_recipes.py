"""Correct mixed training targets with the original earlier-work supervision retained.

DESIGN CHECK: C05/X01/X08. Earlier expert works keep their independently correct
labels. The current learner-produced prefix is always masked. Up to four correct
teacher tails at one preassigned actual visited state receive labels. Earlier works
appear once, so repeating teacher continuations does not double their exposure.
The exact original expert half is fixed; final count matching only removes labels.
No learner-generated token is converted into a target to meet a budget.
"""
import copy
from collections import Counter
from pathlib import Path

from runners.stage8.reader import logfmt as LF
from runners.stage9.common import REPO,ROOT,closure,digest,file_hash,freeze,read
from runners.stage9.matching import earlier_context,mixture_keys,replay_row,match_budget,target_positions,audit
from runners.stage9.learner import MATCHED_TEACHER_DRAWS


def candidate(tok,source,collection,maximum_tokens=2048):
    if collection['lineage']!=source['key'] or collection['domain']!=source['raw_record']['domain']:
        raise ValueError('mixed example does not belong to collected source')
    visited=[e for e in collection['examples'] if e['learner_actions_applied']>0 and e['targets']]
    if not visited:
        return replay_row(source)|{'kind':'assigned_learner_unrealized','actual_learner_states':0}
    state=visited[int(digest({'matched_state':source['key']})[:12],16)%len(visited)]
    previous=earlier_context(source)
    if not state['prefix'].startswith(previous):
        raise ValueError('collection earlier-work context differs from the paired expert source')
    current=state['prefix'][len(previous):]
    # A copied expert example's earlier works are independently correct. They
    # are different from the current history produced by the learner itself.
    earlier_text=previous[:-len(LF.NOW+'\n')] if previous else ''
    ids=tok(earlier_text,add_special_tokens=True).input_ids if earlier_text else []
    labels=list(ids)
    earlier_span=[0,len(ids)]
    spans=[]
    for number,target in enumerate(state['targets'][:MATCHED_TEACHER_DRAWS]):
        context=(LF.NOW+'\n' if previous else '')+current
        prefix=tok(context,add_special_tokens=not bool(ids)).input_ids
        tail=tok(target['target']+tok.eos_token,add_special_tokens=False).input_ids
        if len(ids)+len(prefix)+len(tail)>maximum_tokens:
            break
        start=len(ids);ids.extend(prefix+tail);labels.extend([-100]*len(prefix)+tail)
        spans.append({'context':[start,start+len(prefix)],'correct_target':[start+len(prefix),len(ids)]})
    if not spans:
        raise ValueError('no complete teacher tail fits beside the unchanged earlier works')
    return {'key':source['key'],'input_ids':ids,'labels':labels,'lineages':list(source['lineages']),
            'kind':'learner_visited','actual_learner_states':state['learner_actions_applied'],
            'state_sha256':state['actual_state_sha256'],'spans':spans,'earlier_expert_span':earlier_span,
            'n_earlier':source['raw_record']['n_earlier'],
            'earlier_expert_supervised_tokens':sum(v!=-100 for v in labels[1:earlier_span[1]]),
            'complete_continuations_retained':len(spans),'complete_continuations_excluded':len(state['targets'])-len(spans)}


def build(tok,pool,expert_rows,records,budget):
    selected=mixture_keys(pool)
    if set(records)!=selected:
        raise ValueError('collection differs from the frozen mixture assignment')
    expert={r['key']:r for r in expert_rows}
    rows=[candidate(tok,s,records[s['key']]) if s['key'] in selected else copy.deepcopy(expert[s['key']]) for s in pool]
    fixed={r['key'] for r in rows if r['kind']!='learner_visited'}
    available=sum(len(target_positions(r)) for r in rows)
    # Keep the unchanged earlier expert targets exact; match only the current
    # independently correct tails. A shortage refuses, never labels the learner.
    protected={}
    for row in rows:
        end=row.get('earlier_expert_span',[0,0])[1]
        if end:
            protected[row['key']]=list(row['labels'][:end])
            row['labels'][:end]=[-100]*end
    preserved=sum(sum(v!=-100 for v in labels[1:]) for labels in protected.values())
    rows=match_budget(rows,budget-preserved,fixed_keys=fixed)
    for row in rows:
        if row['key'] in protected:
            original=protected[row['key']];row['labels'][:len(original)]=original
    if sum(len(target_positions(r)) for r in rows)!=budget:
        raise AssertionError('protected earlier-target matching differs')
    for row in rows:
        for span in row.get('spans',[]):
            start,end=span['context']
            if any(v!=-100 for v in row['labels'][start:end]):
                raise ValueError('learner prefix became a target')
    return rows,{'available_targets':available,'matched_targets':budget,'assigned_sources':len(selected),
                 'actual_visited_sources':sum(r['kind']=='learner_visited' for r in rows),
                 'protected_earlier_expert_targets':preserved,
                 'packing':'earlier expert works supervised once; current learner history masked; up to four independently correct current continuations',
                 'fixed_expert_rows_byte_preserved':all(r==expert[r['key']] for r in rows if r['key'] not in selected),
                 'dose':dict(Counter(str(r['raw_record']['n_earlier']) for r in pool))}


def prepare(family,coverage,collection_root,*,rehearsal_root=None,training=None):
    from transformers import AutoTokenizer
    from runners.stage9.train import BASES
    base=BASES[family];tok=AutoTokenizer.from_pretrained(base['model'],revision=base['revision'],local_files_only=True)
    rehearsal=rehearsal_root is not None
    if rehearsal:
        from runners.stage9.scientific_collector import collection_inputs
        from runners.stage9.training_jobs import rehearsal_input
        root=Path(rehearsal_root).resolve()
        if not root.is_relative_to(ROOT/'private/packing-handler-pilots') or root==ROOT/'private/packing-handler-pilots':
            raise ValueError('discarded packing requires its isolated namespace')
        _,_,pool,_=collection_inputs(family,coverage,training,rehearsal=True)
        old_path,_=rehearsal_input(family);old=read(old_path)
        expert={'examples':[replay_row(s) for s in pool['candidate_examples']],
                'validation':old['validation'],'validation_choices':old['validation_choices']}
    else:
        root=ROOT/'private/scientific-recipes'/family
        pool=read(ROOT/'private/training-pools'/family/(coverage+'.json'))
        expert=read(root/(coverage+'_expert.json'))
    collection_root=Path(collection_root).resolve();complete=read(collection_root/'COMPLETE.json')
    identity=read(collection_root/'IDENTITY.json')
    # Units stores the declared identity as JSON without wrapping it.
    if (identity['family']!=family or identity['coverage']!=coverage
            or identity.get('discarded_rehearsal') is not rehearsal
            or identity['pool_sha256']!=digest(pool) or complete['identity_sha256']!=digest(identity)
            or closure([REPO/p for p in complete['outputs']['files']])!=complete['outputs']):
        raise ValueError('scientific collection identity or pool mismatch')
    saved=[read(p) for p in sorted((collection_root/'units').glob('*.json'))]
    if any(r['identity']!=digest(identity) or r['complete'] is not True for r in saved):
        raise ValueError('mixed packing received a changed or incomplete collection unit')
    records={r['key']:r['row'] for r in saved}
    if len(records)!=len(saved):raise ValueError('duplicate collection source unit')
    budget=sum(len(target_positions(r)) for r in expert['examples'])
    rows,matching=build(tok,pool['candidate_examples'],expert['examples'],records,budget)
    comparison=audit({'expert':expert['examples'],'mixed':rows},pool['private_worlds'].keys())
    record={'family':family,'coverage':coverage,'discarded_rehearsal':rehearsal,
            'collection_identity':digest(identity),'collection_complete_sha256':file_hash(collection_root/'COMPLETE.json'),
            'sources':closure([REPO/'runners/stage9'/n for n in ('mixed_recipes.py','matching.py','common.py','learner.py')]),
            'matching':matching,'comparison':comparison,'source_pool_sha256':digest(pool)}
    result={'split':'pilot' if rehearsal else 'training','identity':record,'examples':rows,
            'validation':expert['validation'],'validation_choices':expert['validation_choices']}
    freeze(root/(coverage+'_mixed.json'),result)
    freeze(root/(coverage+'_MIXED_PREPARATION.json'),record)
    return record
