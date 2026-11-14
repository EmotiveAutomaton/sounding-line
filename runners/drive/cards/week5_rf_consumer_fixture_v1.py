"""Authored RF1 source -> identity gate -> complete statistical handler fixture.

No public source, real participant or inferred election identity is accepted.
Synthetic native envelopes exercise downstream contracts; only the owner's
external counted producer/fresh-verifier chain can supply actual native proof.
"""
from pathlib import Path
import gzip
import itertools
import json
import math
from . import week5_rf_cp_source_v1 as source
from . import week5_rf_cp_fixture_v1 as intake_fixture
from . import week5_rf_cp_instrument_v1 as instrument
from . import week5_rf_cp_native_fixture_v1 as intake_native
from . import week5_rf_qualified_v1 as qualified
from . import week5_rf_analysis_v3 as analysis
from . import week5_rf_math_fixture_v2 as math_fixture
from . import week5_rf_prefix_v1 as prefix

MODULE = 'runners.drive.cards.week5_rf_consumer_fixture_v1'
WORLDS = ('three-read', 'null', 'against')


def write_bytes_equal(path, data):
    path = Path(path)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError('Authored immutable fixture bytes changed')
    else:
        with path.open('xb') as stream:
            stream.write(data)


def read(path):
    return json.loads(Path(path).read_text('utf8'))


def seal_native(root, module, names):
    root = Path(root)
    source.write_equal(root/'PLAN.json', {'module': module, 'constructed_fixture': True})
    source.write_equal(root/'VERIFIED.json', {'verified': True, 'constructed_fixture': True})
    source.write_equal(root/'COMPLETE.json', {'status': 'COMPLETE', 'fresh_process_verified': True,
        'constructed_fixture': True, 'outputs': {name: source.sha(root/name) for name in ('PLAN.json', 'VERIFIED.json', *names)}})


def authored(root, world, candidates=None):
    if world not in WORLDS:
        raise ValueError('Unknown constructed world')
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    candidates = candidates if candidates is not None else (20 if world == 'against' else 40)
    salt = bytes(range(32))
    write_bytes_equal(root/'constructed-salt.bin', salt)
    lines, assignments = [], []
    ordinal = 0
    for candidate in range(candidates):
        for pattern, bits in enumerate(itertools.product((0, 1), repeat=3)):
            election = f'constructed-{world}-{candidate:03d}-{pattern}'
            if world == 'against':
                a, b, c = bits
                six = (a, b, c, a ^ b, a ^ c, b ^ c)
                early_n, later_n = 24, 48
                later_support = 16 if six[3] else 24
            else:
                early_n, later_n = 10, 20
                respect, trust, liking = bits
                later_support = 10 if world == 'null' or trust == liking else 16 if trust else 4
            for j in range(early_n+later_n):
                if j < early_n:
                    vote = 1 if j < early_n//2 else -1
                    if world == 'against':
                        terms = ('Experienced', 'Inexperienced', 'Trustworthy', 'Dishonest', 'Friendly', 'Rude')
                        words = [terms[k] for k, flag in enumerate(six) if flag and ((k % 2 == 0 and j < 6) or (k % 2 == 1 and 6 <= j < 12))]
                    else:
                        words = [term for term, bit in zip(('Experienced', 'Trustworthy', 'Friendly'), bits) if bit]
                    text = '. '.join(words)+'.' if words else 'Ordinary recorded comment.'
                else:
                    vote = 1 if j-early_n < later_support else -1
                    text = 'Ordinary recorded comment.'
                lines.append(f'SRC:constructed-voter-{ordinal}\nTGT:constructed-candidate-{candidate:03d}\nVOT:{vote}\nRES:1\nYEA:2010\nDAT:{12+j//60:02d}:{j%60:02d}, 01 January 2010\nTXT:{text}\n\n')
                # This map is authored with each synthetic record, never inferred
                # from candidate, year, result, source order or elapsed time.
                assignments.append({'comment_id': source.identity(salt, 'RF1', 'ordinal', str(ordinal)), 'election_id': election})
                ordinal += 1
    archive = root/'constructed-rfa.txt.gz'
    write_bytes_equal(archive, gzip.compress(''.join(lines).encode('utf8'), mtime=0))
    source.write_equal(root/'AUTHORED_IDENTITIES.json', assignments)
    return {'inputs': {'archive': str(archive.resolve()), 'identity_salt': str((root/'constructed-salt.bin').resolve())},
        'config': {'family': 'RF1', 'constructed_fixture': True, 'fixture_archive_sha256': source.sha(archive), 'fixture_expected_records': ordinal}}


