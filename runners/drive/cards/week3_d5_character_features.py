"""D5 exact character n-gram preparation, before any identification scores.

DESIGN CHECK: LESSONS 3-5 reread 2026-10-29. Under NULL and ALTERNATIVE,
retain every source session, exact Unicode codepoints and every declared
length. No n-gram crosses a missing human-text span. Known-answer counts,
prefix boundaries and source seals must pass; short text stays unsupported.
This instrument chooses no vocabulary, writer classifier, bin or claim gate.
"""
from collections import Counter
from pathlib import Path
import math
import time

from runners.stage14.common import read, filehash, freeze, atomic, digest
from . import week3_d5_features as source
from .timing_text import TOKEN, WORD
from .timing_p6 import gzread, gzip_equal

ORDERS = (2, 3, 4)
CONFIG = dict(card='D5-character-features', schema=1, mode='full', sessions=1399, writers=61)
CONSTRUCTED = dict(CONFIG, mode='constructed', sessions=4, writers=2)


def word_count(groups):
    return sum(bool(WORD.fullmatch(m.group())) for text in groups for m in TOKEN.finditer(text))


def prefix_groups(groups, length):
    """Cut original codepoints at word N; never join across a provenance gap."""
    if type(length) is not int or length < 1:
        raise ValueError('Positive integer word length required')
    out = []; words = 0
    for text in groups:
        for match in TOKEN.finditer(text):
            words += bool(WORD.fullmatch(match.group()))
            if words == length:
                out.append(text[:match.end()])
                return out
        out.append(text)
    return None


def counts(groups):
    """Unnormalized, case-sensitive exact n-grams; no hash collisions or fit."""
    if not isinstance(groups, list) or any(not isinstance(t, str) for t in groups):
        raise ValueError('Explicit text groups required')
    result = {}; opportunities = {}
    for n in ORDERS:
        count = Counter(text[i:i+n] for text in groups for i in range(max(0, len(text)-n+1)))
        total = sum(max(0, len(text)-n+1) for text in groups)
        if sum(count.values()) != total:
            raise ValueError('Character opportunities differ')
        result[str(n)] = dict(sorted(count.items()))
        opportunities[str(n)] = total
    return dict(counts=result, opportunities=opportunities, words=word_count(groups),
                codepoints=sum(map(len, groups)), groups=len(groups))


def prepare(unit):
    groups = [g['text'] for g in unit['final_typed_groups']]
    final = counts([unit['final_document']]); human = counts(groups)
    prefixes = {}
    for length in source.LENGTHS:
        selected = prefix_groups(groups, length)
        prefixes[str(length)] = (dict(supported=False, required_words=length,
            available_words=human['words']) if selected is None else dict(supported=True, **counts(selected)))
    return dict(**{k:unit[k] for k in ('session', 'writer', 'prompt', 'timestamp', 'end_at',
                                      'model_share', 'model_share_missing_reason', 'codepoints_by_origin')},
                final=final, human=human, human_prefixes=prefixes,
                source_only=True, scientific_admission=False)


def load(inputs, config):
    if config not in (CONFIG, CONSTRUCTED):
        raise ValueError('Frozen character configuration required')
    old = source.CONFIG if config == CONFIG else source.CONSTRUCTED
    units, _, bindings = source.load(inputs, old)
    return units, bindings


def compute(output, inputs, config, verification=False):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    units, bindings = load(inputs, config)
    if (len(units) != config['sessions'] or len({u['session'] for u in units}) != len(units)
            or len({u['writer'] for u in units}) != config['writers']):
        raise ValueError('Complete source census differs')
    def retain(path, value):
        if verification:
            actual = gzread(path) if path.suffix == '.gz' else read(path)
            if actual != value: raise ValueError('Full character replay differs: '+path.name)
        elif path.suffix == '.gz': gzip_equal(path, value)
        else: freeze(path, value)
    retain(output/'BINDING.json', dict(config=config, inputs=bindings, orders=list(ORDERS),
        normalization='none; exact Unicode codepoints; case and whitespace preserved',
        human_boundaries='count separately inside each surviving human source group'))
    started = time.process_time(); index = []; support = Counter()
    for i, unit in enumerate(sorted(units, key=lambda u:u['session'])):
        if (output/'YIELD_REQUEST.json').exists() or (output.parent/'STOP').exists():
            if verification: raise InterruptedError('Character features yield at session boundary')
            return dict(status='yielded', source_only=True)
        value = prepare(unit); rel = 'sessions/'+digest(unit['session'])+'.json.gz'
        retain(output/rel, value)
        index.append(dict(session=unit['session'], writer=unit['writer'], file=rel, sha256=filehash(output/rel)))
        for n, p in value['human_prefixes'].items(): support[n] += int(p['supported'])
        if (i+1)%25 == 0:
            atomic(output/'PROGRESS.json', dict(phase='verify' if verification else 'execute', done=i+1, total=len(units)))
        if not verification and i+1 == math.ceil(.1*len(units)) and not (output/'FIRST_TENTH.json').exists():
            freeze(output/'FIRST_TENTH.json', dict(sessions=i+1,
                projected_cpu_seconds=max(.001, 4*(time.process_time()-started)*len(units)/(i+1)),
                scope='Both complete character passes times two; not identification cost'))
    retain(output/'FEATURE_INDEX.json', index)
    retain(output/'SUMMARY.json', dict(sessions=len(units), writers=config['writers'], all_sessions_retained=True,
        orders=list(ORDERS), prefix_supported_sessions=dict(sorted(support.items())),
        source_only=True, effect_computed=False, scientific_admission=False,
        scope='Exact final and human character counts with word-matched candidate prefixes; no fitted identification'))
    return dict(verified=True, full_fresh_character_replay=True, source_only=True) if verification else dict(status='complete', source_only=True)


def execute(output, inputs, config): return compute(output, inputs, config)
def verify(output, inputs, config): return compute(output, inputs, config, True)
