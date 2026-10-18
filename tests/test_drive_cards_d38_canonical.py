import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from runners.drive.cards import events_d38_canonical as card
from runners.stage14.common import digest
from runners.drive.cards.menus_io import read, write, sha256

spec = importlib.util.spec_from_file_location('d38_fixture', Path(__file__).with_name('test_drive_cards_events_d38.py'))
fixture = importlib.util.module_from_spec(spec); spec.loader.exec_module(fixture)


class Audit:
    def __init__(self, mapping): self.mapping = mapping
    def join(self, row):
        old = [i for i, text in enumerate(row['menu']) if text == row['inserted']]
        new = [self.mapping.get(row['key'], old[0])] if row['handling'] in ('accept','edit') else []
        return dict(key=row['key'],writer=row['writer'],session=row['session'],ordinal=row['ordinal'],
            canonical_positions=new, prepared_positions=old,
            verified_insertion=True,canonical_usable=True,
            index_status='same_unique_choice' if new == old else 'proven_disjoint_choice',
            canonical_sha256='fixture', raw_source_sha256='fixture')


def fixture_data(tmp_path):
    inputs = fixture.full_fixture(tmp_path/'source')
    data = list(card.original.source(inputs))
    visibility = [dict(role='suggestion',text_sha256=digest(s)) for s in ('near','middle','far')]
    saved = {}
    for writer in sorted({s['writer'] for s in data[0]}):
        support = card.original.writer_support(writer,*data,card.CONFIG)
        anchors, scopes = fixture.FakeEncoder().encode([e['text'] for e in support['events']])
        saved[writer] = card.original.score_writer(support,anchors,scopes,data[2])
    return data,visibility,saved


def native_fixture(root):
    """Actual authenticated synthetic files; no monkeypatch in either child."""
    root = Path(root).resolve()
    inputs = fixture.full_fixture(root/'old-source')
    sessions = read(inputs['sessions']); proofs=[]; pins={}; sourcepins={}
    for session in sessions:
        events=[]
        for row in session['rows']:
            row['open_at'] = row['ordinal']
            old = row['menu'].index(row['inserted'])
            chosen = 0 if session['timestamp']==0 or row['ordinal']<130 else 2
            row['inserted'] = row['menu'][(chosen+1)%3]
            prepared = (chosen+1)%3
            events.append(dict(ordinal=row['ordinal'],decision=row['handling'],usable=True,verified_insertion=True,
                options=[dict(index=i+7,original=t) for i,t in enumerate(row['menu'])],
                matched_option_indices=[chosen+7],selected_index=prepared,logged_index_agrees=False))
            proofs.append(dict(key=row['key'],writer=row['writer'],session=row['session'],ordinal=row['ordinal'],open_at=row['open_at'],
                canonical_handling=row['handling'],prepared_handling=row['handling'],canonical_positions=[chosen],prepared_positions=[prepared],
                canonical_option_ids=[7,8,9],verified_insertion=True,canonical_usable=True,logged_selected_index=prepared,
                logged_index_agrees=False,index_status='proven_disjoint_choice',raw_source_sha256=digest(session['session'])))
        path=root/'canonical'/(session['session']+'.json');write(path,dict(usable=True,reconstructed=True,events=events))
        sourcepins[path.relative_to(root).as_posix()]=sha256(path);pins[str(path)]=sha256(path)
        for proof in proofs[-len(session['rows']):]:proof.update(canonical_path=str(path),canonical_sha256=sha256(path))
    base=root/'results/phase_2_4_stage_15/raw';path=base/'phase0-v1/prepared/SESSIONS.json';write(path,sessions)
    sourcepath=path.with_name('SOURCE_PINS.json');write(sourcepath,sourcepins)
    inputs['sessions']=str(path)
    def overwrite(path,value):Path(path).write_text(json.dumps(value),encoding='utf8')
    p5=read(inputs['p5_inputs']);p5['paths']['sessions']=str(path);p5['sha256']['sessions']=sha256(path);overwrite(inputs['p5_inputs'],p5)
    d39=read(inputs['d39_inputs']);d39['paths']['sessions']=str(path);d39['pins']={str(path):sha256(path)};overwrite(inputs['d39_inputs'],d39)
    for prefix,keys in [('p5',('p5_inputs','p5_summary')),('d39',('d39_inputs','d39_failures'))]:
        receipt=read(inputs[prefix+'_completion']);directory=Path(inputs[prefix+'_completion']).parent
        for key in keys:receipt['outputs'][Path(inputs[key]).relative_to(directory).as_posix()]=sha256(inputs[key])
        overwrite(inputs[prefix+'_completion'],receipt)
    foundation=base/'drive-foundation-v1';plan=foundation/'PLAN.json';complete=foundation/'COMPLETE.json'
    write(plan,dict(pins={p.relative_to(root).as_posix():sha256(p) for p in (path,sourcepath)},synthetic_fixture_only=True))
    write(complete,dict(status='COMPLETE',plan_sha256=sha256(plan),synthetic_fixture_only=True))
    for p in (path,sourcepath,plan,complete):pins[str(p)]=sha256(p)
    audit=root/'audit';write(audit/'ROWS.json',proofs);write(audit/'INPUT_PINS.json',pins)
    script=root/'synthetic_audit.py';script.write_text('# Constructed audit only.\n',encoding='utf8')
    write(audit/'COMPLETE.json',dict(status='COMPLETE',schema_version=1,source_path=str(script),source_sha256=sha256(script),
        outputs={n:sha256(audit/n) for n in ('ROWS.json','INPUT_PINS.json')},no_fits=True,no_raw_replay=True,no_inference=True,no_repaired_scores=True,synthetic_fixture_only=True))
    visibility=Path(inputs['content_records']).with_name('VISIBILITY.json')
    write(visibility,[dict(role='suggestion',text_sha256=digest(t)) for t in ('near','middle','far')])
    receipt=read(inputs['content_complete']);receipt['outputs']['VISIBILITY.json']=sha256(visibility);overwrite(inputs['content_complete'],receipt)
    original_root=root/'original';old_encoder=card.original.Encoder
    try:
        card.original.Encoder=fixture.FakeEncoder
        card.original.execute(original_root/'output',inputs,card.original.CONFIG)
    finally:card.original.Encoder=old_encoder
    assert card.original.verify(original_root/'output',inputs,card.original.CONFIG)['verified']
    write(original_root/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,synthetic_fixture_only=True,
        outputs={p.relative_to(original_root).as_posix():sha256(p) for p in original_root.rglob('*') if p.is_file()}))
    helper=Path(__file__).resolve().parents[1]/'.agent-state/drive-20261017/builder3/selected_source_audit_reader.py'
    inputs.update(selection_reader=str(helper),selection_complete=str(audit/'COMPLETE.json'),visibility=str(visibility),original_complete=str(original_root/'COMPLETE.json'))
    return inputs


