"""Exact archived metadata resolution and explicit millisecond/second comparison repair.

DESIGN CHECK: LESSONS 3-5. Every original source, transform and expected digest
remains unchanged. Session bounds are milliseconds; P6 word onsets are seconds.
Only bounds in the containment comparison divide by 1000; earlier-session ordering,
last-use seconds, recency arithmetic and original inputs remain unchanged.
Only the single inaccessible old parity receipt may resolve
from two old-pin-authenticated embedded copies. NULL/ALTERNATIVE are identical;
changed, missing or unknown evidence refuses. No global validator mutation.
"""
from pathlib import Path
from types import FunctionType, SimpleNamespace
import hashlib
import json
import os
import math

from . import week6_kp_source_v1 as original

digest = original.digest
read = original.read
REPO = Path(__file__).resolve().parents[3]
PARITY_REL = '.agent-state/drive-20261017/builder2/d33-supported-counts-tests-01/test_full_authenticated_source0/MATCHING_SOURCE_PARITY.json'
PARITY_SHA = '762f6e3e82e5c08b78e323f6f2cf284908ccb744ceb62f777096547b2f2c4d7c'
ANCHORS = (
    ('.agent-state/drive-20261017/builder2/D33_SUPPORTED_COUNTS_TESTS_20261018.json',
     'd76c1dff57fdc0c24a8be06c4966ed047b70f35efb0571c504e1a0fb08726727', ('parity',)),
    ('.agent-state/drive-20261017/builder2/READY_D33_SUPPORTED_COUNTS_20261018.json',
     'be8a383c5e0fafc3c4d3326462dee0534fe05cc4bd92eb645b98d9d24cb71f78',
     ('tests', 'receipt', 'parity')),
)
LOADER_PINS = {
    'runners/drive/cards/week6_kp_source_v1.py':
        '41aeb6bb6922864727204e7d780a74ca792bef548110559678a250c37960186e',
    'runners/drive/cards/timing_d33_calibrated.py':
        'c1faea075630aedd7673f383a7cd13f4b03953766138a64a16d9a389f67ec620',
}


def path_key(path):
    # Lexical identity: resolving the denied ancestor is neither needed nor allowed.
    return os.path.normcase(os.path.abspath(os.fspath(path)))


def copied(function, **replacements):
    result = FunctionType(function.__code__, dict(function.__globals__, **replacements),
                          function.__name__, function.__defaults__, function.__closure__)
    result.__kwdefaults__ = function.__kwdefaults__
    return result


class ExactParityResolver:
    """Parameters are constructor-only for literal fixtures; production is fixed below."""
    def __init__(self, target, expected, anchors, filehash=digest):
        self.target = Path(target)
        self.expected = expected
        self.anchors = tuple(anchors)
        self.filehash = filehash

    def evidence(self):
        if len(self.anchors) != 2:
            raise ValueError('Both independent preserved metadata anchors required')
        payloads, proofs = [], []
        for path, expected, route in self.anchors:
            raw = Path(path).read_bytes()
            if hashlib.sha256(raw).hexdigest() != expected:
                raise ValueError('Original metadata anchor pin differs')
            value = json.loads(raw)
            for key in route:
                value = value[key]
            if (path_key(value['path']) != path_key(self.target)
                    or value['sha256'] != self.expected):
                raise ValueError('Archived receipt path or original digest differs')
            # Original timing_census.write serialization, including the LF.
            payload = (json.dumps(value['receipt'], ensure_ascii=False, sort_keys=True,
                                  allow_nan=False) + '\n').encode('utf8')
            if hashlib.sha256(payload).hexdigest() != self.expected:
                raise ValueError('Embedded original bytes do not match old digest')
            payloads.append(payload)
            proofs.append(dict(path=str(Path(path).absolute()), sha256=expected,
                               member=list(route)))
        if payloads[0] != payloads[1]:
            raise ValueError('Original metadata anchors disagree')
        return dict(schema='KP_EXACT_PARITY_ARCHIVE_V1',
                    original_path=str(self.target.absolute()), original_sha256=self.expected,
                    original_bytes=len(payloads[0]), anchors=proofs,
                    semantics='Only this path and old hash, only on PermissionError errno 13; all other failures propagate')

    def check_files(self, bindings):
        # Authenticate both anchors even if the original leaf becomes readable.
        self.evidence()
        for name, expected in bindings.items():
            if path_key(name) == path_key(self.target) and expected != self.expected:
                raise ValueError('Original parity pin changed')
            try:
                actual = self.filehash(Path(name))
            except PermissionError as error:
                if (path_key(name) != path_key(self.target) or expected != self.expected
                        or error.errno != 13 or getattr(error, 'winerror', None) not in (None, 5)):
                    raise
                self.evidence()
                actual = self.expected
            if actual != expected:
                raise ValueError('Frozen source/input changed: ' + str(name))
        self.evidence()


def resolver():
    return ExactParityResolver(REPO / PARITY_REL, PARITY_SHA,
                               [(REPO / p, h, route) for p, h, route in ANCHORS])


def metadata_resolution():
    for name, expected in LOADER_PINS.items():
        if digest(REPO / name) != expected:
            raise ValueError('Original loader code changed')
    proof = resolver().evidence()
    return dict(proof, original_loader_pins=LOADER_PINS, clock_units=dict(
        session_bounds='milliseconds', word_clock='seconds', comparison='session_bounds_divided_by_1000',
        earlier_session_selection='unchanged_strict_millisecond_end_before_start'))


def isolated_loader(receipt_resolver, d33_template=original.d33):
    # The original code objects, defaults, closures and all other globals survive.
    # No assignment is made to any original module or validator.
    source_loader = copied(d33_template.load_source, check_files=receipt_resolver.check_files)
    view = SimpleNamespace(**dict(vars(d33_template), load_source=source_loader))
    return copied(original.load_authenticated, d33=view, prior_usage=prior_usage)


def load_authenticated(inputs, *, decisions):
    before = metadata_resolution()
    result = isolated_loader(resolver())(inputs, decisions=decisions)
    if metadata_resolution() != before:
        raise ValueError('Archived metadata proof changed during source projection')
    return result


def prior_usage(target, lookup):
    """Earlier completed sessions only; typed P6 occurrences including revisions."""
    result = {}
    for session in sorted(lookup.values(), key=lambda s: (s['timestamp'], s['session'])):
        if session['writer'] != target['writer'] or not session['end_at'] < target['timestamp']:
            continue
        for word in session['words']:
            if not word['is_word']:
                continue
            stamp = float(word['seconds'])
            if not session['timestamp'] / 1000. <= stamp <= session['end_at'] / 1000.:
                raise ValueError('Word clock outside authenticated session')
            count, last = result.get(word['token'], (0, -math.inf))
            result[word['token']] = (count + 1, max(last, stamp))
    return result
