import copy
import json
from pathlib import Path

import pytest

from runners.drive.cards import week_genre_inputs as card


def population(writers=15):
    rows = []
    for wi in range(writers):
        for genre, count in [('creative', 3), ('argumentative', 5)]:
            for si in range(4):
                words = [dict(index=i, is_word=True, token=['café', 'one', 'two', 'three', 'four'][i],
                    ordinal=i, completed_ordinal=i+1, seconds=float(i)) for i in range(count)]
                words.append(dict(index=count, is_word=False, token='.', ordinal=count,
                                  completed_ordinal=count+1, seconds=float(count)))
                rows.append(dict(session=f'{wi}-{genre}-{si}', writer=f'w{wi:02}',
                    prompt=f'p{si % 2}', timestamp=float(si), genre=genre, words=words))
    return rows


def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf8')


def fixture(root):
    root = Path(root).resolve(); rows = population()
    roster, index = [], []
    for row in rows:
        path = root/'p6'/f"{row['session']}.json"
        write(path, {k: v for k, v in row.items() if k != 'genre'})
        index.append(dict(session=row['session'], file=path.name, sha256=card.filehash(path)))
        roster.append(dict(**{k: row[k] for k in ('session', 'writer', 'prompt', 'timestamp')}, domain=row['genre']))
    roster_path, index_path = root/'ROSTER.json', root/'p6/INDEX.json'
    write(roster_path, roster); write(index_path, index)
    write(root/'p6/COMPLETE.json', dict(status='COMPLETE', fresh_process_verified=True,
        outputs={'INDEX.json': card.filehash(index_path)}))
    write(root/'foundation/PLAN.json', dict(pins={'ROSTER.json': card.filehash(roster_path)}))
    write(root/'foundation/COMPLETE.json', dict(status='COMPLETE',
        plan_sha256=card.filehash(root/'foundation/PLAN.json')))
    write(root/'PLAN.json', dict(inputs=dict(repo_root=str(root), raw_roster=str(roster_path),
        foundation_plan=str(root/'foundation/PLAN.json'), foundation_complete=str(root/'foundation/COMPLETE.json'),
        p6_completion=str(root/'p6/COMPLETE.json'), p6_index=str(index_path))))
    write(root/'COMPLETE.json', dict(status='COMPLETE', fresh_process_verified=True,
        outputs={'PLAN.json': card.filehash(root/'PLAN.json')}))
    return dict(pmap_completion=str(root/'COMPLETE.json'))


def test_exact_primary_pairing_words_and_original_halves():
    summary, manifest = card.match(population())
    assert summary['mode'] == 'primary' and summary['primary_population_supported']
    assert (summary['retained_writers'], summary['retained_sessions'], summary['retained_typed_words']) == (15, 120, 360)
    for row in manifest:
        assert row['typed_words'] == 3 and row['word_indices'] == [0, 1, 2]
        assert row['half'] == int(row['prompt'][-1])
        assert row['token_stop_exclusive'] == (4 if row['genre'] == 'creative' else 3)
    assert card.match(list(reversed(population()))) == (summary, manifest)


def test_count_matching_keeps_prompt_diversity_and_exclusion():
    rows = population()
    extra = copy.deepcopy(rows[0]); extra.update(session='extra', timestamp=100.)
    rows.append(extra)
    summary, manifest = card.match(rows)
    assert len(manifest) == 120
    assert summary['excluded_sessions'] == [dict(session='extra', writer='w00', reason='session_count_match')]
    chosen = card.diverse_prefix([dict(session=str(i), prompt='a' if i < 4 else 'b', timestamp=i) for i in range(5)], 2)
    assert [r['session'] for r in chosen] == ['0', '4']


def test_fallback_is_labeled_and_missing_cells_remain_missing():
    rows = population(1)
    for row in rows:
        row['prompt'] = row['genre']
    summary, manifest = card.match(rows)
    assert summary['mode'] == 'exploratory_mixed_genre_fallback'
    assert not summary['primary_population_supported'] and summary['retained_writers'] == 1
    assert all(r['half'] == 0 for r in manifest if r['genre'] == 'argumentative')
    assert all(r['half'] == 1 for r in manifest if r['genre'] == 'creative')
    assert summary['scientific_admission'] is False


