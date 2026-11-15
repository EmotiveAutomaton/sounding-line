"""TR2 metadata support gate and constructed-only reporting scaffold.

DESIGN CHECK: LESSONS 2, 3 and 5; CONTROLS 1 and 6-7. A missing mapping is
source-held, a measured failed floor is unsupported, and neither is a null.
With orthogonal half-errors the constructed correction recovers 0, .5 and 1;
no true person variance blocks stability. Ratios are never clipped. This is
not a source-specific sampling-model qualification or a human analysis adapter.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SETTINGS = ('refusing', 'slowing', 'returning')
SEED = 20261107
MAX_METADATA_BYTES = 4 * 1024 * 1024


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def read(path):
    path = Path(path)
    if path.stat().st_size > MAX_METADATA_BYTES:
        raise ValueError('Only bounded metadata is admitted')
    return json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=_pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    if path.exists() and path.read_bytes() != encoded:
        raise ValueError('Immutable TR2 output differs')
    if not path.exists():
        path.write_bytes(encoded)


def _exact(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError('Exact TR2 metadata fields required')


def _text(value):
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError('Nonblank exact text required')


def _pin(record, base):
    _exact(record, ('path', 'sha256'))
    _text(record['path'])
    expected = record['sha256']
    if not isinstance(expected, str) or len(expected) != 64 or any(c not in '0123456789abcdef' for c in expected):
        raise ValueError('Lowercase SHA256 required')
    path = (base / record['path']).resolve()
    path.relative_to(base.resolve())
    if path.suffix.lower() not in ('.json', '.md') or path.stat().st_size > MAX_METADATA_BYTES:
        raise ValueError('Only small source/design metadata pins are admitted')
    if sha(path) != expected:
        raise ValueError('TR2 metadata pin differs')
    return path


def support_report(manifest, base=ROOT):
    """Authenticate declarations, without opening a corpus or computing a score.

    Counts here are supplied metadata, not a newly executed source census.
    A later source adapter must bind each count to its complete source census.
    """
    _exact(manifest, ('schema', 'source_kind', 'source_pins', 'settings'))
    if manifest['schema'] != 'TR2-support-v1' or manifest['source_kind'] not in ('human_metadata', 'constructed'):
        raise ValueError('TR2 support schema/source kind differs')
    pins = manifest['source_pins']
    if not isinstance(pins, dict) or not pins:
        raise ValueError('Pinned source design or census metadata required')
    for key, record in pins.items():
        _text(key)
        _pin(record, Path(base))
    records = manifest['settings']
    if not isinstance(records, list) or len(records) != 3:
        raise ValueError('Exactly three commissioned settings required')
    if {r.get('id') for r in records if isinstance(r, dict)} != set(SETTINGS):
        raise ValueError('Duplicate, missing or substituted TR2 setting')
    result = []
    for setting in sorted(records, key=lambda r: SETTINGS.index(r['id'])):
        _exact(setting, ('id', 'measurement', 'unit', 'mapping_frozen', 'checks', 'holds'))
        _text(setting['measurement']); _text(setting['unit'])
        if type(setting['mapping_frozen']) is not bool:
            raise ValueError('Mapping state must be explicit')
        holds = setting['holds']
        if not isinstance(holds, list) or any(not isinstance(h, str) or not h.strip() for h in holds):
            raise ValueError('Explicit hold list required')
        checks = setting['checks']
        if not isinstance(checks, list) or not checks:
            raise ValueError('Every setting begins with its support checks')
        names = set()
        for check in checks:
            _exact(check, ('id', 'status', 'count', 'floor', 'unit', 'evidence'))
            _text(check['id']); _text(check['unit'])
            if check['id'] in names or check['evidence'] not in pins:
                raise ValueError('Unique check and pinned evidence required')
            names.add(check['id'])
            if check['status'] == 'pending':
                if check['count'] is not None:
                    raise ValueError('Pending check cannot claim an observed count')
                if check['floor'] is not None and (type(check['floor']) is not int or check['floor'] < 1):
                    raise ValueError('Pending support floor is invalid')
            elif check['status'] in ('passed', 'failed'):
                if type(check['count']) is not int or type(check['floor']) is not int or check['count'] < 0 or check['floor'] < 1:
                    raise ValueError('Completed support check requires integer count and floor')
                if (check['count'] >= check['floor']) != (check['status'] == 'passed'):
                    raise ValueError('Count does not support declared check status')
            else:
                raise ValueError('Unknown support check status')
        failed = [c['id'] for c in checks if c['status'] == 'failed']
        pending = [c['id'] for c in checks if c['status'] == 'pending']
        status = ('unsupported' if failed else 'source-held' if pending or holds or not setting['mapping_frozen']
                  else 'support-declared; source-specific estimator still required')
        result.append(dict(setting, status=status, failed_checks=failed, pending_checks=pending,
                           scientific_verdict=None))
    return dict(card='TR2', result_kind='support_metadata_only', source_kind=manifest['source_kind'],
                settings=result, source_pins=pins, human_outcomes_loaded=False,
                human_inference_computed=False, production_adapter_implemented=False,
                count_provenance='supplied pinned metadata; this handler does not execute a corpus census',
                budget_key='TR2', family='MD', card_ceiling_cpu_seconds=60000,
                scientific_admission=False)


def whole_unit_halves(units, setting, seed=SEED):
    """Balanced hash halves of whole sessions/prompts; explicitly not time order."""
    if setting not in SETTINGS or type(seed) is not int or seed != SEED:
        raise ValueError('Declared setting and prospective seed required')
    units = list(units)
    for unit in units:
        _text(unit)
    if len(units) < 2 or len(set(units)) != len(units):
        raise ValueError('At least two distinct whole units required')
    ordered = sorted(units, key=lambda u: (hashlib.sha256(f'{seed}\0{setting}\0{u}'.encode()).digest(), u))
    return {unit: i % 2 for i, unit in enumerate(ordered)}


def grammatical_counts(sentences):
    """WC4's token denominator; a constructed-input projection, no tagger run.

    NOUN includes PROPN; VERB excludes AUX, matching WC4's lexical set.
    Counts refer to complete final documents, not solely human-produced text.
    """
    counts = dict(nouns=0, verbs=0, adjectives=0, adverbs=0)
    mapping = {'NOUN': 'nouns', 'PROPN': 'nouns', 'VERB': 'verbs', 'ADJ': 'adjectives', 'ADV': 'adverbs'}
    denominator = 0
    for sentence in sentences:
        for token in sentence:
            _exact(token, ('text', 'pos'))
            if not isinstance(token['text'], str) or not isinstance(token['pos'], str):
                raise ValueError('Exact WC4 token text and POS fields required')
            if any(c.isalpha() for c in token['text']):
                denominator += 1
                if token['pos'] in mapping:
                    counts[mapping[token['pos']]] += 1
    return dict(counts=counts, letter_bearing_tokens=denominator,
                fractions={k: v / denominator if denominator else None for k, v in counts.items()})


def reporting_gate(variance_interval, stability_interval, *, qualified, complete_uncertainty):
    """TR1's ordered report rule, tested on constructed interval inputs only."""
    if type(qualified) is not bool or type(complete_uncertainty) is not bool:
        raise ValueError('Explicit qualification and complete uncertainty required')
    for interval in (variance_interval, stability_interval):
        if interval is not None and (not isinstance(interval, (list, tuple)) or len(interval) != 2
                or any(type(v) not in (int, float) or not math.isfinite(v) for v in interval)
                or interval[0] > interval[1]):
            raise ValueError('Finite ordered intervals required')
    if not qualified:
        return 'estimator unqualified'
    if variance_interval is None or variance_interval[0] <= 0:
        return 'no between-person differences in sensitivity could be measured in this task'
    if not complete_uncertainty or stability_interval is None:
        return 'invalid uncertainty; no stability inference'
    low, high = stability_interval
    if low > .5:
        return 'supports a stable sensitivity'
    if high < .2:
        return 'not stable at the registered band'
    if low >= .2 and high <= .5:
        return 'partly stable'
    return 'inconclusive across the registered stability bands'


