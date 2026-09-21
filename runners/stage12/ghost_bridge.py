"""Consumer of the versioned Ghost local-world export; source role separation.

DESIGN CHECK: LESSONS 2-5. NULL: indistinguishable histories retain alternatives,
and outside-family evidence stays unknown. ALTERNATIVE: more witnessed process
may narrow candidates, never silently reveal unobserved selected goals. Exact
likelihood and uniform compatible templates are declared privileged references;
the learned reader gets only PUBLIC_PACKET, never source parameters or labels.
"""
import importlib
import sys
from pathlib import Path
from .common import read,freeze,digest,filehash
from .provider import packet


def load_source(source):
    source=Path(source).resolve()
    name='ghostscale.validation.soundingline.v19.local_world'
    if name in sys.modules:
        module=sys.modules[name]
        if not Path(module.__file__).resolve().is_relative_to(source):raise ValueError('different Ghost source already loaded')
        return module
    sys.path.insert(0,str(source))
    module=importlib.import_module(name)
    if not Path(module.__file__).resolve().is_relative_to(source):raise ValueError('Ghost import escaped frozen source')
    return module


def local_packet(case,reference,method):
    text='\n'.join(r['rendering'] for r in case['passages']);anchors=[];offset=0
    for row in case['passages']:
        anchors.append(dict(id=row['id'],start=offset,end=offset+len(row['rendering'])))
        offset+=len(row['rendering'])+1
    evidence=dict(endpoint=text,anchors=anchors,source_public=case['packet'])
    alternatives=reference.get('complete_hypotheses',[])
    p=packet(case['case_id'],evidence,method,[],alternatives,tier=case['packet']['tier'],origin='constructed Ghost local world')
    # Candidate goal support is explicitly a finite reference, not a human
    # mental observation or calibrated probability from a learned reader.
    p['candidate_local_goals']=reference.get('goal_support',[])
    p['candidate_governing_purposes']=reference.get('governing_support',[])
    p['support_semantics']=reference.get('support_kind','unknown outside finite support')
    p['next_discriminator']='An observed operation at the ambiguous step or a choice under a changed request; if every compatible goal predicts it identically, this observation cannot distinguish them.'
    return p


def consume(out,card,pulse,raw):
    root=Path(card['export_root']);source=Path(card['generator_source'])
    export=read(root/'PUBLIC_PACKET.json');manifest=read(root/'EXPORT_MANIFEST_2.json')
    for name,h in manifest['files'].items():
        if filehash(root/name)!=h:raise ValueError('Ghost export changed: '+name)
    for name,h in card['generator_pins'].items():
        if filehash(source/name)!=h:raise ValueError('Ghost extracted source changed')
    model=load_source(source);cases=export['cases'];by={c['case_id']:c for c in cases}
    if set(card['candidate_ids'])!=set(by):raise ValueError('Ghost public roster differs')
    groups={};rows=[];packets=[];requests=[];evaluators=[]
    for i,key in enumerate(card['candidate_ids']):
        case=by[key];public=case['packet'];model.validate_public(public)
        if model.digest(public)!=case['input_sha256']:raise ValueError('native public projection digest differs')
        lineage=int(key.split('-')[0])
        if lineage not in groups:
            records=model.enumerate_world(model.law(lineage))
            if len(records)!=13824 or abs(sum(r['probability'] for r in records)-1)>1e-10:raise ValueError('Ghost support normalization')
            groups[lineage]=records
        records=groups[lineage];exact=model.infer(public,records);template=model.infer(public,records,False)
        if exact['candidate_count']==0:raise ValueError('supplied native case outside source support')
        if {h['compatibility_id'] for h in exact['complete_hypotheses']}!={h['compatibility_id'] for h in template['complete_hypotheses']}:
            raise ValueError('likelihood and template support disagree')
        for name,reference in [('supplied-law likelihood',exact),('uniform compatible complete templates',template)]:
            packets.append(local_packet(case,reference,name))
        # O receives the actual synthetic record. It is never a learned arm.
        truth=next(r for r in records if r['maker_index']==0 and r['context_index']==0 and all(e['operation']=='inspect' for e in r['steps']))
        if model.project(truth,public['tier'])!=public:raise ValueError('fixture source replay failed')
        actual=tuple(e['operation'] for e in truth['steps'])
        coverage=any(tuple(h['operations'])==actual for h in exact['complete_hypotheses'])
        rows.append(dict(case_id=key,tier=public['tier'],input_hash=case['input_sha256'],candidate_count=exact['candidate_count'],
            joint_hypotheses=len(exact['complete_hypotheses']),historical_process_covered=coverage,
            located_candidate_goals=len(exact['goal_support']),unknown_values=True,adoption_unknown=True))
        evaluators.append(dict(case_id=key,exact=exact,template=template,actual=truth,
            label_role='synthetic evaluator only; never reader features'))
        for method in ('direct','coherent-account'):
            requests.append(dict(id=digest([key,method]),source_id=key,method=method,public=public,passages=case['passages'],
                question='Recover compatible passage-linked local purposes and process alternatives; keep governing purpose, external request, adoption and persistent values distinct.',
                schema='soundingline.provider.1',target_fields=['g_t','process','G','C_ext','adoption'],
                access='public projection only; generator coefficients and evaluator records withheld'))
        pulse(phase='Ghost-source-consumer',completed=i+1,total=len(cases))
    invalid=dict(schema='v19.local.public.1',tier='E0',inputs=dict(artifact=[2,0,0]))
    unknown=model.infer(invalid,next(iter(groups.values())))['unknown']
    controls=dict(model.controls(),outside_family_unknown=unknown,all_historical_processes_covered=all(r['historical_process_covered'] for r in rows),
        source_replay=True,exact_template_support_equal=True)
    freeze(out/'ROWS.json',rows);freeze(out/'PACKETS.json',packets);freeze(out/'REQUESTS.json',requests)
    freeze(out/'EVALUATOR_ONLY.json',evaluators)
    return dict(status='complete',kind='infrastructure',cases=len(rows),distinct_public_inputs=len({r['input_hash'] for r in rows}),
        lineages=len(groups),reader_requests=len(requests),packets=len(packets),learned_calls=0,
        scope='all-inspect ambiguity fixtures; not varied training population or learned local-goal evidence',controls=controls,
        files={n:filehash(out/n) for n in ('ROWS.json','PACKETS.json','REQUESTS.json','EVALUATOR_ONLY.json')})
