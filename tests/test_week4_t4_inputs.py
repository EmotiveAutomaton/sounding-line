import copy
import numpy as np
import pytest
from runners.drive.cards import week4_t4_inputs as s
from runners.drive.cards import week4_t4_matched_cost as c


def test_complete_packing_and_training_only_scaling():
    rows=s.fixture();a=s.assemble(rows,2,3)
    changed=copy.deepcopy(rows)
    for r in changed:
        if r['half']=='test':
            r['state']=[10000.,-4000.]
            for f in r['features'][:-1]:f[0]+=10000
    b=s.assemble(changed,2,3)
    assert a['scaling']==b['scaling'] and a['train']==b['train']
    assert all(s.known_answers().values())
    assert s.assemble(list(reversed(rows)),2,3)==a
    s.independently_check(rows,a)


def test_invalid_source_and_support_refuse():
    rows=s.fixture()
    for kind in ('duplicate','choice','time','dismissal','session'):
        r=copy.deepcopy(rows)
        if kind=='duplicate':r.append(copy.deepcopy(r[0]))
        if kind=='choice':r[0]['choice']=5
        if kind=='time':r[0]['open_at']=300
        if kind=='dismissal':r[0]['features'][-1][0]=1
        if kind=='session':r[4]['session']=r[0]['session']
        with pytest.raises(ValueError):s.assemble(r,2,3)
    assert not s.assemble(rows,5,3)['summary']['support_pass']


def test_native_input_reentry_and_tamper(tmp_path):
    conf=s.configuration('constructed');s.execute(tmp_path,{},conf)
    assert s.verify(tmp_path,{},conf)['complete_input_replay']
    (tmp_path/'SUMMARY.json').write_text('{}')
    with pytest.raises(ValueError,match='replay'):s.verify(tmp_path,{},conf)


def test_generated_cost_never_uses_human_choices():
    assert all(c.known_answers().values())
    p=s.assemble(s.fixture(),2,3)
    for regime in (False,True):
        d=c.generated(p,20261102,regime)
        assert not np.any((d['y']<5)&~d['mask'][np.arange(len(d['y'])),np.minimum(d['y'],4)])


def test_cost_native_complete_fit_and_tamper(tmp_path):
    conf=c.configuration('constructed');c.execute(tmp_path,{},conf)
    assert c.verify(tmp_path,{},conf)['complete_generated_fit_replay']
    (tmp_path/'PRIVATE_FITS.json').write_text('[]')
    with pytest.raises(ValueError,match='replay'):c.verify(tmp_path,{},conf)


def test_completed_producer_consumer_boundary(tmp_path):
    import json
    from runners.stage14.common import filehash
    rows=[]
    for writer in range(25):
        for half,start in (('train',0),('test',100)):
            for i in range(24):
                r=copy.deepcopy(s.fixture()[i%4]);r.update(key=f'{writer}-{half}-{i}',writer=str(writer),
                    session=f'{writer}-{half}',half=half,open_at=start+i)
                rows.append(r)
    packed=s.assemble(rows);ic=tmp_path/'inputs/COMPLETE.json';bc=tmp_path/'bank/COMPLETE.json'
    for path in (ic,bc):path.parent.joinpath('output').mkdir(parents=True)
    def completion(path,names):
        path.write_text(json.dumps(dict(status='COMPLETE',fresh_process_verified=True,
            outputs={f'output/{n}':filehash(path.parent/'output'/n) for n in names})))
    s.gzip_equal(ic.parent/'output/PRIVATE_DATA.json.gz',packed)
    (ic.parent/'output/SUMMARY.json').write_text(json.dumps(dict(packed['summary'],mode='full')))
    (bc.parent/'output/SUMMARY.json').write_text(json.dumps(dict(complete_bank=True,bank_gate=True,worlds=40)))
    completion(ic,['PRIVATE_DATA.json.gz','SUMMARY.json']);completion(bc,['SUMMARY.json'])
    inputs=dict(inputs_completion=str(ic),bank_completion=str(bc));assert c.load(inputs)==packed
    (bc.parent/'output/SUMMARY.json').write_text(json.dumps(dict(complete_bank=True,bank_gate=False,worlds=40)))
    completion(bc,['SUMMARY.json'])
    with pytest.raises(ValueError,match='validation'):c.load(inputs)
    (bc.parent/'output/SUMMARY.json').write_text('{}')
    with pytest.raises(ValueError,match='changed'):c.load(inputs)
