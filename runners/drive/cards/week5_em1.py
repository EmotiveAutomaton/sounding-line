"""EM1 private correspondence materials from an owner-pinned local capsule.

DESIGN CHECK: LESSONS 1d/2/5. Reuse is a count, not inferred authorship. No
training, source acquisition, external communication or third-party text export.
An undocumented historical prefix rule remains unresolved, never reverse-fit.
"""
from pathlib import Path
import hashlib
import json
import time
from . import week5_em1_hashes as hashes
from . import week5_qualification_io as io
from . import week5_engine_export_io as sealed

PAN_ROLES = ('train_2023', 'train_2024', 'validation_2024')


def capsule(path):
    path = Path(path); manifest = sealed.read(path)
    if set(manifest) != {'schema', 'pan', 'schola', 'prefix_rule'} or manifest['schema'] != 'EM1-LOCAL-1':
        raise ValueError('Exact EM1 source capsule required')
    rule = manifest['prefix_rule']
    if set(rule) != {'characters', 'historical_definition_recovered', 'definition_note_sha256', 'definition_note_path'}:
        raise ValueError('Explicit prefix definition and its reviewed note hash required')
    if not isinstance(rule['characters'], int) or rule['characters'] < 1:
        raise ValueError('Historical prefix length is unresolved; no inferred default')
    note_path = Path(rule['definition_note_path']).resolve()
    note_path.relative_to(Path(__file__).resolve().parents[3])
    if len(rule['definition_note_sha256']) != 64 or io.sha(note_path) != rule['definition_note_sha256']:
        raise ValueError('Reviewed prefix-definition note must be pinned')
    note = sealed.read(note_path)
    if (note.get('characters') != rule['characters'] or type(rule['historical_definition_recovered']) is not bool
            or note.get('historical_definition_recovered') is not rule['historical_definition_recovered']):
        raise ValueError('Reviewed prefix definition and capsule disagree')
    if set(manifest['pan']) != set(PAN_ROLES):
        raise ValueError('Both training years and 2024 hard validation are required')
    for spec in [*manifest['pan'].values(), manifest['schola']]:
        if set(spec) != {'root', 'files'} or not spec['files']:
            raise ValueError('Nonempty exact source tree required')
        root = Path(spec['root']).resolve()
        repo = Path(__file__).resolve().parents[3]
        root.relative_to(repo)
        if root.is_symlink():
            raise ValueError('Source symlink refused')
        for name, expected in spec['files'].items():
            p = root / name; p.resolve().relative_to(root)
            if p.is_symlink() or io.sha(p) != expected:
                raise ValueError('EM1 original source tree changed')
        actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
        if actual != set(spec['files']):
            raise ValueError('Unpinned or missing source members')
    return manifest


def schola_source(spec):
    from datasets import load_from_disk
    dataset = load_from_disk(spec['root'])
    if not {'train', 'test'} <= set(dataset):
        raise ValueError('Original shipped train/test required')
    # Explicit projection before iteration: no author, timestamp, after-text or labels.
    projected = {split: dataset[split].select_columns(['project', 'before text']) for split in ('train', 'test')}
    projects = sorted(set(projected['train']['project']) | set(projected['test']['project']))
    ordered = [hashes.text_hash(json.dumps(project, ensure_ascii=False, sort_keys=True)) for project in projects]
    return projected, ordered


