"""Known-answer CPU fixture for the actual B01 queue; never a scientific source.

DESIGN CHECK: B01/X05/X12; LESSONS 3--5, CONTROLS 6--7.
NULL: requested scientific output or changed fixture identity refuses. ALTERNATIVE:
fixed positive, negative and centered-equivalence forecast grids traverse the real
producer/consumer boundary, with synthetic seed identities explicitly labeled.
All source roles are pilot fixtures; no model is trained or called, no reserve
payload exists and no fixture output can satisfy discovery-role validation.
"""
import argparse
import math
import time
from pathlib import Path

from .common import ROOT, Units, digest, freeze
from .queue import inside, writer
from .revision_predictions import sources, reentry, finish
from .training_jobs import cell_identity


def run(directory, seed):
    start, cpu = time.monotonic(), time.process_time()
    directory = inside(directory)
    if not directory.is_relative_to(ROOT / 'private/confirmation-freeze-pilots'):
        raise ValueError('confirmation fixtures cannot enter a scientific namespace')
    if type(seed) is not int or seed not in (9001, 9002, 9003):
        raise ValueError('only fixed known-answer seed identities are supported')
    fit_sha = digest(['synthetic-seed-binding-only', seed])
    identity = {'cell_identity': cell_identity(), 'operation': 'confirmation-known-answer-fixture-v1',
                'role': 'pilot', 'scope': 'pilot', 'source': sources(),
                'seed': seed, 'training_complete_sha256': fit_sha,
                'synthetic_seed_metadata': True, 'models_trained_or_called': False}
    with writer(directory):
        Units(directory, identity)
        prior = reentry(directory, identity)
        if prior is not None:
            return prior
        outputs = ['IDENTITY.json', 'PACKAGE.json', 'GATES.json']
        freeze(directory / 'PACKAGE.json', {'kind': 'known-answer probability table',
            'scope': 'pilot only', 'models_trained_or_called': False})
        freeze(directory / 'GATES.json', {'known_fixture': True, 'should_refuse': False,
            'scientific_admission': False})
        freeze(directory / 'TRAINING.json', {'seed': seed,
            'training_complete_sha256': fit_sha, 'synthetic_seed_metadata': True,
            'models_trained_or_called': False, 'scientific_admission': False})
        outputs.append('TRAINING.json')
        shift = {9001: -.02, 9002: 0., 9003: .02}[seed]
        for kind, center in [('positive', .1), ('negative', -.1), ('equivalence', 0.)]:
            rows = []
            for i, delta in enumerate((-.1, 0., .1)):
                # Seed shifts average out within every unit; unequal target
                # counts must not change the equal-source-unit variance.
                for target in range(i + 1):
                    difference = center + delta + shift
                    p = .5 * math.exp(difference)
                    rows.append({'unit': 'fixture-u' + str(i), 'target': str(target), 'truth': 'a',
                        'valid': True, 'left': {'a': p, 'b': 1 - p}, 'right': {'a': .5, 'b': .5}})
            name = kind + '.json'
            freeze(directory / name, rows)
            outputs.append(name)
        return finish(directory, identity, start, cpu, outputs, known_fixture=True,
                      models_trained_or_called=False, scientific_admission=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seed', type=int, required=True)
    args = parser.parse_args()
    run(args.output, args.seed)
