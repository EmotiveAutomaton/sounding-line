from runners.stage13.located import train_crossfit,features,predict,overlap,windows
from runners.stage13.legacy import diff_features


def test_known_location_fit_source_folds_and_json_roundtrip(tmp_path):
    import json
    rows=[]
    for i in range(30):
        for label,text in [(0,'quiet calm ordinary human '*8),(1,'AUTOMATIC SYNTHETIC GENERATED '*8)]:
            rows.append(dict(key=f'{i}-{label}',unit=f'u{i}',text=text,label=label,spans=[[0,len(text)]] if label else [],location_truth_valid=True))
    model=train_crossfit(rows,tmp_path);replay=json.loads(json.dumps(model))
    assert len(model['oof'])==60 and len(model['folds'])==30
    assert features(rows,model,True)==features(rows,replay,True)
    assert predict(model['models'][0],rows[0]['text'])[0][0]<predict(model['models'][0],rows[1]['text'])[0][0]
    assert overlap((0,4),[[4,8]])==0 and overlap((0,4),[[0,4]])==1
    assert windows('x'*321)[-1][:2]==(320,321)


def test_diff_rival_uses_actual_added_material():
    a=diff_features(dict(before='red road',after='red quiet road',review_request='quiet'))
    b=diff_features(dict(before='red road',after='red road',review_request='quiet'))
    assert a[0]>b[0] and a[4]>b[4]


def test_joint_independence_severing_and_operation_controls():
    import numpy as np
    from runners.stage13.schola import joint,operation
    g,p=joint([.2,.8],[.6,.4],np.ones((2,2)))
    assert np.allclose(g,[.2,.8]) and np.allclose(p,[.6,.4])
    assert operation('old','old')=='unchanged'
    assert operation('old','old new')=='insert'
    assert operation('old new','old')=='delete'
    coupled=joint([.5,.5],[.99,.01],np.array([[2.,.1],[.1,2.]]))[0]
    assert coupled[0]>.9