def run(output, inputs, config):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    if set(inputs) != {'source_capsule'} or set(config) - {'phase', 'max_new_draws', 'max_wall_seconds'} or config.get('phase') != 'EM1':
        raise ValueError('Exact EM1 contract required')
    manifest = capsule(inputs['source_capsule'])
    binding = hashes.text_hash(json.dumps({'capsule': io.sha(inputs['source_capsule']), 'module': io.sha(__file__),
                                           'hashes': io.sha(hashes.__file__), 'io': io.sha(io.__file__)}, sort_keys=True))
    path = output / 'CHECKPOINT.json'
    state = sealed.state(path, binding, {'pan': {role: [] for role in PAN_ROLES}, 'schola': [], 'cost_prefix_done': False})
    started = time.monotonic(); units = 0
    max_units = int(config.get('max_new_draws', 100)); max_wall = float(config.get('max_wall_seconds', 900))
    if max_units < 1 or max_wall <= 0:
        raise ValueError('Bounded positive checkpoint quantum required')
    def stop():
        return (units >= max_units or time.monotonic() - started >= max_wall
                or any((p / 'YIELD_REQUEST.json').exists() for p in [output, *output.parents[:3]]))
    def pause(phase, completed, total):
        return {'status': 'yielded', 'verified': False, 'phase': phase, 'completed': completed, 'total': total}
    total_pan = sum(len([n for n in manifest['pan'][role]['files'] if Path(n).name.startswith('truth-problem-') and n.endswith('.json')]) for role in PAN_ROLES)
    if total_pan < 1:
        raise ValueError('No original PAN truth/text pairs')
    pilot = max(1, (total_pan + 19) // 20)
    for role in PAN_ROLES:
        spec = manifest['pan'][role]; root = Path(spec['root'])
        names = sorted(n for n in spec['files'] if Path(n).name.startswith('truth-problem-') and n.endswith('.json'))
        for ordinal in range(len(state['pan'][role]), len(names)):
            if stop():
                return pause('pan_fingerprints', sum(map(len, state['pan'].values())), total_pan)
            name = names[ordinal]; truth_path = Path(name)
            text_name = truth_path.with_name(truth_path.name.removeprefix('truth-')).with_suffix('.txt').as_posix()
            if text_name not in spec['files']:
                raise ValueError('PAN truth lacks its pinned text member')
            fingerprint = hashes.pan_fingerprint((root / text_name).read_bytes(), sealed.read(root / name), role + '/' + text_name)
            state['pan'][role].append(fingerprint); units += 1; sealed.checkpoint(path, state)
            completed = sum(map(len, state['pan'].values()))
            io.write_json(output / 'PROGRESS.json', {'phase': 'pan_fingerprints', 'completed': completed, 'total': total_pan})
            if completed == pilot and not state['cost_prefix_done']:
                state['cost_prefix_done'] = True; sealed.checkpoint(path, state)
                return pause('source_cost_prefix', completed, total_pan)
    dataset, ordered_projects = schola_source(manifest['schola'])
    cursor = 0; total = len(dataset['train']) + len(dataset['test'])
    completed = len(state['schola'])
    for split in ('train', 'test'):
        for ordinal in range(len(dataset[split])):
            cursor += 1
            if cursor <= completed:
                continue
            if stop():
                sealed.checkpoint(path, state)
                return pause('schola_fingerprints', len(state['schola']), total)
            state['schola'].append(hashes.schola_fingerprint(dataset[split][ordinal], split, ordinal, manifest['prefix_rule']['characters']))
            if len(state['schola']) % 256 == 0 or len(state['schola']) == total:
                units += 1; sealed.checkpoint(path, state)
                io.write_json(output / 'PROGRESS.json', {'phase': 'schola_fingerprints', 'completed': len(state['schola']), 'total': total})
    sealed.checkpoint(path, state)
    overlaps = {role: hashes.pan_overlap(state['pan'][role], state['pan']['validation_2024']) for role in ('train_2023', 'train_2024')}
    schola = hashes.schola_tables(state['schola'], ordered_projects)
    bundle = output / 'bundle'
    for name in ('pan_style', 'scholawrite'):
        (bundle / name).mkdir(parents=True, exist_ok=True)
    for role in PAN_ROLES:
        io.write_json(bundle / 'pan_style' / (role + '_hashes.json'), state['pan'][role])
    io.write_json(bundle / 'pan_style/OVERLAP.json', overlaps)
    io.write_json(bundle / 'scholawrite/ROW_HASHES.json', state['schola'])
    io.write_json(bundle / 'scholawrite/FOLDS_AND_COUNTS.json', schola)
    source_script = Path(hashes.__file__).read_text('utf8')
    for name in ('pan_style', 'scholawrite'):
        (bundle / name / 'hash_arithmetic.py').write_text(source_script, encoding='utf8', newline='\n')
    pan_summary = ('These materials identify exact content reuse between each named training source and the 2024 hard validation set. '
                   'The tables separate document, stripped-paragraph and ordered-pair hashes, unique values and occurrences, and mismatched pair alignment. '
                   'They do not infer hidden test-set overlap, author identity or any new model performance; L106/L108 remain the historical evidence.')
    schola_summary = ('These materials define the original five-project leave-one-project-out rule on the union of shipped train and test, '
                      'and count exact before-text prefix reuse in each project without author fields, labels or text. '
                      f"The explicit current prefix is {manifest['prefix_rule']['characters']} Unicode code points; "
                      + ('its historical definition was recovered in the pinned owner-reviewed note.' if manifest['prefix_rule']['historical_definition_recovered']
                         else 'the historical L68 prefix width was not recovered, so this does not claim to reproduce its 1,060/1,241 count.'))
    for name, summary in (('pan_style', pan_summary), ('scholawrite', schola_summary)):
        note = ('# Private local correspondence materials\n\n' + summary + '\n\n'
                'Contents are hashes, counts and our audit code only. No third-party text, author field or contact details. '
                'Nothing is sent, published or copied outside this repository by this handler. '
                'Source and attribution remain with the original PAN multi-author analysis data or minnesotanlp/ScholaWrite corpus.\n')
        (bundle / name / 'README.md').write_text(note, encoding='utf8', newline='\n')
        (bundle / name / 'SUMMARY.md').write_text(summary + '\n', encoding='utf8', newline='\n')
    members = {p.relative_to(bundle).as_posix(): io.sha(p) for p in sorted(bundle.rglob('*')) if p.is_file() and p.name != 'MANIFEST.json'}
    io.write_json(bundle / 'MANIFEST.json', {'card': 'EM1', 'source_capsule_sha256': io.sha(inputs['source_capsule']), 'binding': binding,
                 'prefix_rule': {key: value for key, value in manifest['prefix_rule'].items() if key != 'definition_note_path'},
                 'files': members, 'text_included': False, 'transmitted': False})
    result = {'card': 'EM1', 'record_kind': 'run', 'theory_tags': [], 'by_construction': False,
              'complete_materials': True, 'pan_documents': {role: len(state['pan'][role]) for role in PAN_ROLES},
              'schola_rows': len(state['schola']), 'projects': len(ordered_projects), 'historical_prefix_definition_recovered': manifest['prefix_rule']['historical_definition_recovered'],
              'local_only': True, 'sent': False, 'source_capsule_sha256': io.sha(inputs['source_capsule'])}
    io.write_json(output / 'RESULT.json', result); return result


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    output = Path(output); result = run(output / 'independent-replay', inputs, config)
    if result.get('status') == 'yielded':
        return {**result, 'verified': False}
    sealed.replay_bundle(output / 'bundle', output / 'independent-replay/bundle')
    if sealed.read(output / 'RESULT.json') != result:
        raise ValueError('EM1 complete source replay differs')
    return {'verified': True, 'complete_hashes_counts_and_materials_replayed': True}
