"""Normalize serialized input paths for the unchanged MD3 qualification.

DESIGN CHECK: LESSONS 3-5. JSON plan paths must reach the original Path-only
hash reader unchanged in meaning. Signed/null gates, complete banks and replay
are inherited verbatim. Bad hashes and malformed contracts must still refuse.
"""
from pathlib import Path
from . import week5_md3_followup_fixture_v2 as original

bank_census = original.bank_census


def execute(output, inputs, config):
    return original.execute(output, {key: Path(value) for key, value in inputs.items()}, config)


def verify(output, inputs, config):
    return original.verify(output, {key: Path(value) for key, value in inputs.items()}, config)
