"""Literal constructed B2 archive and complete preparation/inference replay.

DESIGN CHECK: LESSONS 2-5. A deliberately rigid species choice and variable
mundane choices recover the positive sign; exact arithmetic nulls are separate.
"""
from pathlib import Path
import io,csv,tarfile
from runners.stage14.common import read,freeze,filehash
from . import moral

def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);s=io.StringIO();w=csv.writer(s);w.writerow(moral.COLUMNS)
    for user in range(1000):
        for dim,levels in [('Species',('Hoomans','Pets')),('Gender',('Females','Males')),('Fitness',('Fit','Fat'))]:
            for trial in range(4):
                choice=1 if dim=='Species' else trial%2
                for side in range(2):
                    w.writerow([f'r{user}-{dim}-{trial}',f's{user}-{trial%2}',f'u{user}','0' if side==0 else '1',str(choice if side==0 else 1-choice),levels[side],dim,dim])
    data=s.getvalue().encode();source=output/'fixture.tar.gz'
    with tarfile.open(source,'w:gz') as t:
        info=tarfile.TarInfo('data.csv');info.size=len(data);t.addfile(info,io.BytesIO(data))
    inp=dict(source=dict(path=str(source),sha256=filehash(source)))
    moral.execute(output/'prepare',inp,dict(phase='prepare'))
    counts=output/'prepare/PRIVATE_COUNTS.jsonl.gz';science=moral.analyze(counts)
    assert science['common_fingerprints']==1000 and science['primary']['verdict']=='supports'
    freeze(output/'SCIENCE.json',science);freeze(output/'INPUTS.json',inp)
    return dict(constructed=True,actual_handler_executed=True)

def verify(output,inputs,config):
    output=Path(output);moral.verify(output/'prepare',read(output/'INPUTS.json'),dict(phase='prepare'))
    assert moral.analyze(output/'prepare/PRIVATE_COUNTS.jsonl.gz')==read(output/'SCIENCE.json')
    return dict(verified=True,complete_handler_replay=True)
