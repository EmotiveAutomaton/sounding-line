import copy
import gzip
import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest
from runners.drive.cards import events_d4 as card
from runners.drive.cards import events_d4_sources as sources
from runners.drive.cards import events_d4_stats as stats
from runners.drive.cards.events_p5 import classify


def directions():
    return np.eye(384)


def test_soft_votes_conflict_is_uniform_and_optimal():
    x = np.vstack([directions()[0], -directions()[0]])
    for penalty in stats.PENALTIES:
        fit = stats.fit_votes(x, penalty)
        assert np.array_equal(fit['coefficients'], np.zeros(384))
        assert fit['gradient_max'] == 0
        assert stats.probabilities(x, fit['coefficients']) == pytest.approx([.5, .5])
    with pytest.raises(ValueError, match='unit'):
        stats.fit_votes(x * 2, .1)


@pytest.mark.parametrize('chosen,expected', [(0, 'positive'), (1, 'negative')])
def test_planted_choice_gain_and_reverse(chosen, expected):
    e = directions()
    models = dict(content=[stats.fit_votes(np.vstack([e[0]] * 6), p) for p in stats.PENALTIES],
                  housekeeping=[stats.fit_votes(np.vstack([e[1], -e[1]] * 3), p) for p in stats.PENALTIES])
    vectors = np.vstack([e[0], -e[0]])
    rows = [dict(session='s', key=f'k{i}', chosen=chosen, options=[0, 1]) for i in range(10)]
    result = stats.score_pair(models, rows, rows, vectors)
    interval = stats.interval([result['scores']['primary']] * 4, 2000, 19)
    assert interval['state'] == expected
    assert result['scores']['housekeeping_gain'] == 0
    assert result['scores']['content_gain'] == result['scores']['primary']
    # Test outcomes cannot choose the penalty or alter any fitted coefficient.
    changed = [dict(r, chosen=1 - chosen) for r in rows]
    other = stats.score_pair(models, rows, changed, vectors)
    assert result['selected'] == other['selected']
    assert result['calibration_losses'] == other['calibration_losses']


def test_exact_null_primary_and_half_brier():
    e = directions()
    fits = [stats.fit_votes(np.vstack([e[0], -e[0]]), p) for p in stats.PENALTIES]
    rows = [dict(session='s', key='k', chosen=0, options=[0, 1])]
    result = stats.score_pair(dict(content=fits, housekeeping=fits), rows, rows, e)
    assert result['scores'] == dict(primary=0., content_gain=0., housekeeping_gain=0.)
    assert stats.interval([0.] * 4, 2000, 1)['state'] == 'null'
    assert stats.half_brier([.2, .8], 1) == pytest.approx(.04)
    assert stats.interval([1.], 2000, 1)['state'] == 'invalid'


def test_session_weight_and_permutation_support():
    rows = [dict(session='a', key=f'a{i}', chosen=i % 2, options=[0, 1]) for i in range(20)]
    rows += [dict(session='b', key='b', chosen=2, options=[0, 1, 2])]
    assert stats.session_mean(rows, [1] * 20 + [0]) == .5
    shuffled, audit = stats.permuted_choices(rows, 20261017)
    assert shuffled[-1]['chosen'] == 2
    assert sorted(r['chosen'] for r in shuffled[:-1]) == sorted(r['chosen'] for r in rows[:-1])
    assert audit['singleton_size_strata'] == 1 and audit['changed'] > 0
    assert shuffled == stats.permuted_choices(rows, 20261017)[0]


def edit_fixture(ordinal, split, origin='model', vector_offset=0):
    e = directions()
    before, after = ('The stone is dark.', 'A bright bird travels north.') if split == 'content' else ('cat', 'bat')
    v = np.vstack([e[2], e[0] if split == 'content' else e[1]])
    # Housekeeping takes precedence over embedding shift, as frozen in P5.
    fields = classify(before, after, v[0], v[1], 1, 1)
    assert fields['split'] == split
    edit = dict(ordinal=ordinal, before=before, after=after, origin=origin,
        accepted_owners_touched=[10] if origin == 'model' else [],
        deleted_origin_counts={'accepted' if origin == 'model' else 'typed': 3},
        before_vector=vector_offset, after_vector=vector_offset + 1, **fields)
    return edit, v


