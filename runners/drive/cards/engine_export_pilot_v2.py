"""Prevent script-directory imports in the external pinned exporter interpreter.

DESIGN CHECK (2026-10-18)
Lessons read: LESSONS sections 3-5. Under null and alternative, imports must come
from the pinned environment and explicit engine archive. Failure direction:
refuse changed source or output under the original full handler's gates.
Operational bands exhaustive as before; no scientific or cost change.
The failed native v1 and its source capsule remain untouched.
"""
import os

from . import engine_export_pilot as original

CONSTRUCTED=original.CONSTRUCTED
PILOT=original.PILOT
validate=original.validate


def execute(output,inputs,config):
    os.environ['PYTHONSAFEPATH']='1'
    return original.execute(output,inputs,config)


def verify(output,inputs,config):
    os.environ['PYTHONSAFEPATH']='1'
    return original.verify(output,inputs,config)
