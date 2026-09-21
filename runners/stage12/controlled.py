"""Consumers of retained worlds; no substitute human or local-goal verdict.

DESIGN CHECK: LESSONS 3-5; CONTROLS 6. NULL: same informative inputs can make
direct and coherent references equal. ALTERNATIVE: marginalization may lose a
dependency, but a structural difference is not a learned-reader advantage.
Independent static assignments commute; ordered dependent updates need not.
"""
from __future__ import annotations
import copy
import json
import sys
from .common import REPO, read, freeze, filehash, digest, distribution

PUBLIC=REPO/'results/phase_2_4_stage_10/raw/interface-v3/ghost-public'

def ghost_reference(out,card,pulse,raw):
    from runners.stage10.ghost import envelopes
    sys.path.insert(0,str(PUBLIC/'public/consumer'))
    from v16_reference.reconstruction import reader
    from v16_reference.opportunity import public_reader
    rows,_=envelopes(PUBLIC)
    by={r['envelope']['task_id']:r['envelope'] for r in rows}
    result=[];controls=[]
    for identifier in card['candidate_ids']:
        e=by[identifier];c=e['declared_context']
        if c['operation'] not in ('reading','opportunity'):raise ValueError('wrong frozen source target')
        payload=c['observation'];frames={}
        strategies=('generic','primitive','direct-table','maker') if c['operation']=='reading' else ('generic','fixed-menu','budget-only','accurate-belief','direct-table','latent-menu')
        for strategy in strategies:
            data=json.dumps(payload,sort_keys=True,separators=(',',':')).encode()
            p=reader(data,strategy=strategy) if c['operation']=='reading' else public_reader(data,model=strategy)
            frames[strategy]=p
            if p.get('model_mismatch'):continue
            if abs(sum(p['future_probabilities'])-1)>1e-10:raise ValueError('invalid reference distribution')
        main='maker' if c['operation']=='reading' else 'latent-menu'
        agreement=max(abs(a-b) for a,b in zip(frames['direct-table']['future_probabilities'],frames[main]['future_probabilities']))<1e-10
        # Independently construct the direct joint mixture under the same law;
        # equality is an instrument invariant, not a required learned-model win.
        controls.append(agreement)
        result.append(dict(id=identifier,lineage=e['lineage_id'],public_sha256=digest(payload),
            operation=c['operation'],inputs=payload,readers=frames,local_goals='unavailable in this retained export',
            reverse_process='candidate construction, not identified historical route',
            forward_target='future artifact under supplied finite laws',values='bounded acquired-library hypothesis only'))
        pulse(completed=len(result),total=len(card['candidate_ids']))
    if len(result)!=16 or not all(controls):raise ValueError('complete sixteen-unit source reference gate')
    freeze(out/'REFERENCE_ROWS.json',result)
    return dict(status='complete',kind='infrastructure',units=16,rivals=dict(reading=4,opportunity=6),
        scope='retained constructed Ghost export, exact supplied-law reference; learned/local-goal comparisons pending',
        local_goal_status='unavailable; never relabel governing target as local goal',
        controls=dict(distributions_normalized=True,full_direct_table_equals_coherent_mixture=True,complete_frozen_roster=True),
        files={'REFERENCE_ROWS.json':filehash(out/'REFERENCE_ROWS.json')})

