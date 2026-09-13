"""Source-bound earlier-draft effort input projection; evaluation answers stay sealed.

DESIGN CHECK: LESSONS3-5. Under NULL/ALTERNATIVE identical public rosters and
writer/event groups persist. Altered source bytes refuse. Only a complete
development producer may trigger the separate development outcome join.
"""
from pathlib import Path
import hashlib
from .contracts import digest
from .queue import read
from .ollama import write_new

FIELDS = ('task_id', 'writer_component', 'prompt_component', 'source_event')

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def verify(prepared):
    frozen = read(prepared/'FROZEN.json')
    for path, expected in frozen.get('source_pins', {}).items():
        if sha(path) != expected:
            raise ValueError('earlier-effort original source changed')
    return frozen

def prepare(source, output):
    frozen = read(source/'FROZEN.json')
    ids = read(source/'IDENTITIES.json')
    if digest(ids) != frozen['identities_sha256']:
        raise ValueError('earlier identities changed')
    original = Path(frozen['original_root'])
    original_frozen = read(original/'FROZEN.json')
    if digest(original_frozen) != frozen['original_frozen_sha256']:
        raise ValueError('original cohort changed')
    records = {}
    for phase in ('train', 'development', 'evaluation'):
        public = read(source/(phase+'-public.json'))
        if digest(public) != frozen['public_sha256'][phase] or {r['task_id'] for r in ids[phase]} != {r['task_id'] for r in public['tasks']}:
            raise ValueError('earlier public/identity join changed')
        records[phase+'-public.json'] = public
        if phase == 'train':
            labels = read(source/'train-evaluator.json')
            if digest(labels) != frozen['evaluator_sha256']['train']:
                raise ValueError('training outcomes changed')
        else:
            labels = {'targets': [{k: r[k] for k in FIELDS} for r in ids[phase]],
                      'scope': 'identity-only projection; target answers deliberately absent'}
        records[phase+'-evaluator.json'] = labels
    paths = [source/'FROZEN.json', source/'IDENTITIES.json', original/'FROZEN.json', original/'development-evaluator.json', original/'evaluation-evaluator.json']
    paths += [source/(p+'-public.json') for p in ('train', 'development', 'evaluation')]
    paths += [source/'train-evaluator.json']
    result = {'schema': 'stage10.earlier-effort-inputs.1', 'source_root': str(source), 'original_root': str(original),
              'source_pins': {str(p): sha(p) for p in paths},
              'public_sha256': {p: digest(records[p+'-public.json']) for p in ('train', 'development', 'evaluation')},
              'evaluator_sha256': {p: digest(records[p+'-evaluator.json']) for p in ('train', 'development', 'evaluation')},
              'scope': 'unchanged earlier-draft cohort; identity-only evaluation file; development answers joined only after complete producer',
              'original_exclusions': frozen['exclusions']}
    records['FROZEN.json'] = result
    for name, value in records.items():
        p = output/name
        if p.exists():
            if read(p) != value:
                raise ValueError('earlier-effort preparation changed')
        else:
            write_new(p, value)
    return result

def development_labels(prepared):
    frozen = verify(prepared)
    if frozen.get('schema') != 'stage10.earlier-effort-inputs.1':
        # Known-answer fixture protocol; it is never literal-pilot admission.
        labels = read(prepared/'development-evaluator.json')
        if digest(labels) != frozen['evaluator_sha256']['development']:
            raise ValueError('development fixture changed')
        return labels
    source = Path(frozen['source_root']); original = Path(frozen['original_root'])
    labels = read(original/'development-evaluator.json')
    original_frozen = read(original/'FROZEN.json')
    if digest(labels) != original_frozen['evaluator_sha256']['development']:
        raise ValueError('original development outcomes changed')
    original_rows = {r['task_id']: r for r in labels['targets']}
    if len(original_rows) != len(labels['targets']):
        raise ValueError('duplicated original development target')
    rows = []
    for identity in read(source/'IDENTITIES.json')['development']:
        label = original_rows[identity['original_task_id']]
        if any(label[k] != identity[k] for k in FIELDS[1:]):
            raise ValueError('development original group join changed')
        rows.append({**label, 'task_id': identity['task_id']})
    return {'targets': rows}
