"""Run the hermetic projection jobs in fresh processes on literal made files."""
import json
import os
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from runners.drive.sealed.week7_projection_build import package
from tests.test_week7_sealed_sound_words import GATE,word_fixture
from tests.test_week7_sealed_pace_purpose import conversation_fixture


def prepare(card,root):
    if card=='cad2':
        (root/'words.json').write_text(json.dumps(word_fixture()),'utf8')
    elif card=='sld2':
        for wave in (1,2,3):
            df=pd.DataFrame(dict(person=range(48),item1=np.arange(48)%5+wave%2,item2=np.arange(48)%7))
            if wave==2:df=df.assign(family=np.arange(48)//2,role_loss=1)
            df.to_csv(root/f'made_wave_{wave}.csv',index=False)
    elif card=='lgh2':
        i=np.arange(80)
        pd.DataFrame(dict(speaker=i,conversation=i//2,minutes=2,pre_affect=i%7,
            affect=.2*(i%7)+.4*(i%5),laugh_count=2*(i%5))).to_csv(root/'mood.csv',index=False)
    else:
        rng=np.random.default_rng(55)
        i=np.arange(384)
        data={'x':(rng.normal(size=(384,6))+.3*(i%2)[:,None]).tolist(),'meta':[
            dict(speaker=int(j%32),conversation=int(j%16),joined=int(j%3==0),
                 speaking=int(j%4==0),overlap_other=int(j%5==0),target_share_change=.2*(j%2))
            for j in i]}
        (root/'sound.json').write_text(json.dumps(data),'utf8')


@pytest.mark.parametrize('card',['sld2','cad2','lgh1','lgh2'])
def test_projection_package(card,tmp_path):
    mount=tmp_path/'fixture';mount.mkdir()
    out=tmp_path/'out';out.mkdir()
    prepare(card,mount)
    job=tmp_path/'job'
    package(card,mount,job,draws=6)
    cmd=[sys.executable,'-I','-B',str(job/'run.py'),str(mount),str(out)]
    done=subprocess.run(cmd,cwd=tmp_path,capture_output=True)
    assert done.returncode==0,done.stderr.decode(errors='replace')
    assert subprocess.run([sys.executable,'-B',str(GATE),str(out)],capture_output=True).returncode==0
    first=next(mount.iterdir())
    with first.open('ab') as f:f.write(b' ')
    assert subprocess.run(cmd,cwd=tmp_path,capture_output=True).returncode==11


@pytest.mark.parametrize('card',['cad1','sld3'])
def test_original_layout_package(card,tmp_path):
    from runners.drive.sealed import week7_cad1_build,week7_sld3_build
    out=tmp_path/'out';out.mkdir()
    job=tmp_path/'job'
    work=Path('.agent-state/drive-20261115').resolve()
    env=os.environ.copy()
    if card=='cad1':
        mount=tmp_path/'data';mount.mkdir()
        pins={}
        for name,frame in conversation_fixture().items():
            p=mount/(name+'.parquet')
            frame.to_parquet(p,index=False)
            pins[name]=(p.name,p.stat().st_size,sha256(p.read_bytes()).hexdigest())
        week7_cad1_build.package(job,pins)
    else:
        mount=work/'lattice-20261120/spark-family-constructed-v2'
        manifest=json.loads((mount/'MANIFEST.json').read_text('utf8'))
        assert manifest['constructed_only'] and manifest['private_source_reads']==0
        week7_sld3_build.package(job,manifest['sources'])
        env['PYTHONPATH']=str(work/'lattice-20261119/fixture-reader-native')
    cmd=[sys.executable,'-B',str(job/'run.py'),str(mount),str(out)]
    result=subprocess.run(cmd,cwd=tmp_path,env=env,capture_output=True)
    assert result.returncode==0,result.stderr.decode(errors='replace')
    assert subprocess.run([sys.executable,'-B',str(GATE),str(out)],capture_output=True).returncode==0
