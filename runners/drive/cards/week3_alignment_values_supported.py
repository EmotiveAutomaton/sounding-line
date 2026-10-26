"""Approved CA3 supported-input variant; original full population retained.

DESIGN CHECK: LESSONS 2-5 read 2026-10-25. This is source preparation,
not a statistic. Under either a scientific null or alternative, membership
depends only on nonempty unexplained-choice and sampled-explanation inputs.
Missing either input excludes a recipient explicitly, never imputes a score.
Source mutations, forged support flags and census drift must refuse. Full raw
partition reconstruction guards against a self-consistent but false manifest.
"""
from collections import Counter
from pathlib import Path

from runners.stage14.common import filehash, freeze, read
from . import week3_alignment_values_inputs as original
from .timing_pmap_source import completed

INPUTS = original.INPUTS | {'partition_summary', 'partition_complete'}
CONFIG = {'variant', 'expected_fixed_annotators', 'expected_supported_annotators'}
VARIANT = 'CA3.supported-inputs'


def select(census, config):
    if set(config) != CONFIG or config['variant'] != VARIANT:
        raise ValueError('explicit supported variant required')
    for name in CONFIG - {'variant'}:
        if type(config[name]) is not int or config[name] <= 0:
            raise ValueError('positive exact expected census required')
    if len(census) != config['expected_fixed_annotators']:
        raise ValueError('fixed annotator census differs')
    writers = [row['writer'] for row in census]
    if writers != sorted(set(writers)):
        raise ValueError('unique canonical annotator order required')
    supported, dispositions = [], []
    for row in census:
        reasons = []
        if not row['fit_indices']:
            reasons.append('no-comparisons-without-explanations')
        if not row['targets']:
            reasons.append('no-sampled-explanation-targets')
        state = 'unsupported-inputs' if reasons else 'pending-value-labels-and-model-fit'
        if row['unsupported_reasons'] != reasons or row['support'] != state:
            raise ValueError('source support disposition differs')
        fit = row['fit_indices']
        targets = [target['comparison_index'] for target in row['targets']]
        if (len(set(fit)) != len(fit) or len(set(targets)) != len(targets)
                or set(fit) & set(targets)):
            raise ValueError('duplicate or overlapping fit and target rows')
        if not reasons:
            supported.append(row)
        dispositions.append(dict(writer=row['writer'], included=not reasons,
                                 unsupported_reasons=reasons))
    if len(supported) != config['expected_supported_annotators']:
        raise ValueError('supported annotator census differs')
    return supported, dispositions


def calculate(inputs, config):
    if set(inputs) != INPUTS:
        raise ValueError('exact supported source inputs required')
    path = Path(inputs['partition_summary']).resolve()
    completed(inputs['partition_complete'], path)
    saved = read(path)
    if saved.get('card') != 'CA3-inputs' or saved.get('state') != 'source_support_census':
        raise ValueError('original complete CA3 census required')
    if set(saved['output_hashes']) != {'PRIVATE_REFIT_TARGETS.json'}:
        raise ValueError('original census payload contract differs')
    for name, expected in saved['output_hashes'].items():
        if filehash(path.parent / name) != expected:
            raise ValueError('original census payload changed')
    source_inputs = {key: inputs[key] for key in original.INPUTS}
    census, reconstructed = original.calculate(source_inputs, {})
    if read(path.parent / 'PRIVATE_REFIT_TARGETS.json') != census:
        raise ValueError('raw source partition reconstruction differs')
    if {k: v for k, v in saved.items() if k != 'output_hashes'} != reconstructed:
        raise ValueError('original census summary reconstruction differs')
    supported, dispositions = select(census, config)
    summary = dict(
        card=VARIANT, state='supported_inputs_prepared',
        input_hashes={key: filehash(value) for key, value in inputs.items()},
        config=config, fixed_annotators=len(census),
        supported_annotators=len(supported), excluded_annotators=len(census)-len(supported),
        supported_fit_comparisons=sum(len(row['fit_indices']) for row in supported),
        supported_explanation_targets=sum(len(row['targets']) for row in supported),
        full_census_explanation_targets=sum(len(row['targets']) for row in census),
        unsupported_reason_counts=dict(sorted(Counter(
            reason for row in census for reason in row['unsupported_reasons']).items())),
        full_population_question='open; not answered by the supported-input variant',
        scope='Only recipients with both input types; full census and original partition retained',
        selection='Input presence only; no value label, feature or model performance read',
        downstream_admission=False, scientific_admission=False,
        remaining=reconstructed['remaining'])
    return census, supported, dispositions, summary


def payloads(inputs, config):
    census, supported, dispositions, summary = calculate(inputs, config)
    return {'PRIVATE_FULL_CENSUS.json': census,
            'PRIVATE_SUPPORTED_REFIT_TARGETS.json': supported,
            'PRIVATE_MEMBERSHIP.json': dispositions}, summary


def execute(output, inputs, config):
    output = Path(output)
    files, summary = payloads(inputs, config)
    for name, value in files.items():
        freeze(output/name, value)
    summary['output_hashes'] = {name: filehash(output/name) for name in files}
    freeze(output/'SUMMARY.json', summary)
    return summary


def verify(output, inputs, config):
    output = Path(output)
    files, summary = payloads(inputs, config)
    for name, value in files.items():
        if read(output/name) != value:
            raise ValueError('fresh supported source payload differs: '+name)
    summary['output_hashes'] = {name: filehash(output/name) for name in files}
    if read(output/'SUMMARY.json') != summary:
        raise ValueError('fresh supported summary differs')
    return dict(verified=True, full_census_replayed=True,
                supported_membership_replayed=True, scientific_admission=False)
