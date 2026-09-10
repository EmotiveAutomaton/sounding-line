import copy
import numpy as np
import pytest
from runners.stage9.repair_features import LABELS,features,predict,rule,validate
from runners.stage9.repair_fit import fit,objective,select
from runners.stage9.repair_runtime import execute


def evidence(index,*,tight=False,library=False):
    return {'view':'artifact','current':{'context':{'topic':'fixture-'+str(index),'audience':'peer',
        'tools':{'library':library,'source_access':False},'deadline':'tight' if tight else 'loose',
        'sections':[{'name':'intro','slots':['claim']}]},'marks':[]},
        'requested_mark':'write:intro:claim','proposed_edit':'cite:intro:ref'}


def planted(start=0):
    return [{'unit':str(i),'evidence':evidence(i,tight=bool(i%2)),'target':'done' if i%2 else 'failed'} for i in range(start,start+80)]


def test_independent_gradient_and_visible_signal_learning():
    matrix=np.array([[1.,0.],[1.,1.],[1.,-1.]])
    weights=np.arange(8,dtype=float)*.03;targets=np.array([0,2,3]);sw=np.array([.2,.3,.5])
    _,analytic=objective(weights,matrix,targets,sw,.03)
    numerical=[]
    for i in range(8):
        plus=weights.copy();minus=weights.copy();plus[i]+=1e-6;minus[i]-=1e-6
        numerical.append((objective(plus,matrix,targets,sw,.03)[0]-objective(minus,matrix,targets,sw,.03)[0])/2e-6)
    assert np.allclose(analytic,numerical,atol=1e-8)
    models,receipt=fit(planted());selection=select(models,planted(),planted(100))
    assert selection['selected'].startswith('logistic-')
    assert selection['scores'][selection['selected']]>selection['scores']['class_prior']+.5
    assert all(r['converged'] for r in receipt['optimizers'].values())
    for row in planted(100):assert predict(row['evidence'],models[selection['selected']])[row['target']]>.9


def test_absent_signal_and_repeated_unit_weight_do_not_create_gain():
    rows=[{'unit':str(i),'evidence':evidence(i),'target':LABELS[i%4]} for i in range(80)]
    models,_=fit(rows)
    for parameters in models.values():assert all(abs(v-.25)<1e-10 for v in predict(evidence(999),parameters).values())
    original=planted();replicated=[*original,*[copy.deepcopy(original[0]) for _ in range(4)]]
    a,_=fit(original);b,_=fit(replicated)
    for name in a:
        pa,pb=predict(evidence(999,tight=True),a[name]),predict(evidence(999,tight=True),b[name])
        assert np.allclose(list(pa.values()),list(pb.values()),atol=1e-8)


def test_public_rule_and_schema_boundaries():
    row=evidence(0);assert rule(row)=='failed'
    row['current']['marks']=['cite:intro:ref'];assert rule(row)=='illegal'
    row['proposed_edit']='consult:intro:src';assert rule(row,True)=='failed'
    row['proposed_edit']='stop';assert rule(row)=='stopped'
    row['hidden_clock']=7
    with pytest.raises(ValueError,match='undeclared'):validate(row)
    a=evidence(0);b=evidence('renamed');assert features(a)==features(b)


def test_development_selection_refuses_source_and_exact_public_copies():
    rows=planted();models,_=fit(rows)
    with pytest.raises(ValueError,match='source overlap'):select(models,rows,rows)
    copied=copy.deepcopy(rows)
    for row in copied:row['unit']='new-'+row['unit']
    with pytest.raises(ValueError,match='public-task overlap'):select(models,rows,copied)


def test_actual_capsule_all_models_and_hidden_information_refusal(tmp_path):
    models,_=fit(planted());visible=evidence(999,tight=True);bundle={'evidence':visible,'models':models}
    result=execute(bundle,root=tmp_path/'models');assert result['accepted'],result
    assert result['prediction']['predictions']=={k:predict(visible,v) for k,v in models.items()}
    assert not any('construction' in p or 'local_repair' in p or 'fit' in p for p in result['copied_sources']['files'])
    hidden=copy.deepcopy(bundle);hidden['evidence']['truth']='CANARY'
    assert not execute(hidden,root=tmp_path/'private')['accepted']
    private=tmp_path/'private.json';private.write_text('private fixture',encoding='utf-8')
    result=execute(None,task={'probe':True,'forbidden_paths':[str(private)],'other_port':65534},root=tmp_path/'probe')
    assert result['accepted'],result
