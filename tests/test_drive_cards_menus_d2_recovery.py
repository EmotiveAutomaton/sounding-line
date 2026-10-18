import math
import json
import os
import subprocess
import sys
import numpy as np
import pytest
from runners.drive.cards import menus_d2 as original, menus_d2_recovery as repaired
from runners.drive.cards.menus_io import write, read, sha256, input_hashes
from tests.test_drive_cards_menus_d2 import fixture


def test_changed_writer_order_is_repaired_without_changing_statistic(tmp_path):
    inputs,config=fixture(tmp_path);out=tmp_path/'output';out.mkdir()
    rng=np.random.default_rng(612);rows=[];manifest={}
    for w in range(12):
        group=[]
        for q in range(5):
            lp=-float(rng.uniform(.1,1.5))
            group.append(dict(writer=f'w{w:02}',quintile=q,gain=lp+math.log(2),
                              log_probability=lp,truth=0,size=2))
        rows.extend(group)
        # Deliberately reverse the serialized recipient traversal.
        name=f'recipients/{11-w:02}.json'
        write(out/name,dict(binding=dict(inputs=input_hashes(inputs),config=config),
             result=dict(arms={a:dict(predictions=group) for a in ['primary','uniform_control']})))
        manifest[name]=sha256(out/name)
    expected=original.summarize(rows,config)
    assert original.summarize(rows[::-1],config)!=expected
    assert repaired.summarize(rows[::-1],config)==expected
    report=dict(**expected,uniform_control=expected,recipient_hashes=manifest,
                input_hashes=input_hashes(inputs),config=config)
    write(out/'SUMMARY.json',report)
    with pytest.raises(ValueError,match='recomputation differs'):original.verify(out,inputs,config)
    before={str(p):sha256(p) for p in out.rglob('*') if p.is_file()}
    assert repaired.execute(out,inputs,config)==report
    assert repaired.verify(out,inputs,config)['refitted'] is False
    assert before=={str(p):sha256(p) for p in out.rglob('*') if p.is_file()}
    request=tmp_path/'REQUEST.json';write(request,dict(output=str(out),inputs=inputs,config=config))
    code='import json,sys; from runners.drive.cards.menus_d2_recovery import verify; r=json.load(open(sys.argv[1])); assert verify(**r)["verified"]'
    env=os.environ.copy();env['PYTHONHASHSEED']='511'
    subprocess.run([sys.executable,'-X','utf8','-B','-c',code,str(request)],env=env,check=True,timeout=45)
    changed=out/next(iter(manifest));changed.write_text(changed.read_text()+' ',encoding='utf8')
    with pytest.raises(ValueError,match='changed saved recipient'):repaired.verify(out,inputs,config)