def execute(output, inputs, config):
    if config == {'mode': 'support_metadata'}:
        _exact(inputs, ('manifest', 'manifest_sha256'))
        manifest_path = _pin({'path': inputs['manifest'], 'sha256': inputs['manifest_sha256']}, ROOT)
        result = support_report(read(manifest_path))
    elif config == {'mode': 'constructed'} and inputs == {}:
        from .week6_tr2_fixture_v1 import run
        result = run(independent=False)
    else:
        raise ValueError('TR2 human outcome execution is not implemented or admitted')
    write(Path(output) / 'RESULT.json', result)
    return result


def _compare(left, right):
    if isinstance(left, dict) and isinstance(right, dict) and left.keys() == right.keys():
        for key in left:
            _compare(left[key], right[key])
    elif isinstance(left, list) and isinstance(right, list) and len(left) == len(right):
        for a, b in zip(left, right):
            _compare(a, b)
    elif type(left) in (int, float) and type(right) in (int, float):
        if not math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError('Constructed arithmetic replay differs')
    elif type(left) is not type(right) or left != right:
        raise ValueError('Complete TR2 replay differs')


def verify(output, inputs, config):
    if config == {'mode': 'constructed'} and inputs == {}:
        from .week6_tr2_fixture_v1 import run
        replay = run(independent=True)
        _compare(read(Path(output) / 'RESULT.json'), replay)
        write(Path(output) / 'independent-replay' / 'RESULT.json', replay)
    else:
        replay = execute(Path(output) / 'independent-replay', inputs, config)
        if read(Path(output) / 'RESULT.json') != replay:
            raise ValueError('Complete metadata replay differs')
    return dict(verified=True, scope='complete metadata/constructed scaffold only',
                human_inference_computed=False, production_adapter_implemented=False)
