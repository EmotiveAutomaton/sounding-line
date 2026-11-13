"""EX4 local KLiCKe essay/stop bundle, no writer identifiers or model inference.

DESIGN CHECK: packet EX4/T/Q; source and independent final text are required.
Parse failures retain the full roster denominator; integrity errors never become
ordinary exclusions. Publication is limited to the named ignored local folder.
"""
from collections import Counter
from pathlib import Path
import hashlib
import json
import shutil
import time
from . import week5_ex4_words as words
from . import week5_bk_s4k_source as source
from . import week5_bk_klicke_intake as intake
from . import week5_qualification_io as io
from . import week5_engine_export_io as sealed
from . import timing_text
from runners.stage9 import coauthor

MODULE = 'runners.drive.cards.week5_ex4'


def authenticate(inputs):
    if set(inputs) != {'intake_complete'}:
        raise ValueError('Exact completed original KLiCKe intake required')
    complete, root, index = source.intake(inputs, 'corpus')
    sealed.complete(complete.parent, 'runners.drive.cards.week5_bk_klicke_intake_v2')
    plan = sealed.read(complete.parent / 'PLAN.json')
    if plan['inputs']['archive_sha256'] != intake.ARCHIVE_SHA:
        raise ValueError('Original KLiCKe archive changed')
    binding = {'intake_complete_sha256': io.sha(complete), 'index_sha256': io.sha(root / 'INDEX.json'),
               'source_modules': {Path(m.__file__).resolve().relative_to(Path(__file__).resolve().parents[3]).as_posix(): io.sha(m.__file__)
                                  for m in (words, words.original, source, intake, io, sealed, timing_text, coauthor)},
               'module_sha256': io.sha(__file__), 'version': 'EX4-SURVIVING-WORDS-1'}
    return complete, root, index, binding


