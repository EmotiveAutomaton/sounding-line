"""IN16 additive numerical repair. DESIGN CHECK: IN16_REML_REPAIR_V1.md."""
from . import week6_in16_run_repair_v1 as run


def execute(output, inputs, config):
    return run.execute('IN16', output, inputs, config)


def verify(output, inputs, config):
    return run.verify('IN16', output, inputs, config)
