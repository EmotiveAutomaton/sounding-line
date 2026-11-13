"""Versioned SG1 input bridge for unchanged carried CH6 and CH7 consumers.

DESIGN CHECK: no mathematical replacement. Child-local callable bindings are
restored in finally; sqlite is never monkeypatched. Source bytes remain immutable.
Source compatibility does not waive the remaining full CH7 numerical review.
"""
from contextlib import contextmanager
from pathlib import Path
from . import week5_sg1_source_v1 as source
from . import week5_ch7_v1 as ch7
from . import week5_ch_analysis_bounded as ch6
from . import week5_ch_histories as histories
from . import week5_ch_pipeline_checkpoint as ck
from .week5_ch_source import digest, write_json

ORIGINAL_CH7_IDENTITY = ch7.identity
ORIGINAL_CH6_SEMANTIC = ch6.semantic
ORIGINAL_CH7_ANALYZE = ch7.analyze


def activation():
    return [dict(channel='SHAME', set_point='seen as competent, game-rating analogy only',
                 moved='public rating relative to the card reference',
                 could_do='play another game or end the observed session',
                 observed='complete behavioral estimates in this result',
                 relation='says nothing about identifying a channel from game behavior')]


def ch7_analyze(*args, **kwargs):
    result = ORIGINAL_CH7_ANALYZE(*args, **kwargs)
    result['activation'] = activation()
    return result


def ch7_identity(inputs, config):
    # Validate every original numerical control using its fixture input shape;
    # then bind the complete actual SG1 inputs without weakening those controls.
    allowed = {'draws', 'null_draws', 'floor', 'constructed_fixture', 'max_new_draws'}
    if set(config) - allowed:
        raise ValueError('Unknown carried CH7 configuration')
    original_inputs = {'histories': inputs['histories']}
    if not config.get('constructed_fixture'):
        original_inputs.update({key: inputs[key] for key in ('index', 'source_seal')})
    ORIGINAL_CH7_IDENTITY(original_inputs, config)
    return ck.binding(inputs, config, dict(bridge=digest(__file__),
        original_ch7=digest(ch7.__file__), original_math=digest(ch7.m.__file__),
        sg1=digest(source.__file__)))


def ch6_semantic(inputs, config):
    value = ORIGINAL_CH6_SEMANTIC(inputs, config)
    value['sg1_bridge_sha256'] = digest(__file__)
    value['sg1_source_sha256'] = digest(source.__file__)
    return value


def ch6_body(output, inputs, config):
    if config.get('card') != 'CH6':
        raise ValueError('This source bridge carries CH6 only')
    allowed = {'card','gap_minutes','time_control','year','draws','floor','streak',
               'constructed_fixture','max_new_draws'}
    if set(config) - allowed:
        raise ValueError('Unknown carried CH6 configuration')
    if not config.get('constructed_fixture') and config.get('draws',2000) != 2000:
        raise ValueError('CH6 retains 2000 whole-player resamples')
    path = source.authenticate_consumer(inputs, config, Path(output))
    with source.HistoryStore(path, bool(config.get('constructed_fixture'))) as store:
        result = histories.stopping(store, config.get('gap_minutes',30),
            config.get('time_control'), config.get('year'), config.get('draws',2000),
            config.get('floor',10000), config.get('streak',False))
    result['constructed_fixture'] = bool(config.get('constructed_fixture'))
    result['activation'] = activation()
    write_json(Path(output)/'SCIENCE.json',result)
    return dict(status='complete',card='CH6')


@contextmanager
def adapted(card):
    if card == 'CH7':
        prior = ch7.identity, ch7.authenticate, ch7.HistoryStore, ch7.analyze
        ch7.identity, ch7.authenticate, ch7.HistoryStore = ch7_identity, source.authenticate_consumer, source.HistoryStore
        ch7.analyze = ch7_analyze
        try:
            yield ch7
        finally:
            ch7.identity, ch7.authenticate, ch7.HistoryStore, ch7.analyze = prior
    elif card == 'CH6':
        prior = ch6.semantic, ch6.body
        ch6.semantic, ch6.body = ch6_semantic, ch6_body
        try:
            yield ch6
        finally:
            ch6.semantic, ch6.body = prior
    else:
        raise ValueError('Only carried CH6 and CH7 are admitted by this bridge')


def execute(output,inputs,config):
    card = config['card']
    controls = {k:v for k,v in config.items() if k != 'card'} if card == 'CH7' else config
    with adapted(card) as module:
        return module.execute(output,inputs,controls)


def verify(output,inputs,config):
    card = config['card']
    controls = {k:v for k,v in config.items() if k != 'card'} if card == 'CH7' else config
    with adapted(card) as module:
        return module.verify(output,inputs,controls)
