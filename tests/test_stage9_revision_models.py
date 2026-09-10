import copy
import pytest
from runners.stage9 import revision_features as features,revision_models as models,revision_runtime as runtime
from runners.stage9.common import digest,read
from runners.stage9.artifact_comparisons import audit_execution
from runners.run_arg_replication import change_features
from runners.stage9.argrewrite_baseline import features as original_features


def rows(classes):
    return [{'key':str(i),'unit':'source'+str(i),
        'evidence':{'before':'plain words','after':('bright proof ' if i%len(classes)==0 else 'smooth prose ' if i%len(classes)==1 else 'ordered detail ')*3},
        'labels':[classes[i%len(classes)]]} for i in range(18)]


def test_exact_historical_features_and_public_schema():
    classes=('a','b','c')
    for old,new in [('', ''),('', 'new words'),('old words',''),('abc','abd'),('The café blue','blue café The'),('x '*100,'x '*99+'y')]:
        assert features.change_features(old,new)==change_features(old,new)
        evidence={'before':old,'after':new}
        assert features.features(evidence,classes)==original_features(evidence)
    with pytest.raises(ValueError):features.features({'text':'public','truth':'private'},classes)
    with pytest.raises(ValueError):features.features({'before':'old','after':'new','earlier_labels':['unknown']},classes)


def test_exported_multiclass_binary_absent_class_and_known_null():
    for classes in [('a','b'),('a','b','c'),('a','b','c','absent')]:
        training=rows(classes[:3]);fitted=models.fit(training,classes)
        p=features.predict({'before':'plain words','after':'bright proof '*3},fitted)
        assert set(p)==set(classes) and abs(sum(p.values())-1)<1e-12
        assert p['a']>p['b']
        if 'absent' in classes:assert p['absent']==.01/len(classes)
        broken=copy.deepcopy(fitted);broken['coefficients']['a'][next(iter(broken['coefficients']['a']))]=float('nan')
        with pytest.raises(ValueError):features.predict(training[0]['evidence'],broken)
    training=rows(('a','b','c'))
    for r in training:r['evidence']={'text':'identical text'}
    fitted=models.fit(training,('a','b','c'))
    assert all(abs(p-1/3)<1e-10 for p in features.predict({'text':'identical text'},fitted).values())
    duplicate=training+[training[0]]
    with pytest.raises(ValueError):models.fit(duplicate,('a','b','c'))
    voting=[{'key':'x','unit':'u','evidence':{'text':'one'},'labels':['a','a','b']},
        {'key':'y','unit':'v','evidence':{'text':'two'},'labels':['b']}]
    expanded,prior=models.training_rows(voting,('a','b','absent'))
    assert abs(sum(r['weight'] for r in expanded)-2)<1e-12
    assert prior['a']==pytest.approx((1+2/3)/5) and prior['absent']==pytest.approx(1/5)


def test_actual_restricted_revision_worker_and_parameter_identity(tmp_path):
    classes=('a','b','c');fitted=models.all_models(rows(classes),classes)
    evidence={'before':'plain words','after':'bright proof '*3}
    task={'operation':'revision_models','parameters':fitted,'parameters_sha256':digest(fitted),'information_sha256':digest(evidence)}
    result=runtime.execute(evidence,root=tmp_path/'caps',task=task)
    assert result['accepted'],result
    audit_execution(result)
    assert result['prediction']['probabilities']=={k:features.predict(evidence,m) for k,m in fitted.items()}
    assert set(read(__import__('pathlib').Path(result['capsule'])/'evidence.json'))=={'before','after'}
    invalid=runtime.execute(evidence,root=tmp_path/'caps',task={**task,'parameters_sha256':'0'*64})
    assert not invalid['accepted'] and 'model identity' in invalid['error']['traceback']
    outside=tmp_path/'private-truth.json';outside.write_text('hidden evaluation labels')
    probe=runtime.execute(None,root=tmp_path/'caps',task={'probe':True,'forbidden_paths':[str(outside)],'other_port':65534})
    assert probe['accepted'] and probe['receipt']['all_raised'] and outside.read_text()=='hidden evaluation labels'