def continuing(out,card,pulse,raw):
    from runners.stage11_2.world import enumerate_predict,POLICIES,reference,decode
    base=REPO/'results/phase_2_4_stage_11_2/raw/fixture'
    public=read(base/'dev-public.json');truth=read(base/'dev-evaluator.json')
    by={r['unit']:(r,t) for r,t in zip(public,truth)};records=[]
    for identifier in card['candidate_ids']:
        u,t=by[identifier]
        for i,q in enumerate(u['queries']):
            obs=q['observation'];full=enumerate_predict(u['history'],obs)
            reordered=enumerate_predict(list(reversed(u['history'])),obs)
            retrieval=enumerate_predict(u['history'][-4:],obs)
            prior=enumerate_predict([],obs)
            # Factorize exactly the same two learned marginals. No planted state
            # enters either estimate; the evaluator remains a separate argument.
            marginal=[full['latent']['preference'][p]*full['latent']['skill'][k] for p,k in POLICIES]
            independent=enumerate_predict([],obs,prior=marginal)
            exact=reference(t['queries'][i]['preference'],t['queries'][i]['skill'],*decode(obs),obs['world_family'],obs['tools'])
            if exact!=t['queries'][i]['probabilities']:raise ValueError('independent executor disagrees')
            if max(abs(a-b) for a,b in zip(full['probabilities'],reordered['probabilities']))>1e-12:raise ValueError('independent evidence order changed exact posterior')
            arms={'full_history':full,'reordered_same_facts':reordered,'retrieval':retrieval,'whole_bundle':full,
                  'independent_marginals':independent,'training_prior':prior}
            records.append(dict(id=identifier,encounter=i,arms={k:dict(probabilities=v['probabilities'],
                metrics=distribution(v['probabilities'],exact)) for k,v in arms.items()},
                dependency_discarded=list(zip(full['weights'],marginal)),
                interpretation='supplied-law structural reference; no neural reorganization or new human result'))
        pulse(completed_units=len(records)//4,total=len(card['candidate_ids']))
    freeze(out/'STRUCTURAL_ROWS.json',records)
    return dict(status='complete',kind='infrastructure',units=len(card['candidate_ids']),queries=len(records),
        target='same-evidence update and whole-hypothesis versus independent-marginal consumer validation',
        neural_C1_C2='separate learned-reader request compilation and current healthy-reader admission required',
        controls=dict(reference_executor_agreement=True,independent_evidence_reordering_invariant=True,
                      all_frozen_arms_complete=True),files={'STRUCTURAL_ROWS.json':filehash(out/'STRUCTURAL_ROWS.json')})

def tiny_rehearsal(out,card,pulse,raw):
    import torch
    from runners.stage11_2.alignment import interchange
    torch.set_num_threads(1);torch.manual_seed(card['seed'])
    base=torch.tensor([[0.,0.,2.,3.]]);donor=torch.tensor([[1.,1.,4.,5.]])
    a=torch.eye(4)[:,:1];b=torch.eye(4)[:,1:2]
    no_op=interchange(base,donor,a,alpha=0)
    ab=interchange(interchange(base,donor,a),donor,b)
    ba=interchange(interchange(base,donor,b),donor,a)
    # Reference update B reads state A. This is a different target from two
    # independent static assignments and must not be conflated with them.
    def update_a(x):y=x.clone();y[:,0]=1;return y
    def update_b(x):y=x.clone();y[:,1]=x[:,0];return y
    controls=dict(noop_exact=torch.equal(base,no_op),static_assignments_commute=torch.equal(ab,ba),
        dependent_updates_ordered=not torch.equal(update_b(update_a(base)),update_a(update_b(base))),
        full_state_copy=torch.equal(interchange(base,donor,torch.eye(4)),donor))
    if not all(controls.values()):raise ValueError('causal consumer known-answer fixture')
    design=dict(schema='s12.shared-tiny.1',proposed_training_owner='Sounding Line',
        shared_settings_maximum=2,settings_used_here=0,training_status='waiting for cross-project ownership receipt and frozen Ghost roster',
        planned_setting=dict(model='single-layer GRU',hidden_width=32,readout='finite action softmax',
            optimizer='Adam',learning_rate=.001,batch_size=64,epochs=20,seeds=[120921,120922],cpu_pilot_seconds=14400),
        source='Ghost generator and reference, not a new Sounding Line world',
        gates=['separated development/test worlds','task competence','no-op invariance','reference consistency'],
        controls=['correct interchange','random','shuffled','wrong variable','no-op','full state'],
        transfer=['new goal/belief combinations','independent assignments commute','dependent updates ordered'],
        mechanism_claim='only after complete admitted learned-reader comparison; algebra fixture is infrastructure')
    freeze(out/'KNOWN_ANSWER.json',controls);freeze(out/'SHARED_TINY_DESIGN.json',design)
    pulse(phase='causal-consumer-rehearsed')
    return dict(status='complete',kind='infrastructure',settings_trained=0,controls=controls,
        scope='existing interchange operator checked on known tensors, not a trained-reader mechanism result',
        next='freeze shared owner, actual Ghost roster and complete training/causal consumer before fit',
        files={n:filehash(out/n) for n in ('KNOWN_ANSWER.json','SHARED_TINY_DESIGN.json')})
