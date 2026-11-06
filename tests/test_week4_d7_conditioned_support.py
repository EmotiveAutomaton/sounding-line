import itertools
import copy
import pytest
from runners.drive.cards import week4_d7_conditioned_support as m


def small():
    # Three early rich sessions, two late sparse ones per writer. Reallocation
    # can preserve or violate the original train/cal/test observed-menu floors.
    rows=[]
    for w in range(2):
        for s in range(5):
            for j in range(10 if s==0 else 2):
                rows.append(dict(key=f'{w}:{s}:{j}',writer=str(w),session=f'{w}:{s}',
                    prompt='p',session_start=s*1000+w*200,session_end=s*1000+w*200+100,
                    open_at=s*1000+w*200+j,dwell_observed=True))
    return rows


def test_finite_conditional_law_and_all_rejections(monkeypatch):
    rows=small();sessions=sorted({r['session'] for r in rows})
    assignments=[dict(zip(sessions,['0' if s in zeros else '1' for s in sessions]))
                 for zeros in itertools.combinations(sessions,5)]
    admissible=[a for a in assignments if sorted(m.c.support(m.c.reassigned(rows,a))[0])==['0','1']]
    assert 0<len(admissible)<len(assignments)
    monkeypatch.setattr(m.c,'session_assignment',lambda rows,index,seed:assignments[index])
    # Exhaust the entire finite proposal population, not a post-outcome sample.
    b=m.bank(rows,len(assignments)+1,len(assignments))
    assert [a['assignment'] for a in b['accepted']]==admissible
    assert len(b['proposals'])==len(assignments) and not b['complete']
    assert len({m.digest(a) for a in admissible})==len(admissible)
    # Every admissible assignment occurs once in this uniform finite universe.
    assert sum(not p['accepted'] for p in b['proposals'])==len(assignments)-len(admissible)


def test_outcomes_and_predictors_cannot_affect_bank():
    rows,_=m.c.world('signed',20261026,6)
    changed=copy.deepcopy(rows)
    for i,r in enumerate(changed):
        r['dwell_seconds']=100000+i;r['accepted']=not r['accepted'];r['mean_novelty']=-100
    assert m.bank(rows,12)==m.bank(changed,12)
    assert set(m.metadata(rows)[0])==set(m.FIELDS)


def test_exhausted_bound_and_unchanged_support_roster():
    rows,_=m.c.world('null',20261026,6)
    b=m.bank(rows,12,5)
    assert not b['complete'] and len(b['proposals'])==len(b['accepted'])==5
    assert [r['proposal'] for r in b['accepted']]==list(range(5))


def test_exact_original_bank_when_condition_always_holds():
    rows,_=m.c.world('null',20261026,6);b=m.bank(rows,12)
    assert b['complete'] and len(b['proposals'])==12
    for index,a in enumerate(b['accepted']):assert a['assignment']==m.c.session_assignment(rows,index,20261026)


def test_native_handler_no_fit_replay_and_tamper(tmp_path,monkeypatch):
    monkeypatch.setattr(m.c,'fits',lambda *a,**kw:(_ for _ in ()).throw(AssertionError('no fits')))
    cfg=m.configuration('constructed');r=m.execute(tmp_path,{},cfg)
    assert r['bank_complete'] and m.verify(tmp_path,{},cfg)['no_fits']
    (tmp_path/'PRIVATE_CONDITIONAL_SUPPORT.json').write_text('{}')
    with pytest.raises(ValueError,match='replay differs'):m.verify(tmp_path,{},cfg)


def test_changed_configuration_and_human_inputs_refused(tmp_path):
    with pytest.raises(ValueError,match='Frozen'):
        m.execute(tmp_path,{},dict(m.configuration('constructed'),maximum_proposals=2001))
    with pytest.raises(ValueError,match='No human'):
        m.execute(tmp_path,{'source':'no'},m.configuration('constructed'))
