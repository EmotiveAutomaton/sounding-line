"""Generic AT-FP64-1 scorer under the reviewed native precision guard.

DESIGN CHECK: LESSONS 3-5. Resource refusal/yield is identical under any
scientific outcome. The guard's actual native identity, 26-GiB commit and
20-GiB RAM start thresholds, seven-GiB requests and six-GiB hard floors remain
unchanged. These conservative first-qualification thresholds do not measure
any reader's peak. Owner admission and measured per-model costs remain needed.
"""
from types import FunctionType
from . import week5_at_precision_guard as guard
from . import week5_at_scoring_v5 as scorer

LIMITS = guard.LIMITS
NUMERICAL_SPEC = scorer.NUMERICAL_SPEC
memory = guard.memory
load_model = scorer.load_model


def invoke(output, inputs, config, verifying):
    # A private function namespace preserves the exact v5/v4 numerical code;
    # constructed fixtures may supply their actual tiny loader without changing
    # any frozen scoring module's implementation or a production manifest.
    fn = FunctionType(scorer.score_batch.__code__,
                      dict(scorer.score_batch.__globals__, load_model=load_model),
                      scorer.score_batch.__name__, scorer.score_batch.__defaults__,
                      scorer.score_batch.__closure__)
    fn.__kwdefaults__ = scorer.score_batch.__kwdefaults__
    return fn(output, scorer.gzread(inputs['rows']), scorer.read(inputs['model_manifest']),
              verifying=verifying, **config)


def run(output, inputs, config, verifying=False):
    if set(inputs) != {'rows', 'model_manifest'}:
        raise ValueError('Exact generic scoring inputs required')
    if set(config) - {'context', 'context_length', 'max_wall_seconds'}:
        raise ValueError('Unknown generic scoring configuration')
    fn = FunctionType(guard.run.__code__,
                      dict(guard.run.__globals__, invoke=invoke, memory=memory),
                      guard.run.__name__, guard.run.__defaults__, guard.run.__closure__)
    return fn(output, inputs, config, verifying)


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, True)
