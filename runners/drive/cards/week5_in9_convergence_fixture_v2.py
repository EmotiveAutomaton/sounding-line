"""Constructed-only IN9 convergence and full successor-boundary qualification."""
from contextlib import contextmanager
from pathlib import Path
import json
import numpy as np
from scipy.special import expit
from . import week5_in9_v2 as study
from . import week5_in9_fixture_v1 as original_fixture


def weighted_case(seed, multiplier):
    """Fixed 720-row, 22-feature near-collinear, unequal-multiplicity world.

    These seeds and multipliers are frozen before execution, never from corpus
    rows or a fitted effect. The high-weight cases probe sum-loss precision.
    """
    rng = np.random.default_rng(seed)
    latent = rng.normal(size=(720, 5))
    raw = np.column_stack([latent[:, j % 5]+1e-7*rng.normal(size=720) for j in range(22)])
    target = (rng.random(720) < expit(.15+.35*latent[:, 0]-.25*latent[:, 1])).astype(float)
    weight = np.resize(np.array([1., 3., 11., 53., 211.]), 720)*multiplier
    center = (raw.T@weight)/weight.sum()
    scale = np.sqrt(np.sum(weight[:, None]*(raw-center)**2, axis=0)/weight.sum())
    design = np.column_stack((np.ones(720), (raw-center)/scale))
    return design, target, weight


@contextmanager
def constructed_source(frame):
    old = study.load
    try:
        identity = study.digest(frame.to_dict(orient='list'))
        study.load = lambda inputs: (frame.copy(), {'constructed_table_digest': identity})
        yield
    finally:
        study.load = old


def child(operation, output, maximum):
    frame = original_fixture.world(0, 200)
    config = {'phase': 'IN9-items', 'draws': 2000, 'max_new_draws': maximum,
              'max_wall_seconds': 150}
    with constructed_source(frame):
        result = getattr(study, operation)(Path(output), {}, config)
    (Path(output)/(operation+'-'+str(maximum)+'-CONTROL.json')).write_text(
        json.dumps(result, sort_keys=True, allow_nan=False)+'\n', encoding='utf8')
    print(json.dumps({'operation': operation, 'status': result.get('status'),
                      'verified': result.get('verified')}, sort_keys=True))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['execute', 'verify'])
    parser.add_argument('output', type=Path)
    parser.add_argument('maximum', type=int)
    args = parser.parse_args()
    child(args.operation, args.output, args.maximum)
