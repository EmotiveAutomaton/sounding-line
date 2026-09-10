"""Publish verified existing discarded inputs for the complete B01/B02 rehearsal.

DESIGN CHECK: B01/B02/X01/X12; LESSONS 3--5, CONTROLS 6--7.
NULL: changed historical predictions, fitting or the preselected contrast refuse.
ALTERNATIVE: the same complete pilot forecasts and actual numerical fitting receipt
are bound as current queue outputs without refitting or calling a reader. This
producer never opens the separately allocated rehearsal payloads and cannot publish
scientific discovery. All inputs are previously exposed discarded pilot evidence.
"""
import argparse
from pathlib import Path
import time

from .artifact_analysis import load_complete
from .artifact_comparisons import model_inputs
from .common import REPO, ROOT, Units, digest, file_hash, freeze
from .launch import checked
from .queue import inside, writer
from .revision_predictions import finish, reentry, sources
from .training_jobs import cell_identity


def run(directory, specification):
    start, cpu = time.monotonic(), time.process_time()
    directory, specification = map(inside, (directory, specification))
    if not directory.is_relative_to(ROOT / 'private/confirmation-execution-pilots'):
        raise ValueError('historical confirmation rehearsal inputs cannot enter science')
    from .common import read
    spec = read(specification)
    if set(spec) != {'predictions', 'models', 'analysis_plan'}:
        raise ValueError('exact historical input pointers required')
    for pointer in spec.values():
        checked(pointer)
    rows, expected, previous_identity, previous_done = load_complete((REPO / spec['predictions']['path']).parent, 'pilot')
    models = model_inputs((REPO / spec['models']['path']).parent, 'pilot')
    if models['completion_sha256'] != previous_identity['model_completion_sha256']:
        raise ValueError('historical predictions came from another fitting package')
    analysis = checked(spec['analysis_plan'])
    if analysis['role'] != 'pilot' or analysis['operation'] != 'evaluate' or len(analysis['contrasts']) != 1:
        raise ValueError('one previously fixed pilot contrast required')
    contrast = analysis['contrasts'][0]
    if any(set(contrast[side]) != {'query', 'model'} for side in ('left', 'right')):
        raise ValueError('rehearsal cannot choose a new score-selected comparator')
    projected = []
    for row in rows:
        item = {'unit': row['unit'], 'target': 'next_recorded_event', 'truth': row['truth'], 'valid': True}
        for name in ('left', 'right'):
            side = contrast[name];cell = row['rows'][side['query']]
            if cell['validity'][side['model']] is not True:
                raise ValueError('original required baseline forecast failed')
            item[name] = cell['predictions'][side['model']]
        projected.append(item)
    identity = {'cell_identity': cell_identity(), 'operation': 'confirmation-rehearsal-inputs-v1',
        'scope': 'pilot', 'role': 'pilot', 'source': sources(), 'specification_sha256': file_hash(specification),
        'prior_prediction_identity_sha256': digest(previous_identity), 'assigned_units': expected}
    with writer(directory):
        Units(directory, identity)
        prior = reentry(directory, identity)
        if prior is not None:
            return prior
        freeze(directory / 'FORECASTS.json', projected)
        freeze(directory / 'GATES.json', {'fixture_inputs_validated': True, 'scientific_admission': False,
                                         'scope': 'existing discarded inputs only'})
        # Include the actual original completion as a hashed output reference;
        # do not copy or relabel fitting parameters as newly trained evidence.
        return finish(directory, identity, start, cpu,
            ['FORECASTS.json', 'GATES.json', str(REPO / spec['models']['path'])],
            models_trained_or_called=False, source_role='previously exposed pilot', assigned_units=len(expected))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--specification', type=Path, required=True)
    args = parser.parse_args()
    run(args.output, args.specification)
