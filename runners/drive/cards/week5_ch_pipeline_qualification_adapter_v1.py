"""Constructed-only transactional pause wrapper over immutable CH adapters.

This is qualification instrumentation, never a human source handler. It pauses
after an actual committed execute transaction, then after an actual fresh verify
transaction in the next attempt. The final attempt verifies again from zero.
"""
from pathlib import Path
import json
from . import week5_ch_pipeline_checkpoint as checkpoint
from . import week5_ch_merge_bounded as merge
from . import week5_ch_sample_bounded as sample
from . import week5_ch_history_index_bounded as history
from . import week5_ch_pipeline_bounded_fixture as frozen_fixture
from .week5_ch_census_replay import compare
from .timing_pmap_source import completed
from .batch_runtime import read, filehash, freeze

MODULE = 'runners.drive.cards.week5_ch_pipeline_qualification_adapter_v1'
COMPONENTS = {'merge': merge, 'sample': sample, 'history': history}


class PilotPause(Exception):
    def __init__(self, receipt):
        self.receipt = receipt


def fixture_inputs(inputs, config):
    if set(inputs) != {'fixture_completion'}:
        raise ValueError('Only an authenticated constructed fixture is accepted')
    component = config.get('component')
    if config != dict(constructed_fixture=True, component=component, max_new_draws=1000000000) or component not in COMPONENTS:
        raise ValueError('Fixed constructed qualification contract required')
    complete = Path(inputs['fixture_completion']).resolve()
    proof_path, plan_path = complete.parent/'output/FIXTURE.json', complete.parent/'PLAN.json'
    completed(complete, proof_path)
    completed(complete, plan_path)
    proof, plan = read(proof_path), read(plan_path)
    if (plan['module'] != 'runners.drive.cards.week5_ch_pipeline_bounded_fixture'
            or plan['config'] != dict(constructed_fixture=True) or plan['inputs']
            or proof.get('passed') is not True or proof.get('constructed') is not True
            or proof.get('source_months') != 3 or proof.get('source_games') != 576):
        raise ValueError('Wrong or incomplete source fixture')
    root = complete.parent/'output'
    def spec(path):
        completed(complete, path)
        return dict(path=str(path), sha256=filehash(path))
    source = root/'constructed_inputs'
    salt = spec(source/'CONSTRUCTED_SALT.bin')
    months = ('2017-04', '2017-05', '2026-07')
    if component == 'merge':
        adapted = dict(salt=salt, **{'frame'+str(i): spec(source/('census-'+month)/'PRIVATE_FRAME.sqlite')
                                    for i,month in enumerate(months)})
        settings = dict(phase='merge', max_new_draws=config['max_new_draws'])
    elif component == 'sample':
        adapted = dict(salt=salt, frame=spec(root/'bounded_merge/PRIVATE_FRAME.sqlite'))
        settings = dict(phase='sample', players=100, max_new_draws=config['max_new_draws'],
                        sources=[dict(month=month, **spec(source/(month+'.pgn'))) for month in months])
    else:
        adapted = dict(histories=spec(root/'bounded_merge/PRIVATE_FRAME.sqlite'))
        settings = dict(max_new_draws=config['max_new_draws'])
    return component, adapted, settings, root


def pause_phase(output):
    root = Path(output).resolve().parent
    plan = read(root/'PLAN.json')
    if plan['module'] != MODULE or plan['config'].get('constructed_fixture') is not True:
        raise ValueError('Actual counted constructed plan required')
    if 'resume' not in plan:
        if (root/'RESUMED_FROM.json').exists():
            raise ValueError('Unexpected copy receipt')
        return 'execute'
    copied = read(root/'RESUMED_FROM.json')
    prior = Path(plan['resume']['root']).resolve()
    if (Path(copied['predecessor']).resolve() != prior
            or copied['plan_sha256'] != filehash(prior/'PLAN.json')
            or copied['paused_sha256'] != filehash(prior/'PAUSED.json')
            or copied['copied'] != read(prior/'PAUSED.json')['checkpoint_outputs']):
        raise ValueError('Qualification continuation is not the runtime-authenticated whole checkpoint')
    operation = read(prior/'PAUSED.json')['paused_operation']
    if operation == 'execute':
        return 'verify'
    if operation == 'verify':
        return None
    raise ValueError('Unexpected predecessor phase')


