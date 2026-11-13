"""Portable hash-only correspondence support. Never reads labels or sends data.

The exact prefix length is an explicit input, not inferred from an old count.
Command-line use compares two already-produced fingerprint files locally.
"""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def text_hash(value):
    return sha_bytes(value.encode('utf8'))


def pan_fingerprint(raw, truth, source_key):
    # This is the original run_pan_winner.load_split paragraph convention.
    paragraphs = [p for p in raw.decode('utf8', errors='replace').split('\n') if p.strip()]
    count = len(truth['changes'])
    ok = len(paragraphs) == count + 1
    pairs = []
    if ok:
        for index in range(count):
            pair = [paragraphs[index].strip(), paragraphs[index + 1].strip()]
            canonical = json.dumps(pair, ensure_ascii=False, separators=(',', ':')).encode('utf8')
            legacy = '|P|'.join(pair).encode('utf8')
            pairs.append({'sha256': sha_bytes(canonical), 'legacy_md5': hashlib.md5(legacy).hexdigest()})
    return {'document_key_sha256': text_hash(source_key), 'raw_sha256': sha_bytes(raw),
            'paragraph_sha256': [text_hash(p.strip()) for p in paragraphs], 'pair_hashes': pairs,
            'valid_pair_alignment': ok, 'paragraphs': len(paragraphs), 'declared_pairs': count}


def pan_overlap(training, validation):
    all_training = {'document': {r['raw_sha256'] for r in training},
                    'paragraph': {h for r in training for h in r['paragraph_sha256']},
                    'pair': {h['sha256'] for r in training for h in r['pair_hashes']}}
    result = {}
    for name, hashes in (('document', [r['raw_sha256'] for r in validation]),
                         ('paragraph', [h for r in validation for h in r['paragraph_sha256']]),
                         ('pair', [h['sha256'] for r in validation for h in r['pair_hashes']])):
        shared = [value for value in hashes if value in all_training[name]]
        result[name] = {'validation_occurrences': len(hashes), 'shared_occurrences': len(shared),
                        'validation_unique': len(set(hashes)), 'shared_unique': len(set(shared)),
                        'shared_sha256': sorted(set(shared))}
    return result


def schola_fingerprint(row, split, ordinal, prefix_characters):
    if not isinstance(prefix_characters, int) or prefix_characters < 1:
        raise ValueError('Explicit positive Unicode-code-point prefix length required')
    text = row['before text']
    if not isinstance(text, str):
        raise ValueError('Original before-text column must contain strings')
    project = json.dumps(row['project'], ensure_ascii=False, sort_keys=True)
    return {'project_sha256': text_hash(project), 'split': split, 'row': ordinal,
            'before_sha256': text_hash(text), 'prefix_sha256': text_hash(text[:prefix_characters]),
            'characters': len(text), 'empty_prefix': not bool(text[:prefix_characters])}


def schola_tables(records, ordered_projects):
    projects = sorted({r['project_sha256'] for r in records})
    if sorted(ordered_projects) != projects or len(set(ordered_projects)) != len(ordered_projects):
        raise ValueError('Original sorted-project fold order is required exactly once')
    table, folds = [], []
    for fold, project in enumerate(ordered_projects):
        rr = [r for r in records if r['project_sha256'] == project]
        train = [r for r in rr if r['split'] == 'train']
        test = [r for r in rr if r['split'] == 'test']
        train_prefix = {r['prefix_sha256'] for r in train if not r['empty_prefix']}
        test_prefix = {r['prefix_sha256'] for r in test if not r['empty_prefix']}
        table.append({'project_sha256': project, 'train_rows': len(train), 'test_rows': len(test),
                      'unique_train_prefixes': len(train_prefix), 'unique_test_prefixes': len(test_prefix),
                      'shared_prefixes': len(train_prefix & test_prefix),
                      'empty_prefix_rows': sum(r['empty_prefix'] for r in rr),
                      'shared_prefix_sha256': sorted(train_prefix & test_prefix)})
        folds.append({'fold': fold, 'held_project_sha256': project,
                      'train_project_sha256': [p for p in ordered_projects if p != project],
                      'test_rows': len(rr), 'train_rows': len(records) - len(rr),
                      'source_splits': ['train', 'test'], 'rule': 'union shipped train and test; hold out entire project'})
    train = {r['prefix_sha256'] for r in records if r['split'] == 'train' and not r['empty_prefix']}
    test = {r['prefix_sha256'] for r in records if r['split'] == 'test' and not r['empty_prefix']}
    return {'per_project': table, 'folds': folds,
            'overall': {'rows': len(records), 'projects': len(projects), 'train_unique_prefixes': len(train),
                        'test_unique_prefixes': len(test), 'shared_unique_prefixes': len(train & test),
                        'empty_prefix_rows': sum(r['empty_prefix'] for r in records)}}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Local reproduction from hash-only PAN tables; no network or text input')
    parser.add_argument('training_hashes', type=Path); parser.add_argument('validation_hashes', type=Path)
    args = parser.parse_args()
    print(json.dumps(pan_overlap(json.loads(args.training_hashes.read_text('utf8')),
                                 json.loads(args.validation_hashes.read_text('utf8'))), indent=2))
