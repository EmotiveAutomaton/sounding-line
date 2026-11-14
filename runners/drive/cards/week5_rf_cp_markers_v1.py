"""Frozen two-day RF1/CP1 lexical instruments, no model or emotion classifier.

DESIGN CHECK: LESSONS sections 2--5. Literal hand answers precede corpus use.
Null/no listed terms => exactly zero; listed terms => exact non-overlapping counts.
Explicit negative RF phrases suppress their overlapping positive substring only.
Semantic correctness and >=3% coverage are separate, still-unrun human gates.
"""
import re
import unicodedata

VERSION = 'RF-CP-MARKERS-1'
RF = {
    'respect': {
        'for': ('experienced', 'competent', 'knowledgeable', 'capable', 'skilled', 'knows policy', 'good contributions'),
        'against': ('inexperienced', 'not enough experience', 'too few edits', 'lack of experience', 'clueless', "doesn't understand policy")},
    'trust': {
        'for': ('trust', 'trustworthy', 'honest', 'integrity', 'fair', 'sound judgment', 'good judgment', 'level-headed', 'responsible', 'mature'),
        'against': ("don't trust", 'untrustworthy', 'dishonest', 'poor judgment', 'immature', 'abuse the tools', 'power hungry', 'deceptive')},
    'liking': {
        'for': ('friendly', 'nice', 'pleasant', 'likeable', 'good guy', 'pleasure to work with', 'cheerful'),
        'against': ('rude', 'abrasive', 'hostile', 'unpleasant', 'unfriendly', 'uncivil', 'arrogant')}}
CP = {
    'warmth': ('thanks', 'thank you', 'appreciate', 'grateful', 'hi', 'hello', 'welcome', 'glad', 'great', 'nice', 'good work', 'good point', 'sorry', 'apologies'),
    'deference': ('perhaps', 'maybe', 'i think', 'i wonder', 'might', 'could you', 'would you', 'would it be', 'please', "if you don't mind", 'correct me'),
    'assertion': ('you need to', 'you should', 'you must', 'you have to', 'obviously', 'clearly', 'the fact is', 'you are wrong')}
COMMANDS = ('stop', 'read', 'see', 'look', 'do', "don't", 'remove', 'fix', 'add', 'check', 'leave', 'quit', 'use', 'provide', 'cite', 'explain')
TOKEN = re.compile(r"[^\W_]+(?:'[^\W_]+)*", re.UNICODE)


def normalize(text):
    if not isinstance(text, str):
        raise TypeError('Marker input must be text')
    return unicodedata.normalize('NFC', text).replace('\u2019', "'").replace('\u2018', "'").replace('\u2010', '-').replace('\u2011', '-').casefold()


def strip_quotes(text):
    # Do not discard Wikipedia colon/list indentation: that is ordinary speech.
    text = re.sub(r'<blockquote\b[^>]*>.*?</blockquote\s*>', '\n', text, flags=re.I | re.S)
    text = re.sub(r'<blockquote\b[^>]*>.*\Z', '\n', text, flags=re.I | re.S)
    return '\n'.join(line for line in text.splitlines() if not re.match(r'^\s*>', line))


def pattern(term):
    return re.compile(r'(?<!\w)' + r'\s+'.join(re.escape(x) for x in term.split()) + r'(?!\w)', re.UNICODE)


def nonoverlap(candidates):
    # Longest phrase first, then negative RF phrases, then stable lexical ties.
    selected = []
    for item in sorted(candidates, key=lambda x: (-(x['end']-x['start']), x['label'] != 'against', x['start'], x['term'])):
        if not any(item['start'] < old['end'] and old['start'] < item['end'] for old in selected):
            selected.append(item)
    return sorted(selected, key=lambda x: (x['start'], x['end'], x['term']))


def occurrences(text, labels):
    return nonoverlap([{'start': m.start(), 'end': m.end(), 'term': term, 'label': label}
        for label, terms in labels.items() for term in terms for m in pattern(term).finditer(text)])


def rf_counts(text):
    text = normalize(text)
    counts = {}
    for family, terms in RF.items():
        hits = occurrences(text, terms)
        counts[family] = {label: sum(h['label'] == label for h in hits) for label in ('for', 'against')}
    return {'tokens': len(TOKEN.findall(text)), 'counts': counts}


def cp_counts(text):
    text = normalize(strip_quotes(text))
    counts = {}
    for family, terms in CP.items():
        hits = occurrences(text, {'marker': terms})
        if family == 'assertion':
            for term in COMMANDS:
                command = re.compile(r'(?:^|[.!?]\s+|[\r\n]+)\s*[\"\x27(\[]*(?P<word>' + re.escape(term) + r')(?!\w)', re.UNICODE)
                for match in command.finditer(text):
                    # "Do you ...?" / "Don't you ...?" are not bare commands.
                    if term in ('do', "don't") and re.match(r'\s+(?:i|you|we|they|he|she|it)\b', text[match.end():]):
                        continue
                    hits.append({'start': match.start('word'), 'end': match.end('word'), 'term': term, 'label': 'marker'})
            hits = nonoverlap(hits)
        counts[family] = len(hits)
    n = len(TOKEN.findall(text))
    return {'tokens': n, 'counts': counts, 'per_100_tokens': {k: 100*v/n if n else None for k, v in counts.items()}}


def families(kind):
    if kind not in ('RF1', 'CP1'):
        raise ValueError('Unknown marker family')
    return tuple(RF if kind == 'RF1' else CP)


def presence(kind, result):
    return {k: (sum(result['counts'][k].values()) > 0 if kind == 'RF1' else result['counts'][k] > 0)
            for k in families(kind)}


def instrument_gate(summary, sample, annotations):
    """No partial correctness scores: every frozen sample item must be judged."""
    expected = {(x['family'], x['id']) for x in sample}
    if len(expected) != len(sample):
        raise ValueError('Duplicate frozen review item')
    labels = {}
    for row in annotations:
        key = (row['family'], row['id'])
        if key in labels or key not in expected:
            raise ValueError('Duplicate or non-sampled adjudication')
        if type(row.get('correct')) is not bool:
            raise ValueError('Manual review is incomplete')
        labels[key] = row['correct']
    if set(labels) != expected:
        raise ValueError('Manual review is incomplete')
    details = {}
    for family in families(summary['family']):
        keys = [key for key in expected if key[0] == family]
        correct = sum(labels[key] for key in keys)
        frequency = summary['family_hits'][family] / summary['records'] if summary['records'] else 0
        details[family] = {'reviewed': len(keys), 'correct': correct, 'frequency': frequency,
                           'pass': len(keys) == 100 and correct >= 80 and frequency >= .03}
    return {'schema': 'RF-CP-INSTRUMENT-1', 'family': summary['family'], 'details': details,
            'admitted': bool(summary['source_gate']) and all(x['pass'] for x in details.values()),
            'record_kind': 'run', 'by_construction': summary['by_construction'],
            'theory_tags': ['H15-T3' if summary['family'] == 'RF1' else 'H15-T4'],
            'not_a_scientific_card_result': True}
