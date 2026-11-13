"""Constructed metadata/correspondence fixture; no archive or third-party text."""
from pathlib import Path
import json
from . import week5_em1 as study


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf8')


def prepare(root):
    root = Path(root); manifest = {'schema': 'EM1-LOCAL-1', 'pan': {}}
    for role in study.PAN_ROLES:
        folder = root / role; folder.mkdir(parents=True)
        for index in range(3):
            # One copy crosses 2023 -> validation; 2024 train differs.
            text = 'First constructed paragraph\nSecond constructed paragraph' if index == 0 and role != 'train_2024' else f'{role} {index} A\n{role} {index} B'
            (folder / f'problem-{index}.txt').write_text(text, encoding='utf8')
            write(folder / f'truth-problem-{index}.json', {'changes': [0]})
        manifest['pan'][role] = {'root': str(folder.resolve()), 'files': {p.name: study.io.sha(p) for p in folder.iterdir()}}
    schola = root / 'schola'; schola.mkdir(); write(schola / 'constructed.json', {'constructed': True})
    manifest['schola'] = {'root': str(schola.resolve()), 'files': {'constructed.json': study.io.sha(schola / 'constructed.json')}}
    note = root / 'prefix-note.json'
    write(note, {'characters': 8, 'historical_definition_recovered': False, 'meaning': 'constructed fixture only'})
    manifest['prefix_rule'] = {'characters': 8, 'historical_definition_recovered': False,
                               'definition_note_path': str(note.resolve()), 'definition_note_sha256': study.io.sha(note)}
    path = root / 'capsule.json'; write(path, manifest)
    dataset = {split: [{'project': project, 'before text': f'prefix-{project} {split} {i}'} for project in range(5) for i in range(4)]
               for split in ('train', 'test')}
    order = [study.hashes.text_hash(json.dumps(i)) for i in range(5)]
    return path, dataset, order


def chain(root, monkeypatch):
    root = Path(root); capsule, dataset, order = prepare(root / 'source')
    monkeypatch.setattr(study, 'schola_source', lambda spec: (dataset, order))
    config = {'phase': 'EM1', 'max_new_draws': 100, 'max_wall_seconds': 60}
    results = []
    for _ in range(4):
        result = study.execute(root / 'run', {'source_capsule': str(capsule)}, config)
        results.append(result)
        if result.get('status') != 'yielded':
            break
    for _ in range(4):
        proof = study.verify(root / 'run', {'source_capsule': str(capsule)}, config)
        results.append(proof)
        if proof.get('verified') is True:
            break
    return root / 'run', result, proof, results