def test_direct_link_mixed_ambiguous_and_zero_exclusions():
    edit, vectors = edit_fixture(20, 'content')
    decision = {10: dict(key='menu', handling='edit')}
    saved = dict(session='s', edits=[edit])
    rows, units, excluded, audit = sources.corrections(saved, vectors, decision)
    assert len(rows) == 1 and rows[0]['key'] == 'menu'
    assert np.linalg.norm(units[0]) == pytest.approx(1)
    assert not excluded and audit['model_content'] == 1
    mixed = dict(edit, deleted_origin_counts={'accepted': 3, 'typed': 1})
    multiple = dict(edit, accepted_owners_touched=[10, 11], ordinal=21)
    own = dict(edit, accepted_owners_touched=[], deleted_origin_counts={'typed': 3}, origin='own', ordinal=22)
    rows, units, exclusions, _ = sources.corrections(dict(session='s', edits=[mixed, multiple, own]), vectors, decision)
    assert [r['origin'] for r in rows] == ['own']
    assert {r['reason'] for r in exclusions} == {'mixed changed-span provenance', 'multiple accepted owners'}
    with pytest.raises(ValueError, match='split differs'):
        sources.corrections(dict(session='s', edits=[dict(edit, split='housekeeping')]), vectors, decision)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf8')


def full_fixture(root, writers=3):
    e = directions()
    vectors = np.vstack([e[0], -e[0]])
    content = root / 'content'
    p5 = root / 'p5'
    sessions, records, index = [], [], []
    for wi in range(writers):
        writer = f'w{wi}'
        for si in range(5):
            sid = f'{writer}s{si}'
            menus = []
            for mi in range(4):
                key = f'{sid}m{mi}'
                row = dict(key=key, session=sid, writer=writer, ordinal=10 + mi,
                    open_at=si * 100 + 10 + mi, menu=['first', 'second'], inserted='first', handling='edit')
                menus.append(row)
                records.append(dict(key=key, session=sid, writer=writer, options=[0, 1]))
            session = dict(session=sid, writer=writer, timestamp=si * 100, end_at=si * 100 + 90, rows=menus)
            sessions.append(session)
            edits, blocks = [], []
            for origin in ('model', 'own'):
                for split in ('content', 'housekeeping'):
                    for repeat in range(2):
                        edit, array = edit_fixture(20 + len(edits), split, origin, len(edits) * 2)
                        edits.append(edit); blocks.append(array)
            saved = dict(session=sid, writer=writer, timestamp=session['timestamp'], end_at=session['end_at'], edits=edits)
            fpath = p5 / 'output/sessions' / (sid + '.json.gz')
            fpath.parent.mkdir(parents=True, exist_ok=True)
            with gzip.open(fpath, 'wt', encoding='utf8') as f:
                json.dump(saved, f)
            vpath = fpath.with_suffix('.npy')
            np.save(vpath, np.concatenate(blocks))
            index.append(dict(session=sid, file=fpath.relative_to(p5 / 'output').as_posix(), sha256=card.filehash(fpath),
                vectors=vpath.relative_to(p5 / 'output').as_posix(), vectors_sha256=card.filehash(vpath)))
    inputs = dict(sessions=str(root / 'sessions.json'), content_records=str(content / 'RECORDS.json'),
        content_vectors=str(content / 'VECTORS.npy'), content_model=str(content / 'MODEL.json'),
        content_complete=str(content / 'COMPLETE.json'), p5_index=str(p5 / 'output/SESSION_INDEX.json'),
        p5_summary=str(p5 / 'output/SUMMARY.json'), p5_inputs=str(p5 / 'output/INPUTS.json'), p5_completion=str(p5 / 'COMPLETE.json'))
    write(Path(inputs['sessions']), sessions)
    write(Path(inputs['content_records']), records)
    np.save(inputs['content_vectors'], vectors)
    write(Path(inputs['content_model']), dict(frozen_model='synthetic same-model identifier; no inference'))
    write(Path(inputs['content_complete']), dict(status='COMPLETE', outputs={Path(inputs[k]).name: card.filehash(inputs[k])
          for k in ('content_records', 'content_vectors', 'content_model')}))
    write(Path(inputs['p5_index']), index)
    write(Path(inputs['p5_summary']), dict(sessions=len(sessions)))
    write(Path(inputs['p5_inputs']), dict(paths={k: inputs[k] for k in ('sessions', 'content_model')},
        sha256={k: card.filehash(inputs[k]) for k in ('sessions', 'content_model')}))
    write(Path(inputs['p5_completion']), dict(status='COMPLETE', fresh_process_verified=True,
        outputs={Path(inputs[k]).relative_to(p5).as_posix(): card.filehash(inputs[k]) for k in ('p5_index', 'p5_summary', 'p5_inputs')}))
    return inputs


