"""Commissioned 0045 duration description with separate full-source replay.

DESIGN CHECK: LESSONS 3-5. Null and alternative have identical descriptive
handling; there is no hypothesis threshold. Invalid units, changed metadata or
source bytes, incomplete execution and changed replay refuse. Literal minutes,
zero values and the untrimmed distribution are retained. No group/trait fields.
"""
from pathlib import Path
import time
from . import es_core_v1 as core, es_source_v1 as source, es_clock_v1 as clock
from . import es_handler_v1 as io, week6_es_v1 as base

LAYOUT = {'status': 'OWNER_REVIEWED', 'duration_unit': 'minutes',
          'duration_kind': 'self-estimated-current-state', 'group_or_trait_analysis': False}


def load(inputs, config):
    intake, panel = base.load(inputs, config)
    core.need(set(config) == {'panel_config', 'max_wall_seconds'}, 'duration operational fields differ')
    core.need(set(panel) == {'member', 'card', 'panel', 'source_pin', 'missing_tokens',
                             'source_layout_review'}, 'duration panel fields differ')
    core.need(panel['member'] == '0045' and panel['card'] == 'ES3' and
              panel['panel'] == 'duration_minutes', 'duration panel scope differs')
    core.need(panel['source_layout_review'] == LAYOUT, 'duration measure or scope differs')
    core.need(panel['source_pin'] == intake['members']['0045']['raw_ts_pin_from_receipt_only'],
              'duration source metadata differs')
    core.need(intake['members']['0045']['classification'] == 'open-tests-only' and
              intake['members']['0045']['licence']['name'] == 'CC-BY-NC-4.0', 'duration handling differs')
    core.need(type(panel['missing_tokens']) is list and all(type(x) is str for x in panel['missing_tokens']),
              'explicit duration missing tokens required')
    wall = config['max_wall_seconds']
    core.need(type(wall) in (int, float) and 0 < wall <= 1500, 'duration wall cap differs')
    return intake, panel


def operation(output, inputs, config, phase):
    core.need(phase in ('execute', 'verify'), 'duration phase differs')
    output = Path(output)
    if phase == 'verify':
        core.need((output/'execute/ENGINE_RESULT.json').is_file(), 'complete execute required before duration replay')
    intake, panel = load(inputs, config)
    output.mkdir(parents=True, exist_ok=True)
    if phase == 'execute':
        base.preserve_inherited_yield(output)
    started = time.monotonic()
    def guard():
        if (output/'STOP_REQUEST.json').exists() or (output/'YIELD_REQUEST.json').exists() or time.monotonic()-started >= config['max_wall_seconds']:
            raise io.Pause('duration cooperative yield')
    files = [Path(m.__file__) for m in (core, source, clock, io, base)]+[Path(__file__)]
    binding = io.digest({'panel': panel, 'intake': intake,
                         'code': {p.name: source.sha256(p) for p in files}})
    root = output/phase
    root.mkdir(exist_ok=True)
    io.exclusive_json(root/'BINDING.json', {'binding': binding, 'phase': phase})
    try:
        guard()
        frames = clock.selected_frames(inputs['source_path'], panel['source_pin'], '0045', 'duration0045', guard)
        summary = clock.duration_description(frames, panel['missing_tokens'])
        guard()
        result = {'status': summary['status'], 'binding': binding, 'summary': summary,
                  'bootstrap_draws': 0, 'decision_bar': None, 'verified': False,
                  'attribution': intake['members']['0045']['licence']['attribution']}
        io.exclusive_json(root/'SUMMARY.json', summary)
        io.exclusive_json(root/'ENGINE_RESULT.json', result)
    except io.Pause:
        return {'status': 'yielded', 'verified': False, 'operation': phase, 'scientific_result_complete': False}
    if phase == 'execute':
        return {'status': 'computed', 'verified': False, 'engine': result, 'requires_fresh_replay': True}
    first = output/'execute'
    core.need(io.read_json(first/'BINDING.json') == {'binding': binding, 'phase': 'execute'}, 'duration execute binding differs')
    for name in ('SUMMARY.json', 'ENGINE_RESULT.json'):
        core.need(io.read_json(first/name) == io.read_json(root/name), 'duration complete replay differs')
    return {'status': 'verified', 'verified': True, 'numerical_replay': True,
            'native_proof_required_from_runtime': True, 'engine_status': summary['status']}


def execute(output, inputs, config):
    return operation(output, inputs, config, 'execute')


def verify(output, inputs, config):
    return operation(output, inputs, config, 'verify')
