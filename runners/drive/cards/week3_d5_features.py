"""D5 complete-source feature preparation; no identification or inference.

DESIGN CHECK: LESSONS 3-5 reread 2026-10-29. NULL and ALTERNATIVE retain
all source sessions. Wrong seals, identity, counts or invalid timing refuse.
Short text and missing timing remain unsupported, never fabricated zero data.
Known answers validate group boundaries, prefix lengths, denominators and
actual completed-producer integration before fresh native replay.
"""
from collections import Counter
from pathlib import Path
import math
import time
import unicodedata

from runners.stage14.common import read, filehash, freeze, atomic, digest
from . import week3_d5_inputs_h1_v2 as source
from .timing_pmap_source import completed, ACTIONS
from .timing_p6 import gzread, gzip_equal
from .timing_text import tokens, WORD
from .week3_fic1_features import style, rhythm

LENGTHS = (32, 64, 128, 256, 512, 1024)
CONFIG = dict(card='D5-features', schema=1, mode='full', sessions=1399, writers=61)
CONSTRUCTED = dict(CONFIG, mode='constructed', sessions=4, writers=2)


def count_tokens(sequence):
    words = Counter(t for t in sequence if WORD.fullmatch(t))
    punctuation = Counter(t for t in sequence if not WORD.fullmatch(t)
                          and all(unicodedata.category(c).startswith('P') for c in t))
    return dict(word_counts=dict(sorted(words.items())),
                punctuation_counts=dict(sorted(punctuation.items())))


def representation(sequence, dictionary):
    counts = count_tokens(sequence)
    return dict(**counts, words=sum(counts['word_counts'].values()),
                punctuation=sum(counts['punctuation_counts'].values()),
                features=style(counts['word_counts'], counts['punctuation_counts'], dictionary))


def prefix(sequence, length):
    result = []; words = 0
    for token in sequence:
        result.append(token)
        words += bool(WORD.fullmatch(token))
        if words == length:
            return result
    return None


def validate_dictionary(dictionary):
    for key in ('words', 'punctuation', 'character_bigrams'):
        values = dictionary[key]
        if not isinstance(values, list) or len(values) != len(set(values)) or any(
                not isinstance(x, str) or not x for x in values):
            raise ValueError('Invalid fixed dictionary')


def prepare(unit, dictionary):
    validate_dictionary(dictionary)
    p = unit['process']
    if any(p[k] != unit[k] for k in ('session', 'writer', 'prompt', 'timestamp')):
        raise ValueError('Source identity differs')
    typed = [t for group in unit['final_typed_groups'] for t in tokens(group['text'])]
    final = tokens(unit['final_document'])
    production = unit['production_tokens']
    wc = dict(sorted(Counter(r['token'] for r in production if r['is_word']).items()))
    pc = dict(sorted(Counter(r['token'] for r in production if not r['is_word'] and
                    all(unicodedata.category(c).startswith('P') for c in r['token'])).items()))
    if wc != p['word_counts'] or pc != p['punctuation_counts'] or sum(wc.values()) != p['typed_words']:
        raise ValueError('Production counts differ')
    handling = p['handling']
    if set(handling)-set(ACTIONS) or any(type(v) is not int or v < 0 for v in handling.values()):
        raise ValueError('Invalid canonical handling counts')
    timing = [p['within_intervals'], p['onset_intervals'], *p['bigram_intervals'].values()]
    if not isinstance(p['tc_timing_mode'], str) or not p['tc_timing_mode'] or any(
            not isinstance(v, list) or any(type(x) not in (int, float) or
            not math.isfinite(x) or x < 0 for x in v) for v in timing):
        raise ValueError('Invalid timing support')
    nh = sum(handling.values())
    prefixes = {}
    for length in LENGTHS:
        seq = prefix(typed, length)
        prefixes[str(length)] = (dict(supported=False, required_words=length,
                                     available_words=sum(bool(WORD.fullmatch(t)) for t in typed))
                                if seq is None else dict(supported=True, **representation(seq, dictionary)))
    return dict(**{k:unit[k] for k in ('session', 'writer', 'prompt', 'timestamp', 'end_at',
                                     'model_share', 'model_share_missing_reason', 'codepoints_by_origin')},
        final=representation(final, dictionary), human=representation(typed, dictionary),
        human_prefixes=prefixes,
        production=dict(word_counts=wc, punctuation_counts=pc, words=sum(wc.values()),
                        features=style(wc, pc, dictionary)),
        process=dict(handling=handling, selection=[handling.get(k, 0)/nh if nh else None for k in ACTIONS],
                     rhythm=rhythm(p, dictionary), tc_timing_mode=p['tc_timing_mode'],
                     within_intervals=p['within_intervals'], onset_intervals=p['onset_intervals'],
                     bigram_intervals=p['bigram_intervals']),
        source_only=True, scientific_admission=False)