def test_source_training_support_chronology_and_choice_exclusions(tmp_path):
    inputs = full_fixture(tmp_path)
    source = sources.source(inputs)
    data, units = sources.writer_data('w0', source, card.CONFIG)
    assert data['partition'] == dict(own_train=['w0s0', 'w0s1', 'w0s2'], calibration=['w0s3'], test=['w0s4'])
    assert data['exclusion'] is None and len(units) == 24
    assert {r['session'] for r in data['corrections']} == {'w0s0', 'w0s1', 'w0s2'}
    assert all(v['corrections'] == 6 and v['eligible'] for origin in data['support'].values() for v in origin.values())
    # A training session ending exactly at calibration start is unavailable.
    source['splits']['w0']['train'][-1]['end_at'] = data['cutoff']
    excluded, _ = sources.writer_data('w0', source, card.CONFIG)
    assert excluded['exclusion'] == 'chronology leaves fewer than 3/1/1 sessions'
    session = copy.deepcopy(source['sessions']['w0s4'])
    session['rows'][0]['handling'] = 'dismiss'
    session['rows'][1]['menu'] = ['first', 'first']
    session['rows'][2]['inserted'] = 'missing'
    rows, exclusions = sources.choices([session], source['records'], source['vectors'])
    assert len(rows) == 1 and len(exclusions) == 3


def test_actual_handler_yield_resume_fresh_replay_and_mutations(tmp_path, monkeypatch):
    inputs = full_fixture(tmp_path / 'source')
    output = tmp_path / 'output'
    original = card.fit_writer
    calls = []
    def fit(*args):
        calls.append(args[0]['writer'])
        result = original(*args)
        if len(calls) == 1:
            write(output / 'YIELD_REQUEST.json', {})
        return result
    monkeypatch.setattr(card, 'fit_writer', fit)
    assert card.execute(output, inputs, card.CONFIG)['status'] == 'yielded'
    (output / 'YIELD_REQUEST.json').unlink()
    result = card.execute(output, inputs, card.CONFIG)
    assert calls == ['w0', 'w1', 'w2']
    assert result['eligible_writers'] == 3 and result['state'] == 'positive'
    assert result['comparisons']['model']['housekeeping_gain']['effect'] == 0
    assert result['comparisons']['own']['primary']['effect'] == result['primary']['effect']
    assert card.read(output / 'FIRST_TENTH.json')['forecast_cpu_seconds'] == 3600
    assert card.verify(output, inputs, card.CONFIG)['verified']
    args = tmp_path / 'args.json'
    write(args, dict(output=str(output), inputs=inputs, config=card.CONFIG))
    script = "import json,sys; from pathlib import Path; from runners.drive.cards.events_d4 import verify; a=json.load(open(sys.argv[1])); print(json.dumps(verify(Path(a['output']),a['inputs'],a['config'])))"
    child = subprocess.run([sys.executable, '-B', '-c', script, str(args)], capture_output=True, text=True,
        env=dict(os.environ, PYTHONHASHSEED='357'), check=True)
    assert json.loads(child.stdout)['verified']
    with pytest.raises(ValueError, match='completed output'):
        card.execute(output, inputs, card.CONFIG)
    Path(inputs['content_vectors']).write_bytes(b'changed')
    with pytest.raises(ValueError, match='input changed'):
        card.verify(output, inputs, card.CONFIG)


def test_fit_failure_invalidates_whole_primary(tmp_path, monkeypatch):
    inputs = full_fixture(tmp_path / 'source')
    original = card.fit_writer
    def fit(data, *args):
        if data['writer'] == 'w1':
            raise ValueError('planted optimizer failure')
        return original(data, *args)
    monkeypatch.setattr(card, 'fit_writer', fit)
    result = card.execute(tmp_path / 'output', inputs, card.CONFIG)
    assert result['state'] == result['primary']['state'] == 'invalid'
    assert len(result['fit_failures']) == 1
    assert result['primary']['effect'] is None


def test_checkpoint_and_completion_mutations_refused(tmp_path):
    path = tmp_path / 'checkpoint.json'
    card.save(path, dict(value=1))
    path.write_text('{}', encoding='utf8')
    with pytest.raises(ValueError, match='hash differs'):
        card.read_sealed(path)
    inputs = full_fixture(tmp_path / 'source')
    Path(inputs['p5_summary']).write_text('{}', encoding='utf8')
    with pytest.raises(ValueError, match='bound by completion'):
        sources.source(inputs)