def test_zero_words_can_remove_support_without_silent_fallback():
    rows = population(); rows[0]['words'] = []
    summary, manifest = card.match(rows)
    assert summary['original_eligible_writers'] == 15 and summary['retained_writers'] == 14
    assert summary['mode'] == 'primary' and not summary['primary_population_supported']
    assert 'w00' in summary['excluded_writers'] and len(manifest) == 112
    assert summary['excluded_sessions'][0]['reason'] == 'zero_completed_typed_words'


def test_missing_genre_and_no_prompt_split_explicitly_unsupported():
    rows = population(1)
    summary, manifest = card.match([r for r in rows if r['genre'] == 'creative'])
    assert not manifest and summary['retained_writers'] == 0
    for row in rows: row['prompt'] = 'one'
    summary, manifest = card.match(rows)
    assert not manifest and 'prompt split' in summary['excluded_writers']['w00']


def test_event_boundaries_do_not_imply_raw_prefix_or_unique_completion():
    rows = population(1)
    for row in rows:
        if row['genre'] == 'argumentative':
            for word in row['words']: word.update(ordinal=0, completed_ordinal=7)
    summary, manifest = card.match(rows)
    assert all(r['boundary_splits_event'] for r in manifest if r['genre'] == 'argumentative')
    assert all(r['word_indices'] == [0, 1, 2] for r in manifest)


@pytest.mark.parametrize('mutation', ['duplicate', 'genre', 'time', 'index', 'boolean', 'boundary'])
def test_malformed_source_fails_closed(mutation):
    rows = population(1)
    if mutation == 'duplicate': rows.append(copy.deepcopy(rows[0]))
    if mutation == 'genre': rows[0]['genre'] = 'unknown'
    if mutation == 'time': rows[0]['timestamp'] = float('nan')
    if mutation == 'index': rows[0]['words'][0]['index'] = 1
    if mutation == 'boolean': rows[0]['words'][0]['is_word'] = 1
    if mutation == 'boundary': rows[0]['words'][0]['completed_ordinal'] = -1
    with pytest.raises(ValueError): card.match(rows)


def test_full_handler_replay_and_saved_output_tampering(tmp_path):
    inputs = fixture(tmp_path/'source'); output = tmp_path/'output'
    assert card.execute(output, inputs, card.CONFIG)['status'] == 'COMPLETE_INPUT_MATCHING'
    assert card.verify(output, inputs, card.CONFIG)['verified']
    write(output/'SUPPORT.json', {})
    with pytest.raises(ValueError, match='replay differs'): card.verify(output, inputs, card.CONFIG)


@pytest.mark.parametrize('target', ['ROSTER.json', 'p6/INDEX.json', 'p6/0-creative-0.json', 'foundation/PLAN.json', 'PLAN.json'])
def test_changed_dependency_refuses(tmp_path, target):
    inputs = fixture(tmp_path/'source'); output = tmp_path/'output'
    card.execute(output, inputs, card.CONFIG)
    with (tmp_path/'source'/target).open('a', encoding='utf8') as stream: stream.write(' ')
    with pytest.raises(ValueError): card.verify(output, inputs, card.CONFIG)


def test_config_and_completion_record_changes_refuse(tmp_path):
    inputs = fixture(tmp_path/'source'); output = tmp_path/'output'
    with pytest.raises(ValueError, match='Frozen'): card.execute(output, inputs, dict(card.CONFIG, seed=7))
    card.execute(output, inputs, card.CONFIG)
    path = tmp_path/'source/p6/COMPLETE.json'
    value = card.read(path); value['note'] = 'changed but valid'
    write(path, value)
    with pytest.raises(ValueError, match='replay differs'): card.verify(output, inputs, card.CONFIG)
