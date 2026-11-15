"""Constructed-only IM1 source boundary and separate-process IN13C replay.

DESIGN CHECK: LESSONS 2-3, packet W. The full roster is independently fixed;
one neutral report is excluded only from the qualified subset. Two declared
incompatible scales preserve perfect class information but opposite motive
signs. Their expected five-versus-zero sign counts are written before fitting.
"""
from contextlib import contextmanager
from pathlib import Path
import csv
import os
import subprocess
import sys
from . import week6_in13_in15_common_v1 as common
from . import week6_in13_v1 as study
from . import week6_in13_in15_fixture_v1 as fixture
import pandas as pd


def bundle(root, people=5):
    root = Path(root); exchange = root/'exchange'; exchange.mkdir(parents=True, exist_ok=True)
    source = root/'constructed-upstream'; source.mkdir()
    salt = source/'constructed-salt.bin'; salt.write_bytes(bytes(range(32)))
    raw = fixture.null_pairs(people)
    base = raw.loc[~raw.text_id.eq(raw.loc[raw.emotion.eq('no-emotion'), 'text_id'].iloc[0])].copy()
    hashed = lambda key: common.original.salted(key, salt.read_bytes(), 'crowd-text')
    base['text_id'] = base.text_id.map(hashed)
    identity = {'constructed': True, 'source_rows': len(raw), 'salt_sha256': common.io.sha(salt),
        'full_text_roster_sha256': common.digest(sorted(raw.text_id.map(hashed))), 'fixture_only': True}
    # Simulates only the already-qualified upstream metadata boundary. The real
    # canonical_source cannot admit this fixture: its corpus/table pins differ.
    common.io.write_json(source/'PLAN.json', {'module': 'runners.drive.cards.week5_in', 'config': {'phase': 'prepare'},
        'inputs': {'salt': str(salt)}, 'pins': {str(salt): common.io.sha(salt)}, 'constructed_only': True})
    common.io.write_json(source/'VERIFIED.json', {'verified': True, 'constructed_upstream_stub': True})
    common.io.write_json(source/'COMPLETE.json', {'status': 'COMPLETE', 'fresh_process_verified': True,
        'constructed_upstream_stub': True, 'not_a_native_qualification_receipt': True,
        'outputs': {name: common.io.sha(source/name) for name in ('PLAN.json', 'VERIFIED.json')}})
    coders = []
    for coder, lo, hi, pin in [('coder_a', 0, 2, '1'*64), ('coder_b', 80, 100, '2'*64)]:
        scale = {'schema': 'IM1-scale-v1', 'coder': coder,
            'motives': {m: {'units': f'constructed separate {coder} units', 'direction': 'higher-is-more',
                'minimum': lo, 'maximum': hi} for m in study.MOTIVES}}
        path = exchange/f'{coder}-scale.json'; common.io.write_json(path, scale)
        coders.append({'id': coder, 'publication': f'constructed method {coder}; not a real publication',
            'implementation_sha256': pin, 'scale': path.name, 'scale_sha256': common.io.sha(path)})
    choice = {'schema': 'IN13C-choice-v1', 'source_archive_sha256': common.original.SOURCE_SHA,
        'primary_coder': 'coder_a', 'declared_before_outcomes': True,
        'coders': {c['id']: {k: c[k] for k in ('implementation_sha256', 'scale_sha256')} for c in coders}}
    # The fixture really writes the choice before the score table and any fit.
    choice_path = exchange/'CHOICE.json'; common.io.write_json(choice_path, choice)
    columns = ['text_id', *(f'{c["id"]}__{m}' for c in coders for m in study.MOTIVES)]
    table = exchange/'SCORES.tsv'
    with table.open('w', encoding='utf8', newline='') as stream:
        writer = csv.writer(stream, delimiter='\t', lineterminator='\n'); writer.writerow(columns)
        for row in raw.itertuples():
            a = {'achievement': 2 if row.emotion == 'pride' else 0,
                 'affiliation': 2 if row.emotion in ('guilt', 'sadness', 'trust') else 0,
                 'power': 2 if row.emotion in ('pride', 'anger') else 0}
            writer.writerow([row.text_id, *[a[m] for m in study.MOTIVES], *[100-10*a[m] for m in study.MOTIVES]])
    manifest = {'schema': 'IM1-v2', 'source_archive_sha256': common.original.SOURCE_SHA,
        'table': table.name, 'table_sha256': common.io.sha(table), 'coders': coders}
    manifest_path = exchange/'IM1.json'; common.io.write_json(manifest_path, manifest)
    inputs = {'source_run': str(source), 'im1_manifest': str(manifest_path), 'im1_manifest_sha256': common.io.sha(manifest_path),
        'im1_choice_manifest': str(choice_path), 'im1_choice_manifest_sha256': common.io.sha(choice_path)}
    config = {'phase': 'IN13C', 'scope': 'qualified_real_events', 'im1_primary_coder': 'coder_a',
        'max_new_draws': 2000, 'max_wall_seconds': 300}
    value = {'frame': base.to_dict('records'), 'identity': identity, 'inputs': inputs, 'config': config,
             'expected_full_rows': len(raw), 'expected_primary_rows': len(base)}
    common.io.write_json(root/'CONSTRUCTED_SOURCE.json', value)
    return value


