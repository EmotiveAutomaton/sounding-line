"""Actual handler rehearsal on explicitly constructed inputs.

DESIGN CHECK: LESSONS 3-5. Synthetic line, independent raters and signed language
examples test supported, null and opposite directions before real outcomes.
"""
from pathlib import Path
import zipfile
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from runners.stage14.common import freeze,read,filehash
from . import emotions as e


def fixture(output,card):
    output.mkdir(parents=True,exist_ok=True)
    if card=='TD4':
        eil=['word\temotion\tintensity'];vad=['term\tvalence\tarousal\tdominance']
        for emotion,words in e.SCALES.values():
            for i,word in enumerate(words.split()):
                value=(i+1)/10
                if emotion:eil.append(f'{word}\t{emotion}\t{value}')
                vad.append(f'{word}\t0\t{value}\t{value}')
        inputs={}
        for key,member,rows in [('eil','NRC-Emotion-Intensity-Lexicon/NRC-Emotion-Intensity-Lexicon-v1.txt',eil),
                               ('vad','NRC-VAD-Lexicon-v2.1/NRC-VAD-Lexicon-v2.1.txt',vad)]:
            path=output/(key+'.zip')
            if not path.exists():
                with zipfile.ZipFile(path,'x') as z:
                    info=zipfile.ZipInfo(member,date_time=(2026,11,6,0,0,0));z.writestr(info,'\n'.join(rows)+'\n')
            inputs[key]=dict(path=str(path),sha256=filehash(path))
        return inputs
    path=output/'constructed.parquet'
    if not path.exists():
        rng=np.random.default_rng(20261106);rows=[]
        count=2000 if card=='TD5' else 800
        for index in range(count):
            for rater in range(3):
                row=dict(zip(e.LABELS,map(int,rng.random(28)<.3))) if card=='TD5' else {k:0 for k in e.LABELS}
                if card=='TD6':row['disgust' if index%2 else 'anger']=1
                row.update(id=f'constructed-{index:05d}',rater_id=rater,
                    subreddit='constructed',example_very_unclear=False,
                    text=('he thinks and she sings now' if index%2 else 'he thinks and she cares now'),
                    author='CONSTRUCTED_DO_NOT_DECODE')
                rows.append(row)
        pq.write_table(pa.Table.from_pylist(rows),path)
    return {'go_emotions':dict(path=str(path),sha256=filehash(path))}


def execute(output,inputs,config):
    output=Path(output);actual=fixture(output/'fixture',config['card'])
    settings=dict(card=config['card'],draws=64)
    result=e.execute(output/'consumer',actual,settings)
    if config['card']=='TD4':assert all(r['verdict']=='supports' for r in result['scales'].values())
    if config['card']=='TD5':assert result['primary']['packet_verdict']=='inconclusive'
    if config['card']=='TD6':assert result['primary']['relative_difference']==-.5
    freeze(output/'FIXTURE_INPUTS.json',actual)
    return dict(constructed=True,actual_handler_executed=True,card=config['card'])


def verify(output,inputs,config):
    output=Path(output);actual=read(output/'FIXTURE_INPUTS.json')
    e.verify(output/'consumer',actual,dict(card=config['card'],draws=64))
    return dict(verified=True,constructed=True,complete_handler_replay=True)
