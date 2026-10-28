import copy
import json
from collections import Counter
import numpy as np
import pytest
from runners.drive.cards import week3_fic1_reassignment as m
from tests.test_week3_fic1_prefixes import fixture as prefix_fixture, built


def fixture():
    f = prefix_fixture()
    units = [built(c, c['metadata']) for c in f['units']]
    rows = [dict(**{k: u[k] for k in ('session','writer','genre','half','pair','prompt','timestamp','typed_words')},
                 final_counts=dict(word_counts=u['whole']['word_counts'], punctuation_counts=u['whole']['punctuation_counts']),
                 final_words=u['typed_words'], final_characters=20, final_accepted_characters=2) for u in units]
    pp=[]
    for g in f['profiles']:
        part=[u for u in units if u['session'] in g['sessions']]
        pp.append(dict(writer=g['writer'], genre=g['genre'], half=g['half'],
                       levels={str(n) if n else 'full':m.prefix.profile(part,n,f['dictionary']) for n in (2,4,8,None)}))
    return dict(units=units,rows=rows,dictionary=f['dictionary'],profiles=f['profiles'],prefixes=pp)


def rebuild(f, labels=None):
    return m.rebuild(f['units'],f['rows'],f['dictionary'],[2,4,8],labels)


def test_identity_exact_prefix_parity_and_unsupported_lengths():
    f=fixture();r=rebuild(f);m.verify_observed(r,f['profiles'],f['prefixes'])
    assert r['assigned_sessions']==24 and r['unsupported_sessions']==0
    assert len(r['profiles'])==12
    assert all(p['levels']['8']['state']=='unsupported' for p in r['profiles'])
    assert all(p['final']['words']==6 and p['final']['accepted_share']==.1 for p in r['profiles'])


def test_permutation_deterministic_order_invariant_and_conserves_counts():
    f=fixture();labels=m.labels_within_prompt(f['units'],np.random.default_rng(20261026))
    assert labels!= {u['session']:u['writer'] for u in f['units']}
    r=rebuild(f,labels);rev=copy.deepcopy(f);rev['units'].reverse();rev['rows'].reverse()
    assert m.labels_within_prompt(rev['units'],np.random.default_rng(20261026))==labels
    assert rebuild(rev,labels)==r
    assert Counter(s for p in r['profiles'] for s in p['sessions'])==Counter(u['session'] for u in f['units'])
    for p in r['profiles']:
        assert all(labels[s]==p['writer'] for s in p['sessions'])


def test_prompt_halves_rebuilt_from_reassigned_dates():
    f=fixture();lookup={r['session']:r for r in f['rows']}
    for u in f['units']:
        if u['writer']=='w1':u['timestamp']=10-u['timestamp']
        lookup[u['session']]['timestamp']=u['timestamp']
    labels={u['session']:'w'+str((int(u['writer'][1:])+1)%3) for u in f['units']}
    r=rebuild(f,labels)
    for genre in m.gallery.base.GENRES:
        a=next(p for p in r['profiles'] if p['writer']=='w2' and p['genre']==genre and p['half']==0)
        assert {next(u for u in f['units'] if u['session']==s)['prompt'] for s in a['sessions']}=={genre+'-1'}
        assert a['sessions'] == sorted(a['sessions'],key=lambda s:(lookup[s]['timestamp'],s))


def test_missing_disjoint_prompt_support_stays_explicit():
    f=fixture()
    for values in (f['units'],f['rows']):
        for r in values:
            if r['writer']=='w0':r['prompt']=r['genre']+'-single'
    r=rebuild(f)
    assert r['unsupported_sessions']==8 and r['assigned_sessions']==16
    missing=[p for p in r['profiles'] if p['state']=='unsupported']
    assert len(missing)==2 and all(p['writer']=='w0' for p in missing)
    with pytest.raises(ValueError,match='lost profile support'):m.verify_observed(r,f['profiles'],f['prefixes'])


@pytest.mark.parametrize('bad',['assignment_missing','assignment_counts','duplicate','feature_identity','observed_change'])
def test_altered_sources_and_labels_refused(bad):
    f=fixture();labels={u['session']:u['writer'] for u in f['units']}
    if bad=='assignment_missing':labels.pop(next(iter(labels)))
    elif bad=='assignment_counts':labels[next(iter(labels))]='wrong'
    elif bad=='duplicate':f['units'].append(f['units'][0])
    elif bad=='feature_identity':f['rows'][0]['timestamp']+=1
    if bad=='observed_change':
        r=rebuild(f);f['prefixes'][0]['levels']['full']['selected_words']+=1
        with pytest.raises(ValueError):m.verify_observed(r,f['profiles'],f['prefixes'])
    else:
        with pytest.raises(ValueError):rebuild(f,labels)


def test_handler_replay_json_reentry_and_mutation_refusal(tmp_path):
    fp=tmp_path/'fixture.json';m.freeze(fp,fixture());inputs=dict(fixture=str(fp));out=tmp_path/'out'
    m.execute(out,inputs,m.CONSTRUCTED)
    assert m.verify(out,inputs,m.CONSTRUCTED)['all_reassignments_recomputed']
    before={p.name:m.filehash(p) for p in out.glob('*.json') if p.name!='PROGRESS.json'}
    m.execute(out,inputs,m.CONSTRUCTED)
    assert before=={p.name:m.filehash(p) for p in out.glob('*.json') if p.name!='PROGRESS.json'}
    p=out/'REASSIGNMENT_0000.json';v=json.loads(p.read_text());v['assigned_sessions']-=1;p.write_text(json.dumps(v))
    with pytest.raises(ValueError,match='replay differs'):m.verify(out,inputs,m.CONSTRUCTED)
