"""Constructed-only TR1 checks. No real source, fit, or qualification admission.

The parent authenticity boundary is explicitly substituted by a sealed local
constructed task; the actual production state machine and full 2,000-draw
execute/verify path are exercised. Native runtime qualification is not claimed.
"""
from contextlib import contextmanager
from pathlib import Path
import numpy as np
from . import week5_tr1 as study
from . import week5_tr1_math as math


def constructed_task(path, people=32, plays=3):
    rng = np.random.default_rng(8513)
    rows = np.zeros((people * plays, 30, 15))
    rows[:, :, 0] = np.arange(1, 31)
    rows[:, :, 2] = 1; rows[:, :, 3] = 10; rows[:, :, 4] = -10
    rows[:, :, 6] = rng.random((len(rows), 30)) > .25
    endpoints = np.where(rng.random((len(rows), 30)) > .5, 10, -10)
    rows[:, :, 7] = np.where(rows[:, :, 6], endpoints, 1)
    rows[:, :, 9] = np.nan
    indices = np.array([0, 2, 5, 8, 11, 14, 17, 20, 23, 26, 28, 29])
    rows[:, indices, 9] = 50
    x, _, _ = math.recent_luck(rows)
    personal = rng.normal(.5, .25, people)
    gain = np.repeat(personal, plays) + rng.normal(0, .1, len(rows))
    noise = rng.normal(0, 3, x.shape)
    rows[:, indices, 9] = 50 + gain[:, None] * x + noise
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        np.savez_compressed(stream, plays=rows, person=np.repeat(np.arange(people), plays),
            counter=np.tile(np.arange(1, plays + 1), people), day=np.tile(np.array([0., 2., 10.])[:plays], people),
            repeat_eligible=np.ones(len(rows), bool))
    return path


@contextmanager
def source_boundary(task):
    prior = study.authenticate
    try:
        study.authenticate = lambda inputs: (Path(task), {'constructed_task': study.io.sha(task), 'implementation': study.dependencies()})
        yield
    finally:
        study.authenticate = prior


def complete_chain(output, task, config=None):
    config = config or {'phase': 'TR1', 'draws': 2000, 'max_new_draws': 2000, 'max_wall_seconds': 150}
    output = Path(output)
    terminals = []
    with source_boundary(task):
        for attempt in range(12):
            result = study.execute(output, {}, config); terminals.append(result.get('status', 'complete'))
            if result.get('status') != 'yielded':
                break
        else:
            raise AssertionError('Constructed execution did not finish in its bounded chain')
        for attempt in range(12):
            proof = study.verify(output, {}, config); terminals.append(proof.get('status', 'verified'))
            if proof.get('verified') is True:
                break
        else:
            raise AssertionError('Constructed verification did not finish')
    return result, proof, terminals
