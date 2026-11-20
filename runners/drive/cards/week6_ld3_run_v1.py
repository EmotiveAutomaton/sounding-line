"""LD3 native entry points. DESIGN CHECK: freeze the card-specific producer."""
from . import week6_ld3_v1 as producer
from .week6_ld_runtime_v1 import operate


def execute(output, inputs, config):
    return operate("LD3", producer, output, inputs, config, verify=False)


def verify(output, inputs, config):
    return operate("LD3", producer, output, inputs, config, verify=True)
