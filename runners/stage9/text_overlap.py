"""Exact, complete prefix-index search for preparation-only text overlaps.

DESIGN CHECK: LESSONS sections 3-5; Stage 9 I02/X01/X05. NULL: unrelated
texts do not acquire a copy edge, nor do short shared phrases imply a maker.
ALTERNATIVE: every exact copy and every pair passing the declared long-text
Jaccard/containment rule is retained. Retrieval is complete, not approximate.
All strings are data; no labels, fitting or reader predictions enter this module.
Bands: overlap under the fixed rule or no detected overlap, not proof of identity.
"""
from collections import Counter, defaultdict
import re
import unicodedata

from runners.stage9.common import digest

RULE = {
    'normalization': 'NFKC casefold Unicode words', 'shingle_words': 5,
    'minimum_words_for_near': 100, 'jaccard_minimum': .85,
    'containment_minimum': .95,
    'candidate_search': 'complete prefix index in increasing set size; global rare-first order',
    'proof': 'either threshold requires overlap >= ceil(.85*smaller_set_size); '
             'therefore at least one of its first size-ceil(.85*size)+1 shingles occurs in the larger set',
    'identity_limits': 'short exact collisions and shared stimuli are evidence reuse, not maker identity',
}


def words(text):
    if not isinstance(text, str):
        raise ValueError('text audit accepts strings only')
    return re.findall(r'\w+', unicodedata.normalize('NFKC', text).casefold())


class Overlaps:
    """Intern exact five-word tuples: no probabilistic hash for near matching."""
    def __init__(self):
        self.vocabulary = {}
        self.texts = []
        self.lookup = {}
        self.exact = defaultdict(list)
        self.frequency = Counter()
        self.inputs = 0

    def add(self, group, text, role='artifact'):
        if role not in {'artifact', 'local_fragment', 'shared_stimulus', 'candidate'}:
            raise ValueError('unregistered audit text role')
        self.inputs += 1
        tokens = words(text)
        if not tokens:
            return
        sha = digest(' '.join(tokens))
        key = (group, sha)
        if key in self.lookup:
            self.texts[self.lookup[key]]['roles'].add(role)
            return
        shingles = set()
        if len(tokens) >= RULE['minimum_words_for_near']:
            for i in range(len(tokens)-4):
                value = tuple(tokens[i:i+5])
                if value not in self.vocabulary:
                    self.vocabulary[value] = len(self.vocabulary)
                shingles.add(self.vocabulary[value])
        index = len(self.texts)
        self.lookup[key] = index
        self.exact[sha].append(index)
        self.texts.append({'group': group, 'exact': sha, 'word_count': len(tokens),
                           'roles': {role}, 'shingles': shingles})
        self.frequency.update(shingles)

    def run(self, progress=None):
        # Original text/shingles never go to the output. Exact short collisions are
        # compact buckets, not a quadratic clique spuriously joining whole people.
        collisions = []
        for sha, indices in sorted(self.exact.items()):
            if len(indices) > 1:
                collisions.append({'text_sha256': sha, 'word_count': self.texts[indices[0]]['word_count'],
                    'members': [{'group': self.texts[i]['group'], 'roles': sorted(self.texts[i]['roles'])}
                                for i in indices]})
        edges = {}
        examined = hits = 0
        index = defaultdict(list)
        order = sorted((i for i, t in enumerate(self.texts) if t['shingles']),
                       key=lambda i: (len(self.texts[i]['shingles']), self.texts[i]['exact'], self.texts[i]['group']))
        for ordinal, i in enumerate(order):
            a = self.texts[i]
            # The same pair of source groups needs only one witnessed overlap.
            # Keep role combinations separate: stimulus reuse must not hide a
            # later artifact overlap between those same groups.
            candidates = set()
            for shingle in a['shingles']:
                candidates.update(index.get(shingle, ()))
            hits += len(candidates)
            for j in sorted(candidates):
                b = self.texts[j]
                if a['group'] == b['group']:
                    continue
                groups = sorted([a['group'], b['group']])
                roles = tuple(sorted((tuple(sorted(a['roles'])), tuple(sorted(b['roles'])))))
                key = (tuple(groups), roles)
                if key in edges:
                    continue
                examined += 1
                common = len(a['shingles'] & b['shingles'])
                small = len(b['shingles'])
                union = len(a['shingles']) + small - common
                if 20*common >= 17*union or 20*common >= 19*small:
                    edges[key] = {'groups': groups, 'jaccard': common/union,
                                  'containment': common/small,
                                  'witnesses': [{'group': t['group'], 'text_sha256': t['exact'],
                                                 'roles': sorted(t['roles']), 'word_count': t['word_count']}
                                                for t in (a,b)]}
            prefix_n = len(a['shingles']) - (17*len(a['shingles'])+19)//20 + 1
            for shingle in sorted(a['shingles'], key=lambda s: (self.frequency[s], s))[:prefix_n]:
                index[shingle].append(i)
            if progress and (ordinal % 1000 == 0 or ordinal+1 == len(order)):
                progress({'processed_long_texts': ordinal+1, 'long_texts': len(order),
                          'verified_candidate_pairs': examined, 'overlap_group_role_pairs': len(edges)})
        return {'rule': RULE, 'input_text_occurrences': self.inputs, 'unique_texts_within_groups': len(self.texts),
                'long_texts': len(order), 'distinct_shingles': len(self.vocabulary),
                'candidate_hits_including_same_group': hits, 'verified_candidate_pairs': examined,
                'exact_collision_buckets': collisions, 'long_overlap_edges': list(edges.values()),
                'fingerprint_inventory': [{'group': t['group'], 'text_sha256': t['exact'],
                                           'word_count': t['word_count'], 'roles': sorted(t['roles'])}
                                          for t in self.texts]}