def prepare(root, world, candidates=None):
    root = Path(root)
    saved = root/'PREPARED.json'
    if saved.exists():
        return read(saved)
    spec = authored(root/'authored', world, candidates)
    src = root/'source-output'
    source.execute(src, spec['inputs'], spec['config'])
    if source.verify(src, spec['inputs'], spec['config']).get('verified') is not True:
        raise ValueError('Constructed raw source did not independently replay')
    inputs, config = intake_fixture.constructed_native_receipt(root/'constructed-source-native', src)
    gate_root = root/'constructed-gate-native'
    instrument.execute(gate_root/'output', inputs, config)
    instrument.verify(gate_root/'output', inputs, config)
    seal_native(gate_root, 'runners.drive.cards.week5_rf_cp_instrument_v1', ('output/INSTRUMENT.json',))
    inputs['instrument_native_root'] = str(gate_root.resolve())
    config['instrument_native_complete_sha256'] = source.sha(gate_root/'COMPLETE.json')
    id_root = root/'constructed-identity-native'
    source_bind = read(src/'BINDING.json')
    bind = {'constructed_fixture': True, 'source_native_complete_sha256': config['source_native_complete_sha256'],
        'source_binding_sha256': source.sha(src/'BINDING.json'), 'source_archive_sha256': source_bind['archive_sha256'],
        'producer_module_sha256': source.sha(__file__), 'identity_method': qualified.IDENTITY_METHOD}
    table = dict(bind, schema=qualified.IDENTITY_SCHEMA, election_identity_qualified=True,
        assignments=read(root/'authored/AUTHORED_IDENTITIES.json'))
    evidence = dict(bind, heuristic_grouping=False,
        original_identifier_evidence_sha256=source.sha(root/'authored/AUTHORED_IDENTITIES.json'),
        scope='authored constructed identities only; no real election identity claim')
    source.write_equal(id_root/'output/ELECTION_IDENTITIES.json', table)
    source.write_equal(id_root/'output/IDENTITY_EVIDENCE.json', evidence)
    source.write_equal(id_root/'output/IDENTITY_VERIFIED.json', {'verified': True,
        'table_sha256': source.sha(id_root/'output/ELECTION_IDENTITIES.json'),
        'evidence_sha256': source.sha(id_root/'output/IDENTITY_EVIDENCE.json')})
    seal_native(id_root, MODULE, ('output/ELECTION_IDENTITIES.json', 'output/IDENTITY_EVIDENCE.json', 'output/IDENTITY_VERIFIED.json'))
    review = root/'CONSTRUCTED_IDENTITY_REVIEW.json'
    source.write_equal(review, {'decision': 'qualified_explicit_original_identifiers', 'reviewer': 'authored fixture truth',
        'constructed_fixture': True, 'identity_native_complete_sha256': source.sha(id_root/'COMPLETE.json'),
        'table_sha256': source.sha(id_root/'output/ELECTION_IDENTITIES.json'),
        'evidence_sha256': source.sha(id_root/'output/IDENTITY_EVIDENCE.json')})
    inputs.update(identity_native_root=str(id_root.resolve()), identity_review=str(review.resolve()))
    config.update(identity_native_complete_sha256=source.sha(id_root/'COMPLETE.json'),
        identity_producer_module=MODULE, identity_producer_sha256=source.sha(__file__), identity_review_sha256=source.sha(review))
    result = {'inputs': inputs, 'config': config, 'source_spec': spec, 'world': world}
    source.write_equal(saved, result)
    return result


def answers(world, result):
    point = result['point']['primary_fit']
    if world == 'three-read':
        gap = point['mean_election_log_losses']['TWO-A']-point['mean_election_log_losses']['THREE']
        if abs(gap-math_fixture.hand_margin()) > 1e-10:
            raise ValueError('Authored raw three-read world missed its hand loss margin')
    if world == 'null':
        if point['primary'] != 0 or result['uncertainty']['primary']['status'] != 'within_practical_band':
            raise ValueError('Complete identical-outcome null did not retain exact zero/null state')
    if world == 'against':
        expected = .5*((1/(1+2**(1/6))-.5)+(1/(1+2**(7/6))-1/3))
        values = result['point']['against_comment']['contrasts']
        if abs(values['trust']-expected) > 1e-10 or max(abs(values[k]) for k in ('respect', 'liking')) > 1e-10:
            raise ValueError('Against-comment probability contrast differs from authored log-odds truth')
    if result['bootstrap_draws'] != 2000:
        raise ValueError('Full native fixture did not complete all candidate draws')
    return {'world': world, 'all_2000_draws': True, 'authored_answer': True}


