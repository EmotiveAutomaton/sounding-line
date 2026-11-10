"""Prepared actual-tiny-model proof of original masked checkpoint equality."""
from pathlib import Path
import shutil

from . import week5_la_mask_checkpoints as new
from .week5_la import ResolutionScorer as Original
from .week5_la_score_fixture import masked_loader
from .week5_at_scoring import digest
from .timing_census import read, filehash
from .timing_p6 import write_equal


def finish(model, tokenizer, torch, output, binding, previous, current, verifying=False, quantum=2):
    for _ in range(300):
        scorer = new.ResolutionScorer(model, tokenizer, torch, output, binding,
                                      verifying=verifying, max_new_batches=quantum, max_wall_seconds=600)
        try:
            return scorer.score(previous, current)
        except new.MaskCheckpointYield:
            pass
    raise ValueError('Constructed masked continuation did not complete')


def refuse(fn):
    try:
        fn()
    except ValueError:
        return
    raise ValueError('Changed masked source/checkpoint was accepted')


def run(output, inputs, config, verifying=False):
    if inputs or config:
        raise ValueError('No human or pretrained model inputs in this fixture')
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    model, tokenizer, torch = masked_loader(dict(model='constructed', revision='fixture'))
    cases = [('short', 'prior constructed words', 'current sentence'), ('crop', 'x' * 550, 'y' * 25)]
    records = []
    for name, previous, current in cases:
        binding = dict(source_row_sha256=digest(dict(case=name, previous=previous, current=current)),
                       masked_manifest_sha256=digest(dict(model='constructed', revision='fixture')))
        expected = Original(model, tokenizer, torch, max_tokens=512, mask_batch=8).score(previous, current)
        target = root / name
        if not verifying:
            actual = finish(model, tokenizer, torch, target, binding, previous, current, quantum=3)
        else:
            actual = finish(model, tokenizer, torch, target, binding, previous, current, True, quantum=3)
        if actual != expected or read(target / 'RESULT.json') != expected:
            raise ValueError('Checkpointed original masked tensor batches or final reduction changed')
        if name == 'crop' and (actual['old_tokens'] != 484 or actual['old_tokens_dropped'] != 66):
            raise ValueError('Known identical old-token crop changed')
        records.append(dict(case=name, result_sha256=filehash(target / 'RESULT.json'),
                            old_tokens=actual['old_tokens'], old_tokens_dropped=actual['old_tokens_dropped']))
    controls = root / ('verify-controls' if verifying else 'execute-controls')
    controls.mkdir()
    previous, current = 'constructed prior words', 'new act'
    binding = dict(source_row_sha256=digest(dict(previous=previous, current=current)),
                   masked_manifest_sha256=digest(dict(model='constructed', revision='fixture')))
    partial = controls / 'partial'
    scorer = new.ResolutionScorer(model, tokenizer, torch, partial, binding, max_new_batches=1)
    try:
        scorer.score(previous, current)
    except new.MaskCheckpointYield as yielded:
        if yielded.receipt['new_mask_batches'] != 1:
            raise ValueError('Yield did not seal exactly one original masked tensor batch')
    else:
        raise ValueError('Within-act masked yield was not exercised')
    copied = controls / 'copied'
    shutil.copytree(partial, copied)
    actual = finish(model, tokenizer, torch, copied, binding, previous, current)
    expected = Original(model, tokenizer, torch, max_tokens=512, mask_batch=8).score(previous, current)
    if actual != expected:
        raise ValueError('Local copied masked checkpoint changed original output')
    finish(model, tokenizer, torch, copied, binding, previous, current, True)
    preserved = filehash(copied / 'RESULT.json')
    finish(model, tokenizer, torch, copied, binding, previous, current)
    if filehash(copied / 'RESULT.json') != preserved:
        raise ValueError('Completed masked-act reentry changed output')
    changed = controls / 'changed'
    shutil.copytree(partial, changed)
    batch = next((changed / 'execute/before').glob('*.seal.json'))
    with batch.open('ab') as stream:
        stream.write(b' ')
    # A changed seal's JSON value remains valid, so change its actual declared
    # input binding too; hash-only output manifests are the native outer layer.
    data = read(batch)
    data['binding']['offset'] = 8
    batch.write_text(__import__('json').dumps(data), encoding='utf8')
    refuse(lambda: finish(model, tokenizer, torch, changed, binding, previous, current))
    refuse(lambda: finish(model, tokenizer, torch, partial, dict(binding, masked_manifest_sha256='0' * 64), previous, current))
    refuse(lambda: finish(model, tokenizer, torch, partial, binding, previous, current + ' changed'))
    early = controls / 'early'
    early.mkdir()
    write_equal(early / 'YIELD_REQUEST.json', dict(reason='constructed cooperative request'))
    before = new.ResolutionScorer(model, tokenizer, torch, early, binding)
    try:
        before.score(previous, current)
    except new.MaskCheckpointYield as yielded:
        if yielded.receipt['new_mask_batches'] != 0 or (early / 'execute').exists():
            raise ValueError('Resource request performed a new masked forward')
    else:
        raise ValueError('Pre-forward cooperative request was ignored')
    for parameter in model.parameters():
        parameter.data.zero_()
    uniform_binding = dict(binding, masked_manifest_sha256=digest(dict(model='uniform-constructed')))
    null = finish(model, tokenizer, torch, controls / 'uniform', uniform_binding, previous, current)
    if null['resolution_nats_per_token'] != 0:
        raise ValueError('Uniform masked reader no longer has exact zero resolution')
    value = dict(fixture_only=True, no_human_or_pretrained_model=True, original_tensor_batches_and_reduction_equal=True,
                 exact_uniform_null=True, identical_old_token_crop=True, cases=records,
                 partial_act_copy_and_complete_reentry=True, changed_model_text_checkpoint_refused=True,
                 resource_yield_before_forward=True, actual_model_threads=torch.get_num_threads(),
                 native_paired_guard_or_human_admission=False, local_checkpoint_copy_is_not_native_resume=True)
    if verifying:
        if read(root / 'FIXTURE.json') != value:
            raise ValueError('Independent masked checkpoint fixture differs')
        return dict(verified=True, complete_original_masked_kernel_replay=True)
    write_equal(root / 'FIXTURE.json', value)
    return dict(status='complete', scientific_admission=False)


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, True)
