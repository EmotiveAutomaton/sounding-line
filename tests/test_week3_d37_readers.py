"""D37 actual fitted-reader engineering checks, not scientific calibration.

DESIGN CHECK: LESSONS 3-5. Positive convex-mixture truth has a known optimum;
identical/constant inputs have exact zero gain, wrong forecasts lose. Temporal
poisoning cannot alter earlier forecasts. Invalid sources refuse, not null.
"""
from copy import deepcopy
from pathlib import Path
import numpy as np
import pytest
from runners.drive.cards import week3_d37_readers as m
from runners.drive.cards import menus_p4 as p4
from runners.drive.cards.timing_census import read, filehash
from runners.drive.cards.timing_p6 import write_equal


def fixture(seed=20261026):
    rng = np.random.default_rng(seed); rows=[]; page=[]; process=[]; embedding=[]; sessions=[]
    for s in range(12):
        for w in range(8):
            start = 1000*s + 50*w
            group=[]
            for j in range(8):
                a, b = rng.integers(4, size=2)
                choice = int(rng.choice([a, w % 4, b]))
                row=dict(key=f'w{w}-s{s}-r{j}', writer=f'w{w}', session=f'w{w}-s{s}', prompt=str(s % 3),
                         setting=str(j % 2), open_at=start+j*3, resolved_at=start+j*3+1,
                         session_time=start, session_end=start+30, handling=p4.ACTIONS[choice])
                rows.append(row); group.append(row); page.append(np.eye(4)[a]); process.append(np.eye(4)[b]); embedding.append(rng.normal(size=8))
            sessions.append(dict(writer=f'w{w}', session=f'w{w}-s{s}', timestamp=start, end_at=start+30, rows=group))
    splits, _=p4.chronological_partitions(sessions); parts={}
    for w in sorted(splits):
        split=p4.recipient_split(w,splits)
        assert split['reason'] is None
        parts[w]={k:[s['session'] for s in split[k]] for k in ('train','own_train','calibration','test')}
        parts[w].update(cutoff=split['cutoff'],test_cutoff=split['test_cutoff'])
    arrays=dict(page=np.array(page),process=np.array(process),embedding=np.array(embedding))
    return rows,arrays,parts,np.array([p4.ACTIONS.index(r['handling']) for r in rows])


