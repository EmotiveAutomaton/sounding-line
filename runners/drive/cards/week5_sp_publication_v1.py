"""Comfort handlers with the qualified UUID JSON publication convention.

DESIGN CHECK: LESSONS 3-5. The complete existing estimator and verifier run
unchanged. Only their two explicit JSON writers are adapted in this child.
Signed/null controls and full-grid equality gate human admission.
"""
from . import week5_sp as core
from . import week5_sp1_h2 as location
from . import week5_sp_analysis_h1 as analysis
from . import week5_qualification_io as publication


def handler(config):
    if config.get('phase') not in ('SP1', 'SP2', 'SP3'):
        raise ValueError('Only the existing comfort analyses are admitted')
    return location if config['phase'] == 'SP1' else analysis


def execute(output, inputs, config):
    with publication.publication([(core, 'write'), (location, 'write')]):
        return handler(config).execute(output, inputs, config)


def verify(output, inputs, config):
    with publication.publication([(core, 'write'), (location, 'write')]):
        return handler(config).verify(output, inputs, config)
