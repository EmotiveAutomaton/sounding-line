"""Preparation-only exhaustive cross-lineage text-duplication audit, without labels.

DESIGN CHECK: H02/X01/X05. Hash exact text, modern arXiv aliases and five-word shingles.
NULL: unrelated text or within-lineage revision pairs must not create cross-source edges.
ALTERNATIVE: an exact copy or almost-contained long text is detected across split labels.
No model sees reserve text; this preparation audit outputs only fingerprints and counts.
It never reallocates or relabels a previously sealed reserve as fresh.
"""
from collections import Counter
import itertools
import re
import time
import unicodedata

from runners.stage9.common import ROOT, REPO, digest, file_hash, freeze, read

RULE = {'normalization': 'NFKC casefold Unicode words', 'shingle_words': 5,
        'minimum_words_for_near': 100, 'jaccard_minimum': .85, 'containment_minimum': .95,
        'candidate_search': 'exhaustive pairs of nonidentical source groups; no approximate retrieval'}


def fingerprint(text):
    words = re.findall(r'\w+', unicodedata.normalize('NFKC', text).casefold())
    normalized = ' '.join(words)
    return {'exact': digest(normalized) if words else None, 'word_count': len(words),
            'shingles': {tuple(words[i:i+5]) for i in range(max(0, len(words)-4))}}


def alias(group):
    match = re.search(r'(?<!\d)(\d{4}\.\d{4,5})(?:v\d+)?(?!\d)', group)
    return 'arxiv:' + match.group(1) if match else group


def audit(records):
    texts, group_splits = [], {}
    seen = set()
    for row in records:
        group = row['independent_unit']
        if group in group_splits and group_splits[group] != row['split']:
            raise ValueError('one declared independent group already spans splits')
        group_splits[group] = row['split']
        for view in ('before', 'artifact'):
            fp = fingerprint(row[view])
            if fp['exact'] is None or (group, fp['exact']) in seen:
                continue
            seen.add((group, fp['exact']))
            texts.append({'group': group, 'split': row['split'], 'key': row['key'], 'view': view, **fp})
    edges, examined = {}, 0
    groups = sorted(group_splits)
    for a, b in itertools.combinations(groups, 2):
        if alias(a) == alias(b):
            edges[(a,b)] = {'groups': [a,b], 'reason': 'same modern arXiv identity under different prefixes'}
    for a, b in itertools.combinations(texts, 2):
        if a['group'] == b['group']:
            continue
        examined += 1
        pair = tuple(sorted((a['group'], b['group'])))
        if pair in edges:
            continue
        reason = None
        if a['exact'] == b['exact']:
            reason, jac, contained = 'exact normalized text', 1., 1.
        elif min(a['word_count'], b['word_count']) >= RULE['minimum_words_for_near']:
            common = len(a['shingles'] & b['shingles'])
            jac = common / len(a['shingles'] | b['shingles'])
            contained = common / min(len(a['shingles']), len(b['shingles']))
            if jac >= RULE['jaccard_minimum'] or contained >= RULE['containment_minimum']:
                reason = 'near or contained long text'
        if reason:
            edges[pair] = {'groups': list(pair), 'reason': reason, 'jaccard': jac, 'containment': contained,
                           'text_hashes': [a['exact'], b['exact']], 'views': [a['view'], b['view']]}
    for edge in edges.values():
        edge['splits'] = [group_splits[g] for g in edge['groups']]
        edge['cross_split'] = len(set(edge['splits'])) > 1
    cross = [e for e in edges.values() if e['cross_split']]
    return {'rule': RULE, 'records': len(records), 'groups': len(groups), 'unique_texts_within_groups': len(texts),
            'cross_group_text_pairs_examined': examined, 'edges': list(edges.values()),
            'cross_split_edges': len(cross), 'reserve_groups_linked_to_other_splits': sorted({g for e in cross for g in e['groups'] if group_splits[g] == 'reserve'}),
            'scientific_split_accepted': not edges,
            'meaning': 'edges require grouping/exposure reconciliation before science; neither zero detected edges nor this rule proves all semantic independence'}


def iterater():
    started = time.time()
    root = ROOT / 'private/prepared/iterater'
    paths = [root / split / 'records.json' for split in ('pilot', 'train', 'development', 'discovery', 'reserve')]
    records = [row for path in paths for row in read(path)]
    # Explicitly project the audit inputs; labels, votes and edit metadata are unused.
    inputs = [{k: row[k] for k in ('key', 'independent_unit', 'split', 'before', 'artifact')} for row in records]
    result = {**audit(inputs), 'input_files': {str(p.relative_to(REPO)): file_hash(p) for p in paths},
              'source_sha256': file_hash(__file__), 'wall_seconds': time.time()-started,
              'scope': 'within newly acquired IteraTeR HUMAN; arXivEdits and older corpora still need cross-source integration'}
    freeze(ROOT / 'private/prepared/iterater-duplicate-audit-v1.json', result)
    public = {k:v for k,v in result.items() if k not in ('edges','reserve_groups_linked_to_other_splits')}
    public['detected_group_edges'] = len(result['edges'])
    public['reserve_groups_linked_to_other_splits'] = len(result['reserve_groups_linked_to_other_splits'])
    freeze(ROOT / 'intake/ITERATER_DUPLICATE_AUDIT.json', public)


if __name__ == '__main__':
    iterater()
