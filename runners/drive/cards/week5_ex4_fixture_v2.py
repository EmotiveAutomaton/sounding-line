"""Constructed EX4 successor checks; native source/receipt authority is stubbed.

All text operations, word timing, aggregate production and independent replay
are real. The tiny resume records below exercise the handler contract and do
not claim an actual native runtime/lease qualification.
"""
from pathlib import Path
import shutil
from . import week5_ex4_v2 as study
from .week5_ex4_fixture import Session


def continuation(old,new,operation,*,request=False):
    old=Path(old);new=Path(new)
    if request:study.io.write_json(old/'output/YIELD_REQUEST.json',dict(reason='constructed owner request'))
    copied={p.relative_to(old/'output').as_posix():study.io.sha(p) for p in (old/'output').rglob('*') if p.is_file()}
    study.io.write_json(old/'PAUSED.json',dict(status='PAUSED',paused_operation=operation,
        checkpoint_validation_required=True,checkpoint_outputs=copied,constructed_receipt_stub=True))
    shutil.copytree(old/'output',new/'output')
    study.io.write_json(new/'RESUMED_FROM.json',dict(predecessor=str(old),paused_sha256=study.io.sha(old/'PAUSED.json'),
        module=study.MODULE,copied=copied,constructed_receipt_stub=True))
    return copied


def constructed_chain(root,monkeypatch):
    root=Path(root);source=root/'source';source.mkdir(parents=True)
    a=Session();a.type('alpha ',2.);a.type('beta ',3.);a.type('gamma',1.)
    b=Session();b.type('bad');broken=b.record('constructed-failure');broken['final_text']='not the replay\n'
    records=[a.record(),broken]
    index=[dict(ordinal=i,session=record['session']) for i,record in enumerate(records)]
    monkeypatch.setattr(study,'authenticate',lambda inputs:(source/'COMPLETE.json',source,index,
        dict(constructed_records=study.io.sha(__file__),module_sha256=study.io.sha(study.__file__))))
    monkeypatch.setattr(study.source,'source_record',lambda complete,folder,entry:records[entry['ordinal']])
    config=dict(phase='EX4',max_new_draws=1,max_wall_seconds=30)
    first=root/'attempt1';second=root/'attempt2';third=root/'attempt3'
    terminals=[study.execute(first/'output',{},config)]
    old1=continuation(first,second,'execute',request=True)
    terminals.append(study.execute(second/'output',{},config))
    terminals.append(study.verify(second/'output',{},config))
    old2=continuation(second,third,'verify')
    result=study.execute(third/'output',{},config);terminals.append(result)
    proof=study.verify(third/'output',{},config);terminals.append(proof)
    for old,expected in ((first,old1),(second,old2)):
        if any(study.io.sha(old/'output'/name)!=value for name,value in expected.items()):
            raise AssertionError('Earlier constructed output changed')
    return third/'output',result,proof,terminals
