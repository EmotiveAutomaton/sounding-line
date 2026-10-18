"""Authenticate the failed D14 pilot and preserve its extraction checkpoints."""
from pathlib import Path
from .events_p5 import read, filehash
from .events_d14 import BASE_INPUTS, load, complete
from .events_d14_features import pilot_writers

EXTRA_INPUTS = {'failed_plan', 'failed_binding', 'failed_receipt'}


def authenticate(inputs, config, writers=None, verified_pins=None):
    root = Path(inputs['failed_plan']).resolve().parent
    if Path(inputs['failed_binding']).resolve() != root / 'output/INPUTS.json' or Path(inputs['failed_receipt']).resolve() != root / 'FAILED.json':
        raise ValueError('failed attempt references do not share an exact root')
    plan, binding, failure = (read(inputs[name]) for name in ('failed_plan', 'failed_binding', 'failed_receipt'))
    expected_inputs = {k: inputs[k] for k in BASE_INPUTS}
    if plan['module'] != 'runners.drive.cards.events_d14' or plan['inputs'] != expected_inputs or plan['config'] != dict(config, phase='pilot'):
        raise ValueError('failed pilot method/input identity differs')
    if binding['paths'] != expected_inputs or binding['config'] != plan['config'] or failure.get('status') != 'FAILED':
        raise ValueError('failed pilot binding/status differs')
    if (root / 'output/SUMMARY.json').exists():
        raise ValueError('completed original pilot is never replaced')
    # Preserve and authenticate old source/input pins, including failed source.
    verified_pins = verified_pins or {}
    for path, expected in {**plan['pins'], **binding['pins']}.items():
        if verified_pins.get(path, expected) != expected or (path not in verified_pins and filehash(path) != expected):
            raise ValueError('failed pilot frozen source/input changed')
    selection = read(root / 'output/SELECTION.json')
    writers = sorted(writers if writers is not None else {s['writer'] for s in read(inputs['sessions'])})
    if selection['full_writers'] != writers or selection['selected_writers'] != pilot_writers(writers, config['seed']):
        raise ValueError('failed pilot writer selection differs')
    checkpoints = {}
    for writer in selection['selected_writers']:
        path = root / 'output/writers' / (writer + '.json')
        if complete(path):
            digest = filehash(path)
            if path.with_name(path.name + '.sha256').read_text(encoding='ascii').strip() != digest:
                raise ValueError('failed extraction checkpoint seal differs')
            checkpoints[writer] = dict(path=str(path), sha256=digest,
                seal_sha256=filehash(path.with_name(path.name + '.sha256')))
    receipt = dict(failed_plan=str(Path(inputs['failed_plan'])), failed_plan_sha256=filehash(inputs['failed_plan']),
        failed_binding_sha256=filehash(inputs['failed_binding']), failed_receipt_sha256=filehash(inputs['failed_receipt']),
        original_plan_pins=plan['pins'], original_input_pins=binding['pins'],
        selected_writers=selection['selected_writers'], reusable_checkpoints=checkpoints,
        repair='Copy authenticated parent end_at onto per-menu session_end before the unchanged D1 prefix feature helper',
        scientific_change=False, original_attempt_retained=True)
    return receipt, checkpoints
