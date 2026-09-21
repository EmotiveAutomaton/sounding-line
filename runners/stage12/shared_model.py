"""Import one reviewed Ghost-owned model; never train a duplicate setting.

DESIGN CHECK: LESSONS 3-5. NULL: a proposal or a ridge scout does not satisfy
the model gate. ALTERNATIVE: exact reviewed weights, source/target roster,
native training identity, cost and capability receipts can admit this consumer.
Unknown architectures require a new reviewed adapter, not permissive loading.
"""
from pathlib import Path
from .common import read,freeze,filehash


def import_model(out,card,pulse,raw):
    reviewed=read(card['reviewed_receipt']);root=Path(reviewed['export_root']);manifest=read(root/'EXPORT.json')
    if reviewed.get('schema')!='s12.shared-model-review.1' or reviewed.get('native_reference_replay') is not True:
        raise ValueError('actual source/interface review required')
    if filehash(root/'EXPORT.json')!=reviewed['export_sha256']:raise ValueError('reviewed export changed')
    if manifest.get('schema')!='ghost.shared-tiny-model.1' or manifest.get('architecture')!='gru-byte-v1':
        raise ValueError('unreviewed shared architecture; never substitute a scout model')
    for name,h in manifest['files'].items():
        path=(root/name).resolve()
        if not path.is_relative_to(root.resolve()) or filehash(path)!=h:raise ValueError('shared export member differs or escapes')
    owner=read(root/'OWNER.json');gate=read(root/'CAPABILITY.json');record=read(root/'MODEL.json')
    if owner.get('training_owner')!='Ghost' or owner.get('combined_settings_maximum')!=2 or not 1<=owner.get('settings_consumed',0)<=2:
        raise ValueError('shared fit ownership or combined allowance differs')
    if not owner.get('native_identity') or not owner.get('charge_receipt_sha256'):raise ValueError('fit identity or accounting absent')
    if gate.get('admitted') is not True or not reviewed.get('development_only_choices'):raise ValueError('task capability or source split not admitted')
    checkpoint=root/record['checkpoint']
    if not checkpoint.resolve().is_relative_to(root.resolve()) or record['checkpoint'] not in manifest['files'] or filehash(checkpoint)!=record['checkpoint_sha256']:raise ValueError('shared model checkpoint differs')
    import torch
    from .tiny import create
    saved=torch.load(checkpoint,map_location='cpu',weights_only=True)
    model=create(record['recipe']);model.load_state_dict(saved['model'])
    # Only tensor-safe checkpoint loading occurs later, after this receipt. No
    # external pickle or dynamically supplied model source is executed here.
    destination=out/'MODEL.pt';destination.write_bytes(checkpoint.read_bytes())
    freeze(out/'MODEL.json',dict(record,checkpoint=str(destination),checkpoint_sha256=filehash(destination)))
    for name in ('CAPABILITY.json','CAUSAL_PAIRS.json'):
        (out/name).write_bytes((root/name).read_bytes())
    pairs=read(out/'CAUSAL_PAIRS.json')
    if filehash(out/'CAUSAL_PAIRS.json')!=reviewed['causal_pairs_sha256'] or set(pairs)!={'development','test'}:
        raise ValueError('reviewed causal roster differs')
    if not pairs['development'] or not pairs['test']:raise ValueError('empty causal roster')
    for split,rows in pairs.items():
        if len({r['id'] for r in rows})!=len(rows):raise ValueError('duplicate causal identity')
        for r in rows:
            from .tiny import tokens,HEADS
            from .common import distribution
            for field in ('base','donor','wrong_variable'):tokens(r[field])
            for target in ('ordinary','counterfactual'):
                if set(r[target])!=set(HEADS):raise ValueError('causal target heads differ')
                for k,n in HEADS.items():
                    if not distribution(r[target][k],[1.]+[0.]*(n-1))['valid']:raise ValueError('invalid reference target')
    if {r['lineage'] for r in pairs['development']}&{r['lineage'] for r in pairs['test']}:raise ValueError('causal source crossover')
    freeze(out/'MODEL_READY.json',dict(status='complete',training_owner='Ghost',review_sha256=filehash(card['reviewed_receipt'])))
    pulse(phase='shared-model-imported')
    return dict(status='complete',kind='infrastructure',settings_trained_here=0,external_settings_consumed=owner['settings_consumed'],
        scope='reviewed finite model import; no causal effect or human mechanism claim',
        controls=dict(sole_external_fit=True,source_model_binding=True,capability_admitted=True,reviewed_reference=True,development_test_separate=True),
        files={n:filehash(out/n) for n in ('MODEL.pt','MODEL.json','CAPABILITY.json','CAUSAL_PAIRS.json','MODEL_READY.json')})
