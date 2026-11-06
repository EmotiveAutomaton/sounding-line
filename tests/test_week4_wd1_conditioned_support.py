import copy
import itertools
import pytest
from runners.drive.cards import week4_wd1_conditioned_support as m


def test_exact_finite_conditional_population(monkeypatch):
    sessions=m.fixture();groups=[[s['session'] for s in sessions if s['prompt']==str(p)] for p in range(2)]
    assignments=[]
    for first,second in itertools.product(itertools.combinations(groups[0],2),itertools.combinations(groups[1],2)):
        zeros=set(first+second);assignments.append({s['session']:'0' if s['session'] in zeros else '1' for s in sessions})
    expected=[a for a in assignments if m.support(sessions,a)[0]==['0','1']]
    assert len(assignments)==36 and len(expected)==16
    monkeypatch.setattr(m.original,'permute_sessions',lambda rows,seed:assignments[seed])
    b=m.bank(sessions,37,36,seed=0)
    assert not b['complete'] and [a['assignment'] for a in b['accepted']]==expected
    assert len({m.digest(a) for a in expected})==16
    assert sum(not a['accepted'] for a in b['proposals'])==20


def test_bank_reads_only_metadata():
    sessions=m.fixture();changed=copy.deepcopy(sessions)
    for s in changed:s.update(handling='accept',sensitivity=999,criterion=-999,document='changed')
    assert m.bank(sessions,12)==m.bank(changed,12)
    assert set(m.metadata(changed)[0])==set(m.FIELDS)|{'decisions'}


def test_counts_match_actual_profile_support_and_order_is_canonical(tmp_path):
    import numpy as np
    from tests.test_week3_sdt import fixture
    from runners.stage14.common import read
    inputs=fixture(tmp_path);sessions=read(inputs['sessions'])
    sessions,rows,scalar,embedding=m.original.population_features(sessions,read(inputs['records']),np.load(inputs['vectors']))
    for index in range(3):
        assignment=m.original.permute_sessions(sessions,100+index)
        profiles=m.original.evaluate(sessions,rows,scalar,embedding,assignment,dict(seed=20261026,pca_dimensions=2))
        assert sorted(profiles['profiles'])==m.support(sessions,assignment)[0]
    assert m.bank(sessions,12)==m.bank(list(reversed(sessions)),12)


def test_exhausted_limit_preserves_rejections():
    b=m.bank(m.fixture(),100,4)
    assert len(b['proposals'])==4 and not b['complete']
    assert len(b['accepted'])<=4


def test_actual_handler_reentry_fresh_replay_tamper_and_no_fit(tmp_path,monkeypatch):
    monkeypatch.setattr(m.original,'evaluate',lambda *a,**kw:(_ for _ in ()).throw(AssertionError('no fits')))
    cfg=m.configuration('constructed');a=m.execute(tmp_path,{},cfg)
    assert a['bank_complete'] and a['rejected']>0
    assert m.verify(tmp_path,{},cfg)['no_fits']
    assert m.execute(tmp_path,{},cfg)==a
    (tmp_path/'PRIVATE_SUPPORT.json').write_text('{}')
    with pytest.raises(ValueError,match='replay differs'):m.verify(tmp_path,{},cfg)


def test_changed_config_and_unverified_original_refused(tmp_path):
    from runners.stage14.common import atomic
    with pytest.raises(ValueError,match='Frozen'):
        m.execute(tmp_path,{},dict(m.configuration('constructed'),draws=11))
    with pytest.raises(ValueError,match='No human'):
        m.execute(tmp_path,{'original_completion':'missing'},m.configuration('constructed'))
    atomic(tmp_path/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=False))
    atomic(tmp_path/'PLAN.json',{})
    with pytest.raises(ValueError,match='verified original'):m.authenticate(tmp_path/'COMPLETE.json')
