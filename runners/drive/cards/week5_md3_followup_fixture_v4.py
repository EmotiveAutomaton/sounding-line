"""Path-compatible byte hashing throughout the unchanged MD3 fixture.

DESIGN CHECK: LESSONS 3-5. Both serialized inputs and internal __file__ strings
must hash the exact original bytes. Changed bytes still refuse. All statistical
null/alternative decisions and complete-bank verification remain inherited.
"""
from contextlib import contextmanager
from pathlib import Path
from . import week5_md as core
from . import week5_md3_followup_fixture_v3 as original

bank_census = original.bank_census


@contextmanager
def path_hashing():
    prior = core.sha
    try:
        core.sha = lambda path: prior(Path(path))
        yield
    finally:
        core.sha = prior


def execute(output, inputs, config):
    with path_hashing():
        return original.execute(output, inputs, config)


def verify(output, inputs, config):
    with path_hashing():
        return original.verify(output, inputs, config)
