import copy,json,hashlib,os,subprocess,sys
from pathlib import Path
from collections import Counter
import numpy as np
import pytest
from runners.drive.cards import engine_departure_pauses as card
from runners.stage14.common import read


def fixture(slope=.5,noise=0.,writers=12,sessions=4,words=16):
    rng=np.random.default_rng(1901);rows=[]
    for w in range(writers):
        for s in range(sessions):
            for i in range(words):
                nuisance=rng.normal(size=6);departure=float(rng.normal()+s*3+w)
                y=float(slope*departure+nuisance@np.arange(1,7)*.03+20*w+8*s+rng.normal()*noise)
                r=dict(writer=f'w{w:02d}',session=f'w{w:02d}-s{s:02d}',index=i,log_pause=y,**dict(zip(card.COVARIATES,map(float,nuisance))))
                rows.append(dict(original=r,disposition='engine-scored',engine=dict(departure=departure)))
    return dict(rows=rows,support=dict(original_rows=len(rows),original_writers=writers,input_sessions=writers*sessions,dispositions={'engine-scored':len(rows)}))


def oracle(rows):
    session=sorted({r['session'] for r in rows})
    x=np.array([[r['departure']]+[r[k] for k in card.COVARIATES]+[float(r['session']==s) for s in session] for r in rows])
    return np.linalg.lstsq(x,[r['log_pause'] for r in rows],rcond=None)[0][0]


def test_planted_full_cell_and_dummy_matrix_oracle():
    s,d=card.analyze(fixture(),card.CONFIG)
    assert s['primary']['effect']==pytest.approx(.5,abs=1e-12)
    assert s['state']=='positive' and s['primary']['ci_low']>0
    assert s['primary']['effect']==pytest.approx(oracle(d['rows']),abs=1e-12)
    assert len(d['bootstrap_slopes'])==2000 and len(d['permutation_slopes'])==200
    assert not s['within_session_reference']['bias_flag']


def test_reversal_and_exact_null():
    s,_=card.analyze(fixture(slope=-.5),card.CONFIG)
    assert s['state']=='negative' and s['primary']['ci_high']<0
    null=fixture()
    for r in null['rows']:r['original']['log_pause']=7.
    s,_=card.analyze(null,card.CONFIG)
    assert s['state']=='null' and s['primary']['effect']==s['primary']['ci_low']==s['primary']['ci_high']==0
    assert s['within_session_reference']['mean']==s['within_session_reference']['sd']==0


def test_offsets_cannot_create_a_slope_and_order_is_canonical():
    joined=fixture();rr,_=card.prepare(joined);x,y,w,cells=card.arrays(rr);base=card.stats.fit(card.stats.sufficient(x,y,w))[0]
    for i,part in enumerate(cells):
        for ix in part:rr[ix]['log_pause']+=i*16;rr[ix]['departure']+=i*8
    x,y,w,_=card.arrays(rr)
    assert card.stats.fit(card.stats.sufficient(x,y,w))[0]==pytest.approx(base,abs=1e-12)
    rev=copy.deepcopy(joined);rev['rows'].reverse()
    assert card.prepare(joined)==card.prepare(rev)


def test_whole_writer_resamples_match_explicit_duplicate_rows():
    rows,_=card.prepare(fixture(noise=.1));x,y,w,_=card.arrays(rows);groups=card.stats.sufficient(x,y,w)
    choice=[0,0,3,5,7,10,11,3,1,8,6,9];names=sorted(set(w));selected=[r for k in choice for r in rows if r['writer']==names[k]]
    assert card.stats.fit([groups[k] for k in choice])[0]==pytest.approx(oracle(selected),abs=1e-12)


def test_every_permutation_stays_within_session_and_reproduces_saved_slope():
    s,d=card.analyze(fixture(noise=.1),card.CONFIG);x,y,w,cells=card.arrays(d['rows']);rng=np.random.default_rng(card.CONFIG['seed'])
    for i in range(200):
        q=x.copy()
        for ix in cells:
            q[ix,0]=rng.permutation(x[ix,0]);assert sorted(q[ix,0])==sorted(x[ix,0])
        assert hashlib.sha256(q[:,0].astype('<f8').tobytes()).hexdigest()==d['permutation_departure_sha256'][i]
        assert card.stats.fit(card.stats.sufficient(q,y,w))[0]==d['permutation_slopes'][i]


@pytest.mark.parametrize('bad',['duplicate','nan','cross-writer','counts','unsupported-score'])
def test_malformed_inputs_refused(bad):
    f=fixture()
    if bad=='duplicate':f['rows'][1]=copy.deepcopy(f['rows'][0])
    elif bad=='nan':f['rows'][0]['engine']['departure']=float('nan')
    elif bad=='cross-writer':f['rows'][0]['original']['writer']='someone-else'
    elif bad=='counts':f['support']['original_rows']-=1
    else:
        f['rows'][0]['disposition']='not-intact-final-word';f['support']['dispositions']={'engine-scored':len(f['rows'])-1,'not-intact-final-word':1}
    with pytest.raises(ValueError):card.prepare(f)


def test_exclusions_stay_counted_and_singular_target_refuses():
    f=fixture();f['rows'][0].update(disposition='engine-not-content',engine=None)
    f['support']['dispositions']={'engine-not-content':1,'engine-scored':len(f['rows'])-1}
    rr,s=card.prepare(f);assert len(rr)==len(f['rows'])-1 and s['original_rows']==len(f['rows'])
    for r in f['rows'][1:]:r['engine']['departure']=r['original']['population_surprisal']
    with pytest.raises(ValueError,match='identifiable'):card.analyze(f,card.CONFIG)


def test_full_handler_fresh_hash_seed_replay_and_mutation(tmp_path):
    f=tmp_path/'fixture.json';f.write_text(json.dumps(fixture()),encoding='utf8');inputs=dict(fixture=str(f));out=tmp_path/'output'
    s=card.execute(out,inputs,card.CONSTRUCTED);assert s['state']=='positive'
    code='from runners.drive.cards import engine_departure_pauses as c;import sys;c.verify(sys.argv[1],dict(fixture=sys.argv[2]),c.CONSTRUCTED)'
    subprocess.run([sys.executable,'-X','utf8','-B','-c',code,str(out),str(f)],env=dict(os.environ,PYTHONHASHSEED='111'),check=True,timeout=120)
    assert card.execute(out,inputs,card.CONSTRUCTED)==s
    (out/'SUMMARY.json').write_text('{}',encoding='utf8')
    with pytest.raises(ValueError,match='changed'):card.verify(out,inputs,card.CONSTRUCTED)


def test_stops_config_and_live_source_boundary(tmp_path):
    out=tmp_path/'out';out.mkdir();(out/'STOP').write_text('stop')
    with pytest.raises(Exception):card.execute(out,dict(fixture='absent'),card.CONSTRUCTED)
    with pytest.raises(ValueError):card.validate({},card.CONFIG)
    with pytest.raises(ValueError):card.validate({'fixture':'x'},dict(card.CONSTRUCTED,permutations=1))