def test_canonical_target_and_vector_identity(tmp_path):
    data,visibility,_ = fixture_data(tmp_path)
    row = data[0][0]['rows'][1]
    corrected,proofs = card.canonicalize(data[0],data[1],visibility,Audit({row['key']:2}))
    assert corrected[0]['rows'][1]['inserted'] == 'far'
    assert row['inserted'] == 'near'
    assert sum(p['index_status']=='proven_disjoint_choice' for p in proofs) == 1
    visibility[0]['text_sha256'] = digest('wrong')
    with pytest.raises(ValueError,match='association'):
        card.canonicalize(data[0],data[1],visibility,Audit({}))


def test_anchor_window_and_deleted_text_cannot_change(tmp_path):
    data,_,saved = fixture_data(tmp_path)
    support = card.original.writer_support('w0',*data,card.CONFIG)
    card.anchors(support,saved['w0'])
    support['events'][0]['text'] += 'changed'
    with pytest.raises(ValueError,match='span changed'):card.anchors(support,saved['w0'])
    support = card.original.writer_support('w0',*data,card.CONFIG)
    support['events'][0]['window']['before'][0]['ordinal'] += 1
    with pytest.raises(ValueError,match='window changed'):card.anchors(support,saved['w0'])


@pytest.mark.parametrize('sign',[0,1,-1])
def test_full_primary_null_positive_reverse_and_all_controls(tmp_path,sign):
    data,visibility,saved = fixture_data(tmp_path)
    mapping = {}
    for session in data[0]:
        for row in session['rows']:
            if row['ordinal'] >= 130:
                mapping[row['key']] = 2 if (sign==1 and session['timestamp']>0) or (sign==-1 and session['timestamp']==0) else 0
    data[0],proofs = card.canonicalize(data[0],data[1],visibility,Audit(mapping))
    units = [card.writer_unit(w,data,saved[w],card.CONFIG) for w in sorted(saved)]
    result = card.summarize(units,proofs,card.CONFIG)
    assert result['primary']['effect'] == pytest.approx(2*sign)
    assert result['primary']['state'] == {0:'null',1:'positive',-1:'negative'}[sign]
    ref = result['repeated_outcome_control']
    assert len(ref['draws']) == 200 and np.isfinite(ref['draws']).all()
    assert ref['bias_flag'] == (abs(np.mean(ref['draws'])) > .25*np.std(ref['draws'],ddof=1))


def test_full_storage_replay_yield_and_immutability(tmp_path,monkeypatch):
    data,visibility,saved = fixture_data(tmp_path)
    data[0],proofs = card.canonicalize(data[0],data[1],visibility,Audit({}))
    monkeypatch.setattr(card,'load',lambda inputs,config:(data,proofs,saved))
    monkeypatch.setattr(card,'input_hashes',lambda inputs:{'fixture':'pinned'})
    output = tmp_path/'output';output.mkdir()
    (output/'YIELD_REQUEST.json').write_text('{}')
    assert card.execute(output,{},card.CONFIG)['status'] == 'yielded'
    (output/'YIELD_REQUEST.json').unlink()
    card.execute(output,{},card.CONFIG)
    assert card.verify(output,{},card.CONFIG)['verified']
    with pytest.raises(ValueError,match='immutable'):card.execute(output,{},card.CONFIG)
    path = output/'writers'/(hashlib.sha256(b'w0').hexdigest()[:24]+'.json')
    path.write_text('{}')
    with pytest.raises(ValueError):card.verify(output,{},card.CONFIG)
