import hashlib
import json

import pytest

from tools.r48_week8_tables import atlas_tables, meeting_tables


def terminal(root, card, corpus, data):
    suffix = 'prejoin' if card == 'LGH6' else 'room'
    path = root / f'{card}-{corpus}-{suffix}-DN'
    path.mkdir()
    data = json.dumps(dict(corpus=corpus, source_class='P', **data)).encode()
    hashes = {}
    for phase in ('execute', 'verify'):
        name = phase + '_SUMMARY.json'
        (path / name).write_bytes(data)
        hashes[name] = hashlib.sha256(data).hexdigest()
    (path / 'COMPLETE.json').write_text(json.dumps({'verified': True, 'results': hashes}))


def test_laughter_replay_requires_both_corpora_and_keeps_small_public_cells(tmp_path):
    model = {'model': 1, 'estimate': .2, 'lower': .1, 'upper': .3, 'shuffle95': .1, 'shuffle_upper': .02}
    data = {'meetings': 3, 'tables': {'short_intervals': {'intervals': 4, 'n': 2},
            'heldout': {'code': 0, 'models': [model], 'n': 5, 'meetings': 3}, 'all': {'code': 12}}}
    terminal(tmp_path, 'LGH6', 'ICSI', data)
    with pytest.raises(FileNotFoundError):
        meeting_tables('LGH6', tmp_path)
    terminal(tmp_path, 'LGH6', 'AMI', data)
    rows = meeting_tables('LGH6', tmp_path)
    for corpus in ('ICSI', 'AMI'):
        match, = [r for r in rows if r[0] == corpus + ', heldout, voicing model 1']
        assert match[1:6] == [.2, .1, .3, 5, 'people']
        assert any(r[0] == corpus + ', heldout, voicing model 1, shuffle95' for r in rows)


def test_room_projection_preserves_corpus_level_and_verifies_bytes(tmp_path):
    data = dict(source_meetings=25, complete_annotation_meetings=24, untimed_laugh_exclusions=1,
                models={'room': {'meetings': 23, 'weights': [[-.4,-.6,-.2]]}, 'pace': {'code': 12}},
                coefficient_order=['absolute change'])
    for corpus in ('AMI','ICSI'):
        terminal(tmp_path, 'RML1', corpus, data)
    rows = meeting_tables('RML1', tmp_path)
    match, = [r for r in rows if r[0] == 'AMI, room, absolute change']
    assert match[1:6] == [-.4, -.6, -.2, 23, 'meetings']
    (tmp_path/'RML1-AMI-room-DN'/'verify_SUMMARY.json').write_bytes(b'{}')
    with pytest.raises(ValueError, match='Receipt differs'):
        meeting_tables('RML1', tmp_path)


def test_atlas_keeps_member_0049_and_the_eight_split_threshold(tmp_path):
    dest = tmp_path/'verified_cells'
    dest.mkdir()
    pairs = [[[.4,.1,.7],[.4,.1,.7]]] * 8 + [[None,None]] * 2
    cell = dict(event='help', feeling='happy', scope='internal', splits=10,
                same_clear=8, defined_both=8, both_positive=8, both_negative=0, paired_intervals=pairs)
    data = json.dumps(cell).encode()
    (dest/'0000.json').write_bytes(data)
    audit = json.dumps(dict(public_rows=0, internal_rows=1,
                           checksums={'0000.json': hashlib.sha256(data).hexdigest()})).encode()
    (tmp_path/'ATLAS_COMPLETE.json').write_bytes(audit)
    rows = atlas_tables(tmp_path, {'verified': True, 'results': {'ATLAS_COMPLETE.json': hashlib.sha256(audit).hexdigest()}})
    assert rows[0][:2] == ['0049, cells with at least eight agreements', 1]
    assert any(r[0] == '0049, help/happy, split 9 half A' and r[1] is None for r in rows)
