import copy
import json
from collections import Counter
import numpy as np
import pytest
from runners.drive.cards import week3_fic1_context as m
from tests.test_week3_fic1_reassignment import fixture as previous_fixture


def fixture():
    f=previous_fixture(); units=copy.deepcopy(f['units']); rows=copy.deepcopy(f['rows'])
    for target,source in ((units,f['units']),(rows,f['rows'])):
        for original in source:
            r=copy.deepcopy(original); w='w'+str(int(r['writer'][1:])+3)
            r['session']=w+r['session'][2:];r['writer']=w;target.append(r)
    return dict(units=units,rows=rows,dictionary=f['dictionary'])


def rebuild(f):
    return m.reconstruction.rebuild(f['units'],f['rows'],f['dictionary'],m.CONFIG['word_limits'])


@pytest.mark.parametrize('values', [[1.], [1.,2.], [1.,2.,2.,9.], [1.,1.,1.,9.,9.]])
def test_weighted_median_matches_integer_replication(values):
    assert m.weighted_median([(v,1.) for v in values])==np.median(values)
    assert m.weighted_median([(v,.1) for v in reversed(values)])==np.median(values)


def test_weighted_median_is_not_mean_of_session_medians():
    assert m.weighted_median([(0.,9.),(100.,1.)])==0.
    assert m.weighted_median([]) is None
    for bad in [[(0.,0.)],[(float('inf'),1.)],[(1.,float('nan'))]]:
        with pytest.raises(ValueError):m.weighted_median(bad)


def test_pool_preserves_denominator_and_interval_mass():
    a=dict(words={'inside':1.,'outside':1.},punctuation={'.':1.},timing={'within':[(1.,9.)]})
    b=dict(words={'inside':1.},punctuation={},timing={'within':[(100.,1.)]})
    d=dict(words=['inside'],punctuation=['.'],character_bigrams=[])
    r=m.pool([(a,1),(b,3)],d)
    assert r['style']==[4/6,1/6] and r['rhythm']==[1.,None]
    assert m.pool([(a,1),(None,3)],d) is None


def test_identical_prompt_profiles_match_at_all_supported_lengths():
    f=fixture();r=rebuild(f);ctx=m.context_profiles(f,r,{'w0','w3'})
    observed={(p['writer'],p['genre'],p['half']):p for p in r['profiles']}
    for p in ctx:
        original=observed[p['writer'],p['genre'],p['half']]
        for level,v in p['levels'].items():
            assert v['state']==original['levels'][level]['state']
            if v['state']=='prepared':
                for channel in ('style','rhythm'):
                    assert np.allclose(np.array(v['features'][channel],float),np.array(original['levels'][level]['features'][channel],float),equal_nan=True)
        assert np.allclose(p['final']['features'],original['final']['features'])


def test_recipient_feature_changes_cannot_enter_independent_context():
    f=fixture();r=rebuild(f);donors={'w0','w3'}
    a=m.context_profiles(f,r,donors); changed=copy.deepcopy(f)
    for u in changed['units']:
        if u['writer'] not in donors:
            u['whole']['word_counts']={'unknown':u['typed_words']}
            u['whole']['within_intervals']=[999.]
    for row in changed['rows']:
        if row['writer'] not in donors:row['final_counts']['word_counts']={'unknown':row['final_words']}
    assert m.context_profiles(changed,r,donors)==a


def test_missing_prompt_and_short_donor_remain_unsupported():
    f=fixture();r=rebuild(f)
    for u in f['units']:
        if u['writer']=='w0':u['prompt']='no-shared-prompt'
    ctx=m.context_profiles(f,r,{'w0'})
    assert all(p['levels']['full']['state']=='unsupported' for p in ctx)
    f=fixture(); rows={r['session']:r for r in f['rows']}
    assert m.mean_measure(f['units'][:1],rows,quota=4) is None
    assert m.mean_measure([],rows) is None


def test_invalid_timing_retains_style_and_missing_rhythm():
    f=fixture(); rows={r['session']:r for r in f['rows']}
    for u in f['units']:u['whole']['tc_timing_mode']='invalid'
    v=m.pool([(m.mean_measure(f['units'],rows),3)],f['dictionary'])
    assert v['style']==pytest.approx([.25,.25,.25])
    assert v['rhythm']==[None]*5


