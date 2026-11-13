"""R3 production adapter for the already qualified MD3.s handler only.

DESIGN CHECK: LESSONS 3-5. Match the qualified fixture's Path normalization,
UUID JSON publication and sealed numerical writes without changing any fit,
source, reference, draw, support rule or verification comparison.
"""
from contextlib import contextmanager
from pathlib import Path
from . import week5_md3_followup as study
from . import week5_qualification_io as publication


@contextmanager
def compatibility():
    prior = study.core.sha
    try:
        study.core.sha = lambda path: prior(Path(path))
        with publication.publication([(study.core, 'save_json')], [(study, 'save_fit')]):
            yield
    finally:
        study.core.sha = prior


def contract(inputs, config):
    if config.get('phase') != 'MD3.s':
        raise ValueError('R3 releases MD3.s only; MD3.m/MD3.p are not admitted here')
    if set(inputs) != {'task', 'parent_run'}:
        raise ValueError('Exact original MD3.s production inputs required')
    return {key: Path(value) for key, value in inputs.items()}


def execute(output, inputs, config):
    paths = contract(inputs, config)
    with compatibility():
        return study.execute(Path(output), paths, config)


def verify(output, inputs, config):
    paths = contract(inputs, config)
    with compatibility():
        return study.verify(Path(output), paths, config)
