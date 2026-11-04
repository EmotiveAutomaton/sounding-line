"""Support-only census for the packet's S5 gap and project textures.

DESIGN CHECK: LESSONS 3-5 reread 2026-11-02. NULL and ALTERNATIVE both retain
every released identity, ambiguous edges and long breaks. A six-author/30-start
known case must pass; five authors or 29 starts must refuse. Threshold equality,
long-break exclusion and project-scoped identities are checked before corpus
access. Support is neither an effect nor sensitivity; no primary is fitted.
"""
from collections import Counter, defaultdict
import json
from pathlib import Path
import time

from .week3_pp3_inputs import load, CONFIG as SOURCE_CONFIG, digest
from .week4_s5_h1 import extract
from .timing_census import read, filehash
from .timing_p6 import write_equal, gzip_equal, gzread


def configuration(mode):
    if mode not in ('constructed', 'full'):
        raise ValueError('Unknown support-census mode')
    return dict(card='S5-texture-support', mode=mode, gap_ceilings_seconds=[600, 3600],
                project_gap_ceiling_seconds=1800, minimum_starts=30, minimum_authors=6,
                expected_rows=366 if mode == 'constructed' else 61504,
                expected_projects=3 if mode == 'constructed' else 5,
                expected_authors=6 if mode == 'constructed' else 12,
                descriptive=True, descendants=False, seed=20261102)


def fixture(authors=6, starts=30):
    rows = []
    for a in range(authors):
        clock = 0
        for i in range(starts * 2 + 1):
            category = 'PLANNING' if i % 2 else 'IMPLEMENTATION'
            if i: clock += 900000 if i % 2 else 1000
            rows.append(dict(project=f'p{a // 2}', author=f'a{a}', timestamp=clock,
                             **{'high-level': category,
                                'label': 'Idea Generation' if i % 2 else 'Text Production',
                                'before text': 'a', 'after text': 'ab'}))
    return rows


def support(records):
    counts = defaultdict(Counter)
    for r in records:
        if not r['break_gap'] and r['high_start'] and r['log_relative_gap'] is not None:
            counts[r['author']][r['category']] += 1
    eligible = sorted(a for a, c in counts.items() if c['PLANNING'] >= 30 and c['IMPLEMENTATION'] > 0)
    return dict(qualifying_authors=len(eligible), required_authors=6, minimum_planning_starts=30,
                observed_author_ids=len({r['author'] for r in records}),
                eligible_intervals=sum(not r['break_gap'] for r in records),
                long_breaks=sum(r['break_gap'] for r in records),
                state='support passes; statistical admission pending' if len(eligible) >= 6 else 'design cannot test',
                scientific_effect_computed=False), {a: dict(c) for a, c in sorted(counts.items())}


def build(rows):
    projects = sorted({digest({'project': r['project']}) for r in rows})
    results, private, gaps, audits = {}, {}, {}, {}
    for ceiling in (600, 1800, 3600):
        records, audit = extract(rows, ceiling)
        gaps[str(ceiling)], audits[str(ceiling)] = records, audit
        if ceiling != 1800:
            key = f'gap-{ceiling // 60}-minutes'
            results[key], private[key] = support(records)
        else:
            for i, project in enumerate(projects):
                key = f'project-{i + 1}'
                results[key], private[key] = support([r for r in records if r['project'] == project])
    return dict(variants=results, audits=audits, source_rows=len(rows),
                source_projects=len(projects),
                source_project_scoped_authors=len({(r['project'], r['author']) for r in rows}),
                scientific_effect_computed=False, descriptive=True,
                scope='Declared gap limits and separate projects; original support floor retained.'), private, gaps, projects


def known_checks():
    summary, _, _, _ = build(fixture())
    assert summary['variants']['gap-10-minutes']['qualifying_authors'] == 0
    assert summary['variants']['gap-60-minutes']['qualifying_authors'] == 6
    assert all(summary['variants'][f'project-{i}']['qualifying_authors'] == 2 for i in (1, 2, 3))
    for authors, starts in ((5, 30), (6, 29)):
        records, _ = extract(fixture(authors, starts), 3600)
        assert support(records)[0]['state'] == 'design cannot test'
    return dict(known_support_and_refusal=True, gap_changes_case=True,
                project_partition=True, original_author_and_start_floors=True)


def run(output, inputs, config, verification=False):
    if config != configuration(config['mode']):
        raise ValueError('Frozen support configuration required')
    started = time.process_time()
    checks = known_checks()
    if config['mode'] == 'constructed':
        if inputs: raise ValueError('No human input in constructed census')
        rows = fixture()
    else:
        rows = load(inputs, SOURCE_CONFIG)
    summary, private, gaps, projects = build(rows)
    if (summary['source_rows'], summary['source_projects'], summary['source_project_scoped_authors']) != (
            config['expected_rows'], config['expected_projects'], config['expected_authors']):
        raise ValueError('Complete declared source population differs')
    summary.update(known_checks=checks, mode=config['mode'], input_sha256={k: filehash(v) for k, v in inputs.items()})
    values = {'SUMMARY.json': summary, 'PRIVATE_SUPPORT.json': private,
              'PRIVATE_PROJECTS.json': dict(projects=projects), 'CONFIG.json': config}
    output = Path(output)
    for name, value in values.items():
        if verification:
            if read(output / name) != json.loads(json.dumps(value)):
                raise ValueError('Complete support replay differs')
        else: write_equal(output / name, value)
    for key, rows in gaps.items():
        path = output / f'GAPS_{key}.json.gz'
        if verification:
            if gzread(path) != rows: raise ValueError('Complete gap replay differs')
        else: gzip_equal(path, rows)
    if not verification: write_equal(output / 'TIMING.json', dict(cpu_seconds=time.process_time() - started))
    return (dict(verified=True, complete_source_replay=True, support_only=True) if verification else
            dict(status='complete', scientific_admission=False))


def execute(output, inputs, config): return run(output, inputs, config)
def verify(output, inputs, config): return run(output, inputs, config, True)