def test_combination_matches_independent_dense_simplex():
    rng=np.random.default_rng(4); ps=[rng.dirichlet(np.ones(4),size=40) for _ in range(3)]; y=rng.integers(4,size=40)
    rows=[dict(session=str(i//4)) for i in range(40)]; w,cert=m.combine_fit(ps,y,rows)
    assert cert['optimality_gap']<=1e-9 and np.all(w>=0) and np.isclose(w.sum(),1)
    grid=[np.array([i,j,100-i-j])/100 for i in range(101) for j in range(101-i)]
    loss=lambda v: float(np.mean(p4.brier(sum(a*p for a,p in zip(v,ps)),y)))
    assert loss(w)<=min(loss(v) for v in grid)+1e-12


def test_known_exact_vertex_and_reverse():
    y=np.arange(24)%4; truth=np.eye(4)[y]; wrong=np.roll(truth,1,axis=1); uniform=np.full_like(truth,.25)
    rows=[dict(session=str(i//4)) for i in range(24)]
    w,c=m.combine_fit([truth,wrong,uniform],y,rows)
    assert np.allclose(w,[1,0,0],atol=1e-12) and c['calibration_loss']<1e-20
    assert np.mean(p4.brier(uniform,y)-p4.brier(wrong,y))<0


def test_identical_readers_and_ties():
    p=np.full((24,4),.25); y=np.arange(24)%4; rows=[dict(session=str(i//4)) for i in range(24)]
    w,c=m.combine_fit([p,p,p],y,rows)
    assert np.array_equal(sum(a*p for a in w),p)
    assert c['calibration_loss']==.375


def test_prior_boundaries():
    counts=np.array([[0,0,0,0],[2,0,0,0]],float); pop=[.1,.2,.3,.4]
    assert np.array_equal(m.person_probabilities(counts,dict(reliability=0,population=pop,prior_count=None)),np.tile(pop,(2,1)))
    got=m.person_probabilities(counts,dict(reliability=1,population=pop,prior_count=0.))
    assert np.array_equal(got[0],pop) and np.array_equal(got[1],[1,0,0,0])
    got=m.person_probabilities(counts,dict(reliability=.5,population=pop,prior_count=1.))
    assert np.allclose(got[1],np.array([2.1,.2,.3,.4])/3)


def test_history_excludes_future_and_unfinished_other_sessions():
    rows=[dict(key='a',writer='w',session='overlap',session_time=0,session_end=50,open_at=1,resolved_at=2),
          dict(key='b',writer='w',session='current',session_time=10,session_end=40,open_at=11,resolved_at=12),
          dict(key='c',writer='w',session='current',session_time=10,session_end=40,open_at=13,resolved_at=14)]
    c,s=m.prefix_counts(rows,[0,1,2]); assert c[1].sum()==0 and np.array_equal(c[2],[0,1,0,0]) and s.sum()==0
    changed=deepcopy(rows); changed[1]['resolved_at']=15
    assert m.prefix_counts(changed,[0,1,2])[0][2].sum()==0


def test_train_only_and_test_poisoning():
    rows,arrays,parts,y=fixture(); partition=parts['w0']; prepared=m.prepare(rows,arrays,partition)
    pred,fit=m.fit_recipient(rows,y,prepared,m.prefix_counts(rows,y))
    final=prepared['groups']['test'][-1]; changed=y.copy(); changed[final]=(changed[final]+1)%4
    pred2,fit2=m.fit_recipient(rows,changed,prepared,m.prefix_counts(rows,changed))
    assert fit==fit2
    assert [{k:v for k,v in p.items() if k!='truth'} for p in pred]==[{k:v for k,v in p.items() if k!='truth'} for p in pred2]
    index=prepared['groups']['train']
    assert fit['prior']==m.prior_fit([rows[i] for i in index],y[index])
    assert set(fit['training_keys']).isdisjoint(fit['calibration_keys']+fit['test_keys'])


def test_future_preprocessing_poisoning():
    rows,arrays,parts,y=fixture(); first=m.prepare(rows,arrays,parts['w0']); arrays2={k:v.copy() for k,v in arrays.items()}
    target=first['groups']['test']; arrays2['embedding'][target]+=10000
    arrays2['page'][target]+=10000; arrays2['process'][target]+=10000
    second=m.prepare(rows,arrays2,parts['w0'])
    for name in ('page','process'):
        assert np.array_equal(first['matrices'][name][first['groups']['train']],second['matrices'][name][second['groups']['train']])
        assert np.array_equal(first['matrices'][name][first['groups']['calibration']],second['matrices'][name][second['groups']['calibration']])


def test_invalid_chronology_and_prior_refuse():
    rows,arrays,parts,y=fixture(); changed=deepcopy(parts['w0']); changed['cutoff']=0
    with pytest.raises(ValueError,match='Future training'):m.prepare(rows,arrays,changed)
    with pytest.raises(ValueError,match='reliability support'):m.prior_fit(rows[:8],y[:8])
    with pytest.raises(ValueError,match='Frozen'):m.prepare(rows,arrays,parts['w0'],m.CONFIG|dict(seed=0))


def test_shuffle_preserves_writer_marginals_rebuilds_history():
    rows,arrays,parts,y=fixture(); changed=m.permute_targets(rows,y,88)
    for w in parts:
        ids=[i for i,r in enumerate(rows) if r['writer']==w]
        assert np.array_equal(np.bincount(y[ids],minlength=4),np.bincount(changed[ids],minlength=4))
    assert not np.array_equal(m.prefix_counts(rows,y)[0],m.prefix_counts(rows,changed)[0])


def execute(output,inputs,config):
    if config!=m.CONFIG or set(inputs)!={'fixture'} or read(inputs['fixture'])!={'constructed':True}:raise ValueError('Invalid constructed input')
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    test_combination_matches_independent_dense_simplex(); test_known_exact_vertex_and_reverse(); test_identical_readers_and_ties()
    test_prior_boundaries(); test_history_excludes_future_and_unfinished_other_sessions()
    test_train_only_and_test_poisoning(); test_future_preprocessing_poisoning(); test_invalid_chronology_and_prior_refuse()
    test_shuffle_preserves_writer_marginals_rebuilds_history()
    rows,arrays,parts,y=fixture(); receipts=[]
    for writer in sorted(parts):
        predicted,fit=m.fit_recipient(rows,y,m.prepare(rows,arrays,parts[writer]),m.prefix_counts(rows,y))
        receipts.append(dict(predictions=predicted,fit=fit))
    write_equal(output/'FITTED_FIXTURE.json',receipts)
    write_equal(output/'SUMMARY.json',dict(constructed=True,fitted_recipients=8,scientific_admission=False,validation='engineering known answers only'))
    return dict(status='complete',constructed=True)


def verify(output,inputs,config):
    output=Path(output); before={p.name:filehash(p) for p in output.glob('*.json')}
    execute(output,inputs,config)
    if before!={p.name:filehash(p) for p in output.glob('*.json')}:raise ValueError('Changed constructed replay')
    return dict(verified=True,full_fitted_replay=True,scientific_admission=False)