def _execute(output, inputs, config):
    if inputs or config.get('constructed_fixture') is not True:
        raise ValueError('Native fixture requires explicit constructed scope and no external inputs')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    proof = {'schema': 'RF1-FULL-CONSUMER-FIXTURE-1', 'hand_answers': intake_native.known_answers(),
        'worlds': {}, 'constructed_fixture': True, 'scientific_admission': False}
    for world in WORLDS:
        analysis.check_yield(output)
        spec = prepare(output/world, world)
        if world == 'three-read':
            prefix_result = prefix.execute(output/world/'cost-prefix', spec['inputs'], dict(spec['config'], prefix_draws=4))
            if prefix_result['status'] == 'yielded':
                return prefix_result
            receipt = read(output/world/'cost-prefix/PREFIX.json')
            if receipt['completed_global_draws'] != 4:
                raise ValueError('Native first-cost fixture did not preserve four global draws')
            proof['cost_prefix'] = {'completed_global_draws': 4, 'receipt_sha256': source.sha(output/world/'cost-prefix/PREFIX.json')}
        result = analysis.execute(output/world/'analysis', spec['inputs'],
            dict(spec['config'], max_new_draw_blocks=config.get('max_new_draw_blocks', 10**9)))
        if result['status'] == 'yielded':
            return result
        proof['worlds'][world] = answers(world, read(output/world/'analysis/RESULT.json'))
    source.write_equal(output/'FIXTURE.json', proof)
    return dict(proof, status='complete')


def execute(output, inputs, config):
    try:
        return _execute(output, inputs, config)
    except analysis.YieldRequested:
        return {'status': 'yielded', 'reason': 'owned constructed fixture checkpoint', 'scientific_admission': False}


def verify(output, inputs, config):
    if inputs or config.get('constructed_fixture') is not True:
        raise ValueError('Wrong fixture scope')
    output = Path(output)
    prior = read(output/'FIXTURE.json')
    if prior['hand_answers'] != intake_native.known_answers():
        raise ValueError('Literal marker answers changed')
    for world in WORLDS:
        try:
            analysis.check_yield(output)
        except analysis.YieldRequested:
            return {'status': 'yielded', 'verified': False, 'reason': 'owned fixture verifier checkpoint'}
        spec = read(output/world/'PREPARED.json')
        # This directory is created only in the external verifier phase. It does
        # not reuse execute's preparatory SOURCE_VERIFIED or source replay cache.
        formal = output/world/'formal-source-replay'
        replay = source.execute(formal, spec['source_spec']['inputs'], spec['source_spec']['config'])
        if replay.get('status') == 'yielded':
            return dict(replay, verified=False)
        original = output/world/'source-output'
        complete = read(original/'SOURCE_COMPLETE.json')
        for name in ('BINDING.json', 'SOURCE_COMPLETE.json', 'SUMMARY.json', 'REVIEW_PRIVATE.json', *complete['blocks']):
            if (original/name).read_bytes() != (formal/name).read_bytes():
                raise ValueError('Fresh native raw-source reconstruction differs')
        gate_root = Path(spec['inputs']['instrument_native_root'])/'output'
        instrument.verify(gate_root, spec['inputs'], spec['config'])
        if world == 'three-read':
            result = prefix.verify(output/world/'cost-prefix', spec['inputs'], dict(spec['config'], prefix_draws=4))
            if result.get('status') == 'yielded':
                return result
            if result.get('verified') is not True or source.sha(output/world/'cost-prefix/PREFIX.json') != prior['cost_prefix']['receipt_sha256']:
                raise ValueError('Native first-cost prefix independent replay differs')
        result = analysis.verify(output/world/'analysis', spec['inputs'],
            dict(spec['config'], max_new_draw_blocks=config.get('max_new_draw_blocks', 10**9)))
        if result.get('status') == 'yielded':
            return result
        if result.get('verified') is not True or answers(world, read(output/world/'analysis/RESULT.json')) != prior['worlds'][world]:
            raise ValueError('Full candidate-refit native fixture replay differs')
    return {'verified': True, 'all_three_complete_raw_source_and_candidate_refit_worlds': True,
        'scientific_admission': False}
