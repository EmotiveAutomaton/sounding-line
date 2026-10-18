"""Saved-profile-only fixtures, including actual serialized fresh verification."""
from pathlib import Path
import json
import os
import subprocess
import sys
import time
import numpy as np
import pytest

from runners.drive.cards import timing_pmap_rhythm as card
from runners.drive.cards import timing_pmap_stats as stats
from runners.drive.cards.timing_pmap import assignments,CONFIG as PRIMARY_CONFIG
from runners.drive.cards.timing_census import read,write,filehash
from runners.drive.cards.timing_p6 import gzwrite,gzread

REPO=Path(__file__).resolve().parents[1]


def fixture(root,mode='positive'):
    root=Path(root).resolve();rows=[]
    dictionary=dict(words=['style'+str(i) for i in range(6)],punctuation=['.'],character_bigrams=['ab'])
    for wi in range(6):
        for si in range(4):
            group=wi//2
            rhythm=wi+1 if mode=='positive' else group+1 if mode=='null' else 1
            rows.append(dict(session=f'w{wi}_s{si}',writer=f'w{wi}',prompt=f'p{si}',timestamp=si*100+wi,
                handling=dict(accept=group+1,dismiss=9-group,edit=0,ignore=0),word_counts={'style'+str(wi):10},
                punctuation_counts={'.':1},revision=dict(content=1,housekeeping=1),accepted_characters=10,
                edited_accepted_characters=1,accepted_options=1,declined_options=1,
                accepted_vector_sum=[0.]*384,declined_vector_sum=[0.]*384,
                tc_timing_mode='first_character_delta',within_intervals=[rhythm],onset_intervals=[rhythm*2],
                bigram_intervals={'ab':[rhythm*3]},requests=1,final_words=100))
    prepared=stats.prepare(rows,dictionary);fakes=[]
    for i,a in enumerate(assignments(rows)):
        f=stats.fake_one(rows,dictionary,prepared,a);fakes.append(f)
        gzwrite(root/'output/permutations'/f'{i:03}.json.gz',f)
    primary=stats.summarize(prepared,fakes)
    assert primary['primary']['state']=='positive'
    write(root/'PLAN.json',dict(module='runners.drive.cards.timing_pmap_recovery',config=PRIMARY_CONFIG))
    write(root/'output/PRIMARY.json',primary);gzwrite(root/'output/PROFILES.json.gz',prepared)
    write(root/'output/STYLE_DICTIONARY.json',dictionary)
    for row in rows:gzwrite(root/'output/sessions'/(row['session']+'.json.gz'),row)
    write(root/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,
        outputs={p.relative_to(root).as_posix():filehash(p) for p in root.rglob('*') if p.is_file()}))
    return dict(pmap_completion=str(root/'COMPLETE.json'))


@pytest.mark.parametrize('mode,state',[('positive','positive'),('null','null'),('negative','negative')])
def test_signed_null_reverse_saved_profile_fresh_process(tmp_path,mode,state):
    start=time.perf_counter();inputs=fixture(tmp_path/'source',mode);output=tmp_path/'output'
    result=card.execute(output,inputs,card.CONFIG)
    assert result['primary']['state']==state
    assert result['primary']['effect']==pytest.approx({'positive':.5,'null':0,'negative':-1/3}[mode])
    call=tmp_path/'CALL.json';write(call,dict(output=str(output),inputs=inputs,config=card.CONFIG))
    code="import json,sys;from pathlib import Path;from runners.drive.cards import timing_pmap_rhythm as c;v=json.load(open(sys.argv[1],encoding='utf8'));assert c.verify(Path(v['output']),v['inputs'],v['config'])['verified']"
    child=subprocess.run([sys.executable,'-c',code,str(call)],cwd=REPO,capture_output=True,text=True,timeout=60,
        creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name=='nt' else 0)
    assert child.returncode==0,child.stderr
    write(tmp_path/'SMOKE.json',dict(mode=mode,seconds=time.perf_counter()-start,fresh_exit=child.returncode,
        bytes=sum(p.stat().st_size for p in output.rglob('*') if p.is_file())))


def test_exact_configuration_source_and_false_extension_refuse(tmp_path):
    inputs=fixture(tmp_path/'source')
    with pytest.raises(ValueError,match='exact PMAP extension'):card.execute(tmp_path/'bad',inputs,dict(card.CONFIG,permutations=25))
    path=tmp_path/'source/output/PRIMARY.json';value=read(path);value['primary']['state']='null'
    path.write_text(json.dumps(value),encoding='utf8')
    with pytest.raises(ValueError,match='dependency changed'):card.load(inputs,card.CONFIG)
    cp=Path(inputs['pmap_completion']);c=read(cp);c['outputs']['output/PRIMARY.json']=filehash(path);cp.write_text(json.dumps(c),encoding='utf8')
    with pytest.raises(ValueError,match='not eligible'):card.load(inputs,card.CONFIG)


def test_missing_fake_support_suppresses_p_and_paired_claim():
    names=dict(lean=['a'],rhythm=['b']);values={str(i):[dict(lean=[0.],rhythm=[float(i)]),dict(lean=[0.],rhythm=[float(i)])] for i in range(3)}
    real=card.channels(values,sorted(values),names)
    fake=dict(channels=real)
    bad=dict(channels=dict(real,lean=dict(state='invalid')))
    original=dict(primary=dict(state='positive'),primary_session_permutation_null=dict(bias_flag=True),fake_channels={})
    result=card.analyze(real,[fake]*199+[bad],original)
    assert result['session_permutation_null']['one_sided_p'] is None
    assert result['own_minus_fake']['state']=='invalid'
    assert result['original_control_warnings']['primary_session_permutation_null']['bias_flag']
    assert result['primary']['bootstrap_se']==0.


def test_yield_resume_unchanged_and_saved_forgery_refuses(tmp_path):
    inputs=fixture(tmp_path/'source');output=tmp_path/'output';write(output/'YIELD_REQUEST.json',dict(reason='fixture'))
    result=card.execute(output,inputs,card.CONFIG);assert result['status']=='yielded' and result['completed']==1
    dest=output/'permutations/000.json.gz';before=dest.read_bytes();(output/'YIELD_REQUEST.json').unlink()
    result=card.execute(output,inputs,card.CONFIG);assert result['primary']['state']=='positive' and dest.read_bytes()==before
    assert card.verify(output,inputs,card.CONFIG)['verified']
    saved=read(output/'PRIMARY.json');saved['primary']['effect']=.9
    (output/'PRIMARY.json').write_text(json.dumps(saved),encoding='utf8')
    binding=read(output/'TIMING_BINDINGS.json');binding['outputs']['PRIMARY.json']=filehash(output/'PRIMARY.json')
    (output/'TIMING_BINDINGS.json').write_text(json.dumps(binding),encoding='utf8')
    with pytest.raises(ValueError,match='primary differs'):card.verify(output,inputs,card.CONFIG)