@contextmanager
def upstream(root, value=None):
    root = Path(root); value = value or common.seal.read(root/'CONSTRUCTED_SOURCE.json')
    old_source, old_exchange = common.canonical_source, study.EXCHANGE_ROOT
    try:
        common.canonical_source = lambda inputs, card, scope: (pd.DataFrame(value['frame']), None, dict(value['identity']))
        study.EXCHANGE_ROOT = (root/'exchange').resolve()
        yield value
    finally:
        common.canonical_source, study.EXCHANGE_ROOT = old_source, old_exchange


def stage(root, output, phase):
    root, output = Path(root), Path(output)
    with upstream(root) as value:
        inputs, config = value['inputs'], value['config']; small = {**config, 'max_new_draws': 1}
        fn = study.execute if phase == 'execute' else study.verify
        first = fn(output, inputs, small)
        assert first['status'] == 'yielded' and first['verified'] is False
        answer = fn(output, inputs, config)
        assert answer.get('complete_card') if phase == 'execute' else answer['verified'] is True
        common.io.write_json(output/f'{phase.upper()}_FIXTURE_STAGE.json',
            {'passed': True, 'constructed_only': True, 'pid': os.getpid(), 'phase': phase, 'pause_reentry': True})


def separate_chain(root):
    root = Path(root); value = bundle(root/'source', people=100); output = root/'output'
    environment = dict(os.environ)
    for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'): environment[key] = '2'
    program = 'from runners.drive.cards.week6_in13_im1_fixture_v1 import stage; import sys; stage(sys.argv[1], sys.argv[2], sys.argv[3])'
    for phase in ('execute', 'verify'):
        completed = subprocess.run([sys.executable, '-c', program, str(root/'source'), str(output), phase],
            capture_output=True, text=True, env=environment, timeout=300, check=False)
        (root/f'{phase}.stdout.log').write_text(completed.stdout, encoding='utf8')
        (root/f'{phase}.stderr.log').write_text(completed.stderr, encoding='utf8')
        assert completed.returncode == 0, completed.stderr
    executed = common.seal.read(output/'EXECUTE_FIXTURE_STAGE.json'); verified = common.seal.read(output/'VERIFY_FIXTURE_STAGE.json')
    assert executed['pid'] != verified['pid']
    result = common.seal.read(output/'RESULT.json')
    assert result['primary_coder'] == 'coder_a' and set(result['analyses']) == {'coder_a', 'coder_b'}
    for coder, count in [('coder_a', 5), ('coder_b', 0)]:
        analysis = result['analyses'][coder]
        assert analysis['pairs_meeting_point_criterion'] == count
        assert analysis['point_rule_clears'] is (count >= 3)
        for pair in analysis['pairs']:
            assert pair['comparison']['ratings'] == .5 and pair['comparison']['augmented'] == 1.
            assert pair['gain']['draws'] == 2000 and pair['gain']['failed_draws'] == []
            assert pair['gain']['interval'] == [.5, .5]
    for relative in ('DRAWS.json', 'independent-replay/DRAWS.json'):
        bank = common.seal.read(output/relative); assert len(bank['draws']) == 2000
        for draw in bank['draws']:
            assert set(draw) == {'coder_a', 'coder_b'}
            for coder in draw:
                assert draw[coder]['mean_gap'] == .5
                assert all(pair['gap'] == .5 for pair in draw[coder]['pairs'])
    proof = {'passed': True, 'record_kind': 'run', 'by_construction': True, 'theory_tags': ['H18-S1'], 'activation': [],
        'full_source_rows': value['expected_full_rows'], 'qualified_rows': value['expected_primary_rows'],
        'execute_pid': executed['pid'], 'verify_pid': verified['pid'], 'separate_processes': True,
        'independent_source_parser': True, 'draws_each_path': 2000, 'separate_coder_point_counts': {'coder_a': 5, 'coder_b': 0},
        'real_IM1_present_or_admitted': False}
    common.io.write_json(root/'FIXTURE.json', proof)
    return proof
