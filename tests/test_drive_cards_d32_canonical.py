import copy
from pathlib import Path
import numpy as np
import pytest
from runners.drive.cards import events_d32_canonical as card
from runners.drive.cards.menus_io import read,write,sha256
from tests.test_drive_cards_d38_canonical import native_fixture as base_fixture
from tests.test_drive_cards_events_d32 import fixture_rows


def native_fixture(root):
    root=Path(root).resolve();base=base_fixture(root)
    sessions=read(base['sessions']);auditroot=Path(base['selection_complete']).parent
    proofs=read(auditroot/'ROWS.json');bykey={p['key']:p for p in proofs}
    pins=read(auditroot/'INPUT_PINS.json');sourcepins={};rows=[];rng=np.random.default_rng(901)
    def overwrite(p,value):Path(p).write_text(__import__('json').dumps(value),encoding='utf8')
    for session in sessions:
        proof=bykey[session['rows'][0]['key']];path=Path(proof['canonical_path']);canonical=read(path)
        byordinal={e['ordinal']:e for e in canonical['events']}
        for menu in session['rows']:
            outside=rng.integers(0,2,3);weights=np.exp(-.7*outside);chosen=int(rng.choice(3,p=weights/weights.sum()));old=(chosen+1)%3
            menu['inserted']=menu['menu'][old];event=byordinal[menu['ordinal']]
            event.update(matched_option_indices=[chosen+7],selected_index=old)
            bykey[menu['key']].update(canonical_positions=[chosen],prepared_positions=[old],logged_selected_index=old)
            dissimilarity=float(rng.random())
            for position,text in enumerate(menu['menu']):
                rows.append(dict(writer=session['writer'],session=session['session'],session_index=int(session['timestamp']>0),
                    key=menu['key'],position=position,length=len(text),menu_dissimilarity=dissimilarity,
                    accepted=int(position==old),outside=int(outside[position]),cluster=int(rng.integers(4)),other_typed_writers=10))
        overwrite(path,canonical);sourcepins[path.relative_to(root).as_posix()]=sha256(path);pins[str(path)]=sha256(path)
        for menu in session['rows']:bykey[menu['key']].update(canonical_sha256=sha256(path))
    overwrite(base['sessions'],sessions)
    sourcepath=Path(base['sessions']).with_name('SOURCE_PINS.json');overwrite(sourcepath,sourcepins)
    foundation=root/'results/phase_2_4_stage_15/raw/drive-foundation-v1'
    plan=read(foundation/'PLAN.json')
    for path in (Path(base['sessions']),sourcepath):plan['pins'][path.relative_to(root).as_posix()]=sha256(path)
    overwrite(foundation/'PLAN.json',plan)
    completion=read(foundation/'COMPLETE.json');completion['plan_sha256']=sha256(foundation/'PLAN.json');overwrite(foundation/'COMPLETE.json',completion)
    for path in (Path(base['sessions']),sourcepath,foundation/'PLAN.json',foundation/'COMPLETE.json'):pins[str(path)]=sha256(path)
    overwrite(auditroot/'ROWS.json',proofs);overwrite(auditroot/'INPUT_PINS.json',pins)
    completion=read(auditroot/'COMPLETE.json');completion['outputs']={n:sha256(auditroot/n) for n in ('ROWS.json','INPUT_PINS.json')};overwrite(auditroot/'COMPLETE.json',completion)
    prior=root/'original-d32';out=prior/'output'
    write(out/'INPUTS.json',dict(paths={'sessions':base['sessions']}))
    write(out/'SOURCE_PINS.json',pins)
    for name,value in [('ROWS_k50.json',rows),('CENTERS_k50.json',[[0.0]]*50),('SUPPORT_k50.json',dict(eligible_rows=len(rows),synthetic_fixture_only=True))]:
        card.original.checkpoint_write(out/name,value)
    write(prior/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,synthetic_fixture_only=True,
        outputs={p.relative_to(prior).as_posix():sha256(p) for p in out.rglob('*') if p.is_file()}))
    return {k:base[k] for k in ('sessions','selection_reader','selection_complete')}|dict(original_complete=str(prior/'COMPLETE.json'))


def test_actual_canonical_source_and_mutation(tmp_path):
    inputs=native_fixture(tmp_path/'fixture');rows,proof,support=card.load(inputs,card.PILOT_CONFIG)
    assert proof['changed_offer_labels']>0 and len(rows)==support['eligible_rows']
    assert len({r['writer'] for r in rows})==3
    Path(inputs['sessions']).write_text('[]')
    with pytest.raises(ValueError,match='source changed'):card.load(inputs,card.PILOT_CONFIG)


def test_frozen_draws_match_original_and_invalid_is_retained():
    arrays=card.original.prepare_arrays(fixture_rows(nwriters=4,n=70))
    point,beta,_=card.original.fitted_contrast(arrays)
    selections=np.random.default_rng(20261017).integers(4,size=(2000,4))
    for index in (0,1,19,1999):
        value=card.fit_draw(arrays,index,selections,beta)
        expected=card.original.fitted_contrast(arrays,np.bincount(selections[index],minlength=4),beta)[0]
        assert value['effect']==pytest.approx(expected)
    broken=copy.deepcopy(arrays);broken['y']=np.zeros_like(broken['y'])
    assert card.fit_draw(broken,0,selections,beta)['effect'] is None


def test_pilot_has_no_partial_verdict_and_replays(tmp_path):
    inputs=native_fixture(tmp_path/'fixture');output=tmp_path/'output'
    result=card.execute(output,inputs,card.PILOT_CONFIG)
    assert result['timing_only'] and 'primary' not in result
    assert result['bootstrap_fits']==20 and result['control_fits']==20
    assert card.verify(output,inputs,card.PILOT_CONFIG)['verified']
    with pytest.raises(ValueError,match='immutable'):card.execute(output,inputs,card.PILOT_CONFIG)
