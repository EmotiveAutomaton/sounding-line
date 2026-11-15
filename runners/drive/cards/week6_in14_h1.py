"""IN14 .h1 entry: identical science with the isolated independent FWL replay."""
from . import week6_in14_run_h1 as run


def execute(output, inputs, config):
    return run.execute('IN14', output, inputs, config)


def verify(output, inputs, config):
    return run.verify('IN14', output, inputs, config)
