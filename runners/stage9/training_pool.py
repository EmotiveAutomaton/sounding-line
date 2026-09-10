"""Paired, parameter-separated 1600-maker candidate pools before token matching.

DESIGN CHECK: C05/C07/X01. Every linked earlier work obeys the training partition.
NULL: no held-out combination, source change or unmatched pool is silently trainable.
ALTERNATIVE: the original recipe is retained beside a paired both-law-family pool.
These candidate pools do not satisfy the learner-state matching or training-launch gate.
"""
import argparse
from collections import Counter
from pathlib import Path
import time

from runners.stage9.common import REPO, ROOT, closure, digest, freeze
from runners.stage9.recipes import eligible_training_pair, parameter_partition, POP
from runners.stage9.train import BASES


def prepare(family):
    from transformers import AutoTokenizer
    started = time.time()
    base = BASES[family]
    tok = AutoTokenizer.from_pretrained(base['model'], revision=base['revision'], local_files_only=True, trust_remote_code=False)
    rows = {'original': [], 'both': []}
    lineage_worlds = {'original': {}, 'both': {}}
    rejected, attempted, laws, partitions = Counter(), Counter(), {'original': Counter(), 'both': Counter()}, Counter()
    for domain in POP.DOMAINS:
        kept = 0
        for i in range(20000):
            attempted[domain] += 1
            allowed, pair, worlds = eligible_training_pair(i, domain, 10000000)
            if not allowed:
                rejected[domain] += 1
                for world in worlds['original']:
                    partitions[parameter_partition(world)] += 1
                continue
            for coverage in rows:
                row = pair[coverage]
                raw_ids = tok(row['text'] + tok.eos_token, add_special_tokens=True).input_ids
                # The exact historical replay comparator retains its explicit 1024 cap.
                # Both raw text and discarded-token count remain visible in preparation.
                ids = raw_ids[:1024] if coverage == 'original' else raw_ids
                rows[coverage].append({'key': row['lid'], 'input_ids': ids, 'lineages': row['lineages'],
                                       'raw_record': row, 'raw_tokens': len(raw_ids),
                                       'historical_tokens_discarded': len(raw_ids) - len(ids)})
                for world in worlds[coverage]:
                    if parameter_partition(world) != 'training':
                        raise ValueError('linked held-out combination reached the training pool')
                    lineage_worlds[coverage][world['lid']] = world
                laws[coverage][worlds[coverage][0]['state']['names']['law']] += 1
            kept += 1
            if kept == 800:
                break
        if kept != 800:
            raise ValueError('bounded search failed to realize 800 eligible maker examples in each domain')
    if [r['key'] for r in rows['original']] != [r['key'] for r in rows['both']]:
        raise ValueError('law coverage arms differ in parent lineage')
    sources = closure([REPO / 'runners/stage9/training_pool.py', REPO / 'runners/stage9/recipes.py',
                       REPO / 'runners/stage9/construction.py', REPO / 'runners/stage7/constructor',
                       REPO / 'runners/stage7/reader', REPO / 'runners/stage8/constructor',
                       REPO / 'runners/stage8/reader/logfmt.py', REPO / 'runners/stage8/engines.py'])
    identity = {'base': base, 'band': 10000000, 'sources': sources, 'examples_per_arm': 1600,
                'split_rule': 'same hashed parameter-combination partition for both role variants; all linked works must be training',
                'historical_original_cap': 1024, 'learner_state_or_token_match_complete': False}
    output = ROOT / 'private/training-pools' / family
    for coverage in rows:
        freeze(output / (coverage + '.json'), {'identity': identity, 'coverage': coverage,
                                               'candidate_examples': rows[coverage], 'private_worlds': lineage_worlds[coverage]})
    receipt = {'identity_sha256': digest(identity), 'family': family, 'attempted': dict(attempted), 'excluded': dict(rejected),
               'usable_per_arm': {k: len(v) for k, v in rows.items()}, 'law_counts': {k: dict(v) for k, v in laws.items()},
               'supervised_tokens_available': {k: sum(len(r['input_ids']) - 1 for r in v) for k, v in rows.items()},
               'historical_tokens_discarded': sum(r['historical_tokens_discarded'] for r in rows['original']),
               'distinct_exposed_lineages_per_arm': {k: len(v) for k, v in lineage_worlds.items()},
               'wall_seconds': time.time() - started, 'scientific_training_accepted': False,
               'next': 'actual learner-state collection and explicit target-token/exposure matching'}
    freeze(output / 'PREPARATION.json', receipt)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--family', choices=BASES, required=True)
    prepare(parser.parse_args().family)