def parity(component, output, fixture_root):
    output = Path(output)
    if component == 'merge':
        reference = fixture_root/'original_merge'
        tables = compare(reference/'PRIVATE_FRAME.sqlite', output/'PRIVATE_FRAME.sqlite')
        if (reference/'SOURCE.json').read_bytes() != (output/'SOURCE.json').read_bytes():
            raise ValueError('Frozen original merge receipt differs')
        return dict(original_scientific_tables=tables, original_receipt_equal=True)
    if component == 'sample':
        reference = fixture_root/'original_sample'
        names = ('PRIVATE_SELECTED_PLAYERS.json', 'PRIVATE_POSITIONS.jsonl.gz', 'SOURCE.json')
        for name in names:
            if filehash(reference/name) != filehash(output/name):
                raise ValueError('Frozen original sample artifact differs')
        return dict(exact_original_hashes={name:filehash(output/name) for name in names})
    reference = fixture_root/'original_index'
    if (reference/'INDEX.json').read_bytes() != (output/'INDEX.json').read_bytes():
        raise ValueError('Frozen original history index differs')
    hashes = {}
    for table in ('player_history', 'settings'):
        actual = frozen_fixture.table_hash(output/'PRIVATE_PLAYER_HISTORY.sqlite', table)
        if actual != frozen_fixture.table_hash(reference/'PRIVATE_PLAYER_HISTORY.sqlite', table):
            raise ValueError('Frozen original history table differs')
        hashes[table] = actual
    return dict(original_tables=hashes, original_index_equal=True)


def run(output, inputs, config, operation):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    component, adapted, settings, fixture = fixture_inputs(inputs, config)
    stop_phase = pause_phase(output)
    original_control = checkpoint.Control
    class QualifyingControl(original_control):
        def tick(self, amount, done, total):
            super().tick(amount, done, total)
            if self.operation == stop_phase and total and done >= (total+19)//20 and done < total:
                raise PilotPause(dict(component=component, operation=self.operation,
                                      source_units=done, source_total=total,
                                      observed_fraction=done/total,
                                      first_complete_transaction_at_or_after_fraction=.05,
                                      exact_five_percent_claimed=False,
                                      source_or_verifier_completed=False,
                                      constructed_fixture_only=True))
    # Process-local instrumentation only. Original files and scientific methods
    # remain byte-identical, and the class is restored even on a refusal.
    checkpoint.Control = QualifyingControl
    try:
        try:
            result = getattr(COMPONENTS[component], operation)(output, adapted, settings)
        except PilotPause as pause:
            freeze(output/('QUALIFICATION_'+operation.upper()+'_PILOT.json'), pause.receipt)
            return dict(status='yielded', reason='Constructed committed '+operation+' pilot boundary',
                        qualification_pilot=pause.receipt)
    finally:
        checkpoint.Control = original_control
    if result.get('status') == 'yielded':
        # An external owner/resource interruption is retained, not relabelled as
        # the requested qualification pilot. The driver refuses automatic advance.
        return result
    if operation == stop_phase:
        raise ValueError('Fixture did not expose a nonterminal transactional pilot')
    equal = parity(component, output, fixture)
    if operation == 'verify':
        if result.get('verified') is not True or result.get('source_start_ordinal', result.get('raw_source_start_ordinal')) != 0:
            raise ValueError('Complete fresh source-zero verification required')
        for phase in ('EXECUTE', 'VERIFY'):
            receipt = read(output/('QUALIFICATION_'+phase+'_PILOT.json'))
            if receipt['operation'] != phase.casefold() or receipt['component'] != component:
                raise ValueError('Both actual pilot phases must precede final qualification')
        proof = dict(verified=True, constructed=True, component=component,
                     full_fresh_verification=result, frozen_original_parity=equal,
                     both_actual_native_pilots_required=True, scientific_admission=False)
        freeze(output/'QUALIFICATION_FINAL.json', proof)
        return proof
    return dict(status='complete', constructed=True, component=component,
                execution_result=result, frozen_original_parity=equal,
                fresh_verification_still_required=True)


def execute(output, inputs, config):return run(output, inputs, config, 'execute')
def verify(output, inputs, config):return run(output, inputs, config, 'verify')
