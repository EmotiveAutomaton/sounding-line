from runners.stage11_2.common import freeze,read


def test_complete_offline_packet_on_fake_queue(tmp_path,monkeypatch):
    from runners.stage11_2 import world,repair,workflow,executable,revision,packet
    world.prepare(tmp_path/'fixture',dict(train=6,dev=6,test=6))
    freeze(tmp_path/'FAKE_ONLY.json',dict(fake=True))
    workflow.fake_transport(tmp_path);repair.run('admission','dev',tmp_path)
    # Scientific population counts remain 96/64/128; this only allows the
    # existing exact runner's explicit small fixture in an isolated rehearsal.
    monkeypatch.setattr(executable,'prepare',lambda *args,**kwargs:None)
    for split in ['dev','test']:
        executable.run(tmp_path,split);revision.run(split,tmp_path)
    packet.prepare(tmp_path);workflow.prepare(tmp_path);workflow.run(tmp_path,fake=True)
    before={str(p):p.read_bytes() for p in tmp_path.rglob('RAW.json')}
    result=packet.collect(tmp_path)
    assert result['status']=='complete' and result['comparisons']==18 and result['cases']==6
    assert packet.collect(tmp_path)==result
    assert before=={str(p):p.read_bytes() for p in tmp_path.rglob('RAW.json')}
    cases=read(tmp_path/'packet/CASES.json')
    assert len({c['row']['unit'] for c in cases})==6
    assert all(c['request']['messages'] and c['saved_model_output'] for c in cases)
    # Exercise the final standby's literal guarded path and verify that changing
    # namespace cannot create another compute budget.
    from runners.stage11_2 import seed_continuation
    workflow.fake_transport(tmp_path);seed_continuation.prepare(tmp_path)
    freeze(tmp_path/'seed-continuation-v1/SELECTION.json',dict(branch='M4',main_landings_complete=True,fake=True))
    count=len(list((tmp_path/'charges').glob('*.json')))
    seed=seed_continuation.run('M4',tmp_path)
    assert seed['status']=='complete'
    assert len(list((tmp_path/'charges').glob('*.json')))==count+896
    assert not (tmp_path/'seed-continuation-v1/charges').exists()
    assert seed_continuation.run('M4',tmp_path)==seed
    assert len(list((tmp_path/'charges').glob('*.json')))==count+896
