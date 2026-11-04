import copy,json,os,subprocess,sys
import pytest
from runners.stage9 import coauthor as old
from runners.drive.cards import week4_revision_utf16_h1 as fast
from runners.drive.cards import week4_revision_source as source
from runners.drive.cards import week4_revision_source_h1 as successor


def test_exact_delta_and_decoder_parity():
    for text in ('','ASCII text. Next.','A\U0001f600 e\u0301 \u4e2d.\nNext'):
        doc=old.units(text);owners=[7]*len(doc)
        assert old.text_of(doc)==fast.text_of(doc)==text
        cases=[[],[{'insert':'x\U0001f600'}],[{'delete':len(doc)}],[{'retain':len(doc)},{'insert':'\n'}]]
        if doc:cases.append([{'retain':1},{'insert':'q'},{'delete':len(doc)-1}])
        for ops in cases:
            value={'ops':ops}
            assert old.apply_delta(doc,owners,value,insertion_owner=9,watched_owner=7)==fast.apply_delta(doc,owners,value,insertion_owner=9,watched_owner=7)
    for value in ({'ops':[{'delete':999}]},{'ops':[{'retain':-1}]},{'ops':[{'retain':True}]},{'ops':[{'retain':1},{'delete':1}]}):
        types=[]
        for f in (old.apply_delta,fast.apply_delta):
            with pytest.raises((ValueError,UnicodeError)) as exc:f(old.units('A\U0001f600'),[7]*3,value)
            types.append(type(exc.value))
        assert types[0] is types[1]


def test_complete_source_branch_parity():
    for source_kind in ('user','api'):
        for cut in (2,3,4,5,6):
            e=source.fixture()[:cut];e[1]['eventSource']=source_kind
            assert source.extract(e)==successor.extract(e)
    # Stop at the edited prefix: later fixture offsets describe the old text.
    e=source.fixture()[:3];e[2]['textDelta']={'ops':[{'retain':5},{'delete':35}]}
    assert source.extract(e)==successor.extract(e)
    assert source.extract(e)['census']['candidate_nonlocal_sentence_targets']==2


def test_outputs_and_fresh_process_parity(tmp_path):
    a=tmp_path/'old';b=tmp_path/'new';cfg=source.configuration('constructed')
    source.execute(a,{},cfg);successor.execute(b,{},cfg)
    for name in ('SUMMARY.json','INDEX.json','BINDING.json'):
        assert (a/name).read_bytes()==(b/name).read_bytes()
    for p in (a/'sessions').glob('*'):assert p.read_bytes()==(b/'sessions'/p.name).read_bytes()
    successor.execute(b,{},cfg)
    code='from runners.drive.cards.week4_revision_source_h1 import verify,configuration;import sys;assert verify(sys.argv[1],{},configuration("constructed"))["complete_source_replay"]'
    subprocess.run([sys.executable,'-X','utf8','-B','-c',code,str(b)],check=True,env=dict(os.environ,PYTHONHASHSEED='271',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1'))
    p=b/'SUMMARY.json';v=json.loads(p.read_text());v['sessions']=100;p.write_text(json.dumps(v))
    with pytest.raises(ValueError,match='summary differs'):successor.verify(b,{},cfg)