def load(inputs, config):
    if config == CONSTRUCTED:
        if set(inputs) != {'fixture'}: raise ValueError('Constructed fixture required')
        f = read(inputs['fixture'])
        if not f.get('constructed'): raise ValueError('Explicit constructed scope required')
        return f['units'], f['dictionary'], {str(Path(inputs['fixture']).resolve()):filehash(inputs['fixture'])}
    if config != CONFIG or set(inputs) != {'source_complete', 'pmap_complete'}:
        raise ValueError('Complete feature predecessors required')
    bindings = {}
    def artifact(key, relative):
        terminal = Path(inputs[key]).resolve(); path = (terminal.parent/relative).resolve()
        path.relative_to(terminal.parent)
        completed(terminal, path)
        bindings[str(terminal)] = filehash(terminal); bindings[str(path)] = filehash(path)
        return gzread(path) if path.suffix == '.gz' else read(path)
    plan = artifact('source_complete', 'PLAN.json')
    if plan['module'] != 'runners.drive.cards.week3_d5_inputs_h1_v2' or plan['config'] != source.CONFIG:
        raise ValueError('Unexpected D5 predecessor')
    if Path(plan['inputs']['pmap_complete']).resolve() != Path(inputs['pmap_complete']).resolve():
        raise ValueError('D5 and dictionary PMAP differ')
    summary = artifact('source_complete', 'output/SUMMARY.json')
    if not summary['all_sessions_retained'] or not summary['final_typed_sequences_equal']:
        raise ValueError('Complete source coverage required')
    index = artifact('source_complete', 'output/SOURCE_UNITS.json'); rows = []
    for item in index:
        relative = 'output/'+item['file']; u = artifact('source_complete', relative)
        path = Path(inputs['source_complete']).resolve().parent/relative
        if filehash(path) != item['sha256'] or any(u[k] != item[k] for k in ('session','writer')):
            raise ValueError('Source index differs')
        rows.append(u)
    dictionary = artifact('pmap_complete', 'output/STYLE_DICTIONARY.json')
    return rows, dictionary, bindings


def compute(output, inputs, config, verification=False):
    if config not in (CONFIG, CONSTRUCTED): raise ValueError('Frozen feature configuration required')
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    units, dictionary, bindings = load(inputs, config)
    if len(units) != config['sessions'] or len({u['session'] for u in units}) != len(units) or len({u['writer'] for u in units}) != config['writers']:
        raise ValueError('Complete source census differs')
    def retain(path, value):
        if verification:
            actual = gzread(path) if path.suffix == '.gz' else read(path)
            if actual != value: raise ValueError('Complete feature replay differs: '+path.name)
        elif path.suffix == '.gz': gzip_equal(path, value)
        else: freeze(path, value)
    retain(output/'BINDING.json', dict(config=config, inputs=bindings))
    retain(output/'DICTIONARY.json', dictionary)
    started = time.process_time(); index = []; support = Counter(); timing = Counter()
    for i, unit in enumerate(sorted(units, key=lambda u:u['session'])):
        if (output/'YIELD_REQUEST.json').exists() or (output.parent/'STOP').exists():
            if verification: raise InterruptedError('D5 features yield at session boundary')
            return dict(status='yielded', source_only=True)
        value = prepare(unit, dictionary); rel = 'sessions/'+digest(unit['session'])+'.json.gz'
        retain(output/rel, value)
        index.append(dict(session=unit['session'], writer=unit['writer'], file=rel, sha256=filehash(output/rel)))
        timing[value['process']['tc_timing_mode']] += 1
        for n, p in value['human_prefixes'].items(): support[n] += int(p['supported'])
        if (i+1)%25 == 0: atomic(output/'PROGRESS.json', dict(phase='verify' if verification else 'execute', done=i+1, total=len(units)))
        if not verification and i+1 == math.ceil(.1*len(units)) and not (output/'FIRST_TENTH.json').exists():
            freeze(output/'FIRST_TENTH.json', dict(sessions=i+1, projected_cpu_seconds=max(.001,4*(time.process_time()-started)*len(units)/(i+1)), scope='Both complete feature passes times two; not identification cost'))
    retain(output/'FEATURE_INDEX.json', index)
    retain(output/'SUMMARY.json', dict(sessions=len(units), writers=config['writers'], all_sessions_retained=True,
        prefix_supported_sessions=dict(sorted(support.items())), timing_modes=dict(sorted(timing.items())),
        source_only=True, effect_computed=False, scientific_admission=False,
        scope='Full and fixed-prefix text counts and canonical process measurements; no fitted identification'))
    return dict(verified=True, full_fresh_feature_replay=True, source_only=True) if verification else dict(status='complete', source_only=True)


def execute(output, inputs, config): return compute(output, inputs, config)
def verify(output, inputs, config): return compute(output, inputs, config, True)