def test_rotations_are_disjoint_fixed_and_cover_every_probe_once():
    f=fixture();r=m.prepare(f,m.CONFIG)
    for name,roster in r['rosters'].items():
        assert Counter(w for rotation in r['rotations'] for w in rotation['probes'][name])==Counter(roster)
        for rotation in r['rotations']:
            assert not set(rotation['donors'])&set(rotation['galleries'][name])
            assert set(rotation['probes'][name])<=set(rotation['galleries'][name])
    assert r['rosters']['style.8']==[]
    assert not r['literal_licenses_claim'] and not r['identification_computed']


def test_each_gallery_refits_nuisance_and_probe_cannot_fit():
    f=fixture();r=rebuild(f);rosters=m.support(r['profiles'],['2','4','8','full'])
    a=m.matrices(r['profiles'],rosters); changed=copy.deepcopy(r['profiles'])
    for p in changed:
        if p['half']==0:p['levels']['full']['features']['style'][0]+=2
    b=m.matrices(changed,rosters)
    for genre in m.gallery.GENRES:
        aa=a['style.full'][genre]['length_adjusted'];bb=b['style.full'][genre]['length_adjusted']
        assert aa['fits']==bb['fits'] and aa['B']==bb['B']
    for p in changed:
        if p['half']==1:p['levels']['full']['features']['style'][0]+=3
    c=m.matrices(changed,rosters)
    assert c['style.full']['creative']['length_adjusted']['fits']!=a['style.full']['creative']['length_adjusted']['fits']


def test_missing_fixed_writer_does_not_shrink_gallery():
    f=fixture();r=rebuild(f);rosters=m.support(r['profiles'],['full'])
    pp=[p for p in r['profiles'] if p['writer']!='w0'];z=m.matrices(pp,rosters)
    assert z['style.full']['creative']['state']=='unsupported'
    assert z['style.full']['creative']['writers']==rosters['style.full']


def test_role_permutation_conserves_counts_and_order():
    f=fixture();folds=m.writer_folds(f['units']);labels=m.role_assignment(f['units'],folds,1,20261026)
    assert labels==m.role_assignment(list(reversed(f['units'])),folds,1,20261026)
    assert all(folds[u['writer']]==folds[labels[u['session']]] for u in f['units'])
    original=Counter((u['genre'],u['prompt'],u['writer']) for u in f['units'])
    assert original==Counter((u['genre'],u['prompt'],labels[u['session']]) for u in f['units'])
    m.prepare(f,m.CONFIG,labels)
    bad=dict(labels);u=f['units'][0];bad[u['session']]=next(w for w in folds if folds[w]!=folds[u['writer']])
    with pytest.raises(ValueError,match='crosses'):m.prepare(f,m.CONFIG,bad)


def test_construction_order_invariance_and_json_replay(tmp_path):
    f=fixture();reversed_f=copy.deepcopy(f);reversed_f['units'].reverse();reversed_f['rows'].reverse()
    assert m.prepare(f,m.CONFIG)==m.prepare(reversed_f,m.CONFIG)
    fp=tmp_path/'fixture.json';m.freeze(fp,f);inputs=dict(fixture=str(fp));out=tmp_path/'out'
    m.execute(out,inputs,m.CONFIG);before={p.name:m.filehash(p) for p in out.iterdir()}
    assert m.verify(out,inputs,m.CONFIG)['all_context_reconstructed']
    m.execute(out,inputs,m.CONFIG)
    assert before=={p.name:m.filehash(p) for p in out.iterdir()}
    p=out/'SUMMARY.json';bad=json.loads(p.read_text());bad['scientific_admission']=True;p.write_text(json.dumps(bad))
    with pytest.raises(ValueError,match='replay differs'):m.verify(out,inputs,m.CONFIG)


def test_human_mode_refused(tmp_path):
    with pytest.raises(ValueError,match='constructed context fixture only'):
        m.execute(tmp_path,dict(fixture='unused'),dict(m.CONFIG,mode='full'))
