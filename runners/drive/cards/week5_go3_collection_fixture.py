"""Constructed five-site producer-contract fixtures; no native-source claim.

DESIGN CHECK: complete, sparse and mutated source contracts must respectively
collect, retain the descriptive route, and refuse. No scientific fit is run.
Artificial COMPLETE envelopes below are explicitly fixture inputs only.
"""
from pathlib import Path
import argparse
import hashlib
import json
import pyarrow as pa
import pyarrow.parquet as pq
from . import week5_go3_collection as collection

core = collection.core


def key(value):
    return hashlib.sha256(('constructed-only:' + value).encode()).hexdigest()


def make_source(root, site, missing_category=False):
    root = Path(root)
    output = root / 'output'
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    labels = collection.source.PRIMARY[:-1] if missing_category else collection.source.PRIMARY
    for post in range(2):
        for user in range(45):
            for label_index, reason in enumerate(labels):
                rows.append(dict(editor=key(site + ':user:' + str(user)), post=key(site + ':post:' + str(post)),
                                 stamp=f'2024-01-01T00:{user:02d}:{label_index:02d}.000', site=site, type=5,
                                 reason=reason, self_edit=user % 2 == 0, owner_known=True,
                                 before='constructed preceding text', after='constructed following text'))
    rows.sort(key=lambda row: (row['post'], row['stamp']))
    pq.write_table(pa.Table.from_pylist(rows, schema=collection.producer.SCHEMA), output / 'edits.parquet')
    # This opaque construction is used only for hashing the producer envelope;
    # the collector never opens a producer's source database or raw archive.
    (output / 'projection.sqlite').write_bytes(b'constructed producer database envelope')
    binding = dict(site=site, archive_sha256=collection.source.ARCHIVES[site],
                   salt_sha256=key('shared-salt'), license_sha256=collection.source.LICENSE_SHA,
                   source_sha256=core.sha(collection.producer.__file__),
                   integrity_sha256=core.sha(collection.producer.integrity.__file__),
                   original_sha256=core.sha(collection.source.__file__))
    core.write(output / 'SNAPSHOT.json', dict(database_sha256=core.sha(output / 'projection.sqlite'),
               state=dict(binding=binding, projection_complete=True)))
    counts = dict(edit_type_5=len(rows), anonymous_edits_excluded=0, missing_before_excluded=0, unchanged_text_excluded=0)
    core.write(output / 'SOURCE.json', dict(site=site, archive_sha256=collection.source.ARCHIVES[site],
               source_only=True, retained_edits=len(rows), projection_sha256=core.sha(output / 'edits.parquet'),
               member_sha256={'Posts.xml': key('constructed-posts'), 'PostHistory.xml': key('constructed-history')}, counts=counts,
               constructed_only=True))
    core.write(root / 'PLAN.json', dict(module='runners.drive.cards.week5_go3_source_checkpointed',
               config={'site': site}, constructed_only=True))
    core.write(root / 'VERIFIED.json', dict(verified=True, complete_independent_source_replay=True,
               constructed_producer_envelope_only=True))
    files = {path.relative_to(root).as_posix(): core.sha(path) for path in root.rglob('*') if path.is_file()}
    core.write(root / 'COMPLETE.json', dict(status='COMPLETE', fresh_process_verified=True,
               constructed_producer_envelope_only=True, outputs=files))
    return dict(root=str(root.resolve()), complete_sha256=core.sha(root / 'COMPLETE.json'))


def prepare(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    for case in ('supported', 'missing-category'):
        roster = {site: make_source(root / case / site, site, case == 'missing-category') for site in collection.SITES}
        path = root / (case + '-roster.json')
        core.write(path, roster)
        core.write(root / (case + '-fixture.json'), dict(constructed_only=True, case=case,
                   roster_sha256=core.sha(path), rows=45 * 2 * (4 if case == 'missing-category' else 5) * 5))


def validate(inputs, config):
    if set(inputs) != {'roster', 'fixture_manifest'}:
        raise ValueError('Exact constructed collection fixture inputs required')
    fixture = collection.read(inputs['fixture_manifest'])
    if fixture.get('constructed_only') is not True or fixture['case'] != config['case']:
        raise ValueError('Constructed collection scope differs')
    if fixture['roster_sha256'] != core.sha(inputs['roster']):
        raise ValueError('Constructed collection roster changed')
    return fixture


def check_result(result, fixture):
    if result['rows'] != fixture['rows'] or result['sites'] != list(collection.SITES):
        raise ValueError('All five constructed sources were not collected')
    expected = fixture['case'] == 'supported'
    if any(row['user_disjoint_support'] != expected for row in result['classifier_support']):
        raise ValueError('Complete supported/descriptive routing differs')
    if not result['habit_structural_support']['fixed_gallery_structural_support']:
        raise ValueError('Known same-post donor coverage missing')
    if result.get('scientific_admission') is not False or result.get('no_fitting_performed') is not True:
        raise ValueError('Source collector improperly licensed a scientific fit')


def execute(output, inputs, config):
    fixture = validate(inputs, config)
    result = collection.execute(output, {'roster': inputs['roster']},
                                dict(phase='collect', max_wall_seconds=config.get('max_wall_seconds', 300)))
    if result.get('status') != 'yielded':
        check_result(result, fixture)
    return result


def verify(output, inputs, config):
    fixture = validate(inputs, config)
    result = collection.verify(output, {'roster': inputs['roster']},
                               dict(phase='collect', max_wall_seconds=config.get('max_wall_seconds', 300)))
    if result.get('status') != 'yielded':
        check_result(collection.read(Path(output) / 'SUPPORT.json'), fixture)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    prepare(parser.parse_args().output)
