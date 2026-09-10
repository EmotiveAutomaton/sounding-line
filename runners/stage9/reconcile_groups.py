"""Versioned duplicate-group repair; previous allocations and predictions stay intact.

DESIGN CHECK: H02/X01. A reserve merged with train/development/pilot becomes exposed.
An unexposed discovery alias may join its already-reserved source unit; no wholly new
group is promoted to reserve. Labels are copied mechanically, never used to allocate.
"""
from collections import Counter, defaultdict
import copy
import math

from runners.stage9.common import ROOT, digest, file_hash, freeze, read


def reconcile(allocation, edges):
    parent = {g:g for g in allocation}
    def find(g):
        while parent[g] != g:
            parent[g] = parent[parent[g]]
            g = parent[g]
        return g
    for edge in edges:
        left, right = edge['groups']
        if left not in parent or right not in parent:
            raise ValueError('duplicate edge names an unknown source group')
        a, b = find(left), find(right)
        if a != b:
            # Prefer an identified domain over an unknown prefix; original row domain
            # metadata is retained and not inferred from the canonical unit label.
            key = lambda g: (g.startswith('unknown:'), g)
            winner, loser = sorted((a,b), key=key)
            parent[loser] = winner
    mapping = {g:find(g) for g in parent}
    components = defaultdict(list)
    for old, new in mapping.items():
        components[new].append(old)
    priority = {'pilot': 0, 'train': 1, 'development': 2, 'reserve': 3, 'discovery': 4}
    updated = {g:min((allocation[x] for x in members), key=priority.get) for g, members in components.items()}
    for group, split in updated.items():
        old_splits = {allocation[x] for x in components[group]}
        if split == 'reserve' and ('reserve' not in old_splits or old_splits & {'pilot','train','development'}):
            raise ValueError('exposed or wholly new reserve promotion')
    return mapping, updated, dict(components)


def iterater():
    original = ROOT / 'private/prepared/iterater'
    output = ROOT / 'private/prepared/iterater-v2'
    old_identity = read(original / 'IDENTITY.json')
    audit_path = ROOT / 'private/prepared/iterater-duplicate-audit-v1.json'
    audit = read(audit_path)
    for path, sha in audit['input_files'].items():
        from runners.stage9.common import REPO
        if file_hash(REPO/path) != sha:
            raise ValueError('audited input source changed')
    mapping, allocation, components = reconcile(old_identity['allocation'], audit['edges'])
    records = [row for split in ('pilot','train','development','discovery','reserve') for row in read(original / split / 'records.json')]
    for row in records:
        previous = row['independent_unit']
        row['previous_independent_unit'] = previous
        row['previous_split'] = row['split']
        row['independent_unit'] = mapping[previous]
        row['split'] = allocation[row['independent_unit']]
    groups = defaultdict(list)
    for row in records:
        groups[row['independent_unit']].append(row)
    links, ambiguous = [], 0
    for rows in groups.values():
        for row in rows:
            following = [r for r in rows if r['revision_depth'] == row['revision_depth']+1 and r['before'] == row['artifact']]
            if len(following) == 1:
                links.append({'current': row['key'], 'future': following[0]['key'], 'split': row['split']})
            elif len(following) > 1:
                ambiguous += 1
    identity = {**old_identity, 'allocation': allocation, 'source_group_repair': {
                'parent_identity_sha256': digest(old_identity), 'duplicate_audit_sha256': file_hash(audit_path),
                'source_sha256': file_hash(__file__), 'old_to_new': mapping, 'components': components,
                'rule': 'exposed split takes precedence; reserve requires an existing unexposed reserved member; no fresh reserve replacements'}}
    freeze(output / 'IDENTITY.json', identity)
    for split in ('pilot','train','development','discovery','reserve'):
        freeze(output / split / 'records.json', [r for r in records if r['split'] == split])
        freeze(output / split / 'future_links.json', [r for r in links if r['split'] == split])
    counts = Counter(allocation.values())
    eligible = len(allocation) - counts['pilot']
    receipt = {'identity_sha256': digest(identity), 'old_groups': len(old_identity['allocation']), 'groups': len(allocation),
               'records': len(records), 'group_counts': dict(counts), 'record_counts': dict(Counter(r['split'] for r in records)),
               'reserve_target_after_grouping': math.ceil(.30*eligible), 'actual_reserve': counts['reserve'],
               'previous_reserve_groups_excluded_by_exposure': sum(old_identity['allocation'][g]=='reserve' and allocation[mapping[g]]!='reserve' for g in mapping),
               'wholly_new_reserve_groups': 0, 'verified_successive_links': len(links), 'ambiguous_successors': ambiguous,
               'old_predictions_preserved': True, 'scientific_split_accepted': False,
               'remaining': 'cross-source duplicate audit and baseline rerun on corrected groups'}
    freeze(ROOT / 'intake/ITERATER_GROUP_REPAIR.json', receipt)
    return receipt


if __name__ == '__main__':
    iterater()
