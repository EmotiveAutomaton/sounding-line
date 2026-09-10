"""Target-token matching without ever supervising learner-generated context.

DESIGN CHECK: C05/X01/X08. The original expert cell is byte-for-byte token replay.
Other cells retain source lineages and exactly its causal target-token budget and
example count. Context length and realized learner exposure are separate receipts.
NULL: absent targets, insufficient capacity or mislabeled context refuses a recipe.
ALTERNATIVE: only independently correct targets receive labels, to the exact budget.
"""
import copy
from collections import Counter
from fractions import Fraction

from runners.stage8.reader import logfmt as LF
from runners.stage9.common import digest


def target_positions(row):
    return [i for i, value in enumerate(row['labels']) if i > 0 and value != -100]


def replay_row(row):
    ids = list(row['input_ids'])
    return {'key': row['key'], 'input_ids': ids, 'labels': list(ids),
            'lineages': list(row['lineages']), 'kind': 'original_replay'}


def match_budget(rows, target_budget, fixed_keys=()):
    """Proportional, deterministic label masking; never add or alter an input token.

    Fixed replay examples stay exact. Other examples keep at least one causal
    target. Largest-remainder allocation and evenly spread target selection use
    only target counts and source hashes, never observed performance.
    """
    result = copy.deepcopy(rows)
    if len({r['key'] for r in rows}) != len(rows):
        raise ValueError('duplicate training example')
    fixed_keys = set(fixed_keys)
    if not fixed_keys <= {r['key'] for r in rows}:
        raise ValueError('unknown fixed example')
    positions = {r['key']: target_positions(r) for r in rows}
    for row in rows:
        if len(row['input_ids']) != len(row['labels']) or any(y not in (-100, x) for x, y in zip(row['input_ids'], row['labels'])):
            raise ValueError('target mask does not label its own input')
        if not positions[row['key']]:
            raise ValueError('training example has no causal targets')
    fixed = sum(len(positions[k]) for k in fixed_keys)
    flexible = [r['key'] for r in rows if r['key'] not in fixed_keys]
    remaining = target_budget - fixed
    capacities = {k: len(positions[k]) for k in flexible}
    if not len(flexible) <= remaining <= sum(capacities.values()):
        raise ValueError('target budget cannot be realized without changing fixed examples or inventing labels')
    extra = remaining - len(flexible)
    spare = sum(v-1 for v in capacities.values())
    quotas = {k: Fraction(extra*(capacities[k]-1), spare) if spare else Fraction(0) for k in flexible}
    counts = {k: 1 + int(quotas[k]) for k in flexible}
    ordered = sorted(flexible, key=lambda k: (-(quotas[k]-int(quotas[k])), digest(k)))
    for k in ordered[:remaining-sum(counts.values())]:
        counts[k] += 1
    for row in result:
        key = row['key']
        if key in fixed_keys:
            continue
        offered = positions[key]
        keep = {offered[(j*len(offered))//counts[key]] for j in range(counts[key])}
        row['labels'] = [v if i in keep else -100 for i, v in enumerate(row['labels'])]
    if sum(len(target_positions(r)) for r in result) != target_budget:
        raise AssertionError('target budget mismatch')
    return result


def mixture_keys(examples):
    """Exactly half in each domain, chosen before collection or performance."""
    by_domain = {}
    for row in examples:
        by_domain.setdefault(row['raw_record']['domain'], []).append(row['key'])
    if any(len(keys) % 2 for keys in by_domain.values()):
        raise ValueError('balanced assignment requires even domain counts')
    return {k for keys in by_domain.values() for k in sorted(keys, key=lambda k: digest({'mixture_assignment': k}))[:len(keys)//2]}


def earlier_context(row):
    raw = row['raw_record']
    if not raw['n_earlier']:
        return ''
    marker = LF.NOW + '\n'
    if raw['text'].count(marker) != 1:
        raise ValueError('ambiguous earlier-work boundary')
    return raw['text'].split(marker)[0] + marker


def learner_candidate(tok, source, collection, maximum_tokens=2048):
    if collection['lineage'] != source['key'] or collection['domain'] != source['raw_record']['domain']:
        raise ValueError('learner source mismatch')
    visited = [e for e in collection['examples'] if e['learner_actions_applied'] > 0 and e['targets']]
    if not visited:
        return replay_row(source) | {'kind': 'assigned_learner_unrealized', 'actual_learner_states': 0}
    # Four independent correct continuations at one actual visited state; choose
    # the state by source hash, never by which targets the model likes or how long.
    state = visited[int(digest({'matched_state': source['key']})[:12], 16) % len(visited)]
    ids, labels, spans = [], [], []
    for target in state['targets']:
        prefix_ids = tok(state['prefix'], add_special_tokens=True).input_ids
        target_ids = tok(target['target'] + tok.eos_token, add_special_tokens=False).input_ids
        if len(ids)+len(prefix_ids)+len(target_ids) > maximum_tokens:
            break  # Whole continuation only; exclusion remains in the receipt.
        start = len(ids)
        ids.extend(prefix_ids + target_ids)
        labels.extend([-100]*len(prefix_ids) + target_ids)
        spans.append({'context': [start, start+len(prefix_ids)], 'correct_target': [start+len(prefix_ids), len(ids)]})
    if not spans:
        raise ValueError('no complete learner continuation fits the explicit training cap')
    return {'key': source['key'], 'input_ids': ids, 'labels': labels, 'lineages': list(source['lineages']),
            'kind': 'learner_visited', 'actual_learner_states': state['learner_actions_applied'],
            'state_sha256': state['actual_state_sha256'], 'spans': spans,
            'complete_continuations_retained': len(spans), 'complete_continuations_excluded': len(state['targets'])-len(spans)}


def audit(cells, expected_lineages=None):
    summary = {}
    for name, rows in cells.items():
        lineages = sorted({k for r in rows for k in r['lineages']})
        if expected_lineages is not None and lineages != sorted(expected_lineages):
            raise ValueError('training source exposure differs')
        summary[name] = {'examples': len(rows), 'target_tokens': sum(len(target_positions(r)) for r in rows),
                         'input_tokens': sum(len(r['input_ids']) for r in rows),
                         'max_input_tokens': max(len(r['input_ids']) for r in rows),
                         'source_lineages': len(lineages), 'lineages_sha256': digest(lineages),
                         'kinds': dict(Counter(r['kind'] for r in rows)),
                         'target_mask_sha256': digest([r['labels'] for r in rows])}
    if len({r['examples'] for r in summary.values()}) != 1 or len({r['target_tokens'] for r in summary.values()}) != 1:
        raise ValueError('unmatched target counts or examples')
    if len({r['lineages_sha256'] for r in summary.values()}) != 1:
        raise ValueError('unmatched source exposure')
    return {'cells': summary, 'matched': ['causal target tokens', 'example count', 'source lineage set'],
            'not_claimed_equal': ['context token count', 'target positions/types', 'realized learner visits'],
            'original_replay_preservation_must_be_checked_against_source': True}
