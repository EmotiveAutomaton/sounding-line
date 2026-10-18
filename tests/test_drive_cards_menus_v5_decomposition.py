import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest
from runners.drive.cards import menus_v5_decomposition as d
from runners.drive.cards import menus_v5_decomposition_stats as s
from runners.drive.cards import menus_v5 as old
from runners.drive.cards.menus_io import read,write,sha256,assert_equal


def fixture(root,mode='context'):
    """Actual files with explicit synthetic upstream receipts, no child monkeypatch."""
    root=Path(root);root.mkdir(parents=True,exist_ok=True);prior=root/'prior';prior.mkdir();out=prior/'output';out.mkdir()
    auditdir=root/'audit';auditdir.mkdir();canonical=root/'canonical';canonical.mkdir()
    sessions=[];metadata=[];audit=[];contexts=[]
    for w in range(8):
        for half in range(2):
            sid=f'w{w}s{half}';rows=[];events=[]
            for j in range(8):
                context=j%4;label=w%4 if mode=='lean' else (context+w+(2*half if mode=='reverse' else 0))%4
                key=f'{sid}d{j}';ordinal=j*10;time=1_600_000_000_000+half*86400000+w*100000+j*1000
                row=dict(key=key,writer=f'w{w}',session=sid,prompt='p',ordinal=ordinal,open_at=time,
                    handling=old.ACTIONS[label],menu=['originalA','originalB'],inserted='wrong logged option')
                rows.append(row);events.append(dict(ordinal=ordinal,decision=row['handling'],usable=True,
                    verified_insertion=label<2,selected_index=1,matched_option_indices=[0] if label<2 else []))
                metadata.append(dict(key=key,writer=f'w{w}',session=sid,prompt='p',outcome=label));contexts.append(context)
            path=canonical/(sid+'.json');write(path,dict(events=events,synthetic_fixture_only=True))
            for row in rows:audit.append(dict(key=row['key'],writer=row['writer'],session=sid,ordinal=row['ordinal'],
                canonical_handling=row['handling'],prepared_handling=row['handling'],open_at=row['open_at'],
                canonical_path=str(path.resolve()),canonical_sha256=sha256(path),canonical_usable=True,
                index_status='mismatch_fixture',timestamp_provenance='frozen prepared synthetic SESSIONS'))
            sessions.append(dict(session=sid,writer=f'w{w}',prompt='p',timestamp=rows[0]['open_at'],rows=rows))
    write(root/'SESSIONS.json',sessions);write(out/'DECISIONS.json',metadata)
    a,b=np.triu_indices(len(metadata),1);keep=np.asarray(contexts)[a]==np.asarray(contexts)[b]
    np.savez_compressed(out/'PAIRS.npz',left=a[keep],right=b[keep],similarity=np.ones(int(keep.sum())))
    write(out/'SUMMARY.json',dict(card='V5',synthetic_fixture_only=True,note='Constructed upstream contract, not a corpus result'))
    write(prior/'PLAN.json',dict(module='runners.drive.cards.menus_v5',inputs={'sessions':str((root/'SESSIONS.json').resolve())},
        pins={str((root/'SESSIONS.json').resolve()):sha256(root/'SESSIONS.json')}))
    write(prior/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,synthetic_fixture_only=True,
        note='Constructed dependency receipt for serialized testing, not a historical run',
        outputs={name:sha256(prior/name) for name in ('PLAN.json','output/DECISIONS.json','output/PAIRS.npz','output/SUMMARY.json')}))
    write(auditdir/'ROWS.json',audit);write(auditdir/'COMPLETE.json',dict(status='COMPLETE',no_fits=True,
        synthetic_fixture_only=True,outputs={'ROWS.json':sha256(auditdir/'ROWS.json')}))
    return dict(sessions=str((root/'SESSIONS.json').resolve()),v5_plan=str((prior/'PLAN.json').resolve()),
        v5_complete=str((prior/'COMPLETE.json').resolve()),v5_decisions=str((out/'DECISIONS.json').resolve()),
        v5_pairs=str((out/'PAIRS.npz').resolve()),v5_summary=str((out/'SUMMARY.json').resolve()),
        selection_audit=str((auditdir/'ROWS.json').resolve()),selection_complete=str((auditdir/'COMPLETE.json').resolve()))


def test_leave_both_out_matches_independent_explicit_counts_and_small_support():
    truth=np.array([0,0,1,2,0,1,1,2]);writer=np.repeat([0,1],4)
    a=np.array([0,0,1,4]);b=np.array([1,4,6,7]);value,valid,_=s.lean_expectation(a,b,truth,writer)
    for k,(i,j) in enumerate(zip(a,b)):
        rates=[]
        for who in (writer[i],writer[j]):
            ids=[n for n in range(len(truth)) if writer[n]==who and n not in (i,j)]
            rates.append(np.bincount(truth[ids],minlength=4)/len(ids))
        assert value[k]==pytest.approx(rates[0]@rates[1],abs=1e-15)
    assert valid.all()
    value,valid,_=s.lean_expectation(np.array([0]),np.array([1]),np.array([0,1]),np.array([0,0]))
    assert not valid[0] and np.isnan(value[0])


