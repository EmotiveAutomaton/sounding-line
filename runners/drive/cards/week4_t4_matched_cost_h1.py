"""T4.h1 generated-label cost on unchanged complete feature geometry.

DESIGN CHECK: LESSONS 3-5 reread for the November 2 T4 build. Under either
generating law, changing only stored human choices cannot change this probe.
Keep all seeds, starts, bounds, original gradient certificates and cost margins.
Incomplete, failed or altered complete-bank dependencies must refuse admission.
This is numerical costing only: no human effect, power or main admission.
"""
from pathlib import Path
from types import FunctionType, SimpleNamespace
from . import week4_t4_matched_cost as original
from . import week4_t4_kernel_h1 as kernel
from .timing_pmap_source import completed
from .timing_p6 import read


def configuration(mode):
    return dict(original.configuration(mode), card='T4.h1-matched-cost',
                runtime_versions=kernel.configuration('constructed')['runtime_versions'])


def load(inputs):
    if set(inputs) != {'inputs_completion', 'bank_completion', 'kernel_completion'}:
        raise ValueError('Original and complete kernel validation dependencies required')
    path = Path(inputs['kernel_completion'])
    completed(path, path.parent/'PLAN.json')
    completed(path, path.parent/'output/SUMMARY.json')
    plan = read(path.parent/'PLAN.json')
    summary = read(path.parent/'output/SUMMARY.json')
    if (plan['module'] != 'runners.drive.cards.week4_t4_kernel_h1'
            or plan['config'] != kernel.configuration('full')
            or not summary['complete_bank'] or not summary['bank_gate']
            or summary['worlds'] != 40):
        raise ValueError('Complete unchanged T4.h1 recovery validation required')
    return original.load({k: inputs[k] for k in ('inputs_completion', 'bank_completion')})


# Preserve the admitted source packing, generating laws, seeds, complete fresh
# refitting and accounting code. Only selected fitting callbacks change; those
# additionally check each solution with the retained original implementation.
run = FunctionType(original.run.__code__, dict(original.__dict__,
    configuration=configuration, load=load, model=SimpleNamespace(fit=kernel.fit)),
    'run', original.run.__defaults__)


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, True)
