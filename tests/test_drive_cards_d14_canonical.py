import copy
from pathlib import Path

import numpy as np
import pytest

from runners.drive.cards import events_d14_canonical as card
from runners.drive.cards.menus_io import read, write, sha256
from tests.test_drive_cards_d32_canonical import native_fixture as source_fixture
from tests.test_drive_cards_events_d14 import known_rows, sessions_fixture, FakeEncoder, FakeNLP
from runners.drive.cards import events_d14_features as features


def test_reselected_offer_nuisance_equals_full_original_assembly():
    sessions, records, vectors, p8 = sessions_fixture(2)
    extraction = features.extract_writer(sessions, records, vectors, FakeEncoder(), FakeNLP())
    rows = extraction['rows']; nuisance, _ = features.nuisance_matrix(rows, sessions, records, vectors, p8, 20261017)
    class Audit:
        def join(self, row):
            chosen = row['handling'] in ('accept', 'edit')
            return dict(prepared_positions=[1] if chosen else [], canonical_positions=[0] if chosen else [],
                        verified_insertion=True, canonical_usable=True)
    corrected, matrix, audit = card.correct(rows, nuisance, extraction['offered_disturbances'], sessions, Audit())
    expected, _ = features.nuisance_matrix(corrected, sessions, records, vectors, p8, 20261017)
    assert np.array_equal(matrix, expected)
    assert audit['corrected_selected_menus'] == 4 and len(corrected) == len(rows)
    assert [r['position'] for r in corrected if r['handling'] == 'accept'] == [0, 0]
    bad = copy.deepcopy(rows); bad[0]['protected'] = 1
    with pytest.raises(ValueError, match='protection outcome'): card.correct(bad, nuisance, extraction['offered_disturbances'], sessions, Audit())


@pytest.mark.parametrize('effect', [0., .6, -.6])
def test_known_signed_ruler_and_invalid_fit(effect):
    rows = known_rows(effect); nuisance = np.zeros((len(rows), 7))
    moments = card.stats.sufficient(rows, nuisance)
    assert card.draw(moments)['effect'] == pytest.approx(effect, abs=1e-12)
    broken = card.stats.sufficient(rows, np.array([[r['topic_drift']] for r in rows]))
    assert card.draw(broken)['effect'] is None


def native_fixture(root):
    root = Path(root).resolve(); inputs = source_fixture(root/'source')
    sessions = read(inputs['sessions']); rng = np.random.default_rng(888)
    original = root/'original-d14'; output = original/'output'; rows = []; nuisance = []; index = []
    for writer in sorted({s['writer'] for s in sessions}):
        offered = []; own = []
        for session in sessions:
            if session['writer'] != writer: continue
            for menu in session['rows']:
                base = rng.normal(size=3)
                for position, text in enumerate(menu['menu']):
                    row = dict(key=menu['key'], writer=writer, session=session['session'], position=position,
                        topic_drift=float(.7 * (menu['handling']=='edit') + .1*rng.random()), disturbance=dict(candidate_characters=len(text)), paragraph_truncated=False)
                    offered.append(row)
                    if text == menu['inserted']:
                        chosen = dict(row, protected=int(menu['handling']=='edit'), handling=menu['handling'])
                        rows.append(chosen); own.append(chosen); nuisance.append(np.r_[base,card.suffix(chosen)].tolist())
        file = f'writers/{writer}.json'; card.old.save(output/file, dict(rows=own, offered_disturbances=offered))
        index.append(dict(writer=writer,file=file,sha256=sha256(output/file)))
    card.old.save(output/'ROWS.json', rows); card.old.save(output/'NUISANCE.json', nuisance)
    card.old.save(output/'PROJECTION.json', dict(synthetic_fixture_only=True,components=[]))
    card.old.save(output/'WRITER_INDEX.json', index)
    write(output/'INPUTS.json', dict(paths=dict(sessions=inputs['sessions']),pins={inputs['sessions']:sha256(inputs['sessions'])}))
    write(original/'COMPLETE.json', dict(status='COMPLETE',fresh_process_verified=True,synthetic_fixture_only=True,
        outputs={p.relative_to(original).as_posix():sha256(p) for p in output.rglob('*') if p.is_file()}))
    return {k:inputs[k] for k in ('sessions','selection_reader','selection_complete')}|dict(original_complete=str(original/'COMPLETE.json'))


def test_actual_source_full_handler_and_mutation(tmp_path):
    inputs = native_fixture(tmp_path/'fixture'); output = tmp_path/'output'
    result = card.execute(output,inputs,card.CONFIG)
    assert result['source_audit']['corrected_selected_menus'] > 0
    assert result['primary']['state'] == 'positive' and result['repeated_outcome_control']['invalid'] == 0
    assert card.verify(output,inputs,card.CONFIG)['verified']
    with pytest.raises(ValueError,match='immutable'): card.execute(output,inputs,card.CONFIG)
    Path(inputs['sessions']).write_text('[]')
    with pytest.raises(ValueError,match='source changed'): card.load(inputs,card.CONFIG)
