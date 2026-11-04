import copy,json,os,subprocess,sys
import pytest
from runners.drive.cards import week4_revision_source_sample as sample
from runners.drive.cards import week4_revision_source_h1 as source


def test_whole_writer_strata_order_and_majority_ties():
    rows=[]
    for i in range(40):
        genres=['a','b'] if i<20 else ['b','b','a']
        for j,g in enumerate(genres):rows.append(dict(session=f's{i}-{j}',writer=f'w{i:02}',genre=g))
    chosen=sample.choose_writers(rows,80)
    assert chosen==sample.choose_writers(list(reversed(rows)),80)
    assert chosen['stratum_population']=={'a':20,'b':20}
    selected=set(chosen['selected_writers'])
    assert len(selected)>=25 and len(chosen['selected_sessions'])<=80
    assert set(chosen['selected_sessions'])=={r['session'] for r in rows if r['writer'] in selected}
    assert abs(chosen['stratum_selected']['a']-chosen['stratum_selected']['b'])<=1
    assert sample.check_manifest(rows,chosen)==set(chosen['selected_sessions'])


def test_floor_refusal_and_no_partial_writer_or_manifest_changes():
    rows=[dict(session=f's{i}-{j}',writer=f'w{i:02}',genre='a') for i in range(30) for j in range(2)]
    with pytest.raises(ValueError,match='floor'):sample.choose_writers(rows,49)
    whole=sample.choose_writers(rows,53)
    assert len(whole['selected_writers'])==26 and len(whole['selected_sessions'])==52
    broken=copy.deepcopy(whole);broken['selected_sessions'].pop()
    with pytest.raises(ValueError,match='manifest'):sample.check_manifest(rows,broken)
    with pytest.raises(ValueError,match='Duplicate'):sample.choose_writers(rows+[rows[0]],53)
    assert sample.selection_fixture()['stratum_selected']=={'a':13,'b':13}


def test_exact_extraction_native_reentry_and_corruption(tmp_path):
    expected=source.extract(source.fixture())
    assert sample.extract(source.fixture())==expected
    out=tmp_path/'source';cfg=sample.configuration('constructed')
    sample.execute(out,{},cfg);sample.execute(out,{},cfg)
    assert sample.verify(out,{},cfg)['complete_source_replay']
    code='from runners.drive.cards.week4_revision_source_sample import verify,configuration;import sys;assert verify(sys.argv[1],{},configuration("constructed"))["complete_source_replay"]'
    subprocess.run([sys.executable,'-X','utf8','-B','-c',code,str(out)],check=True,env=dict(os.environ,PYTHONHASHSEED='313',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1'))
    p=out/'SUMMARY.json';v=json.loads(p.read_text());v['writers']=999;p.write_text(json.dumps(v))
    with pytest.raises(ValueError,match='summary differs'):sample.verify(out,{},cfg)