def test_unequal_marginals_and_balanced_distinct_writer_identity():
    sums=np.zeros((3,11));sums[:,0]=10;sums[:,1]=7;sums[:,2]=5
    sums[:,3:7]=[8,2,0,0];sums[:,7:11]=[4,6,0,0]
    q=s.quantities(sums)
    assert q['chance_endpoint'][0]==pytest.approx(.44)
    assert q['chance_pooled'][0]==pytest.approx(.52)
    assert q['cohen_kappa'][0]==pytest.approx((.7-.44)/.56)
    assert q['pooled_mix_adjustment'][0]==pytest.approx((.7-.52)/.48)
    identity=s.balanced_identity(np.array([[10,0,0,0],[5,5,0,0]]))
    assert identity['summed_population_variance']==.125
    assert identity['finite_writer_factor']==2
    assert identity['identity_gap']==identity['distinct_identity_gap']==0


def test_unequal_graph_degree_and_paired_real_node_weights():
    truth=np.array([0,0,1,1,0,1,0,1,2,2,0,0]);real=np.repeat(np.arange(3),4)
    sessions=np.arange(12);fake=np.array([0,1,2,0,1,2,0,1,2,0,1,2]);a=np.array([0,0,0,0,1,4,8]);b=np.array([1,2,4,8,9,5,9])
    graph,_,_=s.aggregate(a,b,truth,fake,sessions,real,3);copies=np.array([2,1,0])
    weights=copies[:,None]*copies[None,:];np.fill_diagonal(weights,copies)
    got=s.weighted(graph,weights.reshape(1,-1))[0]
    lean,_,_=s.lean_expectation(a,b,truth,fake);expected=np.zeros((3,11))
    for k,(i,j) in enumerate(zip(a,b)):
        g=0 if fake[i]==fake[j] else 1
        weight=copies[real[i]] if real[i]==real[j] else copies[real[i]]*copies[real[j]]
        expected[g]+=weight*np.r_[1,truth[i]==truth[j],lean[k],np.eye(4)[truth[i]],np.eye(4)[truth[j]]]
    np.testing.assert_allclose(got,expected,rtol=0,atol=1e-15)
    # Unequal exposure remains in graph weights and is not replaced by the balanced identity.
    assert graph[0,0].sum()!=graph[1,0].sum()


def test_serialized_planted_resume_reentry_fresh_and_canonical_refusal(tmp_path):
    inputs=fixture(tmp_path/'source');out=tmp_path/'output';out.mkdir();write(out/'YIELD_REQUEST.json',{})
    assert d.execute(out,inputs,d.CONFIG)['status']=='yielded';(out/'YIELD_REQUEST.json').unlink()
    report=d.execute(out,inputs,d.CONFIG)
    assert report['state']=='positive' and report['primary']['effect']>.2
    assert report['outcome_permutations']['draws']==report['fake_writers']['draws']==200
    assert report['label_audit']['all_handling_labels_equal'] and not report['label_audit']['selected_identity_used']
    hashes={str(p):sha256(p) for p in out.rglob('*') if p.is_file()}
    assert d.execute(out,inputs,d.CONFIG)==report
    assert hashes=={str(p):sha256(p) for p in out.rglob('*') if p.is_file()}
    request=tmp_path/'REQUEST.json';write(request,dict(output=str(out),inputs=inputs,config=d.CONFIG))
    code='import json,sys;from runners.drive.cards.menus_v5_decomposition import verify;assert verify(**json.load(open(sys.argv[1]))) ["canonical_handling_replayed"]'
    subprocess.run([sys.executable,'-B','-c',code,str(request)],check=True,timeout=60,env=os.environ|dict(PYTHONHASHSEED='818'))
    canonical=Path(read(inputs['selection_audit'])[0]['canonical_path']);canonical.write_bytes(canonical.read_bytes()+b' ')
    with pytest.raises(ValueError,match='canonical'):d.verify(out,inputs,d.CONFIG)


@pytest.mark.parametrize('mode,expected',[('lean','null'),('reverse','negative')])
def test_full_known_lean_and_reverse_controls(tmp_path,mode,expected):
    inputs=fixture(tmp_path/'source',mode);report=d.execute(tmp_path/'output',inputs,d.CONFIG)
    assert report['state']==expected
    if mode=='lean':
        assert report['primary']['effect']==pytest.approx(0,abs=1e-15)
        assert report['primary']['ci95']==pytest.approx([0,0],abs=1e-15)
        assert report['curves'][2]['contrasts']['H']['effect']>.2
        assert report['outcome_permutations']['biased_pipeline'] is False
    assert d.verify(tmp_path/'output',inputs,d.CONFIG)['verified']


def test_permutation_bias_flag_can_fail_and_zero_spread_is_defined():
    value=s.control_distribution(np.linspace(.1,.2,200),.4)
    assert value['biased_pipeline'] and value['p_one_sided']==1/201
    value=s.control_distribution(np.zeros(200),0.)
    assert not value['biased_pipeline'] and value['p_one_sided']==1
