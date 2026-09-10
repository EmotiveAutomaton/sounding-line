"""Preparation-only canonical records and grouped, sealed allocation.

DESIGN CHECK: Stage 9 H02/X01/X02/X05; LESSONS extractor and grouping corrections.
NULL: labels/IDs in a primary view, cross-split lineages, or invented later versions
invalidate that view. ALTERNATIVE: exact released records reconcile and stay grouped.
Never imported by a reader. Preparation may see labels; inference never sees this store.
"""
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import re
import time
import unicodedata

from runners.stage9.common import ROOT, digest, file_hash, freeze, read, write

# The real HUMAN release also contains "others"; retain it in the complete support.
INTENTS = ('clarity', 'coherence', 'fluency', 'meaning-changed', 'others', 'style')


def normalized(text):
    return ' '.join(unicodedata.normalize('NFKC', text).casefold().split())


def paper_key(doc_id, domain):
    text = str(doc_id)
    modern = re.search(r'\b(\d{4}\.\d{4,5})(?:v\d+)?\b', text)
    if domain == 'arxiv' and modern:
        return 'arxiv:' + modern.group(1)
    return domain + ':' + text


def grouped_allocation(groups, exposed=(), seed=90619):
    """Exact 30% of eligible groups reserved before development/evaluation.

    Previously exposed groups go to discarded pilot, never a freshly named reserve.
    Remaining 70% is divided 50/20/30 into training/development/discovery. Caller must
    union document, duplicate and other dependent lineages before calling this function.
    """
    groups, exposed = set(groups), set(exposed)
    if not exposed <= groups:
        raise ValueError('exposure ledger contains unknown groups')
    eligible = sorted(groups - exposed, key=lambda k: digest([seed, k]))
    reserve_n = math.ceil(.30 * len(eligible))
    reserve, rest = eligible[:reserve_n], eligible[reserve_n:]
    train_n, dev_n = int(.50 * len(rest)), int(.20 * len(rest))
    allocation = {k: 'pilot' for k in exposed}
    allocation.update({k: 'reserve' for k in reserve})
    allocation.update({k: 'train' for k in rest[:train_n]})
    allocation.update({k: 'development' for k in rest[train_n:train_n + dev_n]})
    allocation.update({k: 'discovery' for k in rest[train_n + dev_n:]})
    return allocation


def jsonlines(path):
    with Path(path).open(encoding='utf-8') as source:
        for line_no, line in enumerate(source, 1):
            if len(line.encode('utf-8')) > 4 * 1024**2:
                raise ValueError('record outside frozen parser limit')
            if line.strip():
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError('record must be an object')
                yield line_no, row


def document_record(row, split, line_no, source_sha256):
    """Canonical released document row, shared by preparation and scoped audit."""
    required = {'doc_id', 'revision_depth', 'before_revision', 'after_revision', 'edit_actions', 'sents_char_pos'}
    if not isinstance(row, dict) or not required <= row.keys() or type(row['revision_depth']) is not int:
        raise ValueError('unrecognized HUMAN document schema')
    domain = row.get('domain', 'unknown')
    if not isinstance(domain, str) or any(not isinstance(row[k], str) for k in ('before_revision', 'after_revision')):
        raise ValueError('document text and domain must be strings')
    group = paper_key(row['doc_id'], domain)
    labels, votes, edits = [], [], []
    for edit in row['edit_actions']:
        if edit.get('major_intent') not in INTENTS or not isinstance(edit.get('raw_intents'), list) or any(v not in INTENTS for v in edit['raw_intents']):
            raise ValueError('missing or unrecognized human annotation; FULL cannot be substituted')
        if edit.get('type') not in ('A', 'D', 'R'):
            raise ValueError('invalid edit operation')
        labels.append(edit['major_intent'])
        votes.append(list(edit['raw_intents']))
        edits.append(dict(edit))
    return {'key': digest(['IteraTeR-HUMAN-doc', group, row['revision_depth'], split, line_no]),
            'source': 'IteraTeR-HUMAN-doc', 'group': group, 'domain': domain,
            'revision_depth': row['revision_depth'], 'published_split': split,
            'before': row['before_revision'], 'artifact': row['after_revision'],
            'labels': labels, 'raw_votes': votes, 'edits': edits,
            'source_file_sha256': source_sha256, 'source_line': line_no}


