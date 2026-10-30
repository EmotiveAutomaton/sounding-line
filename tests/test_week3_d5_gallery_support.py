"""D5 support: fixed population, chronology, missing evidence and actual seals."""
from copy import deepcopy
from pathlib import Path
import pytest

from runners.stage14.common import read, freeze
from runners.drive.cards import week3_d5_gallery_support as card


def fixture():
    rows = []
    for w in range(8):
        for i, prompt in enumerate(('p0', 'p1', 'p0', 'p2')):
            share = (0., .25, .5, 1.)[i]
            rows.append(dict(session=f'w{w}s{i}', writer=f'w{w}', prompt=prompt,
                timestamp=float(i), model_share=share, model_share_missing_reason=None,
                share_bin=card.share_bin(share), support={c:True for c in card.COMPONENTS if c != 'process'}))
    return dict(constructed=True, rows=rows)


def test_exact_bin_partition_and_missing():
    assert [card.share_bin(x) for x in [0., .249999, .25, .499999, .5, .749999, .75, 1., None]] == ['0','0','1','1','2','2','3','3','missing']
    for value in [-.001, 1.001, float('nan'), float('inf'), True, '0.5']:
        with pytest.raises(ValueError): card.share_bin(value)


def test_whole_prompt_split_and_rotating_disjoint_roles():
    f = fixture(); summary, detail = card.prepare(f['rows'], card.CONSTRUCTED)
    assert summary['split_supported_writers'] == 8
    assert summary['channels']['process']['full_original_gallery_supported']
    assert detail['halves']['w0'] == [['w0s0','w0s2','w0s3'], ['w0s1']]
    for variant in detail['channels'].values():
        seen = []
        for rotation in variant['independent_rotations']:
            assert not set(rotation['donor_writers']) & set(rotation['gallery_writers'])
            assert set(rotation['probe_writers']) <= set(rotation['gallery_writers'])
            assert not rotation['missing_context_sessions']
            seen += rotation['probe_writers']
        assert sorted(seen) == detail['original_gallery']
    assert card.prepare(list(reversed(f['rows'])), card.CONSTRUCTED) == (summary, detail)


def test_missing_components_and_writer_are_retained():
    f = fixture()
    for r in f['rows']:
        if r['writer'] == 'w0': r['support']['selection'] = False
        if r['writer'] == 'w1': r['prompt'] = 'single'
    summary, detail = card.prepare(f['rows'], card.CONSTRUCTED)
    assert len(detail['original_gallery']) == 8 and summary['sessions'] == 32
    assert not summary['channels']['process']['full_original_gallery_supported']
    assert 'w0' not in detail['channels']['process']['supported_writers']
    assert 'w1' in detail['split_exclusions']
    assert all('w0' in x['gallery_writers'] or 'w0' in x['donor_writers'] for x in detail['channels']['process']['independent_rotations'])
    assert not summary['scientific_admission'] and not summary['effect_computed']


def test_unsupported_context_is_not_zero_or_dropped():
    f = fixture()
    for r in f['rows']:
        if r['writer'] == 'w0': r['prompt'] += '-unique'
    summary, detail = card.prepare(f['rows'], card.CONSTRUCTED)
    assert summary['channels']['final']['literal_missing_context_sessions'] == 4
    assert len(detail['rows']) == 32
    for rotation in detail['channels']['final']['independent_rotations']:
        if 'w0' in rotation['gallery_writers']:
            assert all('w0s'+str(i) in rotation['missing_context_sessions'] for i in range(4))


def test_join_detects_mismatched_features_and_lengths():
    metadata = dict(session='s', writer='w', prompt='p', timestamp=1., model_share=.5, model_share_missing_reason=None)
    w = dict(**metadata, final={'words':64}, human={'words':64},
        process={'selection':[None, .5], 'rhythm':[10., None]}, human_prefixes={})
    c = dict(**metadata, final={'words':64, 'opportunities':{'2':10,'3':9,'4':8}}, human={'words':64}, human_prefixes={})
    for n in card.words.LENGTHS:
        w['human_prefixes'][str(n)] = dict(supported=n<=64, words=n)
        c['human_prefixes'][str(n)] = dict(supported=n<=64, words=n, opportunities={'2':10,'3':9,'4':8})
    joined = card.join(w,c)
    assert joined['support']['human64'] and not joined['support']['human128']
    altered = deepcopy(c); altered['writer']='other'
    with pytest.raises(ValueError, match='identities'): card.join(w, altered)
    altered = deepcopy(c); altered['human_prefixes']['64']['words']=63
    with pytest.raises(ValueError, match='declared word length'): card.join(w, altered)
    with pytest.raises(ValueError, match='Nonfinite'): card.available([float('nan')])


def test_full_handler_reentry_fresh_replay_and_tamper(tmp_path):
    path=tmp_path/'fixture.json'; freeze(path, fixture()); inputs=dict(fixture=str(path)); output=tmp_path/'output'
    assert card.execute(output,inputs,card.CONSTRUCTED)['status']=='complete'
    before={p.name:p.read_bytes() for p in output.iterdir()}
    assert card.verify(output,inputs,card.CONSTRUCTED)['full_fresh_support_replay']
    card.execute(output,inputs,card.CONSTRUCTED)
    assert before=={p.name:p.read_bytes() for p in output.iterdir()}
    changed=read(output/'SUMMARY.json'); changed['writers']=7
    (output/'SUMMARY.json').write_text(__import__('json').dumps(changed),encoding='utf-8')
    with pytest.raises(ValueError, match='replay differs'): card.verify(output,inputs,card.CONSTRUCTED)


def test_actual_completed_features_and_changed_plan_refusal(tmp_path):
    repo=Path(__file__).resolve().parents[1]; raw=repo/'results/phase_2_4_stage_15/raw/drive-week3-20261025'
    inputs=dict(word_complete=str(raw/'D5-features/COMPLETE.json'), character_complete=str(raw/'D5-characters/COMPLETE.json'))
    rows, pins=card.load(inputs,card.CONFIG)
    assert len(rows)==1399 and len({r['writer'] for r in rows})==61 and len(pins)>2800
    terminal=Path(inputs['word_complete']); complete=read(terminal); plan=read(terminal.parent/'PLAN.json')
    plan['module']='wrong.producer'
    freeze(tmp_path/'PLAN.json',plan); freeze(tmp_path/'COMPLETE.json',complete)
    with pytest.raises(ValueError, match='Completed feature bytes differ'):
        card.load(dict(inputs,word_complete=str(tmp_path/'COMPLETE.json')),card.CONFIG)