def run(output, inputs, config):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    if set(config) - {'phase', 'max_new_draws', 'max_wall_seconds'} or config.get('phase') != 'EX4':
        raise ValueError('Fixed EX4 contract required')
    complete, source_root, index, identity = authenticate(inputs)
    binding = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    state_path = output / 'CHECKPOINT.json'
    state = sealed.state(state_path, binding, {'rows': [], 'pilot_released': False})
    began = time.monotonic(); count = 0
    maximum = int(config.get('max_new_draws', 250)); wall = float(config.get('max_wall_seconds', 900))
    if maximum < 1 or wall <= 0:
        raise ValueError('Positive bounded source quantum required')
    pilot = max(1, (len(index) + 19) // 20)
    for ordinal in range(len(state['rows']), len(index)):
        if (count >= maximum or time.monotonic() - began >= wall
                or any((p / 'YIELD_REQUEST.json').exists() for p in [output, *output.parents[:3]])):
            return {'status': 'yielded', 'verified': False, 'phase': 'session_replay', 'completed': ordinal, 'total': len(index)}
        entry = index[ordinal]
        record = source.source_record(complete, source_root, entry)  # Integrity errors stay outside parse exclusion.
        if record.get('status') == 'parse_failed':
            row = {'ordinal': ordinal, 'session': entry['session'], 'status': 'intake_parse_failed'}
        else:
            try:
                projected = words.replay(record)
            except (ValueError, UnicodeError) as error:
                row = {'ordinal': ordinal, 'session': entry['session'], 'status': 'replay_parse_failed', 'error_type': type(error).__name__}
            else:
                path = output / 'bundle/sessions' / f'{ordinal:05d}.json'
                if path.exists() and sealed.read(path) != projected:
                    raise ValueError('Existing complete session projection changed')
                if not path.exists():
                    io.write_json(path, projected)
                row = {'ordinal': ordinal, 'session': entry['session'], 'status': 'complete',
                       'file': path.relative_to(output).as_posix(), 'sha256': io.sha(path), 'counts': projected['counts']}
        state['rows'].append(row); sealed.checkpoint(state_path, state); count += 1
        io.write_json(output / 'PROGRESS.json', {'phase': 'session_replay', 'completed': ordinal + 1, 'total': len(index)})
        if ordinal + 1 == pilot and not state['pilot_released']:
            state['pilot_released'] = True; sealed.checkpoint(state_path, state)
            return {'status': 'yielded', 'verified': False, 'phase': 'source_cost_prefix', 'completed': ordinal + 1,
                    'total': len(index), 'first_fraction': .05}
    counts = Counter(); statuses = Counter()
    for row in state['rows']:
        statuses[row['status']] += 1; counts.update(row.get('counts', {}))
        if row['status'] == 'complete' and io.sha(output / row['file']) != row['sha256']:
            raise ValueError('Saved session projection changed')
    bundle = output / 'bundle'; bundle.mkdir(parents=True, exist_ok=True)
    io.write_json(bundle / 'INDEX.json', state['rows'])
    summary = {'card': 'EX4', 'record_kind': 'run', 'theory_tags': [], 'by_construction': False,
               'complete_export': True, 'source_sessions': len(index), 'session_status': dict(statuses), 'counts': dict(counts),
               'writer_id_included': False, 'licence': 'CC-BY-4.0', 'local_only': True, 'scientific_inference': False}
    io.write_json(bundle / 'SUMMARY.json', summary)
    readme = '''# KLiCKe essays with stop labels: local derived benchmark

Derived from Tian, Crossley and Van Waes, The KLiCKe Corpus: Keystroke Logging in
Compositions for Knowledge Evaluation (2025), DOI 10.17239/jowr-2025.17.01.02.
Acknowledgement: the corpus authors and The Learning Agency. Source data licence:
Creative Commons Attribution 4.0, https://creativecommons.org/licenses/by/4.0/.
This is our derived reconstruction, not an author-supplied stop annotation.

The exact independently reconstructed final essay text is preserved. Offsets are
Unicode code points, with no NFC conversion or extra whitespace trimming. The
original source's single export-record newline is removed by its frozen parser.
The P6 TOKEN/WORD rule identifies final surviving words. Rows containing typed
Input material are ordered by their earliest surviving typing event, then final
offset; ties are explicit event simultaneity, not invented keystroke order.

For wholly supported single-character Input provenance, the first character must
retain its original word-start event and precede every other constituent event.
Its pause is key-down minus previous logged event key-up, agreeing with the
source PauseTime to one millisecond. Missing, overlapping or inconsistent clocks,
bulk/paste/replace mixtures, deleted word starts and merged original word starts
have nullable timing and stop labels with a reason. They are not fluent labels.
Words with no typed Input material are counted and omitted from the typed list.

Stops use pause >=2 seconds, and pause >= the essay's linear 80th percentile of
supported surviving typed-word pauses; ties remain. inserted_later means a
surviving typed character was inserted before the then-current document end.
Moves preserve original timing and have their own quality flag. This is a final-
survivor benchmark, not a record of words later deleted or a writer-level study.

INDEX/SUMMARY retain every source session and aggregate parse exclusions. No
writer id is exported or inferred. Session keys are the intake's salted keys;
raw filename tokens and identity fields are absent. This bundle stays on local
ignored disk. No network, provider, email or public publication is authorized by
its production. Owner-only local ToMpathy copy follows amendment T after replay.
'''
    (bundle / 'README.md').write_text(readme, encoding='utf8', newline='\n')
    files = {p.relative_to(bundle).as_posix(): io.sha(p) for p in sorted(bundle.rglob('*')) if p.is_file() and p.name != 'MANIFEST.json'}
    io.write_json(bundle / 'MANIFEST.json', {'card': 'EX4', 'source_binding': identity, 'files': files})
    io.write_json(output / 'RESULT.json', summary); return summary


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    output = Path(output); result = run(output / 'independent-replay', inputs, config)
    if result.get('status') == 'yielded':
        return {**result, 'verified': False}
    sealed.replay_bundle(output / 'bundle', output / 'independent-replay/bundle')
    if sealed.read(output / 'RESULT.json') != result:
        raise ValueError('EX4 independent complete aggregate differs')
    return {'verified': True, 'complete_session_text_word_timing_replay': True}


def materialize(run_root, destination):
    repo = Path(__file__).resolve().parents[3]
    allowed = repo / 'corpora/store/exports/engine_bench_20261111/EX4'
    destination = Path(destination).resolve()
    if destination != allowed.resolve() or destination.exists():
        raise ValueError('Only a new named ignored local EX4 directory is allowed')
    root, plan, done = sealed.complete(run_root, MODULE)
    if sealed.read(root / 'output/RESULT.json').get('complete_export') is not True:
        raise ValueError('Complete independently verified export required')
    manifest = sealed.read(root / 'output/bundle/MANIFEST.json')
    if manifest['source_binding']['module_sha256'] != io.sha(__file__):
        raise ValueError('Export producer identity differs')
    bundle = root / 'output/bundle'
    expected = set(manifest['files']) | {'MANIFEST.json'}
    actual = {p.relative_to(bundle).as_posix() for p in bundle.rglob('*') if p.is_file()}
    if expected != actual:
        raise ValueError('Export inventory differs')
    for name in sorted(expected):
        path = bundle / name; path.resolve().relative_to(bundle.resolve())
        if path.is_symlink() or (name != 'MANIFEST.json' and io.sha(path) != manifest['files'][name]):
            raise ValueError('Changed export member')
        copied = destination / name; copied.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, copied)
        if io.sha(path) != io.sha(copied):
            raise ValueError('Local copy differs')
    return {'card': 'EX4', 'files': {name: io.sha(destination / name) for name in sorted(expected)}}