def iterater(root, sentence_root=None):
    """Load real HUMAN document JSONL, preserving every human vote and source offset.

    Exact source counts are a reproduction of the published inventory only. They do
    not reproduce the authors' model results. Sentence files are a count/schema check,
    never additional independent samples beside their source documents.
    """
    records, counts, exposed, source_files = [], {}, set(), {}
    missing_domain = 0
    for split in ('train', 'dev', 'test'):
        path = Path(root) / (split + '.json')
        source_files[path.name] = file_hash(path)
        rows = list(jsonlines(path))
        counts[split] = len(rows)
        for line_no, row in rows:
            record = document_record(row, split, line_no, source_files[path.name])
            if 'domain' not in row:
                missing_domain += 1
            if line_no == 1:
                exposed.add(record['group'])  # first schema records inspected during intake
            records.append(record)
    if counts != {'train': 481, 'dev': 27, 'test': 51}:
        raise ValueError('released document counts do not reconcile: ' + str(counts))
    sentence_counts = None
    if sentence_root:
        sentence_counts = {}
        for split in ('train', 'dev', 'test'):
            path = Path(sentence_root) / (split + '.json')
            source_files['sentence/' + path.name] = file_hash(path)
            count = 0
            for line_no, row in jsonlines(path):
                if not {'before_sent', 'after_sent', 'labels', 'doc_id', 'revision_depth'} <= row.keys() or 'confidence' in row:
                    raise ValueError('unrecognized HUMAN sentence schema')
                count += 1
                if line_no == 1:
                    for record in records:
                        if str(record['group']).split(':', 1)[-1] == str(row['doc_id']):
                            exposed.add(record['group'])
            sentence_counts[split] = count
        if sentence_counts != {'train': 3254, 'dev': 400, 'test': 364}:
            raise ValueError('released sentence counts do not reconcile: ' + str(sentence_counts))
    return records, {'published_document_counts': counts, 'published_sentence_counts': sentence_counts,
                     'source_files': source_files, 'exposed_schema_groups': sorted(exposed), 'missing_domain_records': missing_domain,
                     'published_numeric_reproduction': 'document and sentence counts only; no published model result reproduced'}


def union_duplicates(records):
    """Group exact normalized text duplicates with their full document lineages.

    Near-duplicate and cross-corpus audits remain separately required before lock.
    This does not silently claim those attacks are passed.
    """
    parent = {r['group']: r['group'] for r in records}
    def find(key):
        while parent[key] != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key
    seen, merges = {}, []
    for row in records:
        for field in ('before', 'artifact'):
            text = normalized(row[field])
            if not text:
                continue
            key = digest(text)
            if key in seen and find(seen[key]) != find(row['group']):
                a, b = sorted([find(seen[key]), find(row['group'])])
                parent[b] = a
                merges.append({'a': a, 'b': b, 'normalized_text_sha256': key})
            seen[key] = row['group']
    return {key: find(key) for key in parent}, merges


def prepare_iterater(materialized, output):
    started = time.monotonic()
    records, receipt = iterater(Path(materialized) / 'human_doc_level', Path(materialized) / 'human_sent_level')
    unions, merges = union_duplicates(records)
    exposed = {unions[g] for g in receipt['exposed_schema_groups']}
    splits = grouped_allocation(set(unions.values()), exposed)
    by_group = defaultdict(list)
    for row in records:
        row['independent_unit'] = unions[row['group']]
        row['split'] = splits[row['independent_unit']]
        by_group[row['group']].append(row)
    links, ambiguous = [], 0
    for rows in by_group.values():
        for current in rows:
            following = [r for r in rows if r['revision_depth'] == current['revision_depth'] + 1
                         and r['before'] == current['artifact']]
            if len(following) == 1:
                links.append({'current': current['key'], 'future': following[0]['key'], 'split': current['split']})
            elif len(following) > 1:
                ambiguous += 1
    identity = {'source': receipt['source_files'], 'preparation_sha256': file_hash(__file__),
                'allocation': splits, 'duplicates': merges, 'initial_schema_exposure': sorted(exposed),
                'view_contract': 'artifact is after_revision; process pair adds before_revision; labels, edits, IDs and future drafts remain evaluator-only',
                'sealed_reserve_fraction': .30, 'seed': 90619}
    output = Path(output)
    freeze(output / 'IDENTITY.json', identity)
    for split in ('pilot', 'train', 'development', 'discovery', 'reserve'):
        freeze(output / split / 'records.json', [r for r in records if r['split'] == split])
        freeze(output / split / 'future_links.json', [r for r in links if r['split'] == split])
    result = {**receipt, 'schema_valid': True, 'records': len(records), 'groups': len(splits),
              'group_counts': dict(Counter(splits.values())), 'record_counts': dict(Counter(r['split'] for r in records)),
              'verified_successive_revision_pairs': len(links), 'ambiguous_successors': ambiguous,
              'exact_duplicate_lineage_merges': len(merges), 'near_duplicate_audit': 'required before lock',
              'identity_sha256': digest(identity), 'wall_seconds': time.monotonic() - started,
              'ordinary_predictive_baseline': 'not yet run; schema passage alone does not grant readiness'}
    write(ROOT / 'intake/ITERATER_PREPARATION.json', result)
    return result


def visible_revision(record, view):
    """Explicit projection: never copy a prepared record and delete selected secrets."""
    if view == 'artifact':
        return {'text': record['artifact'], 'context': 'A revised text; predict human-assigned revision purposes.'}
    if view == 'process_pair':
        return {'before': record['before'], 'after': record['artifact'], 'context': 'A revision pair; predict human-assigned revision purposes.'}
    raise ValueError('unregistered revision view')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('materialized', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare_iterater(args.materialized, args.output), sort_keys=True))
