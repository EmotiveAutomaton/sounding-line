"""Conditional frozen-site composition and owner-produced practice consumers.

DESIGN CHECK: LESSONS 3-5. NULL: independent reference assignments commute;
dependent updates need not. Failure of that construction voids the ruler, not
the mechanism. Replay with identical frozen state and inputs is identical;
practice labels alone are not a treatment. Actual update/exposure provenance
and complete objective/observation crosses are required before scoring.
Only reviewed native Ghost references enter. No extra tiny fit is launched.
"""
from pathlib import Path
from .common import read,freeze,filehash,distribution


def model_from_record(record,root):
    import torch
    from .tiny import create
    path=(root/record['checkpoint']).resolve()
    if not path.is_relative_to(root.resolve()) or filehash(path)!=record['checkpoint_sha256']:raise ValueError('model checkpoint binding')
    saved=torch.load(path,map_location='cpu',weights_only=True);model=create(record['recipe']);model.load_state_dict(saved['model']);model.eval()
    for p in model.parameters():p.requires_grad_(False)
    return model


def reviewed_source(card):
    receipt=read(card['reviewed_receipt']);path=Path(receipt['path'])
    if receipt.get('native_reference_replay') is not True or filehash(path)!=receipt['sha256']:raise ValueError('unreviewed or changed native reference export')
    return path,read(path)


def reference_composition(row):
    targets=row['reference'];a=targets['ab'];b=targets['ba']
    if set(a)!=set(b):raise ValueError('composition target heads differ')
    from .tiny import HEADS
    if set(a)!=set(HEADS):raise ValueError('composition target heads absent')
    for k,n in HEADS.items():
        if not all(distribution(v,[1.]+[0.]*(n-1))['valid'] for v in (a[k],b[k])):raise ValueError('invalid composition target')
    distance=max(abs(x-y) for k in a for x,y in zip(a[k],b[k]))
    if row['composition']=='independent-static' and distance>1e-12:raise ValueError('independent reference assignments do not commute')
    if row['composition']=='ordered-dependent' and distance<=1e-6:raise ValueError('ordered reference has no detectable order effect')
    if row['composition'] not in ('independent-static','ordered-dependent'):raise ValueError('unknown composition type')
    return distance


def compose(out,card,pulse,raw):
    import torch
    from .tiny import batch,fit_basis
    from runners.stage11_2.alignment import interchange
    path,data=reviewed_source(card);source=raw/'jobs'/card['model_card'];model=model_from_record(read(source/'MODEL.json'),raw)
    primary=raw/'jobs'/card['causal_card'];basis=torch.load(primary/'BASIS.pt',map_location='cpu',weights_only=True)
    if data.get('schema')!='ghost.composition.1' or data.get('frozen_site')!='final-gru-state':raise ValueError('composition source/site differs')
    if {r['lineage'] for r in data['development']} & {r['lineage'] for r in data['test']}:raise ValueError('composition split crossover')
    development=[]
    with torch.no_grad():
        for r in data['development']:
            development.append(dict(r,base=model.encode(*batch([{'public':r['base']}])),donor=model.encode(*batch([{'public':r['donor']}]))))
    if not development:raise ValueError('empty development composition pairs')
    # D1 site and A basis stay frozen. B-variable alignment uses development.
    b=fit_basis(model,development,1,120921,pulse=pulse);bs=fit_basis(model,development,1,120922,True,pulse)
    torch.manual_seed(120921);br=torch.linalg.qr(torch.randn_like(b),mode='reduced')[0]
    arms={'correct':(basis['learned'],b),'random':(basis['random'],br),
          'shuffled':(basis['shuffled'],bs),'wrong-variable':(b,basis['learned'])}
    rows=[]
    for index,r in enumerate(data['test']):
        reference_composition(r);pulse(phase='frozen-site-composition',completed=index,total=len(data['test']))
        with torch.no_grad():h={k:model.encode(*batch([{'public':r[k]}])) for k in ('base','a','b','b_after_a','a_after_b')}
        for name,(qa,qb) in arms.items():
            ab=interchange(interchange(h['base'],h['a'],qa),h['b'] if r['composition']=='independent-static' else h['b_after_a'],qb)
            ba=interchange(interchange(h['base'],h['b'],qb),h['a'] if r['composition']=='independent-static' else h['a_after_b'],qa)
            for order,state in [('ab',ab),('ba',ba)]:
                for head,logits in model.decode(state).items():
                    prediction=torch.softmax(logits[0],-1).tolist()
                    rows.append(dict(id=r['id'],lineage=r['lineage'],composition=r['composition'],arm=name,order=order,head=head,
                        target=distribution(prediction,r['reference'][order][head]),ordinary=distribution(prediction,r['ordinary'][head]),
                        state_discrepancy=float((ab-ba).norm()),intervention_norm=float((state-h['base']).norm())))
        for name,state in [('noop',h['base']),('full-state-ab',h['b_after_a']),('full-state-ba',h['a_after_b'])]:
            for head,logits in model.decode(state).items():
                prediction=torch.softmax(logits[0],-1).tolist()
                rows.append(dict(id=r['id'],lineage=r['lineage'],composition=r['composition'],arm=name,head=head,
                    target_ab=distribution(prediction,r['reference']['ab'][head]),target_ba=distribution(prediction,r['reference']['ba'][head]),ordinary=distribution(prediction,r['ordinary'][head])))
    if not rows or {r['composition'] for r in data['test']}!={'independent-static','ordered-dependent'}:raise ValueError('both reference composition types required')
    freeze(out/'ROWS.json',rows);torch.save(dict(b=b,shuffled=bs,random=br),out/'B_BASIS.pt')
    return dict(status='complete',kind='scientific',test_pairs=len(data['test']),rows=len(rows),
        scope='finite frozen-site transfer; conditional donor access explicit; intervention magnitudes and ordinary damage retained, no human correspondence',
        controls=dict(original_site_frozen=True,development_only_B_alignment=True,both_reference_types=True,all_controls=True),
        files={n:filehash(out/n) for n in ('ROWS.json','B_BASIS.pt')})


def expertise(out,card,pulse,raw):
    import torch
    from .tiny import batch
    path,data=reviewed_source(card);root=path.parent
    if data.get('schema')!='ghost.practice-replay.1' or data.get('training_owner')!='Ghost':raise ValueError('shared practice owner/schema differs')
    if not data.get('production_capability_admitted') or not data.get('charge_receipt_sha256'):raise ValueError('held-out production gate or accounting absent')
    required={'declarative','observational','practice','exact-replay'};groups={};models={};rows=[]
    for record in data['models']:models[record['id']]=model_from_record(record,root)
    for pair in data['pairs']:
        key=(pair['unit'],pair['objective'],pair['quality'],pair['distribution'])
        if pair['arm'] not in required or (key,pair['arm']) in groups:raise ValueError('duplicate or undeclared expertise arm')
        groups[key,pair['arm']]=pair
    keys={k for k,a in groups}
    if not keys or any({a for k,a in groups if k==key}!=required for key in keys):raise ValueError('incomplete practice/replay cross')
    expected={tuple(x) for x in card['cross']}
    if {(k[1],k[2],k[3]) for k in keys}!=expected:raise ValueError('declared objective/quality/distribution cross missing')
    for unit in {k[0] for k in keys}:
        if {(k[1],k[2],k[3]) for k in keys if k[0]==unit}!=expected:raise ValueError('partial source cross')
    for index,key in enumerate(sorted(keys)):
        practice=groups[key,'practice'];replay=groups[key,'exact-replay']
        for field in ('feedback_count','sample_count','tool_access','rng_sha256','initial_weights_sha256','optimizer_recipe_sha256'):
            if practice[field]!=replay[field]:raise ValueError('unmatched practice/replay budget or state: '+field)
        if practice['update_rule']=='frozen':
            if any(practice[k]!=replay[k] for k in ('model_id','public','persistent_state_sha256')):raise ValueError('frozen replay changed the instrument')
        elif practice['update_rule']=='weights-or-persistent-state':
            if not practice.get('update_trace_sha256') or not replay.get('update_trace_sha256'):raise ValueError('unrecorded practice updates')
        else:raise ValueError('unspecified practice treatment')
        for arm in sorted(required):
            pair=groups[key,arm];model=models[pair['model_id']]
            with torch.no_grad():logits=model(*batch([{'public':pair['public']}]))
            for head,values in logits.items():
                prediction=torch.softmax(values[0],-1).tolist()
                rows.append(dict(unit=key[0],objective=key[1],quality=key[2],distribution=key[3],arm=arm,head=head,
                    **distribution(prediction,pair['targets'][head])))
        pulse(phase='shared-practice-replay',completed=index+1,total=len(keys))
    freeze(out/'ROWS.json',rows)
    return dict(status='complete',kind='scientific',matched_cells=len(keys),rows=len(rows),settings_trained_here=0,
        scope='shared finite production/inversion comparison; mechanisms depend on actual recorded updates; no human expertise or flow claim',
        controls=dict(all_four_arms=True,budget_state_matching=True,held_out_production_gate=True,objective_quality_shift_cross=True),files={'ROWS.json':filehash(out/'ROWS.json')})
